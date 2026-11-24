import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.database import SourceVideo, EngagementCandidate, ClipProject, QCReport, Transcript, VideoAnalysisJob
from ..workers.queue import job_runner
from .caption_engine import caption_engine
from .smart_reframer import smart_reframer
from .shorts_renderer import shorts_renderer
from .metadata_generator import metadata_generator
from .thumbnail_generator import thumbnail_generator
from .quality_control import quality_control_engine

logger = logging.getLogger("yt_shorts.unified_shorts")

def run_render_short_task(job_id: str, clip_project_id: str):
    """
    Background worker executing complete Short production pipeline:
    1. Word-level subtitle generation (.ass)
    2. Smart face/subject tracking reframing
    3. FFmpeg 9:16 vertical render (AMF/libx264)
    4. AI SEO Metadata generation
    5. Sharp 9:16 thumbnail frame extraction
    6. Automated Quality Control validation gate
    """
    db: Session = SessionLocal()
    try:
        project = db.query(ClipProject).filter(ClipProject.id == clip_project_id).first()
        if not project:
            logger.error(f"Cannot render short: Project {clip_project_id} not found.")
            return

        source_video = db.query(SourceVideo).filter(SourceVideo.id == project.source_video_id).first()
        if not source_video:
            logger.error(f"Source video {project.source_video_id} not found.")
            return

        project.status = "rendering"
        db.commit()

        # Retrieve transcript words
        transcript = db.query(Transcript).filter(Transcript.source_video_id == source_video.id).first()
        words = json.loads(transcript.words_json) if transcript and transcript.words_json else []

        # Retrieve visual analysis face coordinates
        analysis_job = db.query(VideoAnalysisJob).filter(
            VideoAnalysisJob.source_video_id == source_video.id,
            VideoAnalysisJob.status == "completed"
        ).order_by(VideoAnalysisJob.completed_at.desc()).first()

        face_coordinates = []
        if analysis_job and analysis_job.raw_analysis_json:
            raw_data = json.loads(analysis_job.raw_analysis_json)
            face_coordinates = raw_data.get("visual", {}).get("face_coordinates", [])

        # 1. Smart reframing crop calculation
        job_runner.update_progress(job_id, 15.0)
        face_x, crop_expr = smart_reframer.calculate_crop_window(
            face_coordinates=face_coordinates,
            start_time=project.start_time,
            end_time=project.end_time,
            source_width=source_video.width,
            source_height=source_video.height
        )

        # 2. Generate ASS subtitle file (bouncing karaoke + emojis + top hook header)
        job_runner.update_progress(job_id, 30.0)
        ass_filename = f"{project.id}.ass"
        ass_path = settings.DIR_SHORTS / ass_filename
        
        hook_header = project.title
        if hook_header.startswith("Short - ") or not hook_header.strip():
            hook_header = source_video.title[:45]

        caption_engine.generate_ass_subtitles(
            words=words,
            start_time=project.start_time,
            end_time=project.end_time,
            output_ass_path=ass_path,
            style_name=project.caption_style or "editorial_gold",
            hook_title=hook_header
        )

        # 3. Render 9:16 vertical video using AI automated layout
        job_runner.update_progress(job_id, 50.0)
        output_mp4_path = settings.DIR_SHORTS / f"{project.id}.mp4"
        shorts_renderer.render_short(
            source_video_path=Path(source_video.file_path),
            output_short_path=output_mp4_path,
            start_time=project.start_time,
            end_time=project.end_time,
            subtitle_ass_path=ass_path,
            face_x_ratio=face_x,
            framing_mode=project.framing_mode or "auto"
        )
        project.rendered_video_path = str(output_mp4_path)

        # 4. Generate Metadata
        job_runner.update_progress(job_id, 75.0)
        segment_words = [w["word"] for w in words if project.start_time <= w["start"] <= project.end_time]
        segment_text = " ".join(segment_words) if segment_words else project.title
        metadata = metadata_generator.generate_metadata(segment_text, source_video.title)
        project.metadata_json = json.dumps(metadata)
        project.title = metadata["recommended_title"]

        # 5. Extract 9:16 Thumbnail
        job_runner.update_progress(job_id, 85.0)
        thumb_path = settings.DIR_THUMBNAILS / f"{project.id}.jpg"
        thumbnail_generator.extract_hero_thumbnail(output_mp4_path, thumb_path)
        project.thumbnail_path = str(thumb_path)

        # 6. Quality Control Gate
        job_runner.update_progress(job_id, 92.0)
        qc_result = quality_control_engine.evaluate_short(output_mp4_path, ass_path)

        qc_report = QCReport(
            id=str(uuid.uuid4()),
            clip_project_id=project.id,
            passed=qc_result["passed"],
            overall_score=qc_result["overall_score"],
            video_checks_json=json.dumps(qc_result["video_checks"]),
            audio_checks_json=json.dumps(qc_result["audio_checks"]),
            caption_checks_json=json.dumps(qc_result["caption_checks"]),
            framing_checks_json=json.dumps(qc_result["framing_checks"]),
            repaired=False
        )
        db.add(qc_report)

        project.status = "qc_passed" if qc_result["passed"] else "qc_failed"
        db.commit()

        job_runner.update_progress(job_id, 100.0)
        logger.info(f"Short project {project.id} rendered and QC verified (status: {project.status})!")
    except Exception as e:
        logger.error(f"Render failed for project {clip_project_id}: {e}", exc_info=True)
        project = db.query(ClipProject).filter(ClipProject.id == clip_project_id).first()
        if project:
            project.status = "failed"
            db.commit()
    finally:
        db.close()
