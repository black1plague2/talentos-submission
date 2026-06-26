"""
Multi-dimensional verification & growth scorer (from poojit branch, wrapped as a class).
Outputs 6 sub-scores + composite verification_score that replaces the mock verification.json.
"""
from models.schemas import CandidateProfile, VerificationResult


def _learning_score(c: CandidateProfile) -> float:
    score = len(c.skills) * 5 + len(c.certifications) * 10 + len(c.projects) * 5
    return min(float(score), 100.0)


def _growth_score(c: CandidateProfile) -> float:
    total = len(c.skills) + len(c.certifications) + len(c.projects)
    years = max(c.experience, 0.5)
    return min((total / years) * 10, 100.0)


def _career_score(c: CandidateProfile) -> float:
    return min(len(c.career_progression) * 25.0, 100.0)


def _project_score(c: CandidateProfile) -> float:
    if not c.projects:
        return 0.0
    total = 0.0
    for p in c.projects:
        s = 0.0
        if p.github:
            s += 40
        if p.readme:
            s += 30
        if p.deployment:
            s += 30
        total += s
    return total / len(c.projects)


def _evidence_score(c: CandidateProfile) -> float:
    cert_s = len(c.certifications) * 20
    github_projects = sum(1 for p in c.projects if p.github)
    github_s = github_projects * 15
    # Bonus for platform verification
    platform_bonus = (10 if c.github_verified else 0) + (10 if c.linkedin_verified else 0)
    return min(cert_s + github_s + platform_bonus, 100.0)


def run_verification_scoring(candidate: CandidateProfile) -> VerificationResult:
    learning = _learning_score(candidate)
    growth = _growth_score(candidate)
    career = _career_score(candidate)
    project = _project_score(candidate)
    evidence = _evidence_score(candidate)

    # Composite verification score — equal weighted average of all 5 sub-scores
    verification = round(
        0.20 * learning + 0.20 * growth + 0.20 * career + 0.20 * project + 0.20 * evidence, 2
    )

    return VerificationResult(
        candidate_id=candidate.candidate_id,
        verification_score=verification,
        learning_score=learning,
        growth_score=growth,
        career_score=career,
        project_score=project,
        evidence_score=evidence,
    )
