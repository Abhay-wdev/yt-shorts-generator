import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.config import settings
from ..core.hardware import hardware_governor
from .smart_reframer import smart_reframer
from .content_classifier import content_classifier

logger = logging.getLogger("yt_shorts.renderer")

class ShortsRendererService:
    def render_short(
        self,
        source_video_path: Path,
        output_short_path: Path,
        start_time: float,
        end_time: float,
        subtitle_ass_path: Optional[Path] = None,
        face_x_ratio: float = 0.5,
        framing_mode: Optional[str] = None,
        apply_hook_zoom: bool = True
    ) -> Dict[str, Any]:
        """
        Renders a production-grade human-edited 9:16 vertical Short (1080x1920):
        - Scene-Aware Intelligent Layout: automatically classifies trading charts/screen demos vs talking heads
        - Sleek 3px editorial progress line (no crude thick yellow bars)
        - Human-grade ASS typography with 2.8s fade-out hook card and clean active word highlight
        - Broadcast Sound Design: 80Hz rumble cut, 3kHz presence EQ, EBU R128 loudness normalization,
          100ms head crossfade, and 250ms tail fade-out to prevent jarring speech cutoffs
        - AMD AMF hardware encoding with graceful libx264 software fallback
        - Faststart metadata for web/YouTube streaming
        """
        t0 = time.time()
        duration = max(1.0, end_time - start_time)

        # 1. Scene-Aware Intelligent Framing Decision
        selected_mode = (framing_mode or "auto").lower().strip()
        if selected_mode in ("auto", "ai_blur_canvas"):
            classification = content_classifier.classify_video_content(
                source_video_path,
                start_time=start_time,
                end_time=end_time
            )
            selected_mode = classification["recommended_layout"]
            logger.info(f"Auto-selected scene layout mode '{selected_mode}' for interval [{start_time:.1f}s-{end_time:.1f}s].")

        subtitle_filename = None
        working_dir = None
        if subtitle_ass_path and subtitle_ass_path.exists():
            subtitle_filename = subtitle_ass_path.name
            working_dir = str(subtitle_ass_path.parent)

        filter_complex = smart_reframer.build_layout_filter_complex(
            layout_mode=selected_mode,
            duration=duration,
            face_x_ratio=face_x_ratio,
            subtitle_filename=subtitle_filename
        )

        # 2. Professional Broadcast Sound Design Chain
        tail_fade_start = max(0.1, duration - 0.25)
        af_str = (
            f"highpass=f=80,"
            f"equalizer=f=3000:t=q:w=1.2:g=1.5,"
            f"loudnorm=I=-14:TP=-1.0:LRA=10,"
            f"afade=t=in:st=0:d=0.10,"
            f"afade=t=out:st={tail_fade_start:.2f}:d=0.25"
        )

        encoder_spec = hardware_governor.get_best_video_encoder()
        primary_codec = encoder_spec["name"]

        def _execute_ffmpeg(codec_name: str, extra_flags: list):
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-to", str(end_time),
                "-i", str(source_video_path.resolve()),
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "0:a?",
                "-af", af_str,
                "-c:v", codec_name
            ]
            cmd.extend(extra_flags)
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                "-movflags", "+faststart",
                str(output_short_path.resolve())
            ])
            logger.info(f"FFmpeg render starting with {codec_name} (mode={selected_mode})...")
            old_cwd = os.getcwd()
            try:
                if working_dir:
                    os.chdir(working_dir)
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as cpe:
                logger.error(f"FFmpeg error: {cpe.stderr}")
                raise
            finally:
                os.chdir(old_cwd)

        used_codec = primary_codec
        try:
            if primary_codec == "h264_amf":
                _execute_ffmpeg("h264_amf", ["-usage", "transcoding", "-quality", "speed", "-rc", "cbr", "-b:v", "6M"])
            else:
                _execute_ffmpeg("libx264", ["-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p"])
        except Exception as e:
            logger.warning(f"Primary encoder '{primary_codec}' failed: {e}. Falling back to software libx264...")
            used_codec = "libx264"
            _execute_ffmpeg("libx264", ["-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p"])

        render_seconds = round(time.time() - t0, 2)
        file_size_mb = round(output_short_path.stat().st_size / (1024 * 1024), 2)
        logger.info(f"Render complete: {output_short_path.name} ({duration:.1f}s) in {render_seconds}s using {used_codec} ({file_size_mb} MB)")

        return {
            "output_path": str(output_short_path),
            "duration": round(duration, 2),
            "encoder": used_codec,
            "framing_mode": selected_mode,
            "render_time_seconds": render_seconds,
            "file_size_mb": file_size_mb
        }

shorts_renderer = ShortsRendererService()
