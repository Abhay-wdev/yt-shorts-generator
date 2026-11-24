import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.database import SourceVideo, VideoAnalysisJob, Transcript, EngagementCandidate
from ...models.schemas import CandidateResponse
from ...services.boundary_detector import boundary_detector

router = APIRouter()

@router.get("/{video_id}/candidates", response_model=List[CandidateResponse])
def get_engagement_candidates(
    video_id: str,
    generate_if_missing: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Retrieves or calculates ranked engagement opportunity candidate clips for a video.
    Returns explainable scores (0-100) and justifications.
    """
    # Check existing candidates in DB
    existing = db.query(EngagementCandidate).filter(
        EngagementCandidate.source_video_id == video_id
    ).order_by(EngagementCandidate.overall_score.desc()).all()

    if existing:
        results = []
        for c in existing:
            reasons = json.loads(c.reasons_json) if c.reasons_json else []
            results.append(CandidateResponse(
                id=c.id,
                source_video_id=c.source_video_id,
                start_time=c.start_time,
                end_time=c.end_time,
                duration=c.duration,
                overall_score=c.overall_score,
                scoring_mode=c.scoring_mode,
                confidence=c.confidence,
                hook_score=c.hook_score,
                payoff_score=c.payoff_score,
                emotional_score=c.emotional_score,
                topic_score=c.topic_score,
                visual_score=c.visual_score,
                retention_signal_score=c.retention_signal_score,
                reasons=reasons
            ))
        return results

    if not generate_if_missing:
        return []

    # If missing, compute candidates from completed analysis
    job = db.query(VideoAnalysisJob).filter(
        VideoAnalysisJob.source_video_id == video_id,
        VideoAnalysisJob.status == "completed"
    ).order_by(VideoAnalysisJob.completed_at.desc()).first()

    if not job or not job.raw_analysis_json:
        # If still in progress or not analyzed, return empty list gracefully
        return []

    analysis_data = json.loads(job.raw_analysis_json)
    sentences = analysis_data.get("transcript", {}).get("sentences", [])
    audio_peaks = analysis_data.get("audio", {}).get("peaks", [])
    mean_rms = analysis_data.get("audio", {}).get("mean_rms", 0.05)
    visual_activity = analysis_data.get("visual", {}).get("mean_activity", 0.05)

    candidates = boundary_detector.extract_candidate_clips(
        sentences=sentences,
        audio_peaks=audio_peaks,
        mean_rms=mean_rms,
        visual_activity=visual_activity,
        max_candidates=5
    )

    persisted = []
    for cand in candidates:
        rec = EngagementCandidate(
            id=str(uuid.uuid4()),
            source_video_id=video_id,
            start_time=cand["start_time"],
            end_time=cand["end_time"],
            duration=cand["duration"],
            overall_score=cand["overall_score"],
            scoring_mode=cand["scoring_mode"],
            confidence=cand["confidence"],
            hook_score=cand["hook_score"],
            payoff_score=cand["payoff_score"],
            emotional_score=cand["emotional_score"],
            topic_score=cand["topic_score"],
            visual_score=cand["visual_score"],
            retention_signal_score=cand.get("retention_signal_score"),
            reasons_json=json.dumps(cand.get("reasons", []))
        )
        db.add(rec)
        persisted.append(rec)

    db.commit()

    return [
        CandidateResponse(
            id=p.id,
            source_video_id=p.source_video_id,
            start_time=p.start_time,
            end_time=p.end_time,
            duration=p.duration,
            overall_score=p.overall_score,
            scoring_mode=p.scoring_mode,
            confidence=p.confidence,
            hook_score=p.hook_score,
            payoff_score=p.payoff_score,
            emotional_score=p.emotional_score,
            topic_score=p.topic_score,
            visual_score=p.visual_score,
            retention_signal_score=p.retention_signal_score,
            reasons=json.loads(p.reasons_json or "[]")
        ) for p in persisted
    ]
