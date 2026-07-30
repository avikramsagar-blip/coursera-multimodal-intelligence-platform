from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
class UserUpdate(BaseModel):
    full_name: str
    email: str
    password: str
class UserLogin(BaseModel):
    email: str
    password: str