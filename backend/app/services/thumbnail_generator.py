import logging
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import numpy as np

logger = logging.getLogger("yt_shorts.thumbnail")

class ThumbnailGeneratorService:
    def extract_hero_thumbnail(
        self,
        rendered_short_path: Path,
        output_thumb_path: Path,
        sample_frame_count: int = 15
    ) -> Path:
        """
        Samples frames across the rendered 9:16 Short video,
        evaluates visual sharpness using Laplacian variance,
        and saves the highest-fidelity frame as the 9:16 thumbnail image.
        """
        cap = cv2.VideoCapture(str(rendered_short_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file {rendered_short_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise ValueError("Video has zero frames.")

        step = max(1, total_frames // sample_frame_count)
        best_frame = None
        best_sharpness = -1.0

        for idx in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            # Slight penalty for very early or very late frames (avoid fade-ins/outs)
            progress = idx / total_frames
            if progress < 0.08 or progress > 0.92:
                sharpness *= 0.6

            if sharpness > best_sharpness:
                best_sharpness = sharpness
                best_frame = frame

        cap.release()

        if best_frame is not None:
            # Ensure 1080x1920 dimension
            h, w = best_frame.shape[:2]
            if w != 1080 or h != 1920:
                best_frame = cv2.resize(best_frame, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
            cv2.imwrite(str(output_thumb_path), best_frame)
            logger.info(f"Generated 9:16 thumbnail: {output_thumb_path.name} (sharpness={best_sharpness:.1f})")
            return output_thumb_path

        raise RuntimeError("Failed to extract any valid frame for thumbnail.")

thumbnail_generator = ThumbnailGeneratorService()
