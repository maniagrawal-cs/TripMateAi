from .models import *
from .security import hash_pw
from .kb import MISSIONS, QUIZ_BANK

def seed():
    db = SessionLocal()
    if db.query(User).count(): db.close(); return
    t = User(name="Ms. Sharma", email="teacher@demo.com", password_hash=hash_pw("demo12345"), role="teacher")
    s1 = User(name="Aarav", email="aarav@demo.com", password_hash=hash_pw("demo12345"), role="student", age=13, class_name="8A")
    s2 = User(name="Diya", email="diya@demo.com", password_hash=hash_pw("demo12345"), role="student", age=13, class_name="8A")
    db.add_all([t, s1, s2]); db.flush()
    trip = Trip(teacher_id=t.id, name="Taj Mahal Discovery", destination="taj_mahal", trip_date="2026-12-12", duration="1 day", class_name="8A",
                age_group="12-14", subjects="History, Maths, Science", objectives="Understand Mughal architecture and symmetry", code="TAJ123", published=True, shared_topics=[])
    db.add(trip); db.flush()
    db.add_all([Enrollment(trip_id=trip.id, user_id=s1.id), Enrollment(trip_id=trip.id, user_id=s2.id)])
    g = Group(trip_id=trip.id, name="Marble Explorers", leader_id=s1.id); db.add(g); db.flush()
    db.add_all([GroupMember(group_id=g.id, user_id=s1.id), GroupMember(group_id=g.id, user_id=s2.id)])
    for i, m in enumerate(MISSIONS): db.add(Mission(trip_id=trip.id, order=i, **m))
    for kind in ("pre", "post"):
        q = Quiz(trip_id=trip.id, title=f"Taj Mahal {kind}-trip assessment", subject="History", difficulty="medium", kind=kind, minutes=15)
        q.questions = [Question(**x) for x in QUIZ_BANK]; db.add(q)
    db.commit(); db.close()
