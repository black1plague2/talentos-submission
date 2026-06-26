from __future__ import annotations
from pydantic import BaseModel, Field


# ── Input models ─────────────────────────────────────────────────────────────

class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = []
    github: bool = False
    readme: bool = False
    deployment: bool = False
    github_link: str | None = None

class ExperienceEntry(BaseModel):
    company: str
    title: str
    years: float = 0.0
    technologies: list[str] = []

class JobProfile(BaseModel):
    job_id: str
    title: str
    department: str = ""
    required_skills: list[str]
    preferred_skills: list[str] = []
    soft_skills: list[str] = []
    required_experience: float = 0.0
    required_certifications: list[str] = []
    job_level: str = "Mid"
    location: str = "Remote"

class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    email: str = ""
    skills: list[str]
    experience: float = 0.0
    certifications: list[str] = []
    education: str = ""
    current_role: str = ""
    projects: list[ProjectEntry] = []
    career_progression: list[str] = []
    github_verified: bool = False
    linkedin_verified: bool = False


# ── Per-service result models ─────────────────────────────────────────────────

class SkillMatchDetail(BaseModel):
    job_skill: str
    matched_candidate_skill: str | None
    similarity_score: float
    is_matched: bool

class SemanticMatchResult(BaseModel):
    candidate_id: str
    semantic_match_score: float
    matched_req_pct: float
    matched_pref_pct: float
    matched_skills: list[SkillMatchDetail]
    unmatched_job_skills: list[str]

class CapabilityResult(BaseModel):
    candidate_id: str
    capability_score: float
    feedback: str

class VerificationResult(BaseModel):
    candidate_id: str
    verification_score: float
    learning_score: float
    growth_score: float
    career_score: float
    project_score: float
    evidence_score: float

class GapResult(BaseModel):
    candidate_id: str
    job_id: str
    missing_skills: list[str]
    skill_gap_pct: float
    experience_gap: float
    cert_gap: int
    gap_score: float

class RoleRecommendation(BaseModel):
    job_id: str
    title: str
    score: float

class FeatureVector(BaseModel):
    semantic_match_score: float
    capability_score: float
    matched_req_pct: float
    matched_pref_pct: float
    verification_score: float
    learning_score: float
    growth_score: float
    career_score: float
    project_score: float
    evidence_score: float
    skill_gap_pct: float
    experience_gap: float
    cert_gap: float
    exp_years: float
    cert_count: float


# ── Final output models ───────────────────────────────────────────────────────

class RankedCandidate(BaseModel):
    rank: int
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str
    final_score: float
    semantic_match_score: float
    capability_score: float
    verification_score: float
    growth_score: float
    gap_score: float
    missing_skills: list[str]
    alternative_roles: list[RoleRecommendation]
    explanation: str
    feature_breakdown: FeatureVector


# ── Request / response wrappers ───────────────────────────────────────────────

class RankRequest(BaseModel):
    job: JobProfile
    candidates: list[CandidateProfile]

class RankResponse(BaseModel):
    job_id: str
    job_title: str
    total_candidates: int
    ranked: list[RankedCandidate]
