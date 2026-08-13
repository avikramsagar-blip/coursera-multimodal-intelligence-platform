from sqlalchemy import Column, Integer, String, Text, BigInteger, ForeignKey, TIMESTAMP, DateTime, Float, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from database import Base
import yt_dlp

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

class VideoTranscript(Base):
    __tablename__ = "video_transcripts"

    transcript_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    video_id = Column(
        Integer,
        ForeignKey("course_videos.video_id"),
        nullable=False
    )

    full_text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class VideoTranscriptSegment(Base):
    __tablename__ = "video_transcript_segments"

    segment_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    video_id = Column(
        Integer,
        ForeignKey("course_videos.video_id"),
        nullable=False
    )

    start_time = Column(
        Float,
        nullable=False
    )

    end_time = Column(
        Float,
        nullable=False
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

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

class CourseAudio(Base):
    __tablename__ = "course_audios"

    audio_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.course_id"),
        nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text)
    audio_url = Column(String, nullable=False)
    duration = Column(Integer)
    order_no = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class CourseImage(Base):
    __tablename__ = "course_images"

    image_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.course_id"),
        nullable=False
    )
    title = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String, nullable=False)
    order_no = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class RetrievalRecord(Base):
    __tablename__ = "retrieval_records"

    retrieval_id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    retriever = Column(String, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON-serialized metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, nullable=False)  # e.g., video, transcript, image, slide, quiz, discussion
    source_id = Column(Integer, nullable=True)  # id in the source table when applicable
    segment_id = Column(Integer, nullable=True)  # e.g., transcript segment id
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    snippet_text = Column(Text, nullable=True)
    source_uri = Column(Text, nullable=True)
    embedding_id = Column(String, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON-serialized metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class Insight(Base):
    __tablename__ = "insights"

    insight_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=False)
    generated_by_model_id = Column(Integer, ForeignKey("ai_models.model_id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    status = Column(String, default="pending_review")  # pending_review, approved, rejected
    reviewed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InsightEvidence(Base):
    __tablename__ = "insight_evidence"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.insight_id"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.evidence_id"), nullable=False)
    retrieval_id = Column(Integer, ForeignKey("retrieval_records.retrieval_id"), nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.insight_id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action = Column(String, nullable=False)  # approved, rejected, request_changes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GenerationMetric(Base):
    __tablename__ = "generation_metrics"

    metric_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    prompt_snippet = Column(String(1000), nullable=True)
    prompt_hash = Column(String(128), nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)
    retrieval_id = Column(Integer, ForeignKey("retrieval_records.retrieval_id"), nullable=True)
    insight_id = Column(Integer, ForeignKey("insights.insight_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action_type = Column(String, nullable=False)   # e.g., insight_review, role_change
    target_type = Column(String, nullable=True)   # e.g., insight, user
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
