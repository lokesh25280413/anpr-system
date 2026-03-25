from fastapi import APIRouter
from database import SessionLocal
from models import User
from auth import hash_password,verify_password

router = APIRouter()

@router.post("/signup")

def signup(email:str,password:str):

    db = SessionLocal()

    user = User(
        email=email,
        password=hash_password(password)
    )

    db.add(user)
    db.commit()

    return {"message":"User created"}


@router.post("/login")

def login(email:str,password:str):

    db = SessionLocal()

    user = db.query(User).filter(User.email==email).first()

    if not user:
        return {"error":"User not found"}

    if not verify_password(password,user.password):
        return {"error":"Wrong password"}

    return {"message":"Login successful"}