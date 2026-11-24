from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Base response
class StandardResponse(BaseModel):
    status: str = "ok"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# Hardware
class HardwareStatusResponse(BaseModel):
    os: Dict[str, Any]
    cpu: Dict[str, Any]
    ram: Dict[str, Any]
    gpu: Dict[str, Any]
    video_acceleration: Dict[str, Any]

# YouTube Channels
class ChannelCreateRequest(BaseModel):
    channel_id: str
    title: str
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    title: str
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: int
    video_count: int
    is_authorized: bool
    created_at: datetime

# Source Videos
class DownloadProgressResponse(BaseModel):
    status: str = "downloading"
    percent: float = 0.0
    remaining_percent: float = 100.0
    speed: str = ""
    eta: int = 0
    downloaded_mb: float = 0.0
    total_mb: float = 0.0

class SourceVideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: Optional[str] = None
    youtube_video_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec_video: Optional[str] = None
    codec_audio: Optional[str] = None
    source_status: str
    analysis_status: str
    created_at: datetime
    download_progress: Optional[DownloadProgressResponse] = None

class ExploreChannelRequest(BaseModel):
    channel_url: str
    max_results: Optional[int] = 10

class ImportYouTubeRequest(BaseModel):
    url: str
    auto_analyze: Optional[bool] = True
    title: Optional[str] = None

# Analysis
class AnalysisJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_video_id: str
    status: str
    current_step: Optional[str] = None
    progress_percent: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Engagement Candidates
class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_video_id: str
    start_time: float
    end_time: float
    duration: float
    overall_score: float
    scoring_mode: str
    confidence: float
    hook_score: float
    payoff_score: float
    emotional_score: float
    topic_score: float
    visual_score: float
    retention_signal_score: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)

# Clip Projects & Shorts
class ClipCreateRequest(BaseModel):
    source_video_id: str
    candidate_id: Optional[str] = None
    title: str
    start_time: float
    end_time: float
    caption_style: str = "bold_yellow"
    framing_mode: str = "smart_face"

class ClipProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: Optional[str] = None
    source_video_id: str
    title: str
    start_time: float
    end_time: float
    caption_style: str
    framing_mode: str
    rendered_video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

# Quality Control
class QCReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    clip_project_id: str
    passed: bool
    overall_score: float
    video_checks: Dict[str, Any]
    audio_checks: Dict[str, Any]
    caption_checks: Dict[str, Any]
    framing_checks: Dict[str, Any]
    repaired: bool
    created_at: datetime

# Publishing
class PublishRequest(BaseModel):
    clip_project_id: str
    channel_id: str
    mode: str = "SAFE"  # SAFE or AUTOMATIC
    privacy_status: str = "private"  # private, unlisted, public
    scheduled_publish_time: Optional[datetime] = None

class UploadJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    clip_project_id: str
    channel_id: str
    mode: str
    status: str
    scheduled_publish_time: Optional[datetime] = None
    privacy_status: str
    retry_count: int
    error_message: Optional[str] = None
    created_at: datetime
