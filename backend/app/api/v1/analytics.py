import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.database import YouTubeChannel, PublishedVideo, AnalyticsSnapshot, LearningInsight
from ...services.learning_engine import learning_engine

router = APIRouter()

@router.get("/channel/{channel_id}/summary")
def get_channel_analytics(channel_id: str, db: Session = Depends(get_db)):
    """Retrieves aggregated performance analytics for a connected channel."""
    channel = db.query(YouTubeChannel).filter(
        (YouTubeChannel.id == channel_id) | (YouTubeChannel.channel_id == channel_id)
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    published = db.query(PublishedVideo).filter(PublishedVideo.channel_id == channel.id).all()
    pub_ids = [p.id for p in published]

    snapshots = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.published_video_id.in_(pub_ids)
    ).all() if pub_ids else []

    total_views = sum(s.views for s in snapshots)
    total_likes = sum(s.likes for s in snapshots)
    total_watch_time = sum(s.watch_time_minutes for s in snapshots)

    return {
        "channel_title": channel.title,
        "total_published_shorts": len(published),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_watch_time_minutes": round(total_watch_time, 1),
        "subscribers": channel.subscriber_count
    }

@router.post("/channel/{channel_id}/sync")
def sync_analytics(channel_id: str, db: Session = Depends(get_db)):
    """Triggers sync of performance metrics for published Shorts."""
    channel = db.query(YouTubeChannel).filter(
        (YouTubeChannel.id == channel_id) | (YouTubeChannel.channel_id == channel_id)
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    snapshots = learning_engine.sync_channel_analytics(channel.id, db)
    return {"status": "success", "synced_snapshots": len(snapshots)}

@router.get("/channel/{channel_id}/insights")
def get_channel_insights(channel_id: str, db: Session = Depends(get_db)):
    """Retrieves learning insights and adaptive engagement score weights."""
    channel = db.query(YouTubeChannel).filter(
        (YouTubeChannel.id == channel_id) | (YouTubeChannel.channel_id == channel_id)
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    insight = db.query(LearningInsight).filter(
        LearningInsight.channel_id == channel.id
    ).order_by(LearningInsight.created_at.desc()).first()

    if not insight:
        insight = learning_engine.generate_learning_insights(channel.id, db)

    return {
        "channel_id": channel.id,
        "best_duration_bucket": insight.best_duration_bucket,
        "best_hook_type": insight.best_hook_type,
        "correlations": json.loads(insight.factor_correlations_json),
        "recommended_weights": json.loads(insight.recommended_weights_json),
        "generated_at": insight.created_at
    }
