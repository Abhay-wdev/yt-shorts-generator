import json
import logging
import uuid
from typing import List, Dict, Any

from .engagement_scorer import engagement_scorer

logger = logging.getLogger("yt_shorts.boundary")

def calculate_temporal_iou(s1: float, e1: float, s2: float, e2: float) -> float:
    """Calculates temporal Intersection-over-Union between two time intervals."""
    intersection = max(0.0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    return intersection / union if union > 0 else 0.0

class BoundaryDetector:
    TARGET_DURATION_BRACKETS = [
        (15.0, 25.0),
        (25.0, 35.0),
        (35.0, 45.0),
        (45.0, 58.0)  # Keep under 60s YouTube Shorts hard limit
    ]

    def extract_candidate_clips(
        self,
        sentences: List[Dict[str, Any]],
        audio_peaks: List[Dict[str, Any]],
        mean_rms: float,
        visual_activity: float,
        actual_retention: Dict[str, Any] = None,
        max_candidates: int = 5,
        iou_threshold: float = 0.35,
        total_duration: float = 60.0
    ) -> List[Dict[str, Any]]:
        """
        Identifies coherent candidate clips bounded by full sentences.
        If sentences are absent or sparse (e.g. gameplay or action footage),
        falls back to audio energy clusters and dynamic window extraction.
        Evaluates each candidate and performs non-maximum suppression (deduplication).
        """
        raw_candidates = []
        n_sentences = len(sentences) if sentences else 0

        # 1. Slide through sentence combinations when speech is present
        if n_sentences > 0:
            for start_idx in range(n_sentences):
                accumulated_text = []
                start_time = sentences[start_idx]["start"]

                for end_idx in range(start_idx, n_sentences):
                    accumulated_text.append(sentences[end_idx]["text"])
                    end_time = sentences[end_idx]["end"]
                    duration = round(end_time - start_time, 2)

                    if duration > 58.0:
                        break  # Exceeds maximum Shorts length

                    # Check if duration falls within any target bracket
                    in_bracket = any(min_d <= duration <= max_d for min_d, max_d in self.TARGET_DURATION_BRACKETS)
                    if in_bracket and len(accumulated_text) >= 1:
                        full_segment_text = " ".join(accumulated_text)
                        scores = engagement_scorer.score_segment(
                            segment_text=full_segment_text,
                            start_time=start_time,
                            end_time=end_time,
                            audio_peaks=audio_peaks,
                            mean_rms=mean_rms,
                            visual_activity=visual_activity,
                            actual_retention_data=actual_retention
                        )

                        candidate = {
                            "id": str(uuid.uuid4()),
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": duration,
                            "text": full_segment_text,
                            **scores
                        }
                        raw_candidates.append(candidate)

        # 2. Resilient fallback for action, gaming, reaction, or sparse speech videos
        if not raw_candidates:
            logger.info("Using audio-visual energy cluster fallback for candidate extraction.")
            effective_dur = max(total_duration, 45.0)
            candidate_windows = []

            # Identify top audio peak moments
            if audio_peaks:
                sorted_peaks = sorted(audio_peaks, key=lambda p: p.get("intensity", 0.0), reverse=True)
                for peak in sorted_peaks[:10]:
                    pt = peak["time"]
                    st = max(0.0, round(pt - 5.0, 2))
                    et = min(effective_dur, round(st + 34.0, 2))
                    if et - st >= 15.0:
                        candidate_windows.append((st, et))

            # If no peaks or insufficient windows, sample evenly across duration
            if len(candidate_windows) < max_candidates:
                step = max(35.0, effective_dur / (max_candidates + 1))
                for i in range(1, max_candidates + 1):
                    st = round(min(effective_dur - 30.0, i * step), 2)
                    st = max(0.0, st)
                    et = min(effective_dur, round(st + 32.0, 2))
                    if et - st >= 15.0:
                        candidate_windows.append((st, et))

            for st, et in candidate_windows:
                dur = round(et - st, 2)
                mins_s, secs_s = int(st // 60), int(st % 60)
                mins_e, secs_e = int(et // 60), int(et % 60)
                desc_text = f"High-Impact Action & Reaction Highlight ({mins_s}:{secs_s:02d} - {mins_e}:{secs_e:02d})"
                scores = engagement_scorer.score_segment(
                    segment_text=desc_text,
                    start_time=st,
                    end_time=et,
                    audio_peaks=audio_peaks,
                    mean_rms=mean_rms,
                    visual_activity=visual_activity,
                    actual_retention_data=actual_retention
                )
                raw_candidates.append({
                    "id": str(uuid.uuid4()),
                    "start_time": st,
                    "end_time": et,
                    "duration": dur,
                    "text": desc_text,
                    **scores
                })

        # Sort all raw candidates by overall_score descending
        raw_candidates.sort(key=lambda c: c["overall_score"], reverse=True)

        # Deduplicate using Temporal IoU (Non-Maximum Suppression)
        selected_candidates: List[Dict[str, Any]] = []
        for cand in raw_candidates:
            is_duplicate = False
            for sel in selected_candidates:
                iou = calculate_temporal_iou(
                    cand["start_time"], cand["end_time"],
                    sel["start_time"], sel["end_time"]
                )
                if iou > iou_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                selected_candidates.append(cand)
                if len(selected_candidates) >= max_candidates:
                    break

        return selected_candidates

boundary_detector = BoundaryDetector()
