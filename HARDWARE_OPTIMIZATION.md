# Hardware & Resource Optimization Guide

## Hardware Target Profile: AMD Ryzen 3 5300U + Radeon Graphics

- **CPU**: AMD Ryzen 3 5300U (4 Cores / 8 Threads, 2.6 GHz base, 3.8 GHz boost).
- **RAM**: 16 GB DDR4 (16,070,768 KB visible).
- **GPU**: AMD Radeon(TM) Graphics (512 MB dedicated VRAM, shared system memory).
- **OS**: Windows 11 Home 64-bit.
- **Acceleration**: DirectX 12, DirectML, AMD AMF video encoding (`h264_amf`, `hevc_amf`).

---

## Resource Management Principles

### 1. Zero CUDA Assumption
There is no NVIDIA GPU on this machine. Any code invoking `torch.cuda` or assuming CUDA exists will fail. All AI inference is configured to use:
- CPU int8 quantization via CTranslate2 (`faster-whisper`, model sizes `tiny`, `base`, or `small`).
- DirectML (`onnxruntime-directml`) where applicable for visual embedding and face detection.
- Fast heuristic and rule-based NLP fallbacks requiring 0 MB of GPU memory.

### 2. RAM Pressure Classification & Forecasting
Before launching any memory-intensive task (transcription, proxy generation, 9:16 rendering), the system consults `local_hardware_engine`:
- **`NORMAL`** (Free RAM > 2.5 GB): Proceed with default worker configuration.
- **`WARNING`** (Free RAM between 1.2 GB and 2.5 GB): Throttle concurrency to 1 active heavy task; force `model_size="tiny"`.
- **`CRITICAL`** (Free RAM < 1.2 GB): Pause incoming render jobs until garbage collection and previous processes finish.

### 3. Video Encoding Strategy
- **Primary Hardware Encoder**: `h264_amf` (AMD Advanced Media Framework). Offloads H.264 video encoding to the Radeon video engine, reducing CPU load from 100% to ~25%.
- **Automatic Fallback Encoder**: `libx264` with `preset=fast`, `crf=22`, and `pix_fmt=yuv420p` when AMF is busy, unavailable, or encounters driver locks.
- **Audio Codec**: `aac` at 192k bitrate, 48000 Hz, normalized with EBU R128 (`loudnorm` filter).

### 4. 360p Analysis Proxy Pattern
Processing 1080p or 4K videos frame-by-frame in OpenCV or PySceneDetect quickly exceeds memory boundaries.
- The pipeline immediately extracts a lightweight 360p (640x360) proxy using FFmpeg.
- All visual analysis (scene cuts, face detection, activity metrics) runs on the 360p proxy in a fraction of the time and RAM.
- The final 9:16 vertical render applies the computed crop coordinates back to the original full-resolution master video file.
