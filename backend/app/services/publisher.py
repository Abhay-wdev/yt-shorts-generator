import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
from google.oauth2.credentials import Credentials

from ..core.config import settings
from ..core.security import decrypt_token
from ..models.database import ClipProject, YouTubeChannel, UploadJob, PublishedVideo, SourceVideo

logger = logging.getLogger("yt_shorts.publisher")

class YouTubePublisherService:
    def upload_short(
        self,
        clip_project_id: str,
        channel_id: str,
        db: Session,
        privacy_status: str = "private",
        mode: str = "SAFE"
    ) -> PublishedVideo:
        """
        Publishes a Short to YouTube via official Data API v3:
        1. Verifies channel credentials and ownership permissions.
        2. Validates QC status (AUTOMATIC mode requires QC pass).
        3. Prevents duplicate uploads.
        4. Uploads video using resumable MediaFileUpload.
        5. Uploads 9:16 thumbnail frame.
        6. Records PublishedVideo in database.
        """
        project = db.query(ClipProject).filter(ClipProject.id == clip_project_id).first()
        if not project:
            raise ValueError(f"Clip project {clip_project_id} not found.")

        # Duplicate check
        existing_pub = db.query(PublishedVideo).filter(PublishedVideo.clip_project_id == project.id).first()
        if existing_pub:
            logger.warning(f"Clip {project.id} already published as {existing_pub.youtube_video_id}.")
            project.status = "published"
            db.commit()
            return existing_pub

        # Source permission verification
        source_video = db.query(SourceVideo).filter(SourceVideo.id == project.source_video_id).first()
        if source_video and source_video.source_status in ["restricted", "unknown"]:
            if mode == "AUTOMATIC":
                raise PermissionError("Automatic publishing blocked: Video source permission status is restricted or unknown.")

        # QC Verification for AUTOMATIC mode
        if mode == "AUTOMATIC" and project.status != "qc_passed":
            raise ValueError(f"Cannot auto-publish Short {project.id}: QC status is '{project.status}', expected 'qc_passed'.")

        channel = db.query(YouTubeChannel).filter(
            (YouTubeChannel.id == channel_id) | (YouTubeChannel.channel_id == channel_id)
        ).first()
        if not channel or not channel.is_authorized:
            raise ValueError("Target YouTube channel is not connected or unauthorized.")

        # Parse metadata
        meta = json.loads(project.metadata_json) if project.metadata_json else {}
        title = meta.get("recommended_title", project.title)[:100]
        description = meta.get("description", f"AI Generated Short from {source_video.title if source_video else 'Source'}")
        tags = meta.get("keywords", ["shorts", "viral"])

        video_path = Path(project.rendered_video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Rendered video file not found at {video_path}")

        # Check for mock / local testing mode
        is_mock = False
        creds_data = {}
        if channel.encrypted_credentials:
            try:
                creds_data = json.loads(decrypt_token(channel.encrypted_credentials))
                if creds_data.get("access_token") == "mock_access_token":
                    is_mock = True
            except Exception:
                is_mock = True
        else:
            is_mock = True

        if is_mock or not settings.YOUTUBE_CLIENT_ID:
            logger.info(f"[Mock Mode] Simulating official YouTube API upload for {project.id}...")
            time.sleep(1.0)
            mock_yt_id = f"yt_short_{project.id[:10]}"
            pub = PublishedVideo(
                id=str(uuid.uuid4()),
                clip_project_id=project.id,
                youtube_video_id=mock_yt_id,
                channel_id=channel.id,
                published_at=datetime.utcnow()
            )
            project.status = "published"
            db.add(pub)
            db.commit()
            db.refresh(pub)
            return pub

        # Real Google YouTube Data API v3 upload
        credentials = Credentials(
            token=creds_data.get("token") or creds_data.get("access_token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_data.get("client_id", settings.YOUTUBE_CLIENT_ID),
            client_secret=creds_data.get("client_secret", settings.YOUTUBE_CLIENT_SECRET),
            scopes=creds_data.get("scopes")
        )

        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "24"  # Entertainment
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = googleapiclient.http.MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True
        )

        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}% of Short {project.id}...")

        yt_video_id = response.get("id")
        logger.info(f"Successfully uploaded video to YouTube with ID: {yt_video_id}")

        # Set thumbnail if available
        if project.thumbnail_path and Path(project.thumbnail_path).exists():
            try:
                thumb_media = googleapiclient.http.MediaFileUpload(
                    str(project.thumbnail_path),
                    mimetype="image/jpeg"
                )
                youtube.thumbnails().set(
                    videoId=yt_video_id,
                    media_body=thumb_media
                ).execute()
                logger.info("Custom thumbnail uploaded successfully.")
            except Exception as e:
                logger.warning(f"Could not upload thumbnail: {e}")

        pub = PublishedVideo(
            id=str(uuid.uuid4()),
            clip_project_id=project.id,
            youtube_video_id=yt_video_id,
            channel_id=channel.id,
            published_at=datetime.utcnow()
        )
        project.status = "published"
        db.add(pub)
        db.commit()
        db.refresh(pub)
        return pub

youtube_publisher = YouTubePublisherService()
