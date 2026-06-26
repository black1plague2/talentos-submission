"""Assembles a flat feature vector from all service outputs for ML ranking."""
import numpy as np
from models.schemas import (
    CapabilityResult, FeatureVector, GapResult,
    SemanticMatchResult, VerificationResult,
)

FEATURE_NAMES = [
    "semantic_match_score", "capability_score",
    "matched_req_pct", "matched_pref_pct",
    "verification_score", "learning_score",
    "growth_score", "career_score",
    "project_score", "evidence_score",
    "skill_gap_pct", "experience_gap",
    "cert_gap", "exp_years", "cert_count",
]


def build_feature_vector(
    semantic: SemanticMatchResult,
    capability: CapabilityResult,
    verification: VerificationResult,
    gap: GapResult,
    exp_years: float,
    cert_count: float,
) -> FeatureVector:
    return FeatureVector(
        semantic_match_score=semantic.semantic_match_score,
        capability_score=capability.capability_score,
        matched_req_pct=semantic.matched_req_pct,
        matched_pref_pct=semantic.matched_pref_pct,
        verification_score=verification.verification_score,
        learning_score=verification.learning_score,
        growth_score=verification.growth_score,
        career_score=verification.career_score,
        project_score=verification.project_score,
        evidence_score=verification.evidence_score,
        skill_gap_pct=gap.skill_gap_pct,
        experience_gap=gap.experience_gap,
        cert_gap=float(gap.cert_gap),
        exp_years=exp_years,
        cert_count=cert_count,
    )


def to_numpy(fv: FeatureVector) -> np.ndarray:
    return np.array([getattr(fv, name) for name in FEATURE_NAMES], dtype=np.float32)
