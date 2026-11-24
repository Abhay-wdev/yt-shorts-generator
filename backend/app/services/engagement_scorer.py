import json
import logging
import math
import re
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("yt_shorts.engagement")

# Hook and reaction keywords
HOOK_PATTERNS = [
    r"\b(why|how|what if|the secret|never|shocking|unbelievable|imagine|look at this|did you know)\b",
    r"\b(wait until|the truth|stop doing|nobody talks about|huge mistake|i was wrong)\b",
    r"\b(here's how|let me show you|number one reason|the biggest)\b"
]

PAYOFF_PATTERNS = [
    r"\b(that's why|in conclusion|and that is how|the result|finally|turns out|which means)\b",
    r"\b(lesson here|takeaway|don't forget to|follow for more|subscribe|now you know)\b"
]

EMOTION_KEYWORDS = [
    "crazy", "insane", "amazing", "terrifying", "hilarious", "shocked",
    "genius", "wild", "unreal", "disaster", "brilliant", "heartbreaking", "screaming"
]

class EngagementScorer:
    """
    Engagement Intelligence Engine:
    Evaluates candidate segments and computes normalized 0-100 score.
    Supports Mode 1 (ACTUAL ANALYTICS) and Mode 2 (PREDICTED ENGAGEMENT).
    Dynamically normalizes weights when private analytics signals are absent.
    """

    DEFAULT_WEIGHTS = {
        "hook_strength": 0.15,
        "story_payoff": 0.15,
        "emotional_intensity": 0.10,
        "topic_importance": 0.10,
        "transcript_interest": 0.10,
        "visual_activity": 0.10,
        "audio_dynamics": 0.05,
        "audience_retention": 0.15,  # only when available
        "watch_time_signal": 0.05,   # only when available
        "interaction_signal": 0.05   # only when available
    }

    def score_segment(
        self,
        segment_text: str,
        start_time: float,
        end_time: float,
        audio_peaks: List[Dict[str, Any]],
        mean_rms: float,
        visual_activity: float,
        actual_retention_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        duration = end_time - start_time
        reasons = []

        # 1. Hook Strength (Opening 5 seconds)
        opening_text = segment_text[:min(120, len(segment_text))].lower()
        hook_hits = sum(1 for p in HOOK_PATTERNS if re.search(p, opening_text, re.IGNORECASE))
        hook_score = min(100.0, 40.0 + (hook_hits * 30.0))
        if hook_hits > 0:
            reasons.append("Strong opening question or curiosity hook detected.")

        # 2. Story / Payoff Quality (Final 8 seconds)
        closing_text = segment_text[-min(140, len(segment_text)):].lower()
        payoff_hits = sum(1 for p in PAYOFF_PATTERNS if re.search(p, closing_text, re.IGNORECASE))
        payoff_score = min(100.0, 45.0 + (payoff_hits * 30.0))
        if payoff_hits > 0:
            reasons.append("Segment features a complete conclusion / payoff.")

        # 3. Emotional / Reaction Intensity
        words_lower = segment_text.lower()
        emotion_hits = sum(1 for k in EMOTION_KEYWORDS if k in words_lower)
        emotional_score = min(100.0, 35.0 + (emotion_hits * 22.0))
        if emotion_hits > 0:
            reasons.append(f"Contains high-valence emotional cues ({emotion_hits} triggers).")

        # 4. Topic Importance (information density & question presence)
        question_count = segment_text.count("?")
        topic_score = min(100.0, 50.0 + (question_count * 25.0) + (min(len(segment_text.split()), 100) * 0.2))
        if question_count > 0:
            reasons.append("Addresses an engaging question.")

        # 5. Transcript Interest (Vocabulary variety & pacing)
        tokens = segment_text.split()
        unique_tokens = set(tokens)
        ttr = (len(unique_tokens) / len(tokens)) if tokens else 0.5
        transcript_score = min(100.0, round(ttr * 110.0, 1))

        # 6. Visual Activity
        visual_score = min(100.0, round(visual_activity * 450.0, 1))
        if visual_activity > 0.08:
            reasons.append("High visual motion / dynamic camera transitions.")

        # 7. Audio Dynamics (Peaks within this segment)
        segment_peaks = [p for p in audio_peaks if start_time <= p["time"] <= end_time]
        audio_score = min(100.0, 40.0 + (len(segment_peaks) * 15.0))
        if len(segment_peaks) >= 2:
            reasons.append("Dynamic vocal emphasis and energy peaks.")

        # Determine Mode and Dynamic Weight Normalization
        scoring_mode = "PREDICTED"
        retention_score = None
        watch_time_score = None
        interaction_score = None

        active_signals = {
            "hook_strength": hook_score,
            "story_payoff": payoff_score,
            "emotional_intensity": emotional_score,
            "topic_importance": topic_score,
            "transcript_interest": transcript_score,
            "visual_activity": visual_score,
            "audio_dynamics": audio_score
        }

        if actual_retention_data and "retention_curve" in actual_retention_data:
            scoring_mode = "ACTUAL_ANALYTICS"
            # Extract time-indexed retention slice
            curve = actual_retention_data["retention_curve"]
            pts = [pt["val"] for pt in curve if start_time <= pt["time"] <= end_time]
            if pts:
                retention_score = min(100.0, max(0.0, float(sum(pts) / len(pts))))
                active_signals["audience_retention"] = retention_score
                active_signals["watch_time_signal"] = min(100.0, retention_score * 0.95)
                active_signals["interaction_signal"] = 75.0
                reasons.append("Backed by actual audience retention data.")

        # Dynamic weight normalization: Ensure sum of active weights == 1.0
        total_raw_weight = sum(self.DEFAULT_WEIGHTS[sig] for sig in active_signals.keys())
        normalized_weights = {
            sig: self.DEFAULT_WEIGHTS[sig] / total_raw_weight
            for sig in active_signals.keys()
        }

        # Calculate weighted overall score (0 to 100)
        overall_score = sum(active_signals[sig] * normalized_weights[sig] for sig in active_signals.keys())
        overall_score = round(min(100.0, max(0.0, overall_score)), 1)
        confidence = 0.92 if scoring_mode == "ACTUAL_ANALYTICS" else 0.82

        return {
            "overall_score": overall_score,
            "scoring_mode": scoring_mode,
            "confidence": confidence,
            "hook_score": round(hook_score, 1),
            "payoff_score": round(payoff_score, 1),
            "emotional_score": round(emotional_score, 1),
            "topic_score": round(topic_score, 1),
            "visual_score": round(visual_score, 1),
            "retention_signal_score": round(retention_score, 1) if retention_score is not None else None,
            "reasons": reasons
        }

engagement_scorer = EngagementScorer()
