from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "student"


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    created_at: datetime
    role: str

    class Config:
        from_attributes = True
class UserUpdate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str
class UserLogin(BaseModel):
    email: str
    password: str