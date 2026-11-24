import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from ..core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class YouTubeChannel(Base):
    __tablename__ = "youtube_channels"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    channel_id = Column(String(128), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    custom_url = Column(String(128), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    subscriber_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    encrypted_credentials = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    is_authorized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_videos = relationship("SourceVideo", back_populates="channel", cascade="all, delete-orphan")
    upload_jobs = relationship("UploadJob", back_populates="channel", cascade="all, delete-orphan")
    published_videos = relationship("PublishedVideo", back_populates="channel", cascade="all, delete-orphan")


class SourceVideo(Base):
    __tablename__ = "source_videos"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    channel_id = Column(String(64), ForeignKey("youtube_channels.id", ondelete="SET NULL"), nullable=True)
    youtube_video_id = Column(String(32), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1024), nullable=False)
    proxy_path = Column(String(1024), nullable=True)
    audio_path = Column(String(1024), nullable=True)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    width = Column(Integer, nullable=False, default=1920)
    height = Column(Integer, nullable=False, default=1080)
    fps = Column(Float, nullable=False, default=30.0)
    codec_video = Column(String(32), nullable=True)
    codec_audio = Column(String(32), nullable=True)
    source_status = Column(String(32), default="owned")  # owned, licensed, authorized, unknown, restricted
    analysis_status = Column(String(32), default="pending")  # pending, analyzing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channel = relationship("YouTubeChannel", back_populates="source_videos")
    analysis_jobs = relationship("VideoAnalysisJob", back_populates="source_video", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="source_video", uselist=False, cascade="all, delete-orphan")
    scene_segments = relationship("SceneSegment", back_populates="source_video", cascade="all, delete-orphan")
    candidates = relationship("EngagementCandidate", back_populates="source_video", cascade="all, delete-orphan")
    clip_projects = relationship("ClipProject", back_populates="source_video", cascade="all, delete-orphan")


class VideoAnalysisJob(Base):
    __tablename__ = "video_analysis_jobs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_video_id = Column(String(64), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), default="queued")  # queued, processing, completed, failed, cancelled
    current_step = Column(String(64), nullable=True)
    progress_percent = Column(Float, default=0.0)
    raw_analysis_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_video = relationship("SourceVideo", back_populates="analysis_jobs")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_video_id = Column(String(64), ForeignKey("source_videos.id", ondelete="CASCADE"), unique=True, nullable=False)
    language = Column(String(16), default="en")
    text_full = Column(Text, nullable=False)
    words_json = Column(Text, nullable=False)       # JSON array of {word, start, end, confidence}
    sentences_json = Column(Text, nullable=False)   # JSON array of {text, start, end}
    created_at = Column(DateTime, default=datetime.utcnow)

    source_video = relationship("SourceVideo", back_populates="transcript")


class SceneSegment(Base):
    __tablename__ = "scene_segments"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_video_id = Column(String(64), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    visual_activity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_video = relationship("SourceVideo", back_populates="scene_segments")


class EngagementCandidate(Base):
    __tablename__ = "engagement_candidates"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_video_id = Column(String(64), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)  # 0 to 100
    scoring_mode = Column(String(32), nullable=False)  # ACTUAL_ANALYTICS or PREDICTED
    confidence = Column(Float, nullable=False, default=0.8)
    hook_score = Column(Float, default=0.0)
    payoff_score = Column(Float, default=0.0)
    emotional_score = Column(Float, default=0.0)
    topic_score = Column(Float, default=0.0)
    visual_score = Column(Float, default=0.0)
    retention_signal_score = Column(Float, nullable=True)
    reasons_json = Column(Text, nullable=True)  # JSON array of strings
    created_at = Column(DateTime, default=datetime.utcnow)

    source_video = relationship("SourceVideo", back_populates="candidates")
    clip_projects = relationship("ClipProject", back_populates="candidate")


class ClipProject(Base):
    __tablename__ = "clip_projects"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(64), ForeignKey("engagement_candidates.id", ondelete="SET NULL"), nullable=True)
    source_video_id = Column(String(64), ForeignKey("source_videos.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    caption_style = Column(String(64), default="bold_yellow")
    framing_mode = Column(String(32), default="smart_face")
    rendered_video_path = Column(String(1024), nullable=True)
    thumbnail_path = Column(String(1024), nullable=True)
    status = Column(String(32), default="draft")  # draft, rendering, rendered, qc_passed, qc_failed, approved, scheduled, published
    metadata_json = Column(Text, nullable=True)   # JSON: titles, description, tags, hashtags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_video = relationship("SourceVideo", back_populates="clip_projects")
    candidate = relationship("EngagementCandidate", back_populates="clip_projects")
    qc_reports = relationship("QCReport", back_populates="clip_project", cascade="all, delete-orphan")
    upload_jobs = relationship("UploadJob", back_populates="clip_project", cascade="all, delete-orphan")
    published_videos = relationship("PublishedVideo", back_populates="clip_project", cascade="all, delete-orphan")


class QCReport(Base):
    __tablename__ = "qc_reports"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    clip_project_id = Column(String(64), ForeignKey("clip_projects.id", ondelete="CASCADE"), nullable=False)
    passed = Column(Boolean, nullable=False, default=False)
    overall_score = Column(Float, nullable=False, default=0.0)  # 0 to 100
    video_checks_json = Column(Text, nullable=False)
    audio_checks_json = Column(Text, nullable=False)
    caption_checks_json = Column(Text, nullable=False)
    framing_checks_json = Column(Text, nullable=False)
    repaired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    clip_project = relationship("ClipProject", back_populates="qc_reports")


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    clip_project_id = Column(String(64), ForeignKey("clip_projects.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(String(64), ForeignKey("youtube_channels.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(32), default="SAFE")  # SAFE or AUTOMATIC
    status = Column(String(32), default="queued")  # queued, uploading, completed, failed, cancelled
    scheduled_publish_time = Column(DateTime, nullable=True)
    privacy_status = Column(String(32), default="private")  # private, unlisted, public
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clip_project = relationship("ClipProject", back_populates="upload_jobs")
    channel = relationship("YouTubeChannel", back_populates="upload_jobs")


class PublishedVideo(Base):
    __tablename__ = "published_videos"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    clip_project_id = Column(String(64), ForeignKey("clip_projects.id", ondelete="CASCADE"), nullable=False)
    youtube_video_id = Column(String(64), nullable=False, index=True)
    channel_id = Column(String(64), ForeignKey("youtube_channels.id", ondelete="CASCADE"), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    clip_project = relationship("ClipProject", back_populates="published_videos")
    channel = relationship("YouTubeChannel", back_populates="published_videos")
    analytics_snapshots = relationship("AnalyticsSnapshot", back_populates="published_video", cascade="all, delete-orphan")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    published_video_id = Column(String(64), ForeignKey("published_videos.id", ondelete="CASCADE"), nullable=False)
    views = Column(Integer, default=0)
    watch_time_minutes = Column(Float, default=0.0)
    avg_view_duration_seconds = Column(Float, default=0.0)
    avg_percentage_viewed = Column(Float, default=0.0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    subscribers_gained = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    published_video = relationship("PublishedVideo", back_populates="analytics_snapshots")


class LearningInsight(Base):
    __tablename__ = "learning_insights"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    channel_id = Column(String(64), ForeignKey("youtube_channels.id", ondelete="CASCADE"), nullable=False)
    factor_correlations_json = Column(Text, nullable=False)
    recommended_weights_json = Column(Text, nullable=False)
    best_duration_bucket = Column(String(32), nullable=True)
    best_hook_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
