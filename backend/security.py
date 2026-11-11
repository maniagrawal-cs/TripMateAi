import os, hashlib, hmac, secrets, datetime as dt, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .models import get_db, User

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")
bearer = HTTPBearer(auto_error=False)

def hash_pw(pw: str) -> str:
    salt = secrets.token_hex(16)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200_000).hex()

def check_pw(pw: str, stored: str) -> bool:
    salt, h = stored.split("$")
    return hmac.compare_digest(h, hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200_000).hex())

def make_token(user: User) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(hours=12)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, SECRET, algorithm="HS256")

def current_user(cred=Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred: raise HTTPException(401, "Please log in.")
    try: uid = int(jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401, "Session expired. Please log in again.")
    user = db.get(User, uid)
    if not user: raise HTTPException(401, "Unknown user.")
    return user

def teacher(user: User = Depends(current_user)) -> User:
    if user.role != "teacher": raise HTTPException(403, "Teacher access only.")
    return user
