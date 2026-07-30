from security import hash_password
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate, UserLogin
from security import (
    hash_password,
    verify_password,
    create_access_token
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from security import verify_access_token
security = HTTPBearer()
# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

# -----------------------------
# Gemini Client
# -----------------------------
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

# -----------------------------
# Request Model
# -----------------------------
class ChatRequest(BaseModel):
    message: str

# -----------------------------
# Home Route
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Welcome to Multimodal Intelligence Platform"
    }

# -----------------------------
# About Route
# -----------------------------
@app.get("/about")
def about():
    return {
        "project": "Multimodal Intelligence Platform",
        "developer": "Sumit Mishra"
    }

# -----------------------------
# Chat Route
# -----------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=request.message
        )

        return {
            "reply": response.text
        }

    except Exception as e:
        return {
            "error": str(e)
        }
@app.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)

    print("Original:", user.password)
    print("Hashed:", hashed_password)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.full_name = updated_user.full_name
    user.email = updated_user.email
    user.password = hash_password(updated_user.password)

    db.commit()
    db.refresh(user)

    return user
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
@app.post("/login")
def login(login: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == login.email).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(login.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
    data={"sub": user.email}
)
    return {
    "access_token": token,
    "token_type": "bearer"
}
@app.get("/profile")
def profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    email = verify_access_token(token)

    return {
        "message": "Access Granted",
        "email": email
    }
   
