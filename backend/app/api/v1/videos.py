import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...models.database import SourceVideo
from ...models.schemas import SourceVideoResponse, ExploreChannelRequest, ImportYouTubeRequest
from ...services.ingestion import video_ingestion_service
from ...services.youtube_downloader import youtube_downloader

router = APIRouter()

@router.get("", response_model=List[SourceVideoResponse])
def list_videos(db: Session = Depends(get_db)):
    """Lists all ingested source videos, attaching active download progress if downloading."""
    videos = db.query(SourceVideo).order_by(SourceVideo.created_at.desc()).all()
    results = []
    for v in videos:
        resp = SourceVideoResponse.model_validate(v)
        dl_info = youtube_downloader.get_download_progress(v.id)
        if dl_info:
            resp.download_progress = dl_info
        results.append(resp)
    return results

@router.get("/downloads/active")
def get_active_downloads():
    """Lists all currently active YouTube video downloads with real-time % and speed."""
    return youtube_downloader.get_all_active_downloads()

@router.get("/{video_id}", response_model=SourceVideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata for a single source video."""
    video = db.query(SourceVideo).filter(SourceVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    resp = SourceVideoResponse.model_validate(video)
    dl_info = youtube_downloader.get_download_progress(video.id)
    if dl_info:
        resp.download_progress = dl_info
    return resp

@router.post("/upload", response_model=SourceVideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    source_status: Optional[str] = Form("owned"),
    channel_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Uploads a video file, generates 360p analysis proxy, extracts audio, and indexes metadata."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    temp_path = settings.DIR_CACHE / file.filename
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    video_title = title or Path(file.filename).stem

    try:
        source_video = video_ingestion_service.ingest_local_file(
            source_path=temp_path,
            title=video_title,
            db=db,
            source_status=source_status or "owned",
            channel_id=channel_id
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return source_video

@router.post("/explore-channel")
def explore_youtube_channel(req: ExploreChannelRequest):
    """
    Explores a YouTube channel URL and returns metadata plus the list of recent videos
    without downloading them.
    """
    try:
        return youtube_downloader.explore_channel(
            channel_url=req.channel_url,
            max_results=req.max_results or 10
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import-youtube", response_model=SourceVideoResponse)
def import_youtube_video(req: ImportYouTubeRequest, db: Session = Depends(get_db)):
    """
    Downloads a video from YouTube (URL or video ID), automatically ingests it,
    and enqueues background multi-modal analysis.
    """
    try:
        source_video = youtube_downloader.download_and_ingest(
            video_url=req.url,
            db=db,
            title_override=req.title,
            auto_analyze=req.auto_analyze if req.auto_analyze is not None else True
        )
        return source_video
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
