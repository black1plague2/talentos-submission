"""
Gap intelligence engine (from noel branch).
Enhanced: uses semantic similarity for skill gap instead of exact string match,
so "React" satisfies "JavaScript Framework" requirements.
"""
from models.schemas import CandidateProfile, GapResult, JobProfile
from services.embedding_pipeline import build_index, embed
from config import SIMILARITY_THRESHOLD


def _semantic_skill_gap(
    required_skills: list[str],
    candidate_skills: list[str],
    role: str,
) -> tuple[list[str], float]:
    """Returns (missing_skills, gap_pct) using FAISS similarity."""
    if not required_skills:
        return [], 0.0
    if not candidate_skills:
        return list(required_skills), 100.0

    req_vecs = embed([f"{role}: {s}" for s in required_skills])
    cand_vecs = embed([f"{role}: {s}" for s in candidate_skills])
    index = build_index(cand_vecs)
    distances, _ = index.search(req_vecs, k=1)

    missing = [
        required_skills[i]
        for i, dist in enumerate(distances)
        if dist[0] < SIMILARITY_THRESHOLD
    ]
    gap_pct = (len(missing) / len(required_skills)) * 100
    return missing, round(gap_pct, 2)


def _cert_gap(required: list[str], candidate: list[str]) -> int:
    req_set = {c.lower() for c in required}
    cand_set = {c.lower() for c in candidate}
    return len(req_set - cand_set)


def run_gap_analysis(job: JobProfile, candidate: CandidateProfile) -> GapResult:
    missing_skills, skill_gap_pct = _semantic_skill_gap(
        job.required_skills, candidate.skills, job.title
    )
    experience_gap = max(0.0, job.required_experience - candidate.experience)
    cert_gap = _cert_gap(job.required_certifications, candidate.certifications)

    # Composite gap score (lower is better for the candidate)
    gap_score = round(skill_gap_pct * 0.60 + experience_gap * 10 + cert_gap * 5, 2)

    return GapResult(
        candidate_id=candidate.candidate_id,
        job_id=job.job_id,
        missing_skills=missing_skills,
        skill_gap_pct=skill_gap_pct,
        experience_gap=experience_gap,
        cert_gap=cert_gap,
        gap_score=gap_score,
    )
