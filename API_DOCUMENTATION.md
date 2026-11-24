# API Documentation — AI YouTube Shorts Generator REST API

Base URL: `http://localhost:8000/api/v1`

All responses follow standard HTTP status codes and return JSON payloads with structured error formats:
```json
{
  "status": "error",
  "detail": "Description of error",
  "code": "ERROR_CODE"
}
```

---

## 1. System Health & Hardware Endpoints

### `GET /system/health`
Returns live system health, hardware profiler metrics, memory headroom, and encoder capabilities.
**Response (200 OK)**:
```json
{
  "status": "healthy",
  "hardware": {
    "cpu_model": "AMD Ryzen 3 5300U",
    "cpu_cores": 4,
    "cpu_threads": 8,
    "ram_total_mb": 16070,
    "ram_free_mb": 3746,
    "ram_pressure_state": "NORMAL",
    "gpu_name": "AMD Radeon(TM) Graphics",
    "gpu_dedicated_vram_mb": 512,
    "recommended_encoder": "h264_amf",
    "encoder_fallback": "libx264"
  },
  "queue": {
    "active_jobs": 0,
    "queued_jobs": 0
  }
}
```

---

## 2. YouTube Channel Endpoints

### `GET /channels`
Lists all connected YouTube channels and their authorization status.

### `GET /channels/oauth/authorize`
Generates a secure Google OAuth 2.0 authorization URL with CSRF state protection.

### `GET /channels/oauth/callback`
Handles the OAuth redirect from Google, exchanges authorization code for tokens, encrypts credentials, and registers channel in database.

### `POST /channels/{channel_id}/revoke`
Revokes OAuth token via Google API and removes credentials from vault.

### `GET /channels/{channel_id}/videos`
Discovers and lists latest videos from connected YouTube channel via YouTube Data API v3.

---

## 3. Video Ingestion Endpoints

### `POST /videos/upload`
Uploads a local video file (multipart form data) with FFprobe metadata extraction and permission tagging (`owned`, `licensed`, `authorized`).

### `GET /videos`
Lists all ingested source videos with durations, resolutions, and analysis status.

### `GET /videos/{video_id}`
Returns detailed metadata for a specific source video.

---

## 4. Video Analysis & Intelligence Endpoints

### `POST /videos/{video_id}/analyze`
Enqueues a background multi-modal analysis job:
1. Audio extraction & RMS energy analysis
2. Faster-Whisper word-level transcription
3. PySceneDetect scene boundary detection
4. Visual activity profiling

### `GET /videos/{video_id}/analysis`
Returns the standardized analysis JSON schema containing timestamps for words, sentences, audio peaks, and scene breaks.

---

## 5. Engagement Opportunities Endpoints

### `GET /videos/{video_id}/opportunities`
Retrieves engagement candidate moments scored from 0 to 100 with explainable component breakdowns:
- `scoring_mode`: `ACTUAL_ANALYTICS` or `PREDICTED`
- `hook_score`
- `payoff_score`
- `emotional_score`
- `topic_score`
- `visual_score`
- `reasons`: array of textual justifications

---

## 6. Shorts Generation & Rendering Endpoints

### `POST /shorts/generate`
Creates a clip project from candidate timestamps and enqueues 9:16 vertical render:
- Smart face/subject tracking reframing
- Word-highlighted animated ASS captions
- Audio normalization (EBU R128)
- Hardware encoding (AMD AMF or libx264)

### `GET /shorts`
Lists all rendered and draft Shorts projects.

### `GET /shorts/{short_id}`
Returns details, video stream URL, and QC report for a specific Short.

---

## 7. Quality Control Endpoints

### `POST /shorts/{short_id}/qc`
Runs automated quality control checks (video, audio, subtitle, framing, content) and returns comprehensive pass/fail report.

---

## 8. Publishing Endpoints

### `POST /shorts/{short_id}/publish`
Schedules or triggers direct YouTube upload via official API:
- `mode`: `SAFE` (requires manual confirmation) or `AUTOMATIC` (requires QC pass)
- `privacy_status`: `private`, `unlisted`, or `public`
- `scheduled_time`: optional ISO timestamp

---

## 9. Performance Analytics & Learning Endpoints

### `GET /analytics/channel/{channel_id}`
Retrieves synced performance metrics (`views`, `watchTime`, `avgViewDuration`) for published Shorts.

### `GET /analytics/learning/{channel_id}`
Returns statistical correlation insights and recommended engagement score weighting adjustments.
