from sqlalchemy import Column, Integer, String, Text, BigInteger, ForeignKey, TIMESTAMP,DateTime
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="student")
    created_at = Column(DateTime, default=datetime.utcnow)

class AIModel(Base):
    __tablename__ = "ai_models"

    model_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    file_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger)
    file_path = Column(Text, nullable=False)
    status = Column(String(30), default="Uploaded")
    upload_time = Column(TIMESTAMP, server_default=func.now())


class ChatHistory(Base):
    __tablename__ = "chat_history"

    chat_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    model_id = Column(Integer, ForeignKey("ai_models.model_id"))
    prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())