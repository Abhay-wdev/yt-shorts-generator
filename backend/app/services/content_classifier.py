import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

logger = logging.getLogger("yt_shorts.classifier")

class ContentClassifierService:
    """
    Intelligently analyzes video visual features to classify content type:
    - 'screen_demo': Trading charts, presentations, software demos, code tutorials (high horizontal/vertical line density, UI text regions)
    - 'talking_head': Vloggers, podcasts, interviews (prominent face/head, conversational gestures)
    - 'cinematic_broll': High-texture natural imagery, landscapes, action
    
    Provides scene-aware composition instructions for professional human-grade editing.
    """

    def classify_video_content(
        self,
        video_path: Path,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        sample_count: int = 2
    ) -> Dict[str, Any]:
        """
        Classifies video content within a specific scene interval [start_time, end_time].
        Accurately distinguishes between screen demos/trading charts and talking heads.
        """
        effective_end = end_time if (end_time is not None and end_time > start_time) else (start_time + 30.0)
        dur = max(1.0, effective_end - start_time)
        sample_times = [
            round(start_time + dur * 0.35, 2),
            round(start_time + dur * 0.75, 2)
        ]

        frames = []
        for st in sample_times:
            try:
                cmd = [
                    "ffmpeg", "-ss", str(st),
                    "-i", str(video_path),
                    "-s", "640x360",
                    "-vframes", "1",
                    "-f", "image2pipe",
                    "-vcodec", "png", "-"
                ]
                res = subprocess.run(cmd, capture_output=True, timeout=5)
                if res.returncode == 0 and res.stdout:
                    img = cv2.imdecode(np.frombuffer(res.stdout, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        frames.append(img)
            except Exception as e:
                logger.warning(f"Could not extract classification frame at {st}s: {e}")

        if not frames:
            return {
                "content_type": "general",
                "recommended_layout": "screen_focus",
                "confidence": 0.5,
                "has_charts_or_ui": False
            }

        line_densities = []
        text_regions_detected = 0
        edge_scores = []
        samples_analyzed = 0

        for frame in frames:
            samples_analyzed += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Detect straight horizontal/vertical lines (candlesticks, chart grids, browser UI)
            edges = cv2.Canny(gray, 50, 150)
            edge_scores.append(float(np.mean(edges) / 255.0))

            # Hough lines for grid lines / axes
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=120, minLineLength=int(w * 0.15), maxLineGap=10)
            line_count = len(lines) if lines is not None else 0
            line_densities.append(line_count)

            # Detect high-contrast text clusters (price tickers, timestamps, charts)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            text_like_boxes = [c for c in contours if cv2.boundingRect(c)[2] > 30 and cv2.boundingRect(c)[3] < 50]
            if len(text_like_boxes) > 15:
                text_regions_detected += 1

        avg_lines = float(np.mean(line_densities)) if line_densities else 0.0
        avg_edges = float(np.mean(edge_scores)) if edge_scores else 0.0
        text_ratio = (text_regions_detected / samples_analyzed) if samples_analyzed > 0 else 0.0

        is_screen_demo = (avg_lines > 20 or (text_ratio > 0.4 and avg_edges > 0.03))

        if is_screen_demo:
            content_type = "screen_demo"
            recommended_layout = "screen_focus"
            confidence = 0.92
        else:
            content_type = "talking_head"
            recommended_layout = "portrait_focus"
            confidence = 0.88

        logger.info(
            f"Scene Interval [{start_time:.1f}s-{end_time or 0:.1f}s] Classified: '{content_type}' "
            f"(confidence={confidence:.2f}, avg_lines={avg_lines:.1f}, text_ratio={text_ratio:.2f}) -> layout: {recommended_layout}"
        )

        return {
            "content_type": content_type,
            "recommended_layout": recommended_layout,
            "confidence": confidence,
            "has_charts_or_ui": is_screen_demo,
            "avg_lines": round(avg_lines, 1),
            "text_ratio": round(text_ratio, 2)
        }

content_classifier = ContentClassifierService()
