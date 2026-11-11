import os, io, csv, uuid, time, random, string, logging
from collections import defaultdict
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from .models import *
from .security import hash_pw, check_pw, make_token, current_user, teacher
from . import ai
from .kb import TAJ

log = logging.getLogger("eduvoyage")
UPLOADS = os.path.join(os.path.dirname(__file__), "..", "uploads"); os.makedirs(UPLOADS, exist_ok=True)

# ---------- helpers ----------
def award(db, user_id, trip_id, source, ref, pts):
    """The ONLY place points change. AI never calls this directly."""
    if db.query(PointEvent).filter_by(user_id=user_id, source=source, ref=ref).first(): return 0
    db.add(PointEvent(user_id=user_id, trip_id=trip_id, source=source, ref=ref, points=pts)); db.flush()
    check_badges(db, user_id); return pts

def check_badges(db, uid):
    have = {b.name for b in db.query(Badge).filter_by(user_id=uid)}
    xp = db.query(func.coalesce(func.sum(PointEvent.points), 0)).filter_by(user_id=uid).scalar()
    ok = {"Treasure Hunter": db.query(PointEvent).filter_by(user_id=uid, source="mission").count() >= 1,
          "Quiz Champion": any(s.score / max(s.total, 1) >= .8 for s in db.query(QuizSubmission).filter_by(user_id=uid)),
          "Curious Mind": db.query(Conversation).filter_by(user_id=uid, role="user").count() >= 5,
          "Team Player": db.query(GroupMember).filter_by(user_id=uid).count() >= 1,
          "History Explorer": xp >= 100, "Architecture Detective": db.query(PointEvent).filter_by(user_id=uid, source="mission").count() >= 3}
    for name, cond in ok.items():
        if cond and name not in have: db.add(Badge(user_id=uid, name=name))

def trip_access(db, user, trip_id) -> Trip:
    t = db.get(Trip, trip_id)
    if not t: raise HTTPException(404, "Trip not found.")
    if user.role == "teacher":
        if t.teacher_id != user.id: raise HTTPException(403, "Not your trip.")
    elif not (t.published and db.query(Enrollment).filter_by(trip_id=t.id, user_id=user.id).first()):
        raise HTTPException(403, "You have not joined this trip.")
    return t

def trip_dict(t): return {c.name: getattr(t, c.name) for c in Trip.__table__.columns}

_hits = defaultdict(list)
def rate_limit(uid, n=20, per=60):
    _hits[uid] = [x for x in _hits[uid] if time.time() - x < per]
    if len(_hits[uid]) >= n: raise HTTPException(429, "Slow down a little, the AI needs a breather.")
    _hits[uid].append(time.time())

# ---------- auth ----------
auth = APIRouter(prefix="/auth", tags=["auth"])
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80); email: EmailStr
    password: str = Field(min_length=8, max_length=100); role: str = Field(pattern="^(student|teacher)$")
    age: int = Field(default=14, ge=5, le=99); class_name: str = ""
class LoginIn(BaseModel): email: EmailStr; password: str
def user_out(u): return dict(id=u.id, name=u.name, email=u.email, role=u.role, age=u.age, class_name=u.class_name)

@auth.post("/register")
def register(d: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=d.email.lower()).first(): raise HTTPException(409, "Email already registered.")
    u = User(name=d.name, email=d.email.lower(), password_hash=hash_pw(d.password), role=d.role, age=d.age, class_name=d.class_name)
    db.add(u); db.commit(); return {"token": make_token(u), "user": user_out(u)}

@auth.post("/login")
def login(d: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=d.email.lower()).first()
    if not u or not check_pw(d.password, u.password_hash): raise HTTPException(401, "Wrong email or password.")
    return {"token": make_token(u), "user": user_out(u)}

@auth.get("/me")
def me(u: User = Depends(current_user)): return user_out(u)

# ---------- trips ----------
trips = APIRouter(prefix="/trips", tags=["trips"])
class TripIn(BaseModel):
    name: str = Field(min_length=3, max_length=120); destination: str = "taj_mahal"; trip_date: str = ""
    duration: str = ""; class_name: str = ""; age_group: str = ""; subjects: str = ""; objectives: str = ""
    shared_topics: List[str] = []

@trips.post("")
def create_trip(d: TripIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    t = Trip(**d.model_dump(), teacher_id=u.id, code=code); db.add(t); db.commit(); return trip_dict(t)

@trips.get("")
def list_trips(u: User = Depends(current_user), db: Session = Depends(get_db)):
    if u.role == "teacher": q = db.query(Trip).filter_by(teacher_id=u.id)
    else: q = db.query(Trip).join(Enrollment, Enrollment.trip_id == Trip.id).filter(Enrollment.user_id == u.id, Trip.published == True)
    out = []
    for t in q:
        d = trip_dict(t)
        if u.role != "teacher": d.pop("code")
        d["students"] = db.query(Enrollment).filter_by(trip_id=t.id).count(); out.append(d)
    return out

class JoinIn(BaseModel): code: str
@trips.post("/join")
def join_by_code(d: JoinIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    if u.role != "student": raise HTTPException(403, "Only students can join trips.")
    t = db.query(Trip).filter_by(code=d.code.strip().upper(), published=True).first()
    if not t: raise HTTPException(404, "Invalid or unpublished invitation code.")
    if not db.query(Enrollment).filter_by(trip_id=t.id, user_id=u.id).first(): db.add(Enrollment(trip_id=t.id, user_id=u.id)); db.commit()
    return {"trip_id": t.id, "name": t.name}

@trips.post("/{trip_id}/join")
def join(trip_id: int, d: JoinIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    t = db.get(Trip, trip_id)
    if not t or t.code != d.code.strip().upper() or not t.published: raise HTTPException(404, "Invalid invitation code.")
    return join_by_code(d, u, db)

@trips.get("/{trip_id}")
def get_trip(trip_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id); d = trip_dict(t)
    if u.role != "teacher": d.pop("code")
    return d

@trips.put("/{trip_id}")
def edit_trip(trip_id: int, d: TripIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id)
    for k, v in d.model_dump().items(): setattr(t, k, v)
    db.commit(); return trip_dict(t)

@trips.post("/{trip_id}/publish")
def publish(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id); t.published = True; db.commit(); return trip_dict(t)

@trips.delete("/{trip_id}")
def delete_trip(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id)
    if t.published: raise HTTPException(400, "Only unpublished trips can be deleted.")
    db.query(Enrollment).filter_by(trip_id=t.id).delete(); db.delete(t); db.commit(); return {"ok": True}

class StudentIn(BaseModel): email: EmailStr
@trips.post("/{trip_id}/students")
def add_student(trip_id: int, d: StudentIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id)
    s = db.query(User).filter_by(email=d.email.lower(), role="student").first()
    if not s: raise HTTPException(404, "No student account with that email.")
    if not db.query(Enrollment).filter_by(trip_id=t.id, user_id=s.id).first(): db.add(Enrollment(trip_id=t.id, user_id=s.id)); db.commit()
    return {"ok": True}

@trips.delete("/{trip_id}/students/{sid}")
def remove_student(trip_id: int, sid: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id); db.query(Enrollment).filter_by(trip_id=trip_id, user_id=sid).delete()
    db.query(GroupMember).filter(GroupMember.user_id == sid, GroupMember.group_id.in_(db.query(Group.id).filter_by(trip_id=trip_id))).delete(synchronize_session=False)
    db.commit(); return {"ok": True}

@trips.get("/{trip_id}/students")
def students(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id)
    return [dict(id=s.id, name=s.name, email=s.email) for s in db.query(User).join(Enrollment, Enrollment.user_id == User.id).filter(Enrollment.trip_id == trip_id)]

@trips.get("/{trip_id}/destination")
def destination(trip_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    t = trip_access(db, u, trip_id); secs = TAJ["sections"]
    if u.role != "teacher" and t.shared_topics: secs = {k: v for k, v in secs.items() if k in t.shared_topics}
    return {**{k: v for k, v in TAJ.items() if k != "sections"}, "sections": secs, "all_sections": list(TAJ["sections"])}

@trips.get("/{trip_id}/qr")
def qr(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    import qrcode
    t = trip_access(db, u, trip_id); buf = io.BytesIO(); qrcode.make(t.code).save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")

# ---------- groups ----------
groups = APIRouter(prefix="/groups", tags=["groups"])
class GroupIn(BaseModel): trip_id: int; name: str = Field(min_length=1, max_length=60); leader_id: Optional[int] = None
class MemberIn(BaseModel): user_id: int
def group_dict(db, g): return dict(id=g.id, trip_id=g.trip_id, name=g.name, leader_id=g.leader_id,
    members=[dict(id=m.user_id, name=db.get(User, m.user_id).name) for m in g.members])

@groups.post("")
def create_group(d: GroupIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, d.trip_id); g = Group(**d.model_dump()); db.add(g); db.commit(); return group_dict(db, g)

@groups.get("")
def list_groups(trip_id: Optional[int] = None, u: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Group)
    if trip_id: q = q.filter_by(trip_id=trip_id)
    if u.role == "teacher": q = q.filter(Group.trip_id.in_(db.query(Trip.id).filter_by(teacher_id=u.id)))
    else: q = q.filter(Group.id.in_(db.query(GroupMember.group_id).filter_by(user_id=u.id)))  # students see only their own groups
    return [group_dict(db, g) for g in q]

@groups.post("/{group_id}/members")
def add_member(group_id: int, d: MemberIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g: raise HTTPException(404, "Group not found.")
    trip_access(db, u, g.trip_id)
    if not db.query(Enrollment).filter_by(trip_id=g.trip_id, user_id=d.user_id).first(): raise HTTPException(400, "Student is not on this trip.")
    if not db.query(GroupMember).filter_by(group_id=g.id, user_id=d.user_id).first(): db.add(GroupMember(group_id=g.id, user_id=d.user_id)); db.commit()
    return group_dict(db, g)

# ---------- AI ----------
aiapi = APIRouter(prefix="/ai", tags=["ai"])
class ChatIn(BaseModel): message: str = Field(min_length=1, max_length=1000); trip_id: int; session_id: str = ""
class GenQuizIn(BaseModel):
    trip_id: int; subject: str = "History"; difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    count: int = Field(10, ge=10, le=30); kind: str = Field("practice", pattern="^(pre|post|practice)$"); minutes: int = Field(15, ge=5, le=90)
    group_id: Optional[int] = None
class GenHuntIn(BaseModel): trip_id: int; count: int = Field(3, ge=1, le=8); group_id: Optional[int] = None

@aiapi.post("/chat")
def ai_chat(d: ChatIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    t = trip_access(db, u, d.trip_id); rate_limit(u.id)
    sid = d.session_id or uuid.uuid4().hex[:12]
    hist = db.query(Conversation).filter_by(user_id=u.id, session_id=sid).order_by(Conversation.id).all()
    reply, srcs = ai.chat(d.message, hist, u, t)
    db.add_all([Conversation(user_id=u.id, trip_id=t.id, session_id=sid, role="user", content=d.message),
                Conversation(user_id=u.id, trip_id=t.id, session_id=sid, role="assistant", content=reply)])
    check_badges(db, u.id); db.commit()
    return {"reply": reply, "sources": srcs, "session_id": sid}

def save_quiz(db, d: GenQuizIn):
    qs = ai.generate_quiz(d.subject, d.difficulty, d.count)
    quiz = Quiz(trip_id=d.trip_id, title=f"{d.subject} quiz ({d.difficulty})", subject=d.subject, difficulty=d.difficulty, kind=d.kind, minutes=d.minutes, group_id=d.group_id)
    quiz.questions = [Question(qtype=q["qtype"], text=q["text"], options=q.get("options", []), answer=str(q["answer"]), explanation=q.get("explanation", ""), topic=q.get("topic", d.subject)) for q in qs]
    db.add(quiz); db.commit(); return quiz

@aiapi.post("/generate-quiz")
def gen_quiz(d: GenQuizIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, d.trip_id); rate_limit(u.id, 5); q = save_quiz(db, d); return {"quiz_id": q.id, "questions": len(q.questions)}

@aiapi.post("/generate-treasure-hunt")
def gen_hunt(d: GenHuntIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, d.trip_id); rate_limit(u.id, 5); n = db.query(Mission).filter_by(trip_id=d.trip_id).count()
    for i, m in enumerate(ai.generate_missions(d.count)):
        db.add(Mission(trip_id=d.trip_id, title=m["title"], task=m["task"], criteria=m["criteria"], hint=m.get("hint", ""),
                       points=int(m.get("points", 20)), difficulty=m.get("difficulty", "easy"), game=m.get("game", "treasure"), order=n + i, group_id=d.group_id))
    db.commit(); return {"ok": True}

# ---------- quizzes ----------
quizzes = APIRouter(prefix="/quizzes", tags=["quizzes"])
def quiz_access(db, u, qid):
    q = db.get(Quiz, qid)
    if not q: raise HTTPException(404, "Quiz not found.")
    trip_access(db, u, q.trip_id)
    if u.role == "student" and q.group_id and not db.query(GroupMember).filter_by(group_id=q.group_id, user_id=u.id).first():
        raise HTTPException(403, "This quiz is assigned to another group.")
    return q

@quizzes.get("")
def list_quizzes(trip_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id); mine = {s.quiz_id for s in db.query(QuizSubmission).filter_by(user_id=u.id)}
    mygroups = {m.group_id for m in db.query(GroupMember).filter_by(user_id=u.id)}
    return [dict(id=q.id, title=q.title, kind=q.kind, difficulty=q.difficulty, minutes=q.minutes, questions=len(q.questions), done=q.id in mine)
            for q in db.query(Quiz).filter_by(trip_id=trip_id) if u.role == "teacher" or not q.group_id or q.group_id in mygroups]

@quizzes.get("/{quiz_id}")
def get_quiz(quiz_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    q = quiz_access(db, u, quiz_id)   # answers are never sent here
    return dict(id=q.id, title=q.title, minutes=q.minutes, questions=[dict(id=x.id, type=x.qtype, text=x.text, options=x.options) for x in q.questions])

class SubmitIn(BaseModel): answers: Dict[str, str]; seconds: int = Field(0, ge=0)
def grade(q: Question, given: str):
    g, a = (given or "").strip().lower(), q.answer.strip().lower()
    return g == a if q.qtype != "short" else bool(g) and (g == a or a in g)

@quizzes.post("/{quiz_id}/submit")
def submit(quiz_id: int, d: SubmitIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    if u.role != "student": raise HTTPException(403, "Only students submit quizzes.")
    q = quiz_access(db, u, quiz_id)
    if db.query(QuizSubmission).filter_by(quiz_id=q.id, user_id=u.id).first(): raise HTTPException(400, "You already submitted this quiz.")
    detail, score = [], 0
    for x in q.questions:
        given = d.answers.get(str(x.id), ""); ok = grade(x, given); score += ok
        detail.append(dict(id=x.id, text=x.text, given=given, correct=ok, answer=x.answer, explanation=x.explanation, topic=x.topic))
    s = QuizSubmission(quiz_id=q.id, user_id=u.id, score=score, total=len(q.questions), seconds=d.seconds, detail=detail)
    db.add(s); db.flush(); award(db, u.id, q.trip_id, "quiz", q.id, score * 5); check_badges(db, u.id); db.commit()
    return quiz_result(s)

def quiz_result(s):
    wrong = sorted({x["topic"] for x in s.detail if not x["correct"]})
    return dict(submission_id=s.id, score=s.score, total=s.total, percent=round(100 * s.score / max(s.total, 1)), seconds=s.seconds, detail=s.detail, revise=wrong)

@quizzes.get("/{quiz_id}/results")
def results(quiz_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    q = quiz_access(db, u, quiz_id)
    if u.role == "student":
        s = db.query(QuizSubmission).filter_by(quiz_id=quiz_id, user_id=u.id).first()
        if not s: raise HTTPException(404, "Submit the quiz first.")
        return quiz_result(s)
    return [dict(student=db.get(User, s.user_id).name, score=s.score, total=s.total, seconds=s.seconds) for s in db.query(QuizSubmission).filter_by(quiz_id=quiz_id)]

# ---------- missions / treasure hunt ----------
missions = APIRouter(prefix="/missions", tags=["missions"])
class MissionIn(BaseModel):
    trip_id: int; title: str; task: str; criteria: str; hint: str = ""; points: int = Field(20, ge=1, le=100)
    difficulty: str = "easy"; game: str = "treasure"; group_id: Optional[int] = None
EXT = {"image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG"}; MAX = 5 * 1024 * 1024

@missions.get("")
def list_missions(trip_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id); out = []
    mygroups = {m.group_id for m in db.query(GroupMember).filter_by(user_id=u.id)}
    prev_done = True
    for m in db.query(Mission).filter_by(trip_id=trip_id).order_by(Mission.order, Mission.id):
        if u.role == "student" and m.group_id and m.group_id not in mygroups: continue
        subs = db.query(PhotoSubmission).filter_by(mission_id=m.id, user_id=u.id).order_by(PhotoSubmission.id.desc()).all()
        done = any(s.status in ("verified", "approved") for s in subs)
        locked = u.role == "student" and m.difficulty == "hard" and not prev_done and not done  # hard missions unlock after the previous one
        last = subs[0] if subs else None
        out.append(dict(id=m.id, title=m.title, task=m.task, hint=m.hint if not locked else "", points=m.points, difficulty=m.difficulty, game=m.game,
                        status="locked" if locked else ("completed" if done else "active"), last=last and dict(status=last.status, result=last.result, id=last.id), attempts=len(subs),
                        **({"criteria": m.criteria} if u.role == "teacher" else {})))
        prev_done = done
    return out

@missions.post("")
def create_mission(d: MissionIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, d.trip_id); m = Mission(**d.model_dump(), order=db.query(Mission).filter_by(trip_id=d.trip_id).count()); db.add(m); db.commit(); return {"id": m.id}

@missions.post("/{mission_id}/upload")
async def upload(mission_id: int, file: UploadFile = File(...), u: User = Depends(current_user), db: Session = Depends(get_db)):
    if u.role != "student": raise HTTPException(403, "Only students upload photos.")
    m = db.get(Mission, mission_id)
    if not m: raise HTTPException(404, "Mission not found.")
    trip_access(db, u, m.trip_id); rate_limit(u.id, 10)
    if db.query(PhotoSubmission).filter(PhotoSubmission.mission_id == m.id, PhotoSubmission.user_id == u.id, PhotoSubmission.status.in_(["verified", "approved"])).first():
        raise HTTPException(400, "You already completed this mission.")
    data = await file.read()
    if len(data) > MAX: raise HTTPException(413, "Image too large (max 5 MB).")
    mime = file.content_type
    if mime not in EXT or not data.startswith(EXT[mime]): raise HTTPException(400, "Please upload a real JPEG or PNG photo.")
    try:
        from PIL import Image; Image.open(io.BytesIO(data)).verify()
    except Exception: raise HTTPException(400, "That file is not a valid image.")
    name = uuid.uuid4().hex + (".png" if mime == "image/png" else ".jpg")
    open(os.path.join(UPLOADS, name), "wb").write(data)
    r = ai.verify_photo(m, data, mime)
    sub = PhotoSubmission(mission_id=m.id, user_id=u.id, path=name, status=r["status"], confidence=r.get("confidence"), result=r)
    db.add(sub); db.flush()
    r["points_awarded"] = award(db, u.id, m.trip_id, "mission", m.id, m.points) if r["status"] == "verified" else 0
    sub.result = dict(r); db.commit()
    return {"submission_id": sub.id, **r}

@missions.get("/{mission_id}/submissions")
def submissions(mission_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    m = db.get(Mission, mission_id)
    if not m: raise HTTPException(404, "Mission not found.")
    trip_access(db, u, m.trip_id); q = db.query(PhotoSubmission).filter_by(mission_id=m.id)
    if u.role == "student": q = q.filter_by(user_id=u.id)
    return [dict(id=s.id, student=db.get(User, s.user_id).name, status=s.status, confidence=s.confidence, result=s.result, created=str(s.created)) for s in q.order_by(PhotoSubmission.id.desc())]

@missions.get("/submissions/{sid}/image")
def image(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.get(PhotoSubmission, sid)
    if not s: raise HTTPException(404, "Not found.")
    m = db.get(Mission, s.mission_id)
    if not (s.user_id == u.id or (u.role == "teacher" and trip_access(db, u, m.trip_id))): raise HTTPException(403, "Not allowed.")
    return FileResponse(os.path.join(UPLOADS, s.path))

@missions.get("/review/pending")
def pending(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id)
    rows = db.query(PhotoSubmission).join(Mission, Mission.id == PhotoSubmission.mission_id).filter(Mission.trip_id == trip_id, PhotoSubmission.status == "needs_review")
    return [dict(id=s.id, student=db.get(User, s.user_id).name, mission=db.get(Mission, s.mission_id).title, result=s.result) for s in rows]

class ReviewIn(BaseModel): approve: bool
@missions.post("/submissions/{sid}/review")
def review(sid: int, d: ReviewIn, u: User = Depends(teacher), db: Session = Depends(get_db)):
    s = db.get(PhotoSubmission, sid)
    if not s: raise HTTPException(404, "Not found.")
    m = db.get(Mission, s.mission_id); trip_access(db, u, m.trip_id)
    if s.status != "needs_review": raise HTTPException(400, "Already reviewed.")
    s.status = "approved" if d.approve else "rejected"
    if d.approve: award(db, s.user_id, m.trip_id, "mission", m.id, m.points)
    db.commit(); return {"status": s.status}

# ---------- analytics / leaderboard ----------
analytics = APIRouter(tags=["analytics"])
def xp_of(db, uid, trip_id=None):
    q = db.query(func.coalesce(func.sum(PointEvent.points), 0)).filter_by(user_id=uid)
    return q.filter_by(trip_id=trip_id).scalar() if trip_id else q.scalar()

@analytics.get("/analytics/student")
def a_student(u: User = Depends(current_user), db: Session = Depends(get_db)):
    subs = db.query(QuizSubmission).filter_by(user_id=u.id).all()
    return dict(xp=xp_of(db, u.id), badges=[b.name for b in db.query(Badge).filter_by(user_id=u.id)],
                missions_done=db.query(PointEvent).filter_by(user_id=u.id, source="mission").count(),
                quizzes=[dict(quiz=db.get(Quiz, s.quiz_id).title, kind=db.get(Quiz, s.quiz_id).kind, percent=round(100 * s.score / s.total)) for s in subs],
                questions_asked=db.query(Conversation).filter_by(user_id=u.id, role="user").count())

@analytics.get("/analytics/trip/{trip_id}")
def a_trip(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id); rows = []
    mcount = db.query(Mission).filter_by(trip_id=trip_id).count()
    qids = {q.id: q.kind for q in db.query(Quiz).filter_by(trip_id=trip_id)}
    for s in db.query(User).join(Enrollment, Enrollment.user_id == User.id).filter(Enrollment.trip_id == trip_id):
        subs = db.query(QuizSubmission).filter(QuizSubmission.user_id == s.id, QuizSubmission.quiz_id.in_(qids or [0])).all()
        pct = lambda k: [100 * x.score / x.total for x in subs if qids[x.quiz_id] == k]
        avg = lambda l: round(sum(l) / len(l)) if l else None
        rows.append(dict(id=s.id, name=s.name, xp=xp_of(db, s.id, trip_id), missions=db.query(PointEvent).filter_by(user_id=s.id, trip_id=trip_id, source="mission").count(),
                         quiz_avg=avg([100 * x.score / x.total for x in subs]), pre=avg(pct("pre")), post=avg(pct("post")),
                         questions=db.query(Conversation).filter_by(user_id=s.id, trip_id=trip_id, role="user").count()))
    return dict(students=rows, mission_total=mcount)

@analytics.get("/analytics/trip/{trip_id}/report.csv")
def report(trip_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    data = a_trip(trip_id, u, db); buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Student", "XP", "Missions completed", "Quiz average %", "Pre-trip %", "Post-trip %", "AI questions"])
    for r in data["students"]: w.writerow([r["name"], r["xp"], r["missions"], r["quiz_avg"], r["pre"], r["post"], r["questions"]])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=trip_{trip_id}_report.csv"})

@analytics.get("/analytics/group/{group_id}")
def a_group(group_id: int, u: User = Depends(teacher), db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g: raise HTTPException(404, "Group not found.")
    trip_access(db, u, g.trip_id)
    return dict(name=g.name, xp=sum(xp_of(db, m.user_id, g.trip_id) for m in g.members), members=[dict(name=db.get(User, m.user_id).name, xp=xp_of(db, m.user_id, g.trip_id)) for m in g.members])

@analytics.get("/leaderboard")
def leaderboard(trip_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    trip_access(db, u, trip_id)
    ind = sorted([dict(name=s.name, xp=xp_of(db, s.id, trip_id)) for s in db.query(User).join(Enrollment, Enrollment.user_id == User.id).filter(Enrollment.trip_id == trip_id)], key=lambda r: -r["xp"])
    teams = sorted([dict(name=g.name, xp=sum(xp_of(db, m.user_id, trip_id) for m in g.members)) for g in db.query(Group).filter_by(trip_id=trip_id)], key=lambda r: -r["xp"])
    return dict(students=ind, teams=teams)

ALL = [auth, trips, groups, aiapi, quizzes, missions, analytics]
