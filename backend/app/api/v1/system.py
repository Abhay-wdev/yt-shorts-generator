from fastapi import APIRouter
from ...core.hardware import hardware_governor
from ...workers.queue import job_runner

router = APIRouter()

@router.get("/health")
def get_system_health():
    """Returns comprehensive system health, CPU/RAM/GPU status, and active background queue metrics."""
    hw = hardware_governor.get_hardware_status()
    return {
        "status": "healthy",
        "hardware": hw,
        "queue": {
            "active_count": len(job_runner.active_jobs),
            "cancelled_count": len(job_runner.cancelled_jobs),
            "jobs": list(job_runner.active_jobs.values())
        }
    }

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieves live status for a specific background job."""
    status = job_runner.get_job_status(job_id)
    if not status:
        return {"status": "not_found", "job_id": job_id}
    return status

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancels a running or queued background job."""
    job_runner.cancel_job(job_id)
    return {"status": "cancelling", "job_id": job_id}
