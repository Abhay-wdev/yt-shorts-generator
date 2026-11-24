import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.database import SourceVideo, VideoAnalysisJob
from ...models.schemas import AnalysisJobResponse
from ...services.unified_analysis import run_video_analysis_task
from ...services.youtube_downloader import youtube_downloader
from ...workers.queue import job_runner

router = APIRouter()

@router.get("/active")
def get_active_analysis(db: Session = Depends(get_db)):
    """Returns the currently active processing job or recently completed job with live ETA and progress."""
    # 0. Check if there is an active YouTube download running
    active_dls = youtube_downloader.get_all_active_downloads()
    for dl in active_dls:
        if dl.get("status") in ("downloading", "processing"):
            step_desc = (
                f"Downloading from YouTube: {dl.get('percent', 0):.1f}% ({dl.get('remaining_percent', 100):.1f}% remaining) • {dl.get('speed', '')} • ETA: {dl.get('eta', 0)}s"
                if dl.get("status") == "downloading"
                else "Download Complete! Generating 360p analysis proxy & audio..."
            )
            return {
                "has_active": True,
                "is_downloading": True,
                "job_id": f"dl_{dl['video_id']}",
                "video_id": dl["video_id"],
                "video_title": dl.get("title", "YouTube Video"),
                "status": dl.get("status"),
                "current_step": step_desc,
                "progress_percent": dl.get("percent", 0.0),
                "remaining_percent": dl.get("remaining_percent", 100.0),
                "speed": dl.get("speed", ""),
                "eta": dl.get("eta", 0),
                "downloaded_mb": dl.get("downloaded_mb", 0.0),
                "total_mb": dl.get("total_mb", 0.0),
                "elapsed_seconds": 0,
                "estimated_remaining_seconds": dl.get("eta", 0)
            }

    active_job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.status == "processing"
    ).order_by(VideoAnalysisJob.started_at.desc()).first()

    if active_job:
        status_info = job_runner.get_job_status(active_job.id)
        if not status_info or status_info.get("status") not in ("queued", "processing"):
            # Dangling job from previous crash/restart
            active_job.status = "failed"
            active_job.error_message = "Interrupted by server restart. Ready to retry."
            db.commit()
        else:
            video = db.query(SourceVideo).filter(SourceVideo.id == active_job.source_video_id).first()
            elapsed = (datetime.utcnow() - active_job.started_at).total_seconds() if active_job.started_at else 0
            pct = max(1.0, active_job.progress_percent)
            estimated_total = (elapsed / (pct / 100.0)) if pct > 5 else 90.0
            remaining = max(0, estimated_total - elapsed)

            return {
                "has_active": True,
                "job_id": active_job.id,
                "video_id": active_job.source_video_id,
                "video_title": video.title if video else "Imported Video",
                "status": "processing",
                "current_step": active_job.current_step,
                "progress_percent": active_job.progress_percent,
                "elapsed_seconds": int(elapsed),
                "estimated_remaining_seconds": int(remaining)
            }

    queued_job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.status == "queued"
    ).order_by(VideoAnalysisJob.created_at.desc()).first()

    if queued_job:
        status_info = job_runner.get_job_status(queued_job.id)
        if not status_info or status_info.get("status") not in ("queued", "processing"):
            # Dangling queued job from server restart
            queued_job.status = "failed"
            queued_job.error_message = "Interrupted by server restart. Ready to retry."
            db.commit()
        else:
            video = db.query(SourceVideo).filter(SourceVideo.id == queued_job.source_video_id).first()
            return {
                "has_active": True,
                "job_id": queued_job.id,
                "video_id": queued_job.source_video_id,
                "video_title": video.title if video else "Imported Video",
                "status": "queued",
                "current_step": "Waiting in hardware queue...",
                "progress_percent": 0.0,
                "elapsed_seconds": 0,
                "estimated_remaining_seconds": 90
            }

    recent_job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.status == "completed"
    ).order_by(VideoAnalysisJob.completed_at.desc()).first()

    if recent_job and recent_job.completed_at:
        elapsed_since_completion = (datetime.utcnow() - recent_job.completed_at).total_seconds()
        if elapsed_since_completion < 60:
            video = db.query(SourceVideo).filter(SourceVideo.id == recent_job.source_video_id).first()
            return {
                "has_active": False,
                "is_recently_completed": True,
                "job_id": recent_job.id,
                "video_id": recent_job.source_video_id,
                "video_title": video.title if video else "Imported Video",
                "status": "completed",
                "current_step": "Completed! Viral moments ready.",
                "progress_percent": 100.0
            }

    return {"has_active": False, "is_recently_completed": False}

@router.post("/{video_id}/start", response_model=AnalysisJobResponse)
def start_video_analysis(video_id: str, db: Session = Depends(get_db)):
    """Enqueues a background multi-modal analysis job for the specified video."""
    video = db.query(SourceVideo).filter(SourceVideo.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Source video not found.")

    # Check if an active or queued job already exists for this video
    existing_job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.source_video_id == video_id,
        VideoAnalysisJob.status.in_(["queued", "processing"])
    ).order_by(VideoAnalysisJob.created_at.desc()).first()

    if existing_job:
        status_info = job_runner.get_job_status(existing_job.id)
        if status_info and status_info.get("status") in ("queued", "processing"):
            return existing_job

    job_id = str(uuid.uuid4())
    job = VideoAnalysisJob(
        id=job_id,
        source_video_id=video_id,
        status="queued",
        current_step="queued",
        progress_percent=0.0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Submit to persistent queue runner
    job_runner.submit_job(
        job_id=job_id,
        task_fn=run_video_analysis_task,
        source_video_id=video_id,
        is_heavy=True
    )

    return job

@router.get("/{video_id}/status")
def get_analysis_status(video_id: str, db: Session = Depends(get_db)):
    """Returns the latest analysis job status and progress for a video."""
    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.source_video_id == video_id
    ).order_by(VideoAnalysisJob.created_at.desc()).first()
    if not job:
        return {"status": "none", "video_id": video_id}
    return {
        "job_id": job.id,
        "status": job.status,
        "current_step": job.current_step,
        "progress_percent": job.progress_percent,
        "error_message": job.error_message,
        "completed_at": job.completed_at
    }

@router.get("/{video_id}/results")
def get_analysis_results(video_id: str, db: Session = Depends(get_db)):
    """Retrieves the full standardized multi-modal analysis JSON payload."""
    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.source_video_id == video_id,
        VideoAnalysisJob.status == "completed"
    ).order_by(VideoAnalysisJob.completed_at.desc()).first()
    if not job or not job.raw_analysis_json:
        raise HTTPException(status_code=404, detail="No completed analysis available for this video.")
    return json.loads(job.raw_analysis_json)
