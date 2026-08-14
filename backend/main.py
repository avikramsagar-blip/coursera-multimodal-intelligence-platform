from backend.security import hash_password
from fastapi import BackgroundTasks, FastAPI, Depends, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import time
import cloudinary
import cloudinary.uploader
import whisper
import yt_dlp
import uuid
import subprocess
import json
import traceback
import tempfile
from urllib.request import urlopen

from backend.rag import search_chunks
from backend.vector_store import create_vector_store
from backend.models import CourseChatHistory
from backend.metrics_utils import record_generation_metric
from backend.eval_api import evaluate_faithfulness, evaluate_retrieval_recall
from backend.schemas import (
    CourseChatRequest,
    CourseChatResponse
)
from backend.models import CourseMaterial
from backend.schemas import CourseMaterialResponse
from backend.video_transcription import transcribe_video
from backend.models import User, Course, Enrollment, CourseVideo, CourseMaterial, CourseAudio, CourseImage, VideoTranscript, VideoTranscriptSegment
from backend.schemas import VideoCreate, VideoResponse
from backend.text_splitter import split_text

from backend.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordChange,
    UserLogin,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    ProgressUpdate
)
from langchain_core.documents import Document
from backend.security import (
    hash_password,
    verify_password,
    create_access_token
)

from backend.pdf_utils import extract_pdf_text
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.security import verify_access_token, validate_jwt_secret
from backend.models import Course
from backend.database import DATABASE_URL, engine, Base, get_db, SessionLocal
from backend.storage_service import storage_service

Base.metadata.create_all(bind=engine)

security = HTTPBearer()

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
validate_jwt_secret()

# -----------------------------
# Gemini Client
# -----------------------------
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


# -----------------------------
# Cloudinary Configuration
# -----------------------------
cloudinary.config(
cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
api_key=os.getenv("CLOUDINARY_API_KEY"),
api_secret=os.getenv("CLOUDINARY_API_SECRET"),
secure=True
)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Multimodal Intelligence Platform", version="1.0.0")

# Include evidence traceability API
try:
    from backend.evidence_api import router as evidence_router
    app.include_router(evidence_router, prefix="/api")
except Exception as _e:
    print(f"evidence_api import failed: {_e}")

# Include metrics API
try:
    from backend.metrics_api import router as metrics_router
    app.include_router(metrics_router, prefix="/api")
except Exception as _e:
    print(f"metrics_api import failed: {_e}")

# Include admin API (role management, admin-only)
try:
    from backend.admin_api import router as admin_router
    app.include_router(admin_router, prefix="/api")
except Exception as _e:
    print(f"admin_api import failed: {_e}")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

cors_origins = [
origin.strip()
for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
if origin.strip()
]

app.add_middleware(
CORSMiddleware,
allow_origins=cors_origins,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


@app.middleware("http")
async def security_middleware(request, call_next):
    max_request_size = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "10485760"))
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > max_request_size:
                return JSONResponse(status_code=413, content={"detail": "Request too large."})
        except ValueError:
            pass

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# -----------------------------
# Startup Validation
# -----------------------------
@app.on_event("startup")
def startup_checks():
    import traceback
    print("=== STARTUP CHECKS ===")
    # Database connectivity
    try:
        # engine is imported earlier from backend.database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database: connected")
    except Exception as e:
        print("Database: connection failed")
        traceback.print_exc()

    # Create tables (idempotent)
    try:
        Base.metadata.create_all(bind=engine)
        print("Database: tables created/verified")
    except Exception as e:
        print("Database: failed to create/verify tables")
        traceback.print_exc()

    # Ensure upload directory exists
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        print(f"Upload directory: {UPLOAD_DIR} (exists)")
    except Exception as e:
        print(f"Upload directory: failed to create {UPLOAD_DIR}")
        traceback.print_exc()

    # Ensure faiss_indexes directory exists
    try:
        faiss_root = os.path.join(os.path.dirname(__file__), "faiss_indexes")
        os.makedirs(faiss_root, exist_ok=True)
        print(f"FAISS directory: {faiss_root} (exists)")
    except Exception as e:
        print("FAISS directory: failed to create")
        traceback.print_exc()

    # Gemini API key presence
    if os.getenv("GEMINI_API_KEY"):
        print("Gemini API Key: detected")
    else:
        print("Gemini API Key: NOT detected — RAG embedding/indexing may be disabled or limited")

    # ---------------------------------
    # Create demo user if missing
    # ---------------------------------
    try:
        db = SessionLocal()
        from backend.models import User
        from backend.security import hash_password

        # Replace single demo_email/demo creation with idempotent demo_users list
        demo_users = [
            {
                "email": "admin@test.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": "admin",
            },
            {
                "email": "test@test.com",
                "password": "test123",
                "full_name": "Demo User",
                "role": "student",
            },
        ]

        changed = False
        for item in demo_users:
            existing = db.query(User).filter(User.email == item["email"]).first()
            if existing:
                existing_role = (existing.role or "").lower()
                desired_role = (item["role"] or "").lower()
                if existing_role != desired_role:
                    existing.role = item["role"]
                    db.add(existing)
                    changed = True
                    print(f"Updated role for existing user {item['email']} -> {item['role']}")
                else:
                    print(f"Demo user already exists with correct role: {item['email']} ({existing.role})")
            else:
                new_user = User(
                    full_name=item["full_name"],
                    email=item["email"],
                password=hash_password(demo_password),
                role="admin"
            )
            db.add(demo_user)
            db.commit()
            print(f"Demo user created: {demo_email}")
    except Exception as _e:
        print(f"Warning: failed to create demo user: {_e}")
    finally:
        try:
            db.close()
        except Exception:
            pass

    print("=== END STARTUP CHECKS ===")

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


@app.get('/health')
def health():
    """Health endpoint reporting database, vector store, storage, and AI dependencies."""
    status = {
        "status": "healthy",
        "checks": {
            "database": {"status": "unknown"},
            "vector_store": {"status": "unknown"},
            "storage": {"status": "unknown"},
            "gemini": {"status": "unknown"},
        }
    }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["checks"]["database"] = {"status": "ok", "provider": "postgresql" if not str(DATABASE_URL).startswith("sqlite") else "sqlite"}
    except Exception as exc:
        status["checks"]["database"] = {"status": "error", "detail": str(exc)}
        status["status"] = "unhealthy"

    try:
        from backend.vector_store import client, _collection_name
        collection_name = _collection_name(1)
        status["checks"]["vector_store"] = {
            "status": "ok" if client is not None else "warn",
            "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "collection": collection_name,
        }
    except Exception as exc:
        status["checks"]["vector_store"] = {"status": "error", "detail": str(exc)}
        status["status"] = "unhealthy"

    try:
        storage_service.client
        status["checks"]["storage"] = {"status": "ok", "provider": os.getenv("OBJECT_STORAGE_PROVIDER", "s3")}
    except Exception as exc:
        status["checks"]["storage"] = {"status": "error", "detail": str(exc)}
        status["status"] = "unhealthy"

    if os.getenv("GEMINI_API_KEY"):
        status["checks"]["gemini"] = {"status": "ok", "provider": "google-gemini"}
    else:
        status["checks"]["gemini"] = {"status": "missing", "detail": "GEMINI_API_KEY not configured"}
        status["status"] = "degraded"

    return status


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

        start_ts = time.time()
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=request.message
        )
        latency_ms = (time.time() - start_ts) * 1000.0

        # Extract token usage if available
        try:
            from backend.metrics_utils import extract_token_usage
            tokens_in, tokens_out = extract_token_usage(response)
        except Exception:
            tokens_in, tokens_out = None, None

        # Record metric (best-effort)
        try:
            record_generation_metric(
                            model_name="gemini-3.6-flash",
                            raw_prompt=(request.message if hasattr(request, 'message') else None),
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency_ms=latency_ms,
                            success=True
            )
        except Exception:
            pass

        return {
            "reply": response.text
        }

    except Exception as e:

        # amazonq-ignore-next-line
        err = str(e)
        # Record failure metric
        try:
            record_generation_metric(
                model_name="gemini-3.6-flash",
                            raw_prompt=(request.message if hasattr(request, 'message') else None),
                latency_ms=None,
                success=False,
                error=err
            )
        except Exception:
            pass

        return {
            "error": str(e)
        }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    email = verify_access_token(token)

    user = db.query(User).filter(
        User.email == email
    ).first()

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


@app.get("/users", response_model=list[UserResponse])
def get_users(
    current_user: User = Depends(admin_required),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


@app.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

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
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

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

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.full_name = updated_user.full_name
    user.email = updated_user.email

    if updated_user.password:
        user.password = hash_password(updated_user.password)

    db.commit()
    db.refresh(user)

    return user

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }


@app.post("/login")
def login(
    login: UserLogin,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == login.email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        data={
            "sub": user.email
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.put("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(
        password_data.current_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 6 characters"
        )

    if verify_password(
        password_data.new_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    current_user.password = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
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


@app.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):

    return current_user


@app.get("/admin")
def admin_dashboard(
    current_user: User = Depends(get_current_user)
):

    return {
        "message": "Welcome Admin",
        "user": current_user.full_name
    }


@app.post("/courses", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    current_user: User = Depends(get_current_user),
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
def get_courses(
    db: Session = Depends(get_db)
):

    return db.query(Course).all()


@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

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
    current_user: User = Depends(get_current_user),
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


@app.get("/audios/{course_id}")
def get_audios(
    course_id: int,
    db: Session = Depends(get_db)
):
    audios = db.query(CourseAudio).filter(
        CourseAudio.course_id == course_id
    ).order_by(
        CourseAudio.order_no
    ).all()

    return audios

@app.get("/images/{course_id}")
def get_images(
    course_id: int,
    db: Session = Depends(get_db)
):
    images = db.query(CourseImage).filter(
        CourseImage.course_id == course_id
    ).order_by(
        CourseImage.order_no
    ).all()

    return images
def delete_course_audio(
    audio_id: int,
    db: Session = Depends(get_db)
):
    audio = db.query(CourseAudio).filter(
        CourseAudio.audio_id == audio_id
    ).first()

    if not audio:
        raise HTTPException(
            status_code=404,
            detail="Audio not found."
        )

@app.delete("/course-image/{image_id}")
def delete_course_image(
    image_id: int,
    db: Session = Depends(get_db)
):
    image = db.query(CourseImage).filter(
        CourseImage.image_id == image_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Image not found."
        )

    db.delete(image)
    db.commit()

    return {
        "message": "Course image deleted successfully."
    }

@app.get("/videos/{course_id}", response_model=list[VideoResponse])
def get_videos(
    course_id: int,
    db: Session = Depends(get_db)
):

    videos = db.query(CourseVideo).filter(
        CourseVideo.course_id == course_id
    ).order_by(
        CourseVideo.order_no
    ).all()

    return videos


@app.put("/videos/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: int,
    video: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    existing_video = db.query(
        CourseVideo
    ).filter(
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ---------------------------------
    # Find Video
    # ---------------------------------

    video = db.query(
        CourseVideo
    ).filter(
        CourseVideo.video_id == video_id
    ).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # ---------------------------------
    # Delete Transcript Segments
    # ---------------------------------

    db.query(
        VideoTranscriptSegment
    ).filter(
        VideoTranscriptSegment.video_id == video_id
    ).delete(
        synchronize_session=False
    )

    # ---------------------------------
    # Delete Full Transcript
    # ---------------------------------

    db.query(
        VideoTranscript
    ).filter(
        VideoTranscript.video_id == video_id
    ).delete(
        synchronize_session=False
    )

    # ---------------------------------
    # Delete Video File
    # ---------------------------------

    if video.video_url:

        filename = video.video_url.replace(
            "/uploads/videos/",
            ""
        )

        file_path = os.path.join(
            os.path.dirname(__file__),
            "uploads",
            "videos",
            filename
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    # ---------------------------------
    # Delete Video
    # ---------------------------------

    db.delete(video)
    db.commit()

    return {
        "message": "Video deleted successfully",
        "video_id": video_id
    }
@app.post("/course-chat", response_model=CourseChatResponse)
def course_chat(
    request: CourseChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.course_id == request.course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    start_ts = time.time()
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=request.question
        )
        latency_ms = (time.time() - start_ts) * 1000.0

        # Extract token usage if available
        try:
            from backend.metrics_utils import extract_token_usage
            tokens_in, tokens_out = extract_token_usage(response)
        except Exception:
            tokens_in, tokens_out = None, None

        # best-effort metric record
        try:
            record_generation_metric(
                            model_name="gemini-3.6-flash",
                            raw_prompt=(request.question if hasattr(request, 'question') else None),
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency_ms=latency_ms,
                            success=True
            )
        except Exception:
            pass

        answer = response.text

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

    except Exception as e:
        err = str(e)
        try:
            record_generation_metric(
                model_name="gemini-3.6-flash",
                            raw_prompt=(request.question if hasattr(request, 'question') else None),
                latency_ms=None,
                success=False,
                error=err
            )
        except Exception:
            pass
        raise


@app.post("/upload-course-material")
async def upload_course_material(
    course_id: int = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    print("UPLOAD START")
    print(f"course_id: {course_id}")
    try:
        print("files:", [f.filename for f in files])
        print("current_user:", getattr(current_user, 'email', str(current_user)))

        # ---------------------------------
        # Check Course
        # ---------------------------------

        course = db.query(Course).filter(
            Course.course_id == course_id
        ).first()

        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found"
            )

        # ---------------------------------
        # Create Upload Directory
        # ---------------------------------

        os.makedirs(
            UPLOAD_DIR,
            exist_ok=True
        )

        print("=== MULTI PDF UPLOAD DEBUG ===")
        print(f"UPLOAD_DIR: {UPLOAD_DIR}")
        print(
            f"Number of files received: "
            f"{len(files)}"
        )

        uploaded_files = []

        # ---------------------------------
        # Upload Each PDF
        # ---------------------------------

        for file in files:

            if not file.filename:
                continue

            # ---------------------------------
            # Validate PDF
            # ---------------------------------

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            if extension != ".pdf":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{file.filename} is not a PDF. "
                        "Only PDF files are allowed."
                    )
                )

            # ---------------------------------
            # Read File
            # ---------------------------------

            content = await file.read()

            print(
                f"Filename: {file.filename}"
            )

            print(
                f"Content length: "
                f"{len(content)}"
            )

            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{file.filename} is empty."
                    )
                )

            # ---------------------------------
            # Upload to object storage instead of local filesystem
            # ---------------------------------
            safe_name = file.filename
            object_key = f"course_{course_id}/materials/{uuid.uuid4().hex}_{safe_name}"
            remote_url = storage_service.upload_bytes(
                file_name=object_key,
                content=content,
                folder=f"course_{course_id}/materials",
                content_type="application/pdf",
            )

            print(f"Remote object URL: {remote_url}")

            # ---------------------------------
            # Save Database Record
            # ---------------------------------
            material = CourseMaterial(
                course_id=course_id,
                file_name=file.filename,
                file_path=remote_url
            )

            db.add(material)

            uploaded_files.append(
                file.filename
            )

        # ---------------------------------
        # Commit All Materials
        # ---------------------------------

        db.commit()

        print(
            f"Uploaded files: "
            f"{uploaded_files}"
        )

        print(
            "=== END MULTI PDF UPLOAD ==="
        )

        return {
            "message": (
                "Files uploaded successfully"
            ),
            "files": uploaded_files
        }

    except Exception as e:
        # Print traceback for debugging
        print("UPLOAD ERROR:")
        traceback.print_exc()
        # Return 500 with the error message
        raise HTTPException(status_code=500, detail=str(e))
def get_video_duration(file_path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        duration = float(
            data["format"]["duration"]
        )

        return int(round(duration))

    except Exception as e:
        print("=== FFPROBE DURATION ERROR ===")
        print(str(e))
        print("=== END FFPROBE ERROR ===")

        return None
def process_video_transcription(
    video_id,
    file_path
):
    print("========================================")
    print("=== BACKGROUND TRANSCRIPTION STARTED ===")
    print(f"Video ID: {video_id}")
    print(f"File: {file_path}")
    print("========================================")

    # Create an independent session owned entirely by this
    # background task. The request-scoped session is closed
    # by FastAPI before this task runs, so we must not reuse it.
    from backend.database import SessionLocal
    db = SessionLocal()

    try:
        transcription = transcribe_video(
            file_path
        )

        print("=== TRANSCRIPTION COMPLETED ===")
        print(
            f"Transcript length: "
            f"{len(transcription['text'])}"
        )

        # ---------------------------------
        # Save Full Transcript
        # ---------------------------------

        transcript = VideoTranscript(
            video_id=video_id,
            full_text=transcription["text"]
        )

        db.add(transcript)

        # ---------------------------------
        # Save Timestamped Segments
        # ---------------------------------

        segments = transcription["segments"]

        for segment in segments:

            transcript_segment = VideoTranscriptSegment(
                video_id=video_id,
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"]
            )

            db.add(transcript_segment)

        db.commit()

        print(
            f"Transcript segments saved: "
            f"{len(segments)}"
        )

        print("=== BACKGROUND TRANSCRIPTION COMPLETED ===")

    except Exception as e:

        print("=== BACKGROUND TRANSCRIPTION FAILED ===")
        print(str(e))

        db.rollback()

    finally:
        db.close()
@app.post("/upload-course-video")
async def upload_course_video(
    background_tasks: BackgroundTasks,
    course_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    order_no: int = Form(0),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ---------------------------------
    # Check Course
    # ---------------------------------

    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    # ---------------------------------
    # Validate File
    # ---------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Video file is required"
        )

    allowed_extensions = (
        ".mp4",
        ".webm",
        ".ogg",
        ".mov"
    )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid video format. "
                "Allowed formats: MP4, WEBM, OGG, MOV"
            )
        )

    # ---------------------------------
    # Persist a temp local copy for ffprobe/Whisper processing
    # ---------------------------------
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Video file is empty.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    unique_name = f"{uuid.uuid4().hex}{extension}"
    print("=== VIDEO UPLOAD DEBUG ===")
    print(f"Course ID: {course_id}")
    print(f"Original filename: {file.filename}")
    print(f"Saved filename: {unique_name}")
    print(f"Content length: {len(content)}")

    remote_url = storage_service.upload_bytes(
        file_name=unique_name,
        content=content,
        folder=f"course_{course_id}/videos",
        content_type="video/mp4" if extension == ".mp4" else "application/octet-stream",
    )

    video_url = remote_url
    print(f"Remote video URL: {video_url}")
    print("=== END VIDEO UPLOAD DEBUG ===")

    # ---------------------------------
    # Extract Video Duration
    # ---------------------------------

    print("=== VIDEO DURATION DETECTION ===")

    duration = get_video_duration(tmp_file_path)

    if duration is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine video duration."
        )

    print(
        f"Detected duration: {duration} seconds"
    )

    print("=== END VIDEO DURATION DETECTION ===")

    

    # ---------------------------------
    # Save Video Database Record
    # ---------------------------------

    new_video = CourseVideo(
        course_id=course_id,
        title=title,
        description=description,
        video_url=video_url,
        duration=duration,
        order_no=order_no
    )

    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    print("=== VIDEO DATABASE RECORD CREATED ===")
    print(f"Video ID: {new_video.video_id}")

    # ---------------------------------
    # Generate Transcript
    # ---------------------------------

        # ---------------------------------
    # Start Background Transcription
    # ---------------------------------

    background_tasks.add_task(
        process_video_transcription,
        new_video.video_id,
        tmp_file_path
    )

    print(
        "=== BACKGROUND TRANSCRIPTION QUEUED ==="
    )

    return {
        "message": "Video uploaded successfully",
        "video": new_video,
        "transcription": {
            "status": "processing"
        }
    }

    return {
        "message": "Video uploaded successfully",
        "video": new_video,
        "transcription": {
            "status": "completed"
        }
    }

@app.get("/course-materials/{course_id}", response_model=list[CourseMaterialResponse])
def get_course_materials(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return db.query(CourseMaterial).filter(
        CourseMaterial.course_id == course_id
    ).all()
@app.delete("/course-material/{material_id}")
def delete_course_material(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    material = db.query(CourseMaterial).filter(
        CourseMaterial.material_id == material_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=404,
            detail="Course material not found"
        )

    # Delete remote PDF object
    try:
        object_key = material.file_path.replace(str(os.getenv("AWS_S3_PUBLIC_URL", "")), "").lstrip("/")
        if object_key and object_key != material.file_path:
            storage_service.delete(object_key)
    except Exception:
        pass

    # Delete database record
    db.delete(material)
    db.commit()

    return {
        "message": "Course material deleted successfully"
    }



    

@app.post("/generate-vector-db/{course_id}")
def generate_vector_db(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ---------------------------------
    # Get Course PDFs
    # ---------------------------------

    materials = db.query(CourseMaterial).filter(
        CourseMaterial.course_id == course_id
    ).all()

    # ---------------------------------
    # Get Course Videos
    # ---------------------------------

    videos = db.query(CourseVideo).filter(
        CourseVideo.course_id == course_id
    ).all()

    if not materials and not videos:
        raise HTTPException(
            status_code=404,
            detail="No course materials or videos found"
        )

    all_documents = []

    print("=== GENERATE VECTOR DB DEBUG ===")

    # =================================
    # PROCESS PDF MATERIALS
    # =================================

    print(
        f"Total PDFs in DB for course {course_id}: "
        f"{len(materials)}"
    )

    for material in materials:

        file_path = material.file_path

        # Backward-compatible path resolution:
        # - Old records: file_path is a local filename → join with UPLOAD_DIR.
        # - New records: file_path is a remote object URL → download to a temp file.
        if str(file_path).startswith(("http://", "https://")):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                with urlopen(file_path) as response:
                    tmp_file.write(response.read())
                file_path = tmp_file.name
        elif not os.path.isabs(file_path):
            file_path = os.path.join(
                UPLOAD_DIR,
                file_path
            )

        print(
            f"Processing PDF: {file_path}"
        )

        print(
            f"File exists: "
            f"{os.path.exists(file_path)}"
        )

        pages = extract_pdf_text(
            file_path
        )

        print(
            f"Pages extracted: "
            f"{len(pages)}"
        )

        source_name = os.path.basename(
            file_path
        )

        documents = split_text(
            pages,
            source_name
        )

        print(
            f"PDF documents created: "
            f"{len(documents)}"
        )

        all_documents.extend(
            documents
        )

    # =================================
    # PROCESS VIDEO TRANSCRIPTS
    # =================================

    print(
        f"Total videos in DB for course {course_id}: "
        f"{len(videos)}"
    )

    for video in videos:

        transcript_segments = db.query(
            VideoTranscriptSegment
        ).filter(
            VideoTranscriptSegment.video_id
            == video.video_id
        ).order_by(
            VideoTranscriptSegment.start_time
        ).all()

        print(
            f"\nProcessing video: "
            f"{video.title}"
        )

        print(
            f"Video ID: "
            f"{video.video_id}"
        )

        print(
            f"Transcript segments: "
            f"{len(transcript_segments)}"
        )

        for segment in transcript_segments:

            if not segment.text.strip():
                continue

            document = Document(
                page_content=segment.text,
                metadata={
                    "source": "video",
                    "video_id": video.video_id,
                    "video_title": video.title,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "course_id": course_id
                }
            )

            all_documents.append(
                document
            )

    # =================================
    # FINAL DOCUMENT COUNT
    # =================================

    print(
        f"\nTotal documents across PDFs + videos: "
        f"{len(all_documents)}"
    )

    if not all_documents:

        raise HTTPException(
            status_code=400,
            detail="No searchable content found"
        )

    # =================================
    # CREATE FAISS VECTOR STORE
    # =================================

    folder = create_vector_store(
        all_documents,
        course_id
    )

    print(
        f"FAISS index saved to: {folder}"
    )

    print(
        "=== END GENERATE VECTOR DB DEBUG ==="
    )

    return {
        "message": (
            "Vector database created successfully"
        ),
        "total_files": len(materials),
        "total_videos": len(videos),
        "chunks": len(all_documents),
        "location": folder
    }

@app.post("/course-rag-chat")
def course_rag_chat(
    request: CourseChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ---------------------------------
    # Retrieve Previous Chat History
    # ---------------------------------
    previous_chats = db.query(
        CourseChatHistory
    ).filter(
        CourseChatHistory.user_id == current_user.user_id,
        CourseChatHistory.course_id == request.course_id
    ).order_by(
        CourseChatHistory.created_at.desc()
    ).limit(5).all()

    previous_chats.reverse()

    print("=== CHAT MEMORY DEBUG ===")
    print(
        f"Previous chats found: {len(previous_chats)}"
    )

    for chat in previous_chats:
        print(f"Q: {chat.question}")
        print(f"A: {chat.answer[:300]}")

    print("=== END CHAT MEMORY DEBUG ===")

    # ---------------------------------
    # Build Chat Memory Context
    # ---------------------------------
    memory_parts = []

    for chat in previous_chats:
        memory_parts.append(
            f"""
Previous User Question:
{chat.question}

Previous AI Answer:
{chat.answer}
"""
        )

    chat_memory = "\n\n".join(
        memory_parts
    )

    # ---------------------------------
    # Build Retrieval Query
    # ---------------------------------
    # Use only the current question for FAISS retrieval.
    # Concatenating previous questions pollutes the embedding
    # query and causes irrelevant chunks to rank higher.
    # Chat memory is still passed to Gemini in the prompt
    # so follow-up references ("it", "that", etc.) still work.
    retrieval_query = request.question

    print("=== RETRIEVAL QUERY DEBUG ===")
    print(retrieval_query)
    print("=== END RETRIEVAL QUERY DEBUG ===")

    # ---------------------------------
    # Create Retrieval Record (traceability)
    # ---------------------------------
    try:
        retrieval_rec = models.RetrievalRecord(
            query=retrieval_query,
            user_id=current_user.user_id,
            retriever="faiss_rerank",
            metadata_json=str({"course_id": request.course_id})
        )
        db.add(retrieval_rec)
        db.flush()
        retrieval_id = retrieval_rec.retrieval_id
    except Exception as e:
        db.rollback()
        print(f"Warning: failed to create retrieval record: {e}")
        retrieval_id = None

    # ---------------------------------
    # Retrieve RAG Chunks
    # ---------------------------------
    docs = search_chunks(
        request.course_id,
        retrieval_query
    )

    # ---------------------------------
    # Cheap keyword-overlap reranker
    # ---------------------------------
    # No extra API call. Tokenise the question and each chunk,
    # count shared content words, keep the top-N most relevant.
    # Video chunks are only kept when the question is clearly
    # video-related; otherwise they are deprioritised so
    # Gemini does not receive noisy transcript snippets for
    # PDF/concept questions.
    _STOP = {
        "a", "an", "the", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does",
        "did", "will", "would", "could", "should", "may",
        "might", "shall", "can", "to", "of", "in", "on",
        "at", "by", "for", "with", "about", "as", "into",
        "through", "and", "or", "but", "if", "so", "yet",
        "what", "how", "why", "when", "where", "which",
        "who", "whom", "this", "that", "these", "those",
        "it", "its", "i", "you", "he", "she", "we", "they",
        "me", "him", "her", "us", "them", "my", "your",
        "his", "our", "their", "not", "no", "from", "up",
        "out", "than", "then", "just", "also", "more",
    }

    _VIDEO_KEYWORDS = {
        "video", "watch", "lecture", "clip", "recording",
        "timestamp", "minute", "second", "spoken", "said",
        "mentioned", "talk", "talks",
        "discussed", "shown", "demonstrate", "demonstrates",
    }

    def _tokens(text):
        return {
            w for w in text.lower().split()
            if w.isalpha() and w not in _STOP
        }

    question_tokens = _tokens(request.question)
    is_video_question = bool(
        question_tokens & _VIDEO_KEYWORDS
    )

    def _score(doc):
        chunk_tokens = _tokens(doc.page_content)
        overlap = len(question_tokens & chunk_tokens)
        is_video_chunk = (
            doc.metadata.get("source") == "video"
        )
        # Penalise video chunks when the question is not
        # video-related so they rank below PDF chunks.
        if is_video_chunk and not is_video_question:
            overlap = overlap * 0.3
        return overlap

    scored = sorted(
        docs,
        key=_score,
        reverse=True
    )

    # Keep at most 5 chunks; always keep at least 1 so
    # Gemini has something to work with even on sparse matches.
    docs = scored[:5] if len(scored) >= 5 else scored

    print("=== RERANKER DEBUG ===")
    for i, doc in enumerate(docs):
        print(
            f"Rank {i+1} | "
            f"source={doc.metadata.get('source')} | "
            f"score={_score(doc):.2f} | "
            f"{doc.page_content[:80]}"
        )
    print("=== END RERANKER DEBUG ===")

    print("=" * 60)
    print("Retrieved Chunks:", len(docs))

    for i, doc in enumerate(docs):
        print(f"\nChunk {i + 1}:")
        print(doc.page_content[:1000])
        print("Metadata:", doc.metadata)

    print("=" * 60)

    # ---------------------------------
    # Get Course Videos
    # ---------------------------------
    videos = db.query(
        CourseVideo
    ).filter(
        CourseVideo.course_id == request.course_id
    ).order_by(
        CourseVideo.order_no
    ).all()

    # ---------------------------------
    # Build Video Metadata Context
    # ---------------------------------
    video_metadata = []

    for video in videos:
        duration_seconds = video.duration or 0
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60

        duration_formatted = (
            f"{minutes}:{seconds:02d}"
        )

        video_metadata.append(
            f"""
Video ID: {video.video_id}
Title: {video.title}
Description: {video.description or "No description"}
Runtime: {duration_formatted}
Runtime in seconds: {duration_seconds}
"""
        )

    video_context = "\n".join(
        video_metadata
    )

    # ---------------------------------
    # Build Retrieved Context
    # ---------------------------------
    context_parts = []

    for doc in docs:
        metadata = doc.metadata

        if metadata.get("source") == "video":
            start_time = metadata.get(
                "start_time",
                0
            )

            end_time = metadata.get(
                "end_time",
                0
            )

            video_title = metadata.get(
                "video_title",
                "Unknown video"
            )

            video_id = metadata.get(
                "video_id",
                "Unknown"
            )

            context_parts.append(
                f"""
[VIDEO TRANSCRIPT]
Video ID: {video_id}
Video Title: {video_title}
Timestamp: {start_time:.2f}s - {end_time:.2f}s

Transcript:
{doc.page_content}
"""
            )

        else:
            context_parts.append(
                f"""
[COURSE MATERIAL]
Source: {metadata.get("source", "Unknown")}
Page: {metadata.get("page", "Unknown")}
Chunk: {metadata.get("chunk", "Unknown")}

Content:
{doc.page_content}
"""
            )

    context = "\n\n".join(
        context_parts
    )

    # ---------------------------------
    # Debug
    # ---------------------------------
    print("=== VIDEO METADATA DEBUG ===")
    print(f"Videos found: {len(videos)}")
    print(video_context)
    print("=== END VIDEO METADATA DEBUG ===")

    print("=== CHAT MEMORY CONTEXT ===")
    print(chat_memory[:2000])
    print("=== END CHAT MEMORY CONTEXT ===")

    print("=== PROMPT DEBUG ===")
    print(
        f"Context length sent to Gemini: {len(context)} chars"
    )
    print(
        f"Context preview: {repr(context[:500])}"
    )
    print("=== END PROMPT DEBUG ===")

    # ---------------------------------
    # Prompt
    # ---------------------------------
    prompt = f"""
You are an AI Tutor for an online course.

You must answer ONLY using the provided course
materials, video transcripts, and video metadata.

There are TWO types of information available:

1. COURSE MATERIAL
   - PDF/document content
   - Page and chunk information

2. VIDEO INFORMATION
   - Video title
   - Description
   - Runtime
   - Timestamped transcript segments

IMPORTANT RULES:

- Every answer must include supporting citations.

- When using COURSE MATERIAL, cite:
  Source, Page and Chunk.

Example:
(Source: course_notes.pdf, Page: 12, Chunk: 4)

- When using VIDEO TRANSCRIPT, cite:
  Video Title and Timestamp.

Example:
(Video: Introduction to Python, Timestamp: 120s-145s)

- Include citations immediately after the statement they support.

- Never provide an answer without citations unless responding:
"I don't know from the course material."

- Use the PREVIOUS CONVERSATION only to understand
  references and follow-up questions such as
  "it", "this", "that", or "the above".

- Factual claims must be supported by the current
  retrieved course material, video transcripts,
  or video metadata.

- Use the PREVIOUS CONVERSATION only to understand
  references and follow-up questions such as
  "it", "this", "that", or "the above".

- Factual claims must be supported by the current
  retrieved course material, video transcripts,
  or video metadata.

- Do not treat a previous AI answer as independent
  factual evidence.

- If the question asks about video runtime, title,
  description, or other video metadata, use the
  VIDEO METADATA section.

- If the question asks about the content spoken
  in a video, use the VIDEO TRANSCRIPT sections.

- If the question asks about PDF/course material,
  use the COURSE MATERIAL sections.

- Do not invent information.

- If the answer cannot be found in the provided
  information, reply exactly:

I don't know from the course material.

PREVIOUS CONVERSATION:

{chat_memory}

VIDEO METADATA:

{video_context}

RETRIEVED COURSE CONTENT:

{context}

CURRENT QUESTION:

{request.question}
"""

    # ---------------------------------
    # Generate AI Response
    # ---------------------------------

    start_ts = time.time()
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        latency_ms = (time.time() - start_ts) * 1000.0

        # Create an Insight record and link evidence for traceability
        try:
            insight = models.Insight(
                title=(request.question[:200] if request.question else None),
                summary=response.text if hasattr(response, 'text') else str(response),
                generated_by_model_id=None,
                created_by=current_user.user_id
            )
            db.add(insight)
            db.flush()
            insight_id = insight.insight_id

            # Create Evidence records for each retrieved doc and link
            for doc in docs:
                md = doc.metadata if hasattr(doc, 'metadata') else {}
                ev = models.Evidence(
                    source_type=md.get('source', 'unknown'),
                    source_id=md.get('video_id') or md.get('source_id'),
                    segment_id=md.get('segment_id'),
                    start_time=md.get('start_time'),
                    end_time=md.get('end_time'),
                    snippet_text=(doc.page_content[:4000] if hasattr(doc, 'page_content') else None),
                    source_uri=None,
                    embedding_id=md.get('embedding_id'),
                    metadata=str(md)
                )
                db.add(ev)
                db.flush()

                link = models.InsightEvidence(
                    insight_id=insight_id,
                    evidence_id=ev.evidence_id,
                    retrieval_id=retrieval_id,
                    score=None
                )
                db.add(link)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Warning: failed to create insight/evidence links: {e}")
            insight_id = None

        # Extract token usage if available
        try:
            from backend.metrics_utils import extract_token_usage
            tokens_in, tokens_out = extract_token_usage(response)
        except Exception:
            tokens_in, tokens_out = None, None

        # record metric (with retrieval_id and insight_id)
        try:
            record_generation_metric(
                            model_name="gemini-3.6-flash",
                            raw_prompt=(prompt if prompt is not None else None),
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency_ms=latency_ms,
                            success=True,
                            retrieval_id=retrieval_id,
                            insight_id=insight_id
            )
        except Exception:
            pass

    except Exception as e:

        error_message = str(e)

        print("=== GEMINI ERROR ===")
        print(error_message)
        print("=== END GEMINI ERROR ===")

        try:
            record_generation_metric(
                model_name="gemini-3.6-flash",
                            raw_prompt=(prompt if prompt is not None else None),
                latency_ms=None,
                success=False,
                error=error_message,
                retrieval_id=retrieval_id,
            )
        except Exception:
            pass

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "quota" in error_message.lower()
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please try again after the quota resets."
                )
            )

        raise HTTPException(
            status_code=503,
            detail=(
                "AI service is temporarily "
                "unavailable. Please try again."
            )
        )

    # ---------------------------------
    # Evaluate answer (Faithfulness & Retrieval Recall) using Gemini as judge
    # ---------------------------------
    try:
        # Retrieval recall judge: pass the retrieved docs and question
        retrieval_eval = evaluate_retrieval_recall(docs, request.question)
        if not isinstance(retrieval_eval, dict):
            retrieval_eval = {"score": None, "reason": "Evaluation unavailable"}
    except Exception:
        retrieval_eval = {"score": None, "reason": "Evaluation unavailable"}

    try:
        # Faithfulness judge: pass the generated answer and the retrieved context string
        faith_eval = evaluate_faithfulness(response.text, context, request.question)
        if not isinstance(faith_eval, dict):
            faith_eval = {"score": None, "reason": "Evaluation unavailable"}
    except Exception:
        faith_eval = {"score": None, "reason": "Evaluation unavailable"}

    evaluation = {
        "retrieval_recall": {
            "score": retrieval_eval.get("score") if retrieval_eval else None,
            "reason": retrieval_eval.get("reason") if retrieval_eval else "Evaluation unavailable"
        },
        "faithfulness": {
            "score": faith_eval.get("score") if faith_eval else None,
            "reason": faith_eval.get("reason") if faith_eval else "Evaluation unavailable"
        }
    }

    # ---------------------------------
    # Save Chat History
    # ---------------------------------
    chat = CourseChatHistory(
        user_id=current_user.user_id,
        course_id=request.course_id,
        question=request.question,
        answer=response.text
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    # ---------------------------------
    # Prepare Evidence
    # ---------------------------------
    evidence = []

    for i, doc in enumerate(docs):
        metadata = doc.metadata

        if metadata.get("source") == "video":
            evidence.append({
                "id": i + 1,
                "source": "video",
                "video_id": metadata.get("video_id"),
                "video_title": metadata.get("video_title"),
                "start_time": metadata.get("start_time"),
                "end_time": metadata.get("end_time"),
                "text": doc.page_content[:600]
            })

        else:
            evidence.append({
                "id": i + 1,
                "source": metadata.get(
                    "source",
                    "Unknown source"
                ),
                "page": metadata.get(
                    "page",
                    "Unknown"
                ),
                "chunk": metadata.get(
                    "chunk",
                    "Unknown"
                ),
                "text": doc.page_content[:600]
            })

    # ---------------------------------
    # Final Response
    # ---------------------------------
    return {
        "answer": response.text,
        "evaluation": evaluation,
        "chunks_used": len(docs),
        "evidence": evidence
    }


@app.post("/upload-course-audio")
async def upload_course_audio(
    course_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    order_no: int = Form(0),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio file is required"
        )

    allowed_extensions = (
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".aac"
    )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid audio format. "
                "Allowed formats: MP3, WAV, OGG, M4A, AAC"
            )
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    unique_name = f"{uuid.uuid4().hex}{extension}"
    audio_url = storage_service.upload_bytes(
        file_name=unique_name,
        content=content,
        folder=f"course_{course_id}/audio",
        content_type="audio/mpeg" if extension in {".mp3"} else "application/octet-stream",
    )

    duration = get_video_duration(tmp_file_path)

    new_audio = CourseAudio(
        course_id=course_id,
        title=title,
        description=description,
        audio_url=audio_url,
        duration=duration,
        order_no=order_no
    )

    db.add(new_audio)
    db.commit()
    db.refresh(new_audio)

    return {
        "message": "Audio uploaded successfully",
        "audio": new_audio
    }

@app.post("/upload-course-image")
async def upload_course_image(
    course_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    order_no: int = Form(0),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.course_id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Image file is required"
        )

    allowed_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif"
    )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid image format. "
                "Allowed formats: JPG, JPEG, PNG, WEBP, GIF"
            )
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Image file is empty."
        )

    unique_name = f"{uuid.uuid4().hex}{extension}"
    image_url = storage_service.upload_bytes(
        file_name=unique_name,
        content=content,
        folder=f"course_{course_id}/images",
        content_type="image/jpeg" if extension in {".jpg", ".jpeg"} else "image/png" if extension == ".png" else "image/webp" if extension == ".webp" else "image/gif" if extension == ".gif" else "application/octet-stream",
    )

    new_image = CourseImage(
        course_id=course_id,
        title=title,
        description=description,
        image_url=image_url,
        order_no=order_no
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {
        "message": "Image uploaded successfully",
        "image": new_image
    }

@app.post("/transcribe-youtube-video/{video_id}")
def transcribe_youtube_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
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

    if not video.video_url.startswith(
        ("http://", "https://")
    ):
        raise HTTPException(
            status_code=400,
            detail="This video does not have a YouTube URL"
        )

    temp_dir = os.path.join(
        os.path.dirname(__file__),
        "temp_video"
    )

    os.makedirs(
        temp_dir,
        exist_ok=True
    )

    audio_path = os.path.join(
        temp_dir,
        f"{uuid.uuid4().hex}"
    )

    try:

        print("=" * 60)
        print("=== YOUTUBE TRANSCRIPTION STARTED ===")
        print(f"Video ID: {video_id}")
        print(f"Title: {video.title}")
        print(f"URL: {video.video_url}")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path + ".%(ext)s",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            ydl.download(
                [video.video_url]
            )

        downloaded_file = None

        for filename in os.listdir(temp_dir):

            if filename.startswith(
                os.path.basename(audio_path)
            ):
                downloaded_file = os.path.join(
                    temp_dir,
                    filename
                )
                break

        if not downloaded_file:
            raise Exception(
                "Downloaded audio file not found"
            )

        print(
            f"Audio downloaded: {downloaded_file}"
        )

        print("Loading Whisper model...")

        model = whisper.load_model("base")

        print("Transcribing YouTube video...")

        result = model.transcribe(
            downloaded_file,
            fp16=False
        )

        full_text = result.get(
            "text",
            ""
        ).strip()

        segments = result.get(
            "segments",
            []
        )

        print(
            f"Transcript length: {len(full_text)}"
        )

        print(
            f"Segments found: {len(segments)}"
        )

        # Remove old transcript
        db.query(
            VideoTranscriptSegment
        ).filter(
            VideoTranscriptSegment.video_id
            == video_id
        ).delete(
            synchronize_session=False
        )

        db.query(
            VideoTranscript
        ).filter(
            VideoTranscript.video_id
            == video_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

        # Save full transcript
        transcript = VideoTranscript(
            video_id=video_id,
            full_text=full_text
        )

        db.add(transcript)

        # Save timestamp segments
        for segment in segments:

            segment_text = segment.get(
                "text",
                ""
            ).strip()

            if not segment_text:
                continue

            transcript_segment = (
                VideoTranscriptSegment(
                    video_id=video_id,
                    start_time=float(
                        segment["start"]
                    ),
                    end_time=float(
                        segment["end"]
                    ),
                    text=segment_text
                )
            )

            db.add(transcript_segment)

        db.commit()

        print(
            "=== YOUTUBE TRANSCRIPTION COMPLETED ==="
        )

        print(
            f"Video ID: {video_id}"
        )

        print(
            f"Transcript segments saved: "
            f"{len(segments)}"
        )

        print("=" * 60)

        return {
            "message": (
                "YouTube video transcribed successfully"
            ),
            "video_id": video_id,
            "title": video.title,
            "transcript_length": len(full_text),
            "segments": len(segments)
        }

    except Exception as e:

        db.rollback()

        print(
            "=== YOUTUBE TRANSCRIPTION ERROR ==="
        )

        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=(
                f"YouTube transcription failed: {str(e)}"
            )
        )

    finally:

        if os.path.exists(temp_dir):

            for filename in os.listdir(temp_dir):

                file_path = os.path.join(
                    temp_dir,
                    filename
                )

                try:
                    os.remove(file_path)
                except Exception:
                    pass



















