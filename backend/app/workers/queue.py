import concurrent.futures
import logging
import threading
import time
from typing import Callable, Dict, Any, Optional

from ..core.hardware import hardware_governor
from ..core.config import settings

logger = logging.getLogger("yt_shorts.queue")

class BackgroundJobRunner:
    """
    Lightweight, thread-based job runner for local processing.
    Controls concurrency to protect the AMD Ryzen 3 5300U CPU and 16GB RAM.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, max_workers: int = 4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.cancelled_jobs = set()
        self._lock = threading.Lock()
        self.heavy_semaphore = threading.Semaphore(settings.MAX_CONCURRENT_HEAVY_JOBS)

    def submit_job(self, job_id: str, task_fn: Callable, *args, is_heavy: bool = True, **kwargs):
        """Submits a job to the thread pool with memory pressure checking."""
        with self._lock:
            self.active_jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "progress": 0.0,
                "is_heavy": is_heavy,
                "submitted_at": time.time(),
                "error": None
            }

        def _execute_task():
            if job_id in self.cancelled_jobs:
                with self._lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "cancelled"
                return

            with self._lock:
                if job_id in self.active_jobs:
                    self.active_jobs[job_id]["status"] = "processing"

            try:
                logger.info(f"[JobQueue] Starting job {job_id}")
                task_fn(job_id, *args, **kwargs)
                with self._lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "completed"
                        self.active_jobs[job_id]["progress"] = 100.0
                logger.info(f"[JobQueue] Successfully finished job {job_id}")
            except Exception as e:
                logger.error(f"[JobQueue] Job {job_id} failed: {e}", exc_info=True)
                with self._lock:
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id]["status"] = "failed"
                        self.active_jobs[job_id]["error"] = str(e)

        def _wrapper():
            if is_heavy:
                with self.heavy_semaphore:
                    while not hardware_governor.can_start_heavy_task(required_mb=1200.0):
                        if job_id in self.cancelled_jobs:
                            logger.info(f"Job {job_id} was cancelled before memory freed.")
                            return
                        logger.warning(f"[JobQueue] Memory low (<1200MB). Waiting for headroom for job {job_id}...")
                        time.sleep(3.0)
                    _execute_task()
            else:
                _execute_task()

        self.executor.submit(_wrapper)

    def cancel_job(self, job_id: str):
        with self._lock:
            self.cancelled_jobs.add(job_id)
            if job_id in self.active_jobs:
                self.active_jobs[job_id]["status"] = "cancelling"

    def update_progress(self, job_id: str, progress: float):
        with self._lock:
            if job_id in self.active_jobs:
                self.active_jobs[job_id]["progress"] = min(100.0, max(0.0, progress))

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.active_jobs.get(job_id)

job_runner = BackgroundJobRunner.get_instance()
