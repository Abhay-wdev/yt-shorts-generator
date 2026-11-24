import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.database import ClipProject, SourceVideo, QCReport
from ...models.schemas import ClipCreateRequest, ClipProjectResponse, QCReportResponse
from ...services.unified_shorts import run_render_short_task
from ...workers.queue import job_runner

router = APIRouter()

@router.get("", response_model=List[ClipProjectResponse])
def list_shorts(db: Session = Depends(get_db)):
    """Lists all created Short projects."""
    projects = db.query(ClipProject).order_by(ClipProject.created_at.desc()).all()
    results = []
    for p in projects:
        meta = json.loads(p.metadata_json) if p.metadata_json else None
        results.append(ClipProjectResponse(
            id=p.id,
            candidate_id=p.candidate_id,
            source_video_id=p.source_video_id,
            title=p.title,
            start_time=p.start_time,
            end_time=p.end_time,
            caption_style=p.caption_style,
            framing_mode=p.framing_mode,
            rendered_video_path=p.rendered_video_path,
            thumbnail_path=p.thumbnail_path,
            status=p.status,
            metadata=meta,
            created_at=p.created_at
        ))
    return results

@router.post("/generate", response_model=ClipProjectResponse)
def generate_short(req: ClipCreateRequest, db: Session = Depends(get_db)):
    """Creates a new Short project and enqueues background vertical rendering and QC."""
    video = db.query(SourceVideo).filter(SourceVideo.id == req.source_video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Source video not found.")

    project_id = str(uuid.uuid4())
    project = ClipProject(
        id=project_id,
        source_video_id=req.source_video_id,
        candidate_id=req.candidate_id,
        title=req.title,
        start_time=req.start_time,
        end_time=req.end_time,
        caption_style=req.caption_style,
        framing_mode=req.framing_mode,
        status="queued"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    job_id = f"render_{project_id}"
    job_runner.submit_job(
        job_id=job_id,
        task_fn=run_render_short_task,
        clip_project_id=project_id,
        is_heavy=True
    )

    return ClipProjectResponse(
        id=project.id,
        candidate_id=project.candidate_id,
        source_video_id=project.source_video_id,
        title=project.title,
        start_time=project.start_time,
        end_time=project.end_time,
        caption_style=project.caption_style,
        framing_mode=project.framing_mode,
        rendered_video_path=project.rendered_video_path,
        thumbnail_path=project.thumbnail_path,
        status=project.status,
        metadata=None,
        created_at=project.created_at
    )

@router.get("/{short_id}", response_model=ClipProjectResponse)
def get_short_detail(short_id: str, db: Session = Depends(get_db)):
    """Retrieves full details for a Short project."""
    p = db.query(ClipProject).filter(ClipProject.id == short_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Short project not found.")
    meta = json.loads(p.metadata_json) if p.metadata_json else None
    return ClipProjectResponse(
        id=p.id,
        candidate_id=p.candidate_id,
        source_video_id=p.source_video_id,
        title=p.title,
        start_time=p.start_time,
        end_time=p.end_time,
        caption_style=p.caption_style,
        framing_mode=p.framing_mode,
        rendered_video_path=p.rendered_video_path,
        thumbnail_path=p.thumbnail_path,
        status=p.status,
        metadata=meta,
        created_at=p.created_at
    )

@router.get("/{short_id}/qc", response_model=QCReportResponse)
def get_qc_report(short_id: str, db: Session = Depends(get_db)):
    """Retrieves Quality Control report for a Short."""
    qc = db.query(QCReport).filter(QCReport.clip_project_id == short_id).order_by(QCReport.created_at.desc()).first()
    if not qc:
        raise HTTPException(status_code=404, detail="No QC report found for this Short.")
    return QCReportResponse(
        id=qc.id,
        clip_project_id=qc.clip_project_id,
        passed=qc.passed,
        overall_score=qc.overall_score,
        video_checks=json.loads(qc.video_checks_json),
        audio_checks=json.loads(qc.audio_checks_json),
        caption_checks=json.loads(qc.caption_checks_json),
        framing_checks=json.loads(qc.framing_checks_json),
        repaired=qc.repaired,
        created_at=qc.created_at
    )

@router.post("/{short_id}/approve")
def approve_short(short_id: str, db: Session = Depends(get_db)):
    """Approves a Short in SAFE mode for publishing."""
    p = db.query(ClipProject).filter(ClipProject.id == short_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Short not found.")
    p.status = "approved"
    db.commit()
    return {"status": "success", "message": "Short approved for publishing.", "short_id": short_id}
