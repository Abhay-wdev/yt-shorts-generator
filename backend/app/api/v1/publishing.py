import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.database import UploadJob, PublishedVideo, ClipProject, YouTubeChannel
from ...models.schemas import PublishRequest, UploadJobResponse
from ...services.publisher import youtube_publisher

router = APIRouter()

@router.get("/queue", response_model=List[UploadJobResponse])
def get_publishing_queue(db: Session = Depends(get_db)):
    """Lists queued and completed publishing upload jobs."""
    jobs = db.query(UploadJob).order_by(UploadJob.created_at.desc()).all()
    return jobs

@router.post("/publish")
def publish_clip(req: PublishRequest, db: Session = Depends(get_db)):
    """Triggers or schedules publishing of a Short to YouTube."""
    project = db.query(ClipProject).filter(ClipProject.id == req.clip_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Clip project not found.")

    channel = db.query(YouTubeChannel).filter(
        (YouTubeChannel.id == req.channel_id) | (YouTubeChannel.channel_id == req.channel_id)
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="YouTube channel not found.")

    # In SAFE mode, ensure project has been approved
    if req.mode == "SAFE" and project.status not in ["approved", "qc_passed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Clip {project.id} must be approved before publishing in SAFE mode (current status: {project.status})."
        )

    # In AUTOMATIC mode, verify QC passed
    if req.mode == "AUTOMATIC" and project.status != "qc_passed":
        raise HTTPException(
            status_code=400,
            detail=f"Clip {project.id} cannot be published in AUTOMATIC mode because QC status is '{project.status}'."
        )

    # Execute upload
    try:
        pub = youtube_publisher.upload_short(
            clip_project_id=req.clip_project_id,
            channel_id=channel.id,
            db=db,
            privacy_status=req.privacy_status,
            mode=req.mode
        )
        return {
            "status": "success",
            "message": "Successfully published Short to YouTube!",
            "youtube_video_id": pub.youtube_video_id,
            "published_at": pub.published_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
