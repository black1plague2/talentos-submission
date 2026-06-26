"""
Standalone script: reads data/*.json, runs the full ML pipeline,
and writes output/ranked_output.json (competition submission format).

Usage:
    python run_ranking.py
    python run_ranking.py --job JOB001          # rank for one specific job
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, OUTPUT_DIR
from models.schemas import CandidateProfile, JobProfile
from services.embedding_pipeline import get_model
from ml.ranker import _load_or_train, predict
from services.semantic_matcher import run_semantic_matching
from services.capability_engine import run_capability_evaluation
from services.verification_scorer import run_verification_scoring
from services.gap_engine import run_gap_analysis
from services.role_discovery import find_alternative_roles
from services.recruiter_copilot import generate_explanation
from ml.features import build_feature_vector
from models.schemas import RankedCandidate


def load_data() -> tuple[list[JobProfile], list[CandidateProfile]]:
    with open(DATA_DIR / "jobs.json") as f:
        jobs = [JobProfile(**j) for j in json.load(f)]
    with open(DATA_DIR / "candidates.json") as f:
        candidates = [CandidateProfile(**c) for c in json.load(f)]
    return jobs, candidates


def rank_for_job(
    job: JobProfile,
    candidates: list[CandidateProfile],
    all_jobs: list[JobProfile],
) -> list[dict]:
    results = []
    for c in candidates:
        semantic = run_semantic_matching(job, c)
        capability = run_capability_evaluation(job, c)
        verification = run_verification_scoring(c)
        gap = run_gap_analysis(job, c)
        features = build_feature_vector(
            semantic, capability, verification, gap,
            exp_years=c.experience,
            cert_count=float(len(c.certifications)),
        )
        final_score = predict(features)
        alt_roles = find_alternative_roles(c, all_jobs)

        ranked = RankedCandidate(
            rank=0,
            candidate_id=c.candidate_id,
            candidate_name=c.name,
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
        results.append(ranked)

    results.sort(key=lambda r: r.final_score, reverse=True)
    for i, r in enumerate(results, start=1):
        r.rank = i
        r.explanation = generate_explanation(r)

    return [
        {
            "rank": r.rank,
            "candidate_id": r.candidate_id,
            "candidate_name": r.candidate_name,
            "job_id": r.job_id,
            "job_title": r.job_title,
            "final_score": round(r.final_score, 2),
            "semantic_match_score": round(r.semantic_match_score, 2),
            "capability_score": round(r.capability_score, 2),
            "verification_score": round(r.verification_score, 2),
            "growth_score": round(r.growth_score, 2),
            "gap_score": round(r.gap_score, 2),
            "missing_skills": r.missing_skills,
            "alternative_roles": [a.model_dump() for a in r.alternative_roles],
            "explanation": r.explanation,
        }
        for r in results
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default=None, help="Job ID to rank for (default: all jobs)")
    args = parser.parse_args()

    print("[run_ranking] Loading models...")
    get_model()
    _load_or_train()

    jobs, candidates = load_data()
    target_jobs = [j for j in jobs if j.job_id == args.job] if args.job else jobs

    OUTPUT_DIR.mkdir(exist_ok=True)
    all_output = []

    for job in target_jobs:
        print(f"\n[run_ranking] Ranking {len(candidates)} candidates for: {job.title} ({job.job_id})")
        ranked = rank_for_job(job, candidates, jobs)
        all_output.extend(ranked)
        for r in ranked[:3]:
            print(f"  #{r['rank']} {r['candidate_name']:20s}  score={r['final_score']:.1f}  gap={r['gap_score']:.1f}")

    out_path = OUTPUT_DIR / "ranked_output.json"
    with open(out_path, "w") as f:
        json.dump(all_output, f, indent=2)

    print(f"\n[run_ranking] Saved {len(all_output)} results to {out_path}")


if __name__ == "__main__":
    main()
