# AI YouTube Engagement Analyzer & Automatic Shorts Generator — Architecture Specification

## 1. System Vision & Architecture Overview

The **AI YouTube Engagement Analyzer & Automatic Shorts Generator** is a production-grade, local-first content automation platform. It ingests long-form videos (from connected YouTube channels or local files), performs multi-modal intelligence extraction (audio, visual, transcript, and historical retention signals), calculates explainable engagement scores (0–100), extracts cohesive candidate clips, transforms them into vertical 9:16 Shorts with smart face/subject reframing and animated word-highlighted captions, verifies them via automated quality gates, and publishes them to YouTube via the official Data API.

### High-Level Architectural Flow

```
[Long-Form Video Source]
   │
   ├─► [Video Ingestion Engine] (FFprobe metadata, probe validation, permission check)
   │
   ├─► [Video Intelligence Engine]
   │     ├─ Audio: Voice intensity, speech/silence detection, RMS peaks
   │     ├─ Visual: Scene transitions, shot boundaries, visual activity index
   │     └─ Transcript: Faster-Whisper word-level timestamps, sentence structure
   │
   ├─► [Engagement Intelligence Engine]
   │     ├─ Mode 1: Actual Analytics (YouTube retention curves & watch-time)
   │     ├─ Mode 2: Predicted Engagement (NLP hooks, question detection, audio/visual dynamics)
   │     └─ Dynamic Weight Normalization (0-100 score + explainable factor breakdown)
   │
   ├─► [Intelligent Clip Boundary Detector]
   │     └─ Natural sentence boundaries, complete thoughts, duration brackets (15-60s)
   │
   ├─► [Shorts Rendering Pipeline]
   │     ├─ Smart Reframing (Face & subject tracking with smooth pans, safe center fallback)
   │     ├─ Caption Engine (Word-level animated ASS styles, keyword highlights)
   │     ├─ AI Video Editing (Subtle zoom on hooks, smart silence trimming, audio normalization)
   │     └─ FFmpeg Accelerated Rendering (AMD AMF h264_amf or libx264 software fallback)
   │
   ├─► [Quality Control (QC) Engine]
   │     └─ Video, Audio, Subtitle, Framing & Content checks + Auto-repair loop
   │
   ├─► [Publishing Engine]
   │     ├─ Safe Mode (Human preview, approval & scheduling)
   │     └─ Auto Mode (Strict QC pass, quota-aware background publishing)
   │
   └─► [Performance Learning Engine]
         └─ Post-publish analytics feedback, correlation analysis, adaptive weight tuning
```

---

## 2. Component Design & Module Boundaries

### Module A: YouTube Account Integration (`services/youtube_auth.py`, `services/youtube_api.py`)
- Standard Google OAuth 2.0 PKCE / Authorization Code flow.
- Token vault with symmetric encryption (Fernet AES-128).
- Channel metadata and video listing via YouTube Data API v3 (`channels.list`, `search.list`, `videos.list`).
- Real-time quota tracking and graceful degradation.

### Module B: Video Ingestion Engine (`services/ingestion.py`)
- Supports local uploads (multipart streaming) and authorized channel video processing.
- Probes resolution, aspect ratio, frame rate, audio channels, and duration using `ffprobe`.
- Creates low-resolution 360p analysis proxies to conserve system RAM on the AMD Ryzen 3 5300U.
- Records source ownership and permission status (`owned`, `licensed`, `authorized`, `unknown`).

### Module C: Video Intelligence Engine (`services/transcription.py`, `services/scene_detector.py`, `services/audio_analyzer.py`, `services/visual_analyzer.py`)
- **Transcription**: `faster-whisper` running locally on CPU with int8 quantization. Generates word-level timestamps and segment confidence.
- **Audio Analysis**: RMS energy calculation, silence segmentation, peak detection, and vocal dynamics.
- **Scene Detection**: Content-aware scene break detection via PySceneDetect / FFmpeg scene filter.
- **Visual Activity**: Frame-to-frame pixel delta and motion intensity calculation.
- **Analysis Schema**: Standardized JSON schema containing time-aligned audio, visual, and transcript events.

### Module D: Engagement Intelligence Engine (`services/engagement_scorer.py`)
- Evaluates candidate segments using 10 distinct engagement vectors.
- Supports two operating modes:
  - **Actual Analytics Mode**: Uses time-indexed YouTube audience retention data when authorized.
  - **Predicted Engagement Mode**: Heuristic and NLP-driven engagement estimation when retention data is absent.
- Dynamic Weight Normalization: Dynamically redistributes weights if specific signals (e.g. private analytics) are unavailable.
- Generates an explainable breakdown for every candidate segment.

### Module E: Intelligent Clip Boundary Detector (`services/boundary_detector.py`)
- Identifies sentence starts and ends from word-level transcript timestamps.
- Ensures clips never begin or end mid-sentence.
- Targets duration profiles: 15–25s, 25–35s, 35–45s, 45–60s.
- Deduplication and overlap suppression using temporal IoU (Intersection-over-Union).

### Module F & G: Shorts Rendering & Smart Reframing (`services/shorts_renderer.py`, `services/smart_reframer.py`)
- 9:16 vertical crop (1080x1920).
- Face and subject tracking: Computes center-of-interest coordinate across frames; applies temporal smoothing to eliminate shaky panning.
- Safe-area margins to avoid UI button occlusion on YouTube Shorts.
- Hardware encoding via AMD AMF (`h264_amf`) with automatic fallback to CPU `libx264`.

### Module H & I: Captioning & AI Editing (`services/caption_engine.py`)
- Advanced ASS (Advanced SubStation Alpha) subtitle generator.
- Word-level karaoke highlighting (`{\k...}`).
- High-contrast typography with dark outline and drop shadow.
- Subtle zoom on hook introduction, audio normalization (EBU R128), and silence trimming.

### Module J & K: Metadata & Thumbnails (`services/metadata_generator.py`, `services/thumbnail_generator.py`)
- Generates 5 viral title candidates, SEO descriptions, relevant hashtags, and key tags.
- Extracts visually crisp candidate frames (highest sharpness + face prominence) and produces 9:16 thumbnail image.

### Module L: Quality Control Engine (`services/quality_control.py`)
- Pre-publish validation gate checking:
  - Valid video format, aspect ratio (9:16), duration (<60s).
  - Audio stream integrity, clipping, and silence limits.
  - Subtitle synchronization and screen boundary adherence.
  - Framing checks (face/subject within safe zone).
- Automated repair cycle: Attempt repair -> Re-render -> Verify.

### Module M & N: Publishing & Performance Learning (`services/publisher.py`, `services/learning_engine.py`)
- Official YouTube Data API v3 resumable video upload (`videos.insert`).
- Safe Mode (manual preview & approval) vs Automatic Mode (QC-passed clips).
- Analytics tracking (`views`, `watchTime`, `averageViewDuration`, `likes`).
- Weight optimization feedback loop adjusting candidate score weights based on actual channel performance.

---

## 3. Storage & Data Persistence

- Database: SQLite in WAL (Write-Ahead Logging) mode with foreign keys enabled.
- Data directory structure:
  - `data/db/`: SQLite database files (`production.db`).
  - `data/uploads/`: Ingested source video files.
  - `data/proxies/`: 360p analysis proxies.
  - `data/audio/`: Extracted WAV audio streams.
  - `data/shorts/`: Rendered final vertical MP4 clips.
  - `data/thumbnails/`: Generated 9:16 thumbnail frames.
  - `data/qc/`: Quality control reports and diagnostic logs.
