"""
Skill match scoring against the Senior AI Engineer JD.

For each candidate skill we consider:
  - name match against JD keywords
  - proficiency level (beginner → expert)
  - duration_months (how long they've used it)
  - endorsements (peer validation)
  - redrob skill_assessment_scores (platform-tested, highest trust)
"""
from scoring.jd_profile import REQUIRED_SKILL_KEYWORDS, NICE_TO_HAVE_KEYWORDS

_PROF_MULT = {"beginner": 0.5, "intermediate": 0.75, "advanced": 1.0, "expert": 1.15}


def _skill_weight(skill: dict) -> float:
    """Returns a quality multiplier 0.5–1.5 for a matched skill."""
    prof = _PROF_MULT.get(skill.get("proficiency", "beginner"), 0.5)
    dur = skill.get("duration_months", 0)
    end = skill.get("endorsements", 0)

    dur_bonus = min(dur / 24.0, 1.0) * 0.2     # up to +0.20 for 24+ months
    end_bonus = min(end / 30.0, 1.0) * 0.15    # up to +0.15 for 30+ endorsements
    return prof + dur_bonus + end_bonus


def score_skills(
    skills: list[dict],
    assessment_scores: dict[str, float] | None = None,
) -> float:
    """
    Returns 0–100 skill match score.
    assessment_scores: from redrob_signals.skill_assessment_scores (str → 0-100).
    """
    if not skills:
        return 0.0

    skill_names_lower = [s.get("name", "").lower() for s in skills]
    skill_text = " ".join(skill_names_lower)

    # ── Required skills match ────────────────────────────────────────────────
    required_weight = 0.0
    required_matched = 0

    for kw in REQUIRED_SKILL_KEYWORDS:
        if kw not in skill_text:
            continue
        required_matched += 1
        # Find the best matching skill entry for this keyword
        for s in skills:
            if kw in s.get("name", "").lower():
                w = _skill_weight(s)
                # Boost if platform-tested
                if assessment_scores:
                    for asm_name, asm_score in assessment_scores.items():
                        if kw in asm_name.lower() or asm_name.lower() in kw:
                            w += (asm_score / 100) * 0.3
                required_weight += w
                break
        else:
            required_weight += 0.5  # keyword found in text but no structured entry

    # Normalise: max possible weight per keyword ≈ 1.6; total required keywords
    max_req = len(REQUIRED_SKILL_KEYWORDS) * 1.6
    req_score = min(required_weight / max_req, 1.0) * 82.0

    # ── Nice-to-have bonus (up to 18 points) ────────────────────────────────
    nice_matched = sum(1 for kw in NICE_TO_HAVE_KEYWORDS if kw in skill_text)
    nice_score = min(nice_matched / max(len(NICE_TO_HAVE_KEYWORDS), 1), 1.0) * 18.0

    return min(req_score + nice_score, 100.0)
