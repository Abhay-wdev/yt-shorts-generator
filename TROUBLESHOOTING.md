# Troubleshooting & Operations Guide

## Common Issues & Diagnoses

### 1. Video Processing & FFmpeg Errors

#### Symptom: `h264_amf` encoder fails or crashes during render
- **Cause**: The AMD Radeon driver may be momentarily locked by another GPU task, or AMF initialization timed out.
- **Remedy**: The pipeline automatically switches to CPU `libx264` (`preset=fast`, `crf=22`). You can also force software encoding in `backend/.env` with `FORCE_SOFTWARE_ENCODER=true`.

#### Symptom: FFmpeg subtitle burning fails with `No such filter: 'ass'`
- **Cause**: FFmpeg build lacks `libass` support.
- **Remedy**: The verified installed FFmpeg build (`9.0.2-full_build-www.gyan.dev`) explicitly includes `--enable-libass`. Ensure system PATH points to this Gyan.dev build.

#### Symptom: Subtitle font glyphs missing or replaced with rectangles
- **Cause**: Requested font in `.ass` header is not installed in Windows fonts directory.
- **Remedy**: Default subtitle styles use universal system fonts (`Arial`, `Segoe UI`, `Trebuchet MS`, or `Impact`), which are guaranteed present on Windows 11.

---

### 2. Audio & Transcription Issues

#### Symptom: `faster-whisper` out-of-memory or high CPU lockup
- **Cause**: Large model (`large-v3`) requested on the 16 GB Ryzen 3 5300U.
- **Remedy**: Set `WHISPER_MODEL_SIZE=tiny` or `base` in `.env`. Both models use less than 800 MB RAM and execute in near real-time on CPU with `compute_type="int8"`.

---

### 3. Google OAuth & YouTube API Errors

#### Symptom: `403 Access Blocked: This app has not been verified`
- **Cause**: Google Cloud OAuth consent screen is in "Testing" mode.
- **Remedy**: Add your Google account email to the "Test users" list under **APIs & Services > OAuth consent screen** in Google Cloud Console.

#### Symptom: `quotaExceeded` (403)
- **Cause**: The project reached the daily 10,000 units quota (e.g., after multiple video uploads).
- **Remedy**: Quota resets daily at midnight Pacific Time (PT). Switch to `SAFE` mode to generate and preview Shorts locally, then schedule uploads after quota reset.
