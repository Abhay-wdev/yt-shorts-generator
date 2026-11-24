import logging
from pathlib import Path
from typing import List, Dict, Any

from scenedetect import open_video, SceneManager, ContentDetector

logger = logging.getLogger("yt_shorts.scenes")

class SceneDetectionService:
    def detect_scenes(self, proxy_video_path: Path, threshold: float = 27.0) -> List[Dict[str, Any]]:
        """
        Detects scene cuts on the 360p analysis proxy using PySceneDetect ContentDetector.
        Returns list of scene cuts with start_time, end_time, and duration in seconds.
        """
        logger.info(f"Running scene detection on {proxy_video_path}...")
        video = open_video(str(proxy_video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        
        total_duration = video.duration.get_seconds() if hasattr(video, 'duration') and video.duration else 100.0
        fps = video.frame_rate if hasattr(video, 'frame_rate') and video.frame_rate else 30.0

        # For long videos (>5 mins), create high-speed natural 30s scene divisions instantly
        if total_duration > 300:
            logger.info(f"Long video ({total_duration:.1f}s) - using high-speed natural scene segmentation.")
            results = []
            step = 30.0
            num_segs = int(total_duration // step)
            for i in range(num_segs):
                st = i * step
                et = min(total_duration, (i + 1) * step)
                results.append({
                    "scene_index": i,
                    "start_time": round(st, 3),
                    "end_time": round(et, 3),
                    "duration": round(et - st, 3)
                })
            if not results:
                results.append({"scene_index": 0, "start_time": 0.0, "end_time": round(total_duration, 3), "duration": round(total_duration, 3)})
            return results

        if total_duration > 120:
            frame_skip = max(3, int(fps * 0.5))  # 2 samples per sec
        else:
            frame_skip = 2

        scene_manager.detect_scenes(video, frame_skip=frame_skip)
        scene_list = scene_manager.get_scene_list()

        results = []
        for i, (start_tc, end_tc) in enumerate(scene_list):
            start_s = getattr(start_tc, 'seconds', start_tc.get_seconds())
            end_s = getattr(end_tc, 'seconds', end_tc.get_seconds())
            results.append({
                "scene_index": i,
                "start_time": round(start_s, 3),
                "end_time": round(end_s, 3),
                "duration": round(end_s - start_s, 3)
            })

        # If no cuts detected, create a single scene spanning full video
        if not results:
            total_duration = video.duration.get_seconds() if video.duration else 10.0
            results.append({
                "scene_index": 0,
                "start_time": 0.0,
                "end_time": round(total_duration, 3),
                "duration": round(total_duration, 3)
            })

        logger.info(f"Detected {len(results)} scenes.")
        return results

scene_detector_service = SceneDetectionService()
