import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import yt_dlp

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.database import SourceVideo, VideoAnalysisJob
from .ingestion import video_ingestion_service
from .unified_analysis import run_video_analysis_task
from ..workers.queue import job_runner

logger = logging.getLogger("yt_shorts.downloader")

class YouTubeDownloaderService:
    def __init__(self):
        self._lock = threading.Lock()
        self.active_downloads: Dict[str, Dict[str, Any]] = {}

    def get_download_progress(self, video_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.active_downloads.get(video_id)

    def get_all_active_downloads(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.active_downloads.values())

    def normalize_channel_url(self, raw_url: str) -> str:
        """Ensures the channel URL points to /videos tab for reliable extraction."""
        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            if url.startswith("@"):
                url = f"https://www.youtube.com/{url}"
            else:
                url = f"https://www.youtube.com/@{url}"
        
        # If it's a channel URL without /videos or /featured, append /videos
        if ("youtube.com/@" in url or "youtube.com/channel/" in url or "youtube.com/c/" in url) and not any(sub in url for sub in ["/videos", "/shorts", "/streams", "/playlists", "watch?v="]):
            url = url.rstrip("/") + "/videos"
        return url

    def explore_channel(self, channel_url: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Extracts recent video entries and metadata from a public YouTube channel URL
        without downloading the media files.
        """
        normalized_url = self.normalize_channel_url(channel_url)
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'skip_download': True,
            'playlistend': max_results,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(normalized_url, download=False)
                if not info:
                    raise ValueError(f"Could not retrieve channel info from {channel_url}")

                entries = info.get('entries', []) or []
                channel_name = info.get('channel') or info.get('uploader') or info.get('title') or "YouTube Channel"
                
                videos = []
                for e in entries:
                    if not e or not e.get('id'):
                        continue
                    v_id = e.get('id')
                    duration = e.get('duration') or 0
                    videos.append({
                        "id": v_id,
                        "title": e.get('title') or f"Video {v_id}",
                        "url": f"https://www.youtube.com/watch?v={v_id}",
                        "duration_seconds": duration,
                        "duration_formatted": f"{int(duration // 60)}:{int(duration % 60):02d}",
                        "thumbnail_url": e.get('thumbnails', [{}])[-1].get('url') if e.get('thumbnails') else f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg",
                        "view_count": e.get('view_count'),
                    })

                return {
                    "channel_name": channel_name,
                    "channel_url": normalized_url,
                    "total_found": len(videos),
                    "videos": videos
                }
        except Exception as e:
            logger.error(f"Failed to explore YouTube channel {channel_url}: {e}")
            raise ValueError(f"Could not load channel videos: {str(e)}")

    def download_and_ingest(
        self,
        video_url: str,
        db: Session,
        title_override: Optional[str] = None,
        auto_analyze: bool = True
    ) -> SourceVideo:
        """
        Immediately creates SourceVideo in database and spawns background download worker
        with real-time downloaded % and remaining % progress tracking.
        """
        temp_id = str(uuid.uuid4())
        
        # 1. Fast metadata pre-fetch (<1s)
        video_title = title_override
        yt_video_id = None
        duration = 0.0
        try:
            with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True, 'skip_download': True}) as ydl:
                quick_info = ydl.extract_info(video_url, download=False)
                if quick_info:
                    yt_video_id = quick_info.get('id')
                    if not video_title:
                        video_title = quick_info.get('title')
                    duration = float(quick_info.get('duration') or 0.0)
        except Exception as e:
            logger.warning(f"Quick info fetch failed, proceeding with fallback: {e}")

        if not video_title:
            video_title = f"YouTube Video ({yt_video_id or temp_id[:8]})"

        # 2. Immediately register in active_downloads
        with self._lock:
            self.active_downloads[temp_id] = {
                "video_id": temp_id,
                "title": video_title,
                "status": "downloading",
                "percent": 0.0,
                "remaining_percent": 100.0,
                "speed": "Connecting to YouTube...",
                "eta": 0,
                "downloaded_mb": 0.0,
                "total_mb": 0.0,
                "error": None
            }

        # 3. Create SourceVideo record immediately so it appears in the Video Library right away
        target_file = settings.DIR_UPLOADS / f"{temp_id}.mp4"
        source_video = SourceVideo(
            id=temp_id,
            title=video_title,
            file_path=str(target_file),
            duration_seconds=duration,
            width=1920,
            height=1080,
            fps=30.0,
            source_status="downloading",
            analysis_status="downloading",
            youtube_video_id=yt_video_id
        )
        db.add(source_video)
        db.commit()
        db.refresh(source_video)

        # 4. Spawn background download thread
        thread = threading.Thread(
            target=self._run_download_task,
            args=(temp_id, video_url, target_file, auto_analyze),
            daemon=True
        )
        thread.start()
        logger.info(f"Spawned background download worker for video {temp_id} ({video_title})")

        return source_video

    def _run_download_task(self, video_id: str, video_url: str, target_file: Path, auto_analyze: bool):
        """Worker thread executing yt-dlp download with live progress hooks and automatic post-ingestion."""
        out_template = str(settings.DIR_UPLOADS / f"{video_id}.%(ext)s")

        def _progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                pct = round((downloaded / total * 100.0), 1) if total > 0 else 0.0
                rem_pct = round(max(0.0, 100.0 - pct), 1)
                speed = d.get('speed') or 0
                speed_str = f"{speed / (1024*1024):.1f} MB/s" if speed else "Calculating..."
                eta = int(d.get('eta') or 0)
                dl_mb = round(downloaded / (1024 * 1024), 1)
                tot_mb = round(total / (1024 * 1024), 1) if total else 0.0

                with self._lock:
                    if video_id in self.active_downloads:
                        self.active_downloads[video_id].update({
                            "status": "downloading",
                            "percent": pct,
                            "remaining_percent": rem_pct,
                            "speed": speed_str,
                            "eta": eta,
                            "downloaded_mb": dl_mb,
                            "total_mb": tot_mb
                        })
            elif d['status'] == 'finished':
                with self._lock:
                    if video_id in self.active_downloads:
                        self.active_downloads[video_id].update({
                            "status": "processing",
                            "percent": 100.0,
                            "remaining_percent": 0.0,
                            "speed": "Download Complete",
                            "eta": 0
                        })

        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            'outtmpl': out_template,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'concurrent_fragment_downloads': 4,
            'buffersize': 1024 * 1024,
            'retries': 3,
            'progress_hooks': [_progress_hook]
        }

        db: Session = SessionLocal()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                downloaded_file = Path(ydl.prepare_filename(info))
                if not downloaded_file.exists():
                    downloaded_file = settings.DIR_UPLOADS / f"{video_id}.mp4"

                # Update status to processing proxy & audio
                with self._lock:
                    if video_id in self.active_downloads:
                        self.active_downloads[video_id].update({
                            "status": "processing",
                            "percent": 100.0,
                            "remaining_percent": 0.0,
                            "speed": "Complete",
                            "eta": 0
                        })

                # Ingest & probe metadata, extract fast audio for Whisper
                source_video = db.query(SourceVideo).filter(SourceVideo.id == video_id).first()
                if source_video:
                    probe_meta = video_ingestion_service.probe_video(downloaded_file)
                    audio_path = settings.DIR_AUDIO / f"{video_id}.wav"
                    video_ingestion_service.extract_audio(downloaded_file, audio_path)
                    proxy_path = downloaded_file

                    source_video.file_path = str(downloaded_file.resolve())
                    source_video.proxy_path = str(proxy_path.resolve())
                    source_video.audio_path = str(audio_path.resolve())
                    source_video.duration_seconds = probe_meta.get("duration", source_video.duration_seconds)
                    source_video.width = probe_meta.get("width", 1920)
                    source_video.height = probe_meta.get("height", 1080)
                    source_video.fps = probe_meta.get("fps", 30.0)
                    source_video.codec_video = probe_meta.get("codec_video", "h264")
                    source_video.codec_audio = probe_meta.get("codec_audio", "aac")
                    source_video.source_status = "youtube_import"
                    source_video.analysis_status = "queued" if auto_analyze else "pending"
                    db.commit()

                    logger.info(f"Successfully downloaded and ingested video {video_id} ({source_video.title})")

                    # Auto-enqueue multi-modal analysis if requested
                    if auto_analyze:
                        analysis_job_id = str(uuid.uuid4())
                        job = VideoAnalysisJob(
                            id=analysis_job_id,
                            source_video_id=source_video.id,
                            status="queued",
                            current_step="queued",
                            progress_percent=0.0
                        )
                        db.add(job)
                        db.commit()

                        job_runner.submit_job(
                            job_id=analysis_job_id,
                            task_fn=run_video_analysis_task,
                            source_video_id=source_video.id,
                            is_heavy=True
                        )
                        logger.info(f"Auto-enqueued analysis job {analysis_job_id} for downloaded video {source_video.id}")

            with self._lock:
                if video_id in self.active_downloads:
                    self.active_downloads[video_id]["status"] = "completed"

            # Clean up active_downloads record after 25 seconds
            time.sleep(25.0)
            with self._lock:
                self.active_downloads.pop(video_id, None)

        except Exception as e:
            logger.error(f"Download task failed for video {video_id}: {e}", exc_info=True)
            with self._lock:
                if video_id in self.active_downloads:
                    self.active_downloads[video_id].update({
                        "status": "failed",
                        "error": str(e)
                    })
            source_video = db.query(SourceVideo).filter(SourceVideo.id == video_id).first()
            if source_video:
                source_video.source_status = "failed"
                source_video.analysis_status = "failed"
                db.commit()
        finally:
            db.close()

youtube_downloader = YouTubeDownloaderService()
