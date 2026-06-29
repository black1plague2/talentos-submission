"""
Per-candidate reasoning generation.

Spec requirements (Stage 4 manual review):
  - Specific facts from the profile (years, title, named skills, signal values)
  - Connection to JD requirements, not generic praise
  - Honest concerns (notice period, inactivity, skill gaps, consulting background)
  - No hallucination — every claim must exist in the profile
  - Variation across rows
  - Tone matches rank (rank 1 ≠ rank 95)
"""
from datetime import date, datetime

_TODAY = date.today()


def _days_since(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (_TODAY - d).days
    except Exception:
        return 365


def _top_skills(skills: list[dict], limit: int = 3) -> str:
    """Return top N skill names sorted by endorsements + duration."""
    ranked = sorted(
        skills,
        key=lambda s: s.get("endorsements", 0) + s.get("duration_months", 0),
        reverse=True,
    )
    names = [s.get("name", "") for s in ranked[:limit] if s.get("name")]
    return ", ".join(names) if names else "N/A"


def _consulting_flag(career: list[dict]) -> bool:
    from scoring.jd_profile import CONSULTING_FIRMS
    for role in career:
        co = role.get("company", "").lower()
        if any(firm in co for firm in CONSULTING_FIRMS):
            return True
    return False


def generate_reasoning(c: dict, rank: int, score: float, breakdown: dict) -> str:
    """
    Returns a 1–2 sentence reasoning string grounded in the candidate's data.
    Tone shifts from enthusiastic (rank 1-10) → positive (11-30)
    → neutral (31-70) → honest concern (71-100).
    """
    profile = c.get("profile", {})
    skills = c.get("skills", [])
    signals = c.get("redrob_signals", {})
    career = c.get("career_history", [])

    title = profile.get("current_title", "Unknown")
    years = profile.get("years_of_experience", 0)
    location = f"{profile.get('location', '')}, {profile.get('country', '')}".strip(", ")
    top_sk = _top_skills(skills)

    notice = int(signals.get("notice_period_days", 90))
    rr = float(signals.get("recruiter_response_rate", 0.0))
    days_inactive = _days_since(signals.get("last_active_date", "2020-01-01"))
    open_work = signals.get("open_to_work_flag", False)
    gh = float(signals.get("github_activity_score", -1))
    icr = float(signals.get("interview_completion_rate", 0.5))

    has_consulting = _consulting_flag(career)
    skill_score = breakdown.get("skill", 0.0)
    career_score = breakdown.get("career", 0.0)
    avail_score = breakdown.get("availability", 0.0)

    # ── Sentence 1: who they are + key JD-aligned signal ────────────────────
    s1_parts = [f"{title} ({years:.1f} yrs", f"{location})"]

    if skill_score >= 60:
        s1_parts.append(f"with strong AI/IR skills ({top_sk})")
    elif skill_score >= 35:
        s1_parts.append(f"with partial JD skill overlap ({top_sk})")
    else:
        s1_parts.append(f"— limited AI/IR skill match ({top_sk})")

    sentence1 = " ".join(s1_parts) + "."

    # ── Sentence 2: availability + honest concern ────────────────────────────
    positives: list[str] = []
    concerns: list[str] = []

    if open_work:
        positives.append("actively open to work")
    if days_inactive <= 14:
        positives.append("active on platform recently")
    elif days_inactive > 180:
        concerns.append(f"inactive {days_inactive // 30} months")

    if notice <= 30:
        positives.append(f"{notice}d notice period")
    elif notice > 60:
        concerns.append(f"{notice}d notice")

    if rr >= 0.7:
        positives.append(f"{int(rr * 100)}% recruiter response rate")
    elif rr < 0.25:
        concerns.append(f"low response rate ({int(rr * 100)}%)")

    if gh > 50:
        positives.append(f"GitHub score {int(gh)}")
    if icr < 0.4 and icr > 0:
        concerns.append(f"interview completion {int(icr * 100)}%")

    if has_consulting and career_score < 35:
        concerns.append("predominantly consulting background")

    if rank <= 10:
        # Enthusiastic, cite strength
        s2 = "; ".join(positives[:2]) if positives else "strong overall profile for this role."
        if concerns:
            s2 += f"; note: {concerns[0]}"
    elif rank <= 30:
        # Positive with one caveat
        pos_str = "; ".join(positives[:1]) if positives else "reasonable engagement"
        con_str = f"; concern: {concerns[0]}" if concerns else ""
        s2 = pos_str + con_str + "."
    elif rank <= 70:
        # Neutral, state gaps clearly
        if concerns:
            s2 = f"Concerns: {'; '.join(concerns[:2])}."
        else:
            s2 = "Moderate fit — below threshold on skill or career alignment."
    else:
        # Honest about why they're near the bottom
        s2 = f"Below fit threshold — {'; '.join(concerns[:2]) if concerns else 'limited alignment with JD requirements'}."

    return f"{sentence1} {s2}".strip()
