import json
from fastapi import APIRouter
from config import DATA_DIR
from models.schemas import CandidateProfile

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def _load_candidates() -> list[CandidateProfile]:
    path = DATA_DIR / "candidates.json"
    with open(path) as f:
        return [CandidateProfile(**c) for c in json.load(f)]


@router.get("", response_model=list[CandidateProfile])
def list_candidates():
    return _load_candidates()


@router.get("/{candidate_id}", response_model=CandidateProfile)
def get_candidate(candidate_id: str):
    for c in _load_candidates():
        if c.candidate_id == candidate_id:
            return c
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
