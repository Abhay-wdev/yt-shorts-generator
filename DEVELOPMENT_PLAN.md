# AI YouTube Engagement Analyzer & Automatic Shorts Generator — Development Plan

This document outlines the detailed, phase-by-phase implementation schedule following the required engineering cycle:
**IMPLEMENT → VERIFY → DIAGNOSE → FIX → RETEST**

---

## Phase Overview & Milestones

| Phase | Title | Scope & Deliverables | Acceptance Criteria |
|---|---|---|---|
| **Phase 0** | **Repository & Hardware Audit** | PC specs, installed software, dependency audit, ecosystem analysis, architecture blueprint. | Hardware limits documented; AMF/CPU verified; plan defined. |
| **Phase 1** | **Core Foundation & Architecture** | Project layout, FastAPI app, SQLite WAL database, Pydantic schemas, persistent queue runner, hardware governor integration. | DB initializes; health endpoint reports system status; background jobs run reliably. |
| **Phase 2** | **Video Ingestion Engine** | Local file upload, YouTube metadata scraping (official API/fallback), FFprobe extraction, permission tagging. | Metadata (dimensions, codecs, fps, duration) reliably extracted for test video. |
| **Phase 3** | **Video Intelligence Engine** | Audio extraction, Faster-Whisper transcription (word-level), PySceneDetect/FFmpeg scene detection, visual activity profiling, unified JSON analysis schema. | Complete synchronized analysis JSON generated for sample video with timestamps. |
| **Phase 4** | **Engagement Intelligence Engine** | 10-signal engagement scoring model (0-100), hook detection, story/payoff scoring, emotional dynamics, dynamic weight normalization. | Scores generated in both `ACTUAL_ANALYTICS` and `PREDICTED` modes with clear breakdown. |
| **Phase 5** | **Intelligent Clip Boundary Detector** | Sentence start/end alignment, thought completion, candidate duration brackets (15-60s), temporal IoU deduplication. | No mid-sentence cuts, duration within bounds, no overlapping duplicates. |
| **Phase 6** | **Shorts Rendering, Smart Reframing & Captions** | 9:16 vertical conversion, face/subject tracking crop with safe center fallback, animated ASS karaoke subtitles, AMF/libx264 rendering. | Generates valid 1080x1920 MP4 with synchronized subtitles and smooth framing. |
| **Phase 7** | **Quality Control (QC) Engine** | Automated video, audio, caption, and framing validation gates, auto-repair loop, comprehensive QC report. | Catches defective clips; triggers auto-repair or blocks bad clips from publish. |
| **Phase 8** | **Metadata & Thumbnail Generator** | 5 SEO viral titles, descriptions, hashtags, keywords, sharp 9:16 thumbnail frame extraction with overlay text. | Metadata accurately reflects clip content; valid thumbnail images generated. |
| **Phase 9** | **YouTube Integration & Publishing** | Google OAuth 2.0 flow, AES token encryption, official YouTube Data API v3 upload (`videos.insert`), Safe vs Auto mode, quota management. | Successfully connects channel; uploads test video to authorized account with retries. |
| **Phase 10** | **Performance Learning Engine** | Post-publish analytics sync, correlation matrix across duration/hook/topic, adaptive weight tuning for engagement model. | Stores historical metrics and adjusts scoring weights based on actual views. |
| **Phase 11** | **Frontend Dashboard & Studio UI** | 14-page responsive dashboard (Next.js 15, Tailwind CSS, Lucide icons), preview video player, opportunity cards, publishing queue. | Full interactive UI with zero fake metrics; real-time job tracking. |
| **Phase 12** | **Hardening & Automated Test Suite** | Full automated pytest suite across all modules, documentation completion, system resilience verification. | All tests pass; all documentation files populated; zero regressions. |

---

## Detailed Engineering Checklist

- [x] **Phase 0**: Audit completed. Ryzen 3 5300U, 16GB RAM, Radeon Graphics, FFmpeg 9.0.2 with AMF and libass verified.
- [ ] **Phase 1**: Database models, SQLite WAL, Hardware governor, Async Job Queue, Base API routes.
- [ ] **Phase 2**: Video Ingestion with FFprobe, file storage, permission categorization.
- [ ] **Phase 3**: Audio RMS energy, Scene boundaries, Faster-Whisper word-level transcription.
- [ ] **Phase 4**: Engagement Scoring Engine (0-100) with explainable component weights.
- [ ] **Phase 5**: Sentence-aware Boundary Detector with temporal deduplication.
- [ ] **Phase 6**: Smart 9:16 Reframer, ASS karaoke captions, subtle zoom, AMF video export.
- [ ] **Phase 7**: Quality Control validation suite with automated repair loop.
- [ ] **Phase 8**: AI Metadata generator (titles, descriptions, tags) and 9:16 thumbnail extractor.
- [ ] **Phase 9**: YouTube OAuth 2.0 and official resumable video upload integration.
- [ ] **Phase 10**: Channel Analytics sync and adaptive weight optimization.
- [ ] **Phase 11**: Next.js 15 responsive UI covering all 14 required dashboard views.
- [ ] **Phase 12**: Automated end-to-end regression testing and final documentation.
