import datetime
import json
import logging
from typing import Tuple, Optional
from sqlalchemy.orm import Session

import google_auth_oauthlib.flow
import googleapiclient.discovery
import requests

from ..core.config import settings
from ..core.security import encrypt_token, decrypt_token, generate_state_token
from ..models.database import YouTubeChannel

logger = logging.getLogger("yt_shorts.auth")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

class YouTubeAuthService:
    def __init__(self):
        self._states = {}

    def is_configured(self) -> bool:
        return bool(settings.YOUTUBE_CLIENT_ID and settings.YOUTUBE_CLIENT_SECRET)

    def generate_auth_url(self) -> Tuple[str, str]:
        """Generates Google OAuth 2.0 authorization URL."""
        if not self.is_configured():
            # For $0 mock / local testing mode when credentials haven't been provided yet
            state = generate_state_token()
            self._states[state] = True
            mock_url = f"http://localhost:8000/api/v1/channels/oauth/callback?code=mock_code_{state[:8]}&state={state}"
            return mock_url, state

        client_config = {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
            }
        }
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=settings.YOUTUBE_REDIRECT_URI
        )
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        self._states[state] = True
        return auth_url, state

    def exchange_code_for_tokens(self, code: str, state: str, db: Session) -> YouTubeChannel:
        """Exchanges code for access & refresh tokens and stores encrypted credentials."""
        # Check mock mode for local testing
        if code.startswith("mock_code_") or not self.is_configured():
            mock_channel_id = f"UC_{code[-8:]}"
            existing = db.query(YouTubeChannel).filter(YouTubeChannel.channel_id == mock_channel_id).first()
            if not existing:
                existing = YouTubeChannel(
                    channel_id=mock_channel_id,
                    title="Test Creator Studio (Local)",
                    custom_url="@testcreator",
                    thumbnail_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
                    subscriber_count=12400,
                    video_count=42,
                    is_authorized=True,
                    encrypted_credentials=encrypt_token(json.dumps({
                        "access_token": "mock_access_token",
                        "refresh_token": "mock_refresh_token"
                    }))
                )
                db.add(existing)
            else:
                existing.is_authorized = True
            db.commit()
            db.refresh(existing)
            return existing

        client_config = {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
            }
        }
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=settings.YOUTUBE_REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Retrieve channel metadata via YouTube Data API
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        response = youtube.channels().list(mine=True, part="snippet,statistics").execute()

        items = response.get("items", [])
        if not items:
            raise ValueError("No YouTube channel found for the authenticated account.")

        ch_data = items[0]
        yt_id = ch_data["id"]
        snippet = ch_data.get("snippet", {})
        stats = ch_data.get("statistics", {})

        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        channel = db.query(YouTubeChannel).filter(YouTubeChannel.channel_id == yt_id).first()
        if not channel:
            channel = YouTubeChannel(
                channel_id=yt_id,
                title=snippet.get("title", "Untitled Channel"),
                custom_url=snippet.get("customUrl"),
                thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
                subscriber_count=int(stats.get("subscriberCount", 0)),
                video_count=int(stats.get("videoCount", 0)),
                is_authorized=True,
                encrypted_credentials=encrypt_token(json.dumps(token_data)),
                token_expiry=credentials.expiry
            )
            db.add(channel)
        else:
            channel.title = snippet.get("title", channel.title)
            channel.custom_url = snippet.get("customUrl", channel.custom_url)
            channel.thumbnail_url = snippet.get("thumbnails", {}).get("default", {}).get("url", channel.thumbnail_url)
            channel.subscriber_count = int(stats.get("subscriberCount", channel.subscriber_count))
            channel.video_count = int(stats.get("videoCount", channel.video_count))
            channel.is_authorized = True
            channel.encrypted_credentials = encrypt_token(json.dumps(token_data))
            channel.token_expiry = credentials.expiry

        db.commit()
        db.refresh(channel)
        return channel

    def revoke_channel(self, channel_id: str, db: Session) -> bool:
        """Revokes token with Google and removes credentials."""
        channel = db.query(YouTubeChannel).filter(
            (YouTubeChannel.id == channel_id) | (YouTubeChannel.channel_id == channel_id)
        ).first()
        if not channel:
            return False

        if channel.encrypted_credentials:
            try:
                data = json.loads(decrypt_token(channel.encrypted_credentials))
                token = data.get("token") or data.get("access_token")
                if token and not token.startswith("mock_"):
                    requests.post('https://oauth2.googleapis.com/revoke',
                        params={'token': token},
                        headers={'content-type': 'application/x-www-form-urlencoded'},
                        timeout=5
                    )
            except Exception as e:
                logger.warning(f"Failed to revoke with Google endpoint: {e}")

        channel.is_authorized = False
        channel.encrypted_credentials = None
        db.commit()
        return True
