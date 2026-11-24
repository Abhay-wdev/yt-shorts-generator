import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
from .config import settings

logger = logging.getLogger("yt_shorts.hardware")

# Check if local_hardware_engine is available in parent workspace
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

class HardwareGovernor:
    """
    Hardware Governor for AMD Ryzen 3 5300U + Radeon Graphics.
    Enforces RAM-aware task scheduling and optimal video encoder selection.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._hw_engine = None
        try:
            from local_hardware_engine import LocalHardwareEngine
            self._hw_engine = LocalHardwareEngine.get_instance(workspace_root=str(WORKSPACE_ROOT))
            logger.info("LocalHardwareEngine successfully loaded and integrated.")
        except Exception as e:
            logger.warning(f"Could not load LocalHardwareEngine: {e}. Falling back to standard hardware detection.")

    def get_hardware_status(self) -> Dict[str, Any]:
        """Returns live hardware profile, memory pressure, and encoder status."""
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        cores = psutil.cpu_count(logical=False) or 4
        threads = psutil.cpu_count(logical=True) or 8

        # Determine RAM pressure
        available_mb = mem.available / (1024 * 1024)
        total_mb = mem.total / (1024 * 1024)
        
        if available_mb < 1200:
            pressure = "CRITICAL"
        elif available_mb < 2500:
            pressure = "WARNING"
        else:
            pressure = "NORMAL"

        encoder_info = self.get_best_video_encoder()

        return {
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine()
            },
            "cpu": {
                "model": "AMD Ryzen 3 5300U with Radeon Graphics",
                "physical_cores": cores,
                "logical_threads": threads,
                "utilization_percent": cpu_pct
            },
            "ram": {
                "total_mb": round(total_mb, 1),
                "available_mb": round(available_mb, 1),
                "used_percent": mem.percent,
                "pressure_state": pressure
            },
            "gpu": {
                "name": "AMD Radeon(TM) Graphics",
                "is_integrated": True,
                "dedicated_vram_mb": 512,
                "shared_pool_mb": round(total_mb / 2, 1)
            },
            "video_acceleration": encoder_info
        }

    def get_best_video_encoder(self) -> Dict[str, Any]:
        """Detects if AMD AMF hardware encoder is available, with graceful fallback to libx264."""
        if settings.FORCE_SOFTWARE_ENCODER:
            return {
                "name": "libx264",
                "type": "CPU_SOFTWARE",
                "preset": "fast",
                "crf": 22
            }

        # Check if FFmpeg has h264_amf working
        try:
            res = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                check=False
            )
            if "h264_amf" in res.stdout:
                return {
                    "name": "h264_amf",
                    "type": "GPU_AMF",
                    "extra_args": ["-usage", "transcoding", "-quality", "speed", "-rc", "cbr"]
                }
        except Exception:
            pass

        return {
            "name": "libx264",
            "type": "CPU_SOFTWARE",
            "preset": "fast",
            "crf": 22
        }

    def can_start_heavy_task(self, required_mb: float = 1200.0) -> bool:
        """Checks whether the system has sufficient RAM headroom to start a heavy job."""
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        return available_mb >= required_mb

hardware_governor = HardwareGovernor.get_instance()
