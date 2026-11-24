import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import soundfile as sf

logger = logging.getLogger("yt_shorts.audio")

class AudioAnalyzer:
    def analyze_audio(self, wav_path: Path, chunk_duration_ms: int = 100) -> Dict[str, Any]:
        """
        Analyzes audio waveform:
        - RMS energy timeline
        - Speech vs silence intervals
        - Audio peak detection
        - Mean intensity
        """
        data, sample_rate = sf.read(str(wav_path))
        if data.ndim > 1:
            data = data.mean(axis=1)  # Convert to mono if multi-channel

        total_samples = len(data)
        duration_seconds = total_samples / sample_rate
        chunk_samples = int(sample_rate * (chunk_duration_ms / 1000.0))

        rms_timeline = []
        silence_intervals = []
        peaks = []

        silence_threshold = 0.015  # Amplitude threshold
        in_silence = False
        silence_start = 0.0

        for i in range(0, total_samples, chunk_samples):
            chunk = data[i:i + chunk_samples]
            if len(chunk) == 0:
                continue

            rms = float(np.sqrt(np.mean(chunk**2)))
            timestamp = round(i / sample_rate, 3)
            rms_timeline.append({"time": timestamp, "rms": round(rms, 4)})

            # Silence segmentation
            if rms < silence_threshold:
                if not in_silence:
                    in_silence = True
                    silence_start = timestamp
            else:
                if in_silence:
                    silence_end = timestamp
                    if silence_end - silence_start >= 0.4:  # Only count silences >= 400ms
                        silence_intervals.append({
                            "start": round(silence_start, 3),
                            "end": round(silence_end, 3),
                            "duration": round(silence_end - silence_start, 3)
                        })
                    in_silence = False

        if in_silence:
            silence_intervals.append({
                "start": round(silence_start, 3),
                "end": round(duration_seconds, 3),
                "duration": round(duration_seconds - silence_start, 3)
            })

        all_rms = [pt["rms"] for pt in rms_timeline]
        mean_rms = float(np.mean(all_rms)) if all_rms else 0.0
        max_rms = float(np.max(all_rms)) if all_rms else 0.0

        # Adaptive peak detection: relative to mean energy, minimum 0.035
        peak_threshold = max(0.035, min(0.14, mean_rms * 1.7))
        peaks = [
            {"time": pt["time"], "intensity": pt["rms"]}
            for pt in rms_timeline
            if pt["rms"] >= peak_threshold
        ]

        sorted_peaks = sorted(peaks, key=lambda p: p["intensity"], reverse=True)

        return {
            "duration": round(duration_seconds, 3),
            "sample_rate": sample_rate,
            "mean_rms": round(mean_rms, 4),
            "max_rms": round(max_rms, 4),
            "peaks_count": len(peaks),
            "peaks": sorted_peaks[:100],  # Top 100 energetic peaks across full video
            "silence_intervals": silence_intervals,
            "rms_timeline_sample": rms_timeline[::10]  # Downsample for JSON storage efficiency
        }

audio_analyzer = AudioAnalyzer()
