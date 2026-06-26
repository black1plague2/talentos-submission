"""
FAISS-based semantic skill matching (from garv branch).
Enhanced: returns matched_req_pct and matched_pref_pct for ML feature vector.
"""
from config import SIMILARITY_THRESHOLD
from models.schemas import CandidateProfile, JobProfile, SemanticMatchResult, SkillMatchDetail
from services.embedding_pipeline import build_index, embed


def _contextualize(role: str, skills: list[str]) -> list[str]:
    return [f"{role}: {skill}" for skill in skills]


def _match_skills(
    role: str,
    job_skills: list[str],
    candidate_skills: list[str],
) -> tuple[list[SkillMatchDetail], list[str], float]:
    """Returns (details, unmatched_list, match_pct)."""
    if not job_skills:
        return [], [], 100.0
    if not candidate_skills:
        details = [
            SkillMatchDetail(job_skill=s, matched_candidate_skill=None,
                             similarity_score=0.0, is_matched=False)
            for s in job_skills
        ]
        return details, list(job_skills), 0.0

    job_vecs = embed(_contextualize(role, job_skills))
    cand_vecs = embed(_contextualize(role, candidate_skills))
    index = build_index(cand_vecs)
    distances, indices = index.search(job_vecs, k=1)

    details: list[SkillMatchDetail] = []
    unmatched: list[str] = []
    matched_count = 0

    for i, job_skill in enumerate(job_skills):
        score = float(distances[i][0])
        matched_idx = int(indices[i][0])
        matched_skill = candidate_skills[matched_idx] if matched_idx >= 0 else None
        is_matched = score >= SIMILARITY_THRESHOLD
        if is_matched:
            matched_count += 1
        else:
            unmatched.append(job_skill)
        details.append(SkillMatchDetail(
            job_skill=job_skill,
            matched_candidate_skill=matched_skill if is_matched else None,
            similarity_score=round(score, 4),
            is_matched=is_matched,
        ))

    match_pct = (matched_count / len(job_skills)) * 100
    return details, unmatched, round(match_pct, 2)


def run_semantic_matching(job: JobProfile, candidate: CandidateProfile) -> SemanticMatchResult:
    req_details, req_unmatched, req_pct = _match_skills(
        job.title, job.required_skills, candidate.skills
    )
    pref_details, _, pref_pct = _match_skills(
        job.title, job.preferred_skills, candidate.skills
    )

    semantic_score = round(req_pct * 0.7 + pref_pct * 0.3, 2)

    return SemanticMatchResult(
        candidate_id=candidate.candidate_id,
        semantic_match_score=semantic_score,
        matched_req_pct=req_pct,
        matched_pref_pct=pref_pct,
        matched_skills=req_details + pref_details,
        unmatched_job_skills=req_unmatched,
    )
