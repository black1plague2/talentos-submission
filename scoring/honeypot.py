"""
Honeypot detection.

The dataset contains ~80 candidates with subtly impossible profiles.
Examples flagged by the spec:
  - 8 years experience at a company founded 3 years ago
  - "expert" proficiency in 10 skills with 0 years used

We detect these with several independent checks. Any single check
firing sets honeypot=True so the candidate scores 0.
"""
from datetime import datetime


def _actual_months(role: dict) -> int:
    try:
        start = datetime.strptime(role["start_date"], "%Y-%m-%d")
        end_str = role.get("end_date")
        end = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime.today()
        return max(0, (end.year - start.year) * 12 + (end.month - start.month))
    except Exception:
        return 0


def is_honeypot(c: dict) -> bool:
    """Returns True if the candidate profile is detectably impossible."""
    profile = c.get("profile", {})
    skills = c.get("skills", [])
    career = c.get("career_history", [])
    exp_years = float(profile.get("years_of_experience", 0))

    # ── Check 1: "expert" skills with 0 duration AND 0 endorsements ─────────
    # Claiming expert-level mastery in a skill never actually practiced
    ghost_expert = sum(
        1 for s in skills
        if s.get("proficiency") == "expert"
        and s.get("duration_months", 0) == 0
        and s.get("endorsements", 0) == 0
    )
    if ghost_expert >= 4:
        return True

    # ── Check 2: Career duration inconsistency ───────────────────────────────
    # If the actual months (from start/end dates) for a role is much smaller
    # than the claimed duration_months, the profile was inflated.
    for role in career:
        claimed = role.get("duration_months", 0)
        actual = _actual_months(role)
        if actual > 0 and claimed > actual * 2.5 and claimed > 12:
            return True

    # ── Check 3: Total claimed skill months impossibly large ─────────────────
    # Someone with 3 years experience can't have 5 years of practice in
    # each of 10 different skills simultaneously.
    total_skill_months = sum(s.get("duration_months", 0) for s in skills)
    if exp_years > 0 and total_skill_months > exp_years * 12 * 8:
        return True
    # Also catch 1-year profiles claiming massive skill history
    if exp_years <= 1 and total_skill_months > 300:
        return True

    # ── Check 4: Total career duration much larger than experience ───────────
    total_career_months = sum(_actual_months(r) for r in career)
    if exp_years > 0 and total_career_months > (exp_years + 3) * 12 * 1.5:
        return True

    # ── Check 5: Impossible date order in a single role ─────────────────────
    for role in career:
        try:
            start = datetime.strptime(role["start_date"], "%Y-%m-%d")
            end_str = role.get("end_date")
            if end_str:
                end = datetime.strptime(end_str, "%Y-%m-%d")
                if start > end:
                    return True
        except Exception:
            pass

    return False
