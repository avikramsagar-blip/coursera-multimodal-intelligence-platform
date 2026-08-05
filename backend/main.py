from security import hash_password
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
import os
from rag import search_chunks
from vector_store import create_vector_store
from sqlalchemy.orm import Session
from models import CourseChatHistory
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    CourseChatRequest,
    CourseChatResponse
)
from fastapi import UploadFile, File
from models import CourseMaterial
from schemas import CourseMaterialResponse
from models import User, Course, Enrollment,CourseVideo
from schemas import VideoCreate, VideoResponse
from text_splitter import split_text
from schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserLogin,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    ProgressUpdate
)
from security import (
    hash_password,
    verify_password,
    create_access_token
)
from pdf_utils import extract_pdf_text
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from security import verify_access_token
from models import Course
from database import engine, Base,get_db
Base.metadata.create_all(bind=engine)
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            model="gemini-3.6-flash",
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

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_password,
        role=user.role
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
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    

    email = verify_access_token(token)

    

    user = db.query(User).filter(User.email == email).first()

    

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user

def admin_required(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can access this resource"
        )

    return current_user
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
@app.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user
@app.get("/admin")
def admin_dashboard(
    current_user: User = Depends(admin_required)
):
    return {
        "message": "Welcome Admin",
        "user": current_user.full_name
    }
@app.post("/courses", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    new_course = Course(
        title=course.title,
        description=course.description,
        price=course.price,
        category=course.category,
        difficulty=course.difficulty,
        thumbnail=course.thumbnail,
        instructor_id=current_user.user_id
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course

@app.get("/courses", response_model=list[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):

    course = db.query(Course).filter(Course.course_id == course_id).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    return course

@app.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    updated_course: CourseUpdate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(Course.course_id == course_id).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    course.title = updated_course.title
    course.description = updated_course.description
    course.price = updated_course.price
    course.category = updated_course.category
    course.difficulty = updated_course.difficulty
    course.thumbnail = updated_course.thumbnail

    db.commit()
    db.refresh(course)

    return course

@app.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(Course.course_id == course_id).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    db.delete(course)
    db.commit()

    return {
        "message": "Course deleted successfully"
    }

@app.post("/enroll", response_model=EnrollmentResponse)
def enroll_course(
    enrollment: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == enrollment.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    existing = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.user_id,
        Enrollment.course_id == enrollment.course_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already enrolled"
        )

    new_enrollment = Enrollment(
        student_id=current_user.user_id,
        course_id=enrollment.course_id
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    return new_enrollment

@app.get("/my-courses", response_model=list[EnrollmentResponse])
def my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Enrollment).filter(
        Enrollment.student_id == current_user.user_id
    ).all()

@app.put("/progress/{course_id}", response_model=EnrollmentResponse)
def update_progress(
    course_id: int,
    progress: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.user_id,
        Enrollment.course_id == course_id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found"
        )

    enrollment.progress = progress.progress

    if progress.progress >= 100:
        enrollment.completed = True

    db.commit()
    db.refresh(enrollment)

    return enrollment

@app.post("/videos", response_model=VideoResponse)
def create_video(
    video: VideoCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == video.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    new_video = CourseVideo(
        course_id=video.course_id,
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        duration=video.duration,
        order_no=video.order_no
    )

    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return new_video

@app.get("/videos/{course_id}", response_model=list[VideoResponse])
def get_videos(
    course_id: int,
    db: Session = Depends(get_db)
):

    videos = db.query(CourseVideo).filter(
        CourseVideo.course_id == course_id
    ).order_by(CourseVideo.order_no).all()

    return videos

@app.put("/videos/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: int,
    video: VideoCreate,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    existing_video = db.query(CourseVideo).filter(
        CourseVideo.video_id == video_id
    ).first()

    if not existing_video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    existing_video.title = video.title
    existing_video.description = video.description
    existing_video.video_url = video.video_url
    existing_video.duration = video.duration
    existing_video.order_no = video.order_no

    db.commit()
    db.refresh(existing_video)

    return existing_video

@app.delete("/videos/{video_id}")
def delete_video(
    video_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    video = db.query(CourseVideo).filter(
        CourseVideo.video_id == video_id
    ).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    db.delete(video)
    db.commit()

    return {
        "message": "Video deleted successfully"
    }

@app.post("/course-chat", response_model=CourseChatResponse)
def course_chat(
    request: CourseChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Check course exists
    course = db.query(Course).filter(
        Course.course_id == request.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    # Ask Gemini
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=request.question
    )

    answer = response.text

    # Save chat
    chat = CourseChatHistory(
        user_id=current_user.user_id,
        course_id=request.course_id,
        question=request.question,
        answer=answer
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat

@app.post(
    "/upload-course-material",
    response_model=CourseMaterialResponse
)
def upload_course_material(
    course_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    import os

    os.makedirs("uploads", exist_ok=True)

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    material = CourseMaterial(
        course_id=course_id,
        file_name=file.filename,
        file_path=file_path
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return material

@app.get("/extract-text/{material_id}")
def extract_text(
    material_id: int,
    db: Session = Depends(get_db)
):

    material = db.query(CourseMaterial).filter(
        CourseMaterial.material_id == material_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=404,
            detail="Material not found"
        )

    text = extract_pdf_text(material.file_path)

    return {
        "text": text
    }

@app.get("/chunks/{material_id}")
def get_chunks(
    material_id: int,
    db: Session = Depends(get_db)
):

    material = db.query(CourseMaterial).filter(
        CourseMaterial.material_id == material_id
    ).first()

    if material is None:
        raise HTTPException(
            status_code=404,
            detail="Material not found"
        )

    text = extract_pdf_text(material.file_path)

    chunks = split_text(text)

    return {
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@app.post("/generate-vector-db/{course_id}")
def generate_vector_db(
    course_id: int,
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):

    material = db.query(CourseMaterial).filter(
        CourseMaterial.course_id == course_id
    ).first()

    if material is None:
        raise HTTPException(
            status_code=404,
            detail="Course material not found"
        )

    text = extract_pdf_text(material.file_path)

    chunks = split_text(text)

    folder = create_vector_store(
        chunks,
        course_id
    )

    return {
        "message": "Vector database created successfully",
        "chunks": len(chunks),
        "location": folder
    }
@app.post("/course-rag-chat")
def course_rag_chat(
    request: CourseChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # Step 1: Search relevant chunks from FAISS
    docs = search_chunks(
        request.course_id,
        request.question
    )

    print("=" * 60)
    print("Retrieved Chunks:", len(docs))

    for i, doc in enumerate(docs):
        print(f"\nChunk {i+1}:")
        print(doc.page_content[:1000])

    print("=" * 60)

    # Step 2: Create context
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    # Step 3: Prompt
    prompt = f"""
You are an AI Tutor.

Answer ONLY from the course material below.

If the answer is not present in the course material,
reply exactly:

I don't know from the course material.

Course Material:
{context}

Question:
{request.question}
"""

    # Step 4: Gemini
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    # Step 5: Save chat history
    chat = CourseChatHistory(
        user_id=current_user.user_id,
        course_id=request.course_id,
        question=request.question,
        answer=response.text
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "answer": response.text,
        "chunks_used": len(docs)
    }