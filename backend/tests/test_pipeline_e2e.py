import json
import os
import shutil
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, init_db, engine, Base
from backend.app.core.security import encrypt_token, decrypt_token, validate_safe_path
from backend.app.core.hardware import hardware_governor
from backend.app.models.database import (
    SourceVideo, VideoAnalysisJob, Transcript, SceneSegment,
    EngagementCandidate, ClipProject, QCReport, PublishedVideo, YouTubeChannel
)
from backend.app.services.ingestion import video_ingestion_service
from backend.app.services.audio_analyzer import audio_analyzer
from backend.app.services.scene_detector import scene_detector_service
from backend.app.services.visual_analyzer import visual_analyzer_service
from backend.app.services.engagement_scorer import engagement_scorer
from backend.app.services.boundary_detector import boundary_detector
from backend.app.services.smart_reframer import smart_reframer
from backend.app.services.caption_engine import caption_engine
from backend.app.services.shorts_renderer import shorts_renderer
from backend.app.services.metadata_generator import metadata_generator
from backend.app.services.thumbnail_generator import thumbnail_generator
from backend.app.services.quality_control import quality_control_engine
from backend.app.services.publisher import youtube_publisher
from backend.app.services.learning_engine import learning_engine

TEST_VIDEO_PATH = Path(r"c:\Users\abhay\Music\Antigravity Sites\short-room-309.mp4")

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

def test_hardware_governor_detection():
    """Verifies that Hardware Governor detects Ryzen CPU, Radeon GPU, and video encoder."""
    hw = hardware_governor.get_hardware_status()
    assert "cpu" in hw
    assert "ram" in hw
    assert "gpu" in hw
    assert "video_acceleration" in hw
    assert hw["ram"]["pressure_state"] in ["NORMAL", "WARNING", "CRITICAL"]
    assert hw["video_acceleration"]["name"] in ["h264_amf", "libx264"]

def test_security_token_encryption():
    """Verifies that OAuth token encryption and decryption preserves plain text."""
    secret = "ya29.a0AfH6SMD_mock_test_token_2026"
    encrypted = encrypt_token(secret)
    assert encrypted != secret
    decrypted = decrypt_token(encrypted)
    assert decrypted == secret

def test_security_path_traversal_validation():
    """Verifies path traversal validation prevents unauthorized access."""
    root = settings.DIR_UPLOADS
    safe = root / "valid.mp4"
    unsafe = root / ".." / ".." / "Windows" / "System32"
    assert validate_safe_path(safe, root) is True
    assert validate_safe_path(unsafe, root) is False

def test_video_ingestion_and_metadata_probe(db_session: Session):
    """Verifies FFprobe ingestion, metadata extraction, proxy and audio generation."""
    assert TEST_VIDEO_PATH.exists(), f"Sample video not found at {TEST_VIDEO_PATH}"
    
    source = video_ingestion_service.ingest_local_file(
        source_path=TEST_VIDEO_PATH,
        title="Test Ingest Room 309",
        db=db_session,
        source_status="owned"
    )
    assert source.id is not None
    assert source.duration_seconds > 0.0
    assert source.width > 0
    assert source.height > 0
    assert Path(source.proxy_path).exists()
    assert Path(source.audio_path).exists()

    # Store for subsequent tests
    pytest.test_source_id = source.id
    pytest.test_source_video = source

def test_audio_analysis():
    """Verifies audio RMS energy curve, peaks, and silence segmentation."""
    source: SourceVideo = pytest.test_source_video
    audio_res = audio_analyzer.analyze_audio(Path(source.audio_path))
    assert audio_res["duration"] > 0
    assert "mean_rms" in audio_res
    assert "peaks" in audio_res
    assert "silence_intervals" in audio_res
    pytest.audio_res = audio_res

def test_scene_detection():
    """Verifies scene transition detection on proxy video."""
    source: SourceVideo = pytest.test_source_video
    scenes = scene_detector_service.detect_scenes(Path(source.proxy_path))
    assert len(scenes) >= 1
    assert scenes[0]["start_time"] >= 0.0
    pytest.scenes = scenes

def test_visual_activity_and_subject_tracking():
    """Verifies visual activity and motion centroid coordinates."""
    source: SourceVideo = pytest.test_source_video
    vis_res = visual_analyzer_service.analyze_visual_stream(Path(source.proxy_path))
    assert vis_res["duration"] > 0
    assert 0.0 <= vis_res["mean_activity"] <= 1.0
    assert 0.1 <= vis_res["median_face_x"] <= 0.9
    pytest.vis_res = vis_res

def test_engagement_scoring_modes():
    """Verifies engagement scoring in both Predicted and Actual Analytics modes."""
    # Mode 2: PREDICTED
    pred = engagement_scorer.score_segment(
        segment_text="Why does this happen? The shocking truth about room 309 revealed. That's why you must subscribe!",
        start_time=5.0,
        end_time=32.0,
        audio_peaks=[{"time": 10.0, "intensity": 0.2}],
        mean_rms=0.08,
        visual_activity=0.12,
        actual_retention_data=None
    )
    assert pred["scoring_mode"] == "PREDICTED"
    assert 0.0 <= pred["overall_score"] <= 100.0
    assert len(pred["reasons"]) > 0

    # Mode 1: ACTUAL ANALYTICS
    mock_retention = {
        "retention_curve": [{"time": t, "val": 82.0} for t in range(5, 33)]
    }
    actual = engagement_scorer.score_segment(
        segment_text="Why does this happen? The shocking truth about room 309 revealed.",
        start_time=5.0,
        end_time=32.0,
        audio_peaks=[{"time": 10.0, "intensity": 0.2}],
        mean_rms=0.08,
        visual_activity=0.12,
        actual_retention_data=mock_retention
    )
    assert actual["scoring_mode"] == "ACTUAL_ANALYTICS"
    assert actual["retention_signal_score"] is not None

def test_boundary_detection_and_deduplication():
    """Verifies sentence-bounded clip extraction with temporal IoU deduplication."""
    mock_sentences = [
        {"text": "Why do people always ignore room 309 in this hotel?", "start": 2.0, "end": 6.5},
        {"text": "The manager told us that strange things happen every midnight.", "start": 6.6, "end": 12.0},
        {"text": "When we opened the door, the entire room was completely silent.", "start": 12.1, "end": 18.0},
        {"text": "And that is why you should never stay on the third floor.", "start": 18.1, "end": 24.5},
        {"text": "Follow for more real mystery investigations.", "start": 24.6, "end": 28.0}
    ]
    candidates = boundary_detector.extract_candidate_clips(
        sentences=mock_sentences,
        audio_peaks=[{"time": 8.0, "intensity": 0.2}],
        mean_rms=0.06,
        visual_activity=0.1,
        max_candidates=3
    )
    assert len(candidates) >= 1
    assert candidates[0]["duration"] >= 15.0
    assert candidates[0]["overall_score"] > 0
    pytest.best_candidate = candidates[0]

def test_caption_generation():
    """Verifies Advanced SubStation Alpha (.ass) subtitle file generation."""
    mock_words = [
        {"word": "Why", "start": 2.0, "end": 2.4, "probability": 0.95},
        {"word": "do", "start": 2.4, "end": 2.6, "probability": 0.95},
        {"word": "people", "start": 2.6, "end": 3.0, "probability": 0.95},
        {"word": "ignore", "start": 3.0, "end": 3.5, "probability": 0.95},
        {"word": "room", "start": 3.5, "end": 3.9, "probability": 0.95},
        {"word": "309?", "start": 3.9, "end": 4.5, "probability": 0.95}
    ]
    ass_path = settings.DIR_SHORTS / "test_caption.ass"
    caption_engine.generate_ass_subtitles(
        words=mock_words,
        start_time=2.0,
        end_time=18.0,
        output_ass_path=ass_path,
        style_name="bold_yellow"
    )
    assert ass_path.exists()
    content = ass_path.read_text(encoding="utf-8")
    assert "ScriptType: v4.00+" in content
    assert "Dialogue:" in content
    pytest.test_ass_path = ass_path

def test_smart_reframing_crop_calculation():
    """Verifies crop coordinate math for 9:16 framing."""
    coords = [{"time": 5.0, "x_ratio": 0.65}, {"time": 10.0, "x_ratio": 0.62}]
    ratio, expr = smart_reframer.calculate_crop_window(
        face_coordinates=coords,
        start_time=4.0,
        end_time=12.0,
        source_width=1920,
        source_height=1080
    )
    assert 0.25 <= ratio <= 0.75
    assert "min(iw,ih*9/16)" in expr

def test_render_916_vertical_short():
    """Verifies real FFmpeg rendering to a 1080x1920 MP4 file."""
    source: SourceVideo = pytest.test_source_video
    output_path = settings.DIR_SHORTS / "test_rendered_short.mp4"
    
    result = shorts_renderer.render_short(
        source_video_path=Path(source.file_path),
        output_short_path=output_path,
        start_time=0.0,
        end_time=12.0,
        subtitle_ass_path=pytest.test_ass_path,
        face_x_ratio=0.5
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert result["duration"] == 12.0
    pytest.rendered_short_path = output_path

def test_quality_control_validation():
    """Verifies Quality Control checks catch valid/invalid properties."""
    qc = quality_control_engine.evaluate_short(pytest.rendered_short_path, pytest.test_ass_path)
    assert qc["passed"] is True
    assert qc["overall_score"] >= 85.0
    assert qc["video_checks"]["passed"] is True
    assert qc["audio_checks"]["passed"] is True

def test_metadata_generation():
    """Verifies generation of 5 viral title candidates and SEO description."""
    meta = metadata_generator.generate_metadata(
        segment_text="Why do people ignore room 309 in this hotel? The terrifying secret is finally revealed.",
        source_title="Mystery Hotel Documentary"
    )
    assert len(meta["title_options"]) == 5
    assert len(meta["hashtags"]) >= 4
    assert "Subscribe" in meta["description"]
    pytest.test_metadata = meta

def test_thumbnail_extraction():
    """Verifies extraction of a sharp 9:16 thumbnail image."""
    thumb_path = settings.DIR_THUMBNAILS / "test_hero_thumb.jpg"
    extracted = thumbnail_generator.extract_hero_thumbnail(pytest.rendered_short_path, thumb_path)
    assert extracted.exists()
    assert extracted.stat().st_size > 0

def test_mock_youtube_publishing_flow(db_session: Session):
    """Verifies publishing flow, duplicate check, and database record creation."""
    source: SourceVideo = pytest.test_source_video
    
    # Get or create test channel
    channel = db_session.query(YouTubeChannel).filter(YouTubeChannel.channel_id == "UC_test_e2e_channel").first()
    if not channel:
        channel = YouTubeChannel(
            id="test-channel-uuid-1",
            channel_id="UC_test_e2e_channel",
            title="Automated Test Studio",
            is_authorized=True,
            encrypted_credentials=encrypt_token('{"access_token": "mock_access_token"}')
        )
        db_session.add(channel)
    
    # Get or create clip project
    project = db_session.query(ClipProject).filter(ClipProject.id == "test-clip-uuid-1").first()
    if not project:
        project = ClipProject(
            id="test-clip-uuid-1",
            source_video_id=source.id,
            title="Test Short Title",
            start_time=0.0,
            end_time=12.0,
            rendered_video_path=str(pytest.rendered_short_path),
            status="qc_passed",
            metadata_json=json.dumps(pytest.test_metadata)
        )
        db_session.add(project)
    else:
        project.rendered_video_path = str(pytest.rendered_short_path)
        project.status = "qc_passed"
        project.metadata_json = json.dumps(pytest.test_metadata)
    
    db_session.commit()

    # Publish Short in SAFE mode
    pub = youtube_publisher.upload_short(
        clip_project_id=project.id,
        channel_id=channel.id,
        db=db_session,
        privacy_status="private",
        mode="SAFE"
    )
    assert pub.youtube_video_id is not None
    assert project.status == "published"

    # Verify duplicate prevention
    pub2 = youtube_publisher.upload_short(
        clip_project_id=project.id,
        channel_id=channel.id,
        db=db_session,
        privacy_status="private",
        mode="SAFE"
    )
    assert pub2.id == pub.id

def test_performance_learning_and_insights(db_session: Session):
    """Verifies channel analytics sync and adaptive weight optimization."""
    snapshots = learning_engine.sync_channel_analytics("test-channel-uuid-1", db_session)
    assert len(snapshots) >= 1
    assert snapshots[0].views > 0

    insight = learning_engine.generate_learning_insights("test-channel-uuid-1", db_session)
    assert insight.best_duration_bucket is not None
    weights = json.loads(insight.recommended_weights_json)
    assert "hook_strength" in weights
    assert "visual_activity" in weights
