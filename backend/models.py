import os, datetime as dt
from sqlalchemy import (create_engine, Column, Integer, String, Text, Float, Boolean,
                        DateTime, ForeignKey, JSON, UniqueConstraint)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./eduvoyage.db")  # swap for PostgreSQL later
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
now = lambda: dt.datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)          # minimal personal data
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(10), nullable=False)          # student | teacher
    age = Column(Integer, default=14)
    class_name = Column(String(40), default="")
    created = Column(DateTime, default=now)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(ForeignKey("users.id"))
    name = Column(String(120)); destination = Column(String(80), default="taj_mahal")
    trip_date = Column(String(20)); duration = Column(String(40))
    class_name = Column(String(40)); age_group = Column(String(20))
    subjects = Column(String(200)); objectives = Column(Text)
    code = Column(String(10), unique=True); published = Column(Boolean, default=False)
    shared_topics = Column(JSON, default=list)         # destination sections teacher selected
    lat = Column(Float, default=27.1751); lng = Column(Float, default=78.0421)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    trip_id = Column(ForeignKey("trips.id")); user_id = Column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("trip_id", "user_id"),)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    trip_id = Column(ForeignKey("trips.id")); name = Column(String(60))
    leader_id = Column(ForeignKey("users.id"), nullable=True)
    members = relationship("GroupMember", cascade="all,delete-orphan")

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey("groups.id")); user_id = Column(ForeignKey("users.id"))

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    trip_id = Column(ForeignKey("trips.id")); title = Column(String(120))
    subject = Column(String(40)); difficulty = Column(String(10)); kind = Column(String(10), default="practice")  # pre|post|practice
    minutes = Column(Integer, default=15); group_id = Column(ForeignKey("groups.id"), nullable=True)
    questions = relationship("Question", cascade="all,delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(ForeignKey("quizzes.id")); qtype = Column(String(10))  # mcq|tf|short
    text = Column(Text); options = Column(JSON, default=list)
    answer = Column(String(200)); explanation = Column(Text); topic = Column(String(60), default="")

class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(ForeignKey("quizzes.id")); user_id = Column(ForeignKey("users.id"))
    score = Column(Integer); total = Column(Integer); seconds = Column(Integer)
    detail = Column(JSON); created = Column(DateTime, default=now)

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True)
    trip_id = Column(ForeignKey("trips.id")); title = Column(String(80))
    task = Column(Text); criteria = Column(Text); hint = Column(Text)
    points = Column(Integer, default=20); difficulty = Column(String(10), default="easy")
    game = Column(String(20), default="treasure")   # treasure|find_feature|mystery|team
    order = Column(Integer, default=0); group_id = Column(ForeignKey("groups.id"), nullable=True)

class PhotoSubmission(Base):
    __tablename__ = "photo_submissions"
    id = Column(Integer, primary_key=True)
    mission_id = Column(ForeignKey("missions.id")); user_id = Column(ForeignKey("users.id"))
    path = Column(String(200)); status = Column(String(15))  # verified|try_again|needs_review|approved|rejected
    confidence = Column(Float, nullable=True); result = Column(JSON); created = Column(DateTime, default=now)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id")); trip_id = Column(Integer); session_id = Column(String(40))
    role = Column(String(10)); content = Column(Text); created = Column(DateTime, default=now)

class PointEvent(Base):
    __tablename__ = "points"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id")); trip_id = Column(Integer)
    source = Column(String(20)); ref = Column(Integer); points = Column(Integer); created = Column(DateTime, default=now)
    __table_args__ = (UniqueConstraint("user_id", "source", "ref"),)   # no double-awarding

class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id")); name = Column(String(40)); created = Column(DateTime, default=now)
    __table_args__ = (UniqueConstraint("user_id", "name"),)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
