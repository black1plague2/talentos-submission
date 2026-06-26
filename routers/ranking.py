"""Core ranking router — orchestrates all 4 persons' logic into one pipeline."""
import asyncio
from fastapi import APIRouter
from models.schemas import (
    CandidateProfile, JobProfile, RankRequest, RankResponse, RankedCandidate,
)
from services.semantic_matcher import run_semantic_matching
from services.capability_engine import run_capability_evaluation
from services.verification_scorer import run_verification_scoring
from services.gap_engine import run_gap_analysis
from services.role_discovery import find_alternative_roles
from services.recruiter_copilot import generate_explanation
from ml.features import build_feature_vector
from ml.ranker import predict

router = APIRouter(prefix="/rank", tags=["Ranking"])


def _evaluate_one(job: JobProfile, candidate: CandidateProfile, all_jobs: list[JobProfile]) -> RankedCandidate:
    semantic = run_semantic_matching(job, candidate)
    capability = run_capability_evaluation(job, candidate)
    verification = run_verification_scoring(candidate)
    gap = run_gap_analysis(job, candidate)
    features = build_feature_vector(
        semantic, capability, verification, gap,
        exp_years=candidate.experience,
        cert_count=float(len(candidate.certifications)),
    )
    final_score = predict(features)
    alt_roles = find_alternative_roles(candidate, all_jobs)

    # Placeholder for explanation — filled after ranking
    return RankedCandidate(
        rank=0,
        candidate_id=candidate.candidate_id,
        candidate_name=candidate.name,
        job_id=job.job_id,
        job_title=job.title,
        final_score=final_score,
        semantic_match_score=semantic.semantic_match_score,
        capability_score=capability.capability_score,
        verification_score=verification.verification_score,
        growth_score=verification.growth_score,
        gap_score=gap.gap_score,
        missing_skills=gap.missing_skills,
        alternative_roles=alt_roles,
        explanation="",
        feature_breakdown=features,
    )


@router.post("", response_model=RankResponse)
def rank_candidates(req: RankRequest) -> RankResponse:
    all_jobs = [req.job]  # extend with more jobs if needed for role discovery
    results = [_evaluate_one(req.job, c, all_jobs) for c in req.candidates]

    results.sort(key=lambda r: r.final_score, reverse=True)
    for i, r in enumerate(results, start=1):
        r.rank = i
        r.explanation = generate_explanation(r)

    return RankResponse(
        job_id=req.job.job_id,
        job_title=req.job.title,
        total_candidates=len(results),
        ranked=results,
    )
