import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import validate_safe_path
from ..models.database import SourceVideo

logger = logging.getLogger("yt_shorts.ingestion")

class VideoIngestionService:
    def probe_video(self, file_path: Path) -> Dict[str, Any]:
        """Uses ffprobe to extract reliable video/audio metadata."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(res.stdout)
        
        format_info = probe_data.get("format", {})
        duration = float(format_info.get("duration", 0.0))
        
        video_stream = None
        audio_stream = None
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream
                
        if not video_stream:
            raise ValueError(f"No video stream found in {file_path}")

        width = int(video_stream.get("width", 1920))
        height = int(video_stream.get("height", 1080))
        
        # Calculate frame rate
        r_frame_rate = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = map(int, r_frame_rate.split("/"))
            fps = round(num / den, 2) if den != 0 else 30.0
        except Exception:
            fps = 30.0

        codec_video = video_stream.get("codec_name", "h264")
        codec_audio = audio_stream.get("codec_name", "aac") if audio_stream else None

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "codec_video": codec_video,
            "codec_audio": codec_audio
        }

    def generate_proxy_and_audio(self, input_video: Path, output_proxy: Path, output_wav: Path):
        """Generates 360p analysis proxy and 16kHz mono WAV audio simultaneously in a single FFmpeg pass."""
        proxy_ready = output_proxy.exists() and output_proxy.stat().st_size > 0
        audio_ready = output_wav.exists() and output_wav.stat().st_size > 0
        
        if proxy_ready and audio_ready:
            return

        cmd = ["ffmpeg", "-y", "-i", str(input_video)]
        if not proxy_ready:
            cmd.extend([
                "-vf", "scale=-2:360",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-an",
                str(output_proxy)
            ])
        if not audio_ready:
            cmd.extend([
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(output_wav)
            ])
        
        subprocess.run(cmd, capture_output=True, check=True)

    def generate_proxy(self, input_video: Path, output_proxy: Path) -> Path:
        """Generates a fast 360p analysis proxy (scale=-2:360) for low-memory computer vision."""
        if output_proxy.exists() and output_proxy.stat().st_size > 0:
            return output_proxy
            
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vf", "scale=-2:360",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-an",
            str(output_proxy)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_proxy

    def extract_audio(self, input_video: Path, output_wav: Path) -> Path:
        """Extracts 16kHz mono 16-bit WAV audio for Whisper and voice activity detection."""
        if output_wav.exists() and output_wav.stat().st_size > 0:
            return output_wav

        output_wav.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_wav

    def ingest_local_file(
        self,
        source_path: Path,
        title: str,
        db: Session,
        source_status: str = "owned",
        channel_id: Optional[str] = None
    ) -> SourceVideo:
        """Copies or stores local video file, probes it, creates proxy & audio, and records in database."""
        video_uuid = str(uuid.uuid4())
        ext = source_path.suffix or ".mp4"
        dest_filename = f"{video_uuid}{ext}"
        dest_path = settings.DIR_UPLOADS / dest_filename

        if source_path != dest_path:
            shutil.copy2(source_path, dest_path)

        # Probe metadata
        meta = self.probe_video(dest_path)

        # Generate 360p proxy and WAV audio in one unified FFmpeg pass
        proxy_path = settings.DIR_PROXIES / f"{video_uuid}_360p.mp4"
        audio_path = settings.DIR_AUDIO / f"{video_uuid}.wav"
        
        self.generate_proxy_and_audio(dest_path, proxy_path, audio_path)

        source_video = SourceVideo(
            id=video_uuid,
            channel_id=channel_id,
            title=title,
            file_path=str(dest_path),
            proxy_path=str(proxy_path),
            audio_path=str(audio_path),
            duration_seconds=meta["duration"],
            width=meta["width"],
            height=meta["height"],
            fps=meta["fps"],
            codec_video=meta["codec_video"],
            codec_audio=meta["codec_audio"],
            source_status=source_status,
            analysis_status="pending"
        )
        db.add(source_video)
        db.commit()
        db.refresh(source_video)
        return source_video

video_ingestion_service = VideoIngestionService()
