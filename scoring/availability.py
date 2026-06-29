"""
Availability & engagement scoring from redrob_signals.

These behavioral signals are explicitly called out in the JD:
  "A perfect-on-paper candidate who hasn't logged in for 6 months
   and has a 5% recruiter response rate is, for hiring purposes,
   not actually available."

Also factors in notice period (JD prefers ≤30 days), location
willingness, and GitHub activity for technical engagement.
"""
from datetime import date, datetime

_TODAY = date.today()


def _days_since(date_str: str) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (_TODAY - d).days
    except Exception:
        return 365


def score_availability(signals: dict) -> float:
    """Returns 0–100 availability/engagement score from redrob_signals."""
    if not signals:
        return 25.0

    score = 0.0

    # ── Open to work (most important single signal) ──────────────────────────
    if signals.get("open_to_work_flag", False):
        score += 25.0

    # ── Recency of activity ──────────────────────────────────────────────────
    days_inactive = _days_since(signals.get("last_active_date", "2020-01-01"))
    if days_inactive <= 7:
        score += 22.0
    elif days_inactive <= 30:
        score += 16.0
    elif days_inactive <= 60:
        score += 10.0
    elif days_inactive <= 90:
        score += 5.0
    elif days_inactive <= 180:
        score += 2.0
    # > 180 days inactive → 0 pts (candidate effectively unavailable)

    # ── Recruiter response rate ──────────────────────────────────────────────
    rr = float(signals.get("recruiter_response_rate", 0.0))
    score += rr * 15.0    # 0–15 pts

    # ── Notice period (JD explicitly wants ≤30 days) ────────────────────────
    notice = int(signals.get("notice_period_days", 90))
    if notice <= 0:
        score += 14.0
    elif notice <= 15:
        score += 12.0
    elif notice <= 30:
        score += 10.0
    elif notice <= 60:
        score += 5.0
    elif notice <= 90:
        score += 2.0
    # 90+ days → 0 pts

    # ── Interview reliability ────────────────────────────────────────────────
    icr = float(signals.get("interview_completion_rate", 0.5))
    score += icr * 8.0    # 0–8 pts

    # ── GitHub activity (technical engagement) ───────────────────────────────
    gh = float(signals.get("github_activity_score", -1))
    if gh > 0:
        score += min(gh / 100.0, 1.0) * 8.0   # 0–8 pts

    # ── Profile completeness ─────────────────────────────────────────────────
    pc = float(signals.get("profile_completeness_score", 50.0))
    score += (pc / 100.0) * 4.0   # 0–4 pts

    # ── Verified identity (small trust signal) ───────────────────────────────
    if signals.get("verified_email") and signals.get("verified_phone"):
        score += 2.0
    elif signals.get("verified_email") or signals.get("verified_phone"):
        score += 1.0

    # ── Willing to relocate (useful for non-India candidates) ────────────────
    if signals.get("willing_to_relocate", False):
        score += 2.0

    return max(0.0, min(score, 100.0))
