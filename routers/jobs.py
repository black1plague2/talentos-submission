import json
from fastapi import APIRouter
from config import DATA_DIR
from models.schemas import JobProfile

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _load_jobs() -> list[JobProfile]:
    path = DATA_DIR / "jobs.json"
    with open(path) as f:
        return [JobProfile(**j) for j in json.load(f)]


@router.get("", response_model=list[JobProfile])
def list_jobs():
    return _load_jobs()


@router.get("/{job_id}", response_model=JobProfile)
def get_job(job_id: str):
    for job in _load_jobs():
        if job.job_id == job_id:
            return job
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
