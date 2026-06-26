"""Alternative role recommender (from noel branch, enhanced with semantic matching)."""
from models.schemas import CandidateProfile, JobProfile, RoleRecommendation
from services.embedding_pipeline import build_index, embed


def find_alternative_roles(
    candidate: CandidateProfile,
    all_jobs: list[JobProfile],
    top_n: int = 3,
) -> list[RoleRecommendation]:
    """Rank all jobs by semantic fit to candidate's skill set."""
    if not candidate.skills or not all_jobs:
        return []

    cand_vec = embed([" ".join(candidate.skills)])
    job_vecs = embed([" ".join(j.required_skills) for j in all_jobs])
    index = build_index(job_vecs)
    distances, indices = index.search(cand_vec, k=min(top_n, len(all_jobs)))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        job = all_jobs[int(idx)]
        results.append(RoleRecommendation(
            job_id=job.job_id,
            title=job.title,
            score=round(float(dist) * 100, 2),
        ))
    return results
