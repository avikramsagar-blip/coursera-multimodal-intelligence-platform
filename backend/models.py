from sqlalchemy import Column, Integer, String, Text, BigInteger, ForeignKey, TIMESTAMP,DateTime,Float,Boolean
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

class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    thumbnail = Column(String, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.course_id"),
        nullable=False
    )

    progress = Column(Float, default=0)

    completed = Column(Boolean, default=False)

    enrolled_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class CourseVideo(Base):
    __tablename__ = "course_videos"

    video_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    video_url = Column(String, nullable=False)
    duration = Column(Integer)
    order_no = Column(Integer)
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

class CourseChatHistory(Base):
    __tablename__ = "course_chat_history"

    chat_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.course_id"),
        nullable=False
    )

    question = Column(Text, nullable=False)

    answer = Column(Text, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
class CourseMaterial(Base):
    __tablename__ = "course_materials"

    material_id = Column(Integer, primary_key=True, index=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.course_id"),
        nullable=False
    )

    file_name = Column(String, nullable=False)

    file_path = Column(String, nullable=False)

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )
