from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...models.database import YouTubeChannel
from ...models.schemas import ChannelResponse, StandardResponse
from ...services.youtube_auth import YouTubeAuthService

router = APIRouter()
auth_service = YouTubeAuthService()

@router.get("", response_model=List[ChannelResponse])
def list_channels(db: Session = Depends(get_db)):
    """Lists all registered YouTube channels."""
    channels = db.query(YouTubeChannel).order_by(YouTubeChannel.created_at.desc()).all()
    return channels

@router.get("/oauth/authorize")
def get_authorization_url():
    """Generates a secure Google OAuth 2.0 authorization URL."""
    auth_url, state = auth_service.generate_auth_url()
    return {"authorization_url": auth_url, "state": state}

@router.get("/oauth/callback")
def handle_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Processes Google OAuth callback, verifies state, encrypts tokens, and registers channel."""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth Error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from Google.")
    
    channel = auth_service.exchange_code_for_tokens(code, state, db)
    return {
        "status": "success",
        "message": f"Successfully connected channel: {channel.title}",
        "channel_id": channel.channel_id
    }

@router.post("/{channel_id}/revoke")
def revoke_channel(channel_id: str, db: Session = Depends(get_db)):
    """Revokes channel authorization and deletes credentials from vault."""
    success = auth_service.revoke_channel(channel_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found or revocation failed.")
    return {"status": "success", "message": "Channel authorization revoked."}
