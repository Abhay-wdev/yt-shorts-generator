import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from .audio_analyzer import audio_analyzer
from .scene_detector import scene_detector_service
from .transcription import transcription_service
from .visual_analyzer import visual_analyzer_service
from .boundary_detector import boundary_detector
from .ingestion import video_ingestion_service
from ..core.config import settings
from ..core.database import SessionLocal
from ..models.database import SourceVideo, VideoAnalysisJob, Transcript, SceneSegment, EngagementCandidate
from ..workers.queue import job_runner

logger = logging.getLogger("yt_shorts.unified_analysis")

def run_video_analysis_task(job_id: str, source_video_id: str):
    """
    Background worker task executing multi-modal intelligence extraction:
    Step 1: Audio Energy & Silence
    Step 2: Faster-Whisper Word-Level Transcription
    Step 3: PySceneDetect Scene Transitions
    Step 4: Visual Activity & Face Tracking
    Step 5: Persist Standardized Analysis JSON & Entities
    """
    db: Session = SessionLocal()
    try:
        video = db.query(SourceVideo).filter(SourceVideo.id == source_video_id).first()
        job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.id == job_id).first()
        if not video or not job:
            logger.error(f"Cannot run analysis task: video {source_video_id} or job {job_id} missing.")
            return

        job.status = "processing"
        job.started_at = datetime.utcnow()
        video.analysis_status = "analyzing"
        db.commit()

        # Step 0: Fast audio extraction (if missing) and determine video target
        file_path = Path(video.file_path)
        proxy_path = Path(video.proxy_path) if video.proxy_path else (settings.DIR_PROXIES / f"{video.id}.mp4")
        audio_path = Path(video.audio_path) if video.audio_path else (settings.DIR_AUDIO / f"{video.id}.wav")

        if not audio_path.exists() or audio_path.stat().st_size == 0:
            job.current_step = "Extracting Audio Waveform"
            job_runner.update_progress(job_id, 5.0)
            db.commit()
            video_ingestion_service.extract_audio(file_path, audio_path)
            video.audio_path = str(audio_path.resolve())
            db.commit()

        video_target = proxy_path if (proxy_path.exists() and proxy_path.stat().st_size > 0) else file_path

        # Step 1: Audio Analysis
        job.current_step = "Analyzing Audio Dynamics & Peaks"
        job.progress_percent = 12.0
        job_runner.update_progress(job_id, 12.0)
        db.commit()
        audio_res = audio_analyzer.analyze_audio(Path(video.audio_path))

        # Immediately extract initial energetic candidates so users get instant output in < 2 seconds!
        try:
            initial_candidates = boundary_detector.extract_candidate_clips(
                sentences=[],
                audio_peaks=audio_res.get("peaks", []),
                mean_rms=audio_res.get("mean_rms", 0.05),
                visual_activity=0.05,
                max_candidates=8,
                total_duration=video.duration_seconds
            )
            if initial_candidates:
                db.query(EngagementCandidate).filter(EngagementCandidate.source_video_id == video.id).delete()
                for c in initial_candidates:
                    cand_record = EngagementCandidate(
                        id=c.get("id") or str(uuid.uuid4()),
                        source_video_id=video.id,
                        start_time=c["start_time"],
                        end_time=c["end_time"],
                        duration=c["duration"],
                        overall_score=c["overall_score"],
                        scoring_mode=c["scoring_mode"],
                        confidence=c["confidence"],
                        hook_score=c["hook_score"],
                        payoff_score=c["payoff_score"],
                        emotional_score=c["emotional_score"],
                        topic_score=c["topic_score"],
                        visual_score=c["visual_score"],
                        retention_signal_score=c.get("retention_signal_score"),
                        reasons_json=json.dumps(c.get("reasons", []))
                    )
                    db.add(cand_record)
                db.commit()
                logger.info(f"Instant initial candidates ({len(initial_candidates)}) ready for video {video.id} in 2s!")
        except Exception as e:
            logger.warning(f"Could not save instant initial candidates: {e}")

        # Step 2: Transcription with live progress callback
        job.current_step = "Transcribing Speech (Whisper AI)"
        job.progress_percent = 20.0
        job_runner.update_progress(job_id, 20.0)
        db.commit()

        last_progress_update = [0.0]
        def _on_whisper(curr_s, total_s):
            now = time.time()
            if now - last_progress_update[0] >= 1.0:
                pct = 20.0 + min(48.0, (curr_s / total_s) * 48.0)
                job.progress_percent = round(pct, 1)
                mins_curr = int(curr_s // 60)
                secs_curr = int(curr_s % 60)
                mins_tot = int(total_s // 60)
                secs_tot = int(total_s % 60)
                job.current_step = f"Transcribing Speech ({mins_curr}:{secs_curr:02d} / {mins_tot}:{secs_tot:02d})"
                job_runner.update_progress(job_id, pct)
                try:
                    db.commit()
                except Exception:
                    pass
                last_progress_update[0] = now

        trans_res = transcription_service.transcribe(Path(video.audio_path), on_progress=_on_whisper)

        # Step 3: Scene Detection
        job.current_step = "Detecting Scene Transitions"
        job.progress_percent = 70.0
        job_runner.update_progress(job_id, 70.0)
        db.commit()
        scene_res = scene_detector_service.detect_scenes(video_target)

        # Step 4: Visual Activity & Face Coordinates
        job.current_step = "Tracking Visual Activity & Motion"
        job.progress_percent = 82.0
        job_runner.update_progress(job_id, 82.0)
        db.commit()
        visual_res = visual_analyzer_service.analyze_visual_stream(video_target)

        # Step 5: Save Database Records & Extract Best Shorts Moments
        job.current_step = "Scoring Engagement & Extracting Best Moments"
        job.progress_percent = 90.0
        job_runner.update_progress(job_id, 90.0)

        # 1. Transcript record
        transcript_record = db.query(Transcript).filter(Transcript.source_video_id == video.id).first()
        if not transcript_record:
            transcript_record = Transcript(
                source_video_id=video.id,
                language=trans_res.get("language", "en"),
                text_full=trans_res.get("text_full", ""),
                words_json=json.dumps(trans_res.get("words", [])),
                sentences_json=json.dumps(trans_res.get("sentences", []))
            )
            db.add(transcript_record)
        else:
            transcript_record.language = trans_res.get("language", "en")
            transcript_record.text_full = trans_res.get("text_full", "")
            transcript_record.words_json = json.dumps(trans_res.get("words", []))
            transcript_record.sentences_json = json.dumps(trans_res.get("sentences", []))

        # 2. Scene segments
        db.query(SceneSegment).filter(SceneSegment.source_video_id == video.id).delete()
        for sc in scene_res:
            seg = SceneSegment(
                source_video_id=video.id,
                start_time=sc["start_time"],
                end_time=sc["end_time"],
                duration=sc["duration"],
                visual_activity_score=visual_res.get("mean_activity", 0.0)
            )
            db.add(seg)

        # 3. Standardized Analysis JSON Payload
        analysis_payload = {
            "source_video_id": video.id,
            "duration": video.duration_seconds,
            "audio": audio_res,
            "transcript": trans_res,
            "scenes": scene_res,
            "visual": visual_res,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        job.raw_analysis_json = json.dumps(analysis_payload)

        # 4. Auto-generate Candidate Clips & Opportunity Moments immediately
        sentences = trans_res.get("sentences", [])
        audio_peaks = audio_res.get("peaks", [])
        mean_rms = audio_res.get("mean_rms", 0.05)
        visual_activity = visual_res.get("mean_activity", 0.05)

        candidates = boundary_detector.extract_candidate_clips(
            sentences=sentences,
            audio_peaks=audio_peaks,
            mean_rms=mean_rms,
            visual_activity=visual_activity,
            max_candidates=8,
            total_duration=video.duration_seconds
        )
        db.query(EngagementCandidate).filter(EngagementCandidate.source_video_id == video.id).delete()
        for c in candidates:
            cand_record = EngagementCandidate(
                id=c.get("id") or str(uuid.uuid4()),
                source_video_id=video.id,
                start_time=c["start_time"],
                end_time=c["end_time"],
                duration=c["duration"],
                overall_score=c["overall_score"],
                scoring_mode=c["scoring_mode"],
                confidence=c["confidence"],
                hook_score=c["hook_score"],
                payoff_score=c["payoff_score"],
                emotional_score=c["emotional_score"],
                topic_score=c["topic_score"],
                visual_score=c["visual_score"],
                retention_signal_score=c.get("retention_signal_score"),
                reasons_json=json.dumps(c.get("reasons", []))
            )
            db.add(cand_record)

        job.status = "completed"
        job.current_step = "Analysis Completed - Candidates Ready!"
        job.progress_percent = 100.0
        job.completed_at = datetime.utcnow()
        video.analysis_status = "completed"
        db.commit()

        logger.info(f"Analysis completed successfully for video {video.id} with {len(candidates)} candidates ready!")
    except Exception as e:
        logger.error(f"Analysis failed for video {source_video_id}: {e}", exc_info=True)
        job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
        video = db.query(SourceVideo).filter(SourceVideo.id == source_video_id).first()
        if video:
            video.analysis_status = "failed"
        db.commit()
    finally:
        db.close()
