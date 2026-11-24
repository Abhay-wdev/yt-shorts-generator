import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from faster_whisper import WhisperModel
from ..core.config import settings

logger = logging.getLogger("yt_shorts.transcription")

class TranscriptionService:
    _model = None

    @classmethod
    def get_model(cls) -> WhisperModel:
        if cls._model is None:
            logger.info(f"Loading faster-whisper model '{settings.WHISPER_MODEL_SIZE}' on CPU (compute_type={settings.WHISPER_COMPUTE_TYPE})...")
            cls._model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device="cpu",
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                cpu_threads=4,
                num_workers=1
            )
            logger.info("faster-whisper model loaded successfully.")
        return cls._model

    def transcribe(self, audio_path: Path, on_progress=None) -> Dict[str, Any]:
        """
        Transcribes audio with word-level timestamps using faster-whisper.
        Returns standardized full transcript, words list, and sentence segments.
        Optimized with greedy decoding, condition_on_previous_text=False, and VAD for maximum speed.
        """
        model = self.get_model()
        segments_generator, info = model.transcribe(
            str(audio_path),
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400, threshold=0.45)
        )

        detected_language = info.language
        language_probability = info.language_probability
        total_duration = info.duration if hasattr(info, 'duration') and info.duration else 1.0
        
        words_list: List[Dict[str, Any]] = []
        sentences_list: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for segment in segments_generator:
            if on_progress and total_duration > 0:
                on_progress(segment.end, total_duration)
            full_text_parts.append(segment.text.strip())
            sentences_list.append({
                "text": segment.text.strip(),
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "avg_logprob": round(segment.avg_logprob, 3)
            })

            if segment.words:
                for w in segment.words:
                    words_list.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "confidence": round(w.probability, 3)
                    })

        full_transcript = " ".join(full_text_parts)

        return {
            "language": detected_language,
            "language_probability": round(language_probability, 3),
            "text_full": full_transcript,
            "words": words_list,
            "sentences": sentences_list
        }

transcription_service = TranscriptionService()
