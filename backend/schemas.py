from pydantic import BaseModel
from datetime import datetime

class CourseCreate(BaseModel):
    title: str
    description: str
    price: float
    category: str
    difficulty: str
    thumbnail: str | None = None

class CourseUpdate(BaseModel):
    title: str
    description: str
    price: float
    category: str
    difficulty: str
    thumbnail: str | None = None

class CourseResponse(BaseModel):
    course_id: int
    title: str
    description: str
    price: float
    category: str
    difficulty: str
    thumbnail: str | None
    instructor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


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

class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    enrollment_id: int
    student_id: int
    course_id: int
    progress: float
    completed: bool
    enrolled_at: datetime

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    progress: float

class VideoCreate(BaseModel):
    course_id: int
    title: str
    description: str | None = None
    video_url: str
    duration: int
    order_no: int


class VideoResponse(BaseModel):
    video_id: int
    course_id: int
    title: str
    description: str | None = None
    video_url: str
    duration: int
    order_no: int
    created_at: datetime

    class Config:
        from_attributes = True

class CourseChatRequest(BaseModel):
    course_id: int
    question: str


class CourseChatResponse(BaseModel):
    chat_id: int
    user_id: int
    course_id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True

class CourseMaterialResponse(BaseModel):
    material_id: int
    course_id: int
    file_name: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True