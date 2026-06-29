"""
Career history scoring for the Senior AI Engineer role.

Signals evaluated:
  - Fraction of career in AI/ML roles
  - Product company vs pure consulting background
  - Evidence of production deployments in role descriptions
  - Current title relevance
  - Disqualifiers: pure consulting history, CV/speech-only background
"""
from datetime import datetime

from scoring.jd_profile import (
    AI_TITLE_KEYWORDS,
    CONSULTING_FIRMS,
    NON_FIT_TITLE_KEYWORDS,
    PRODUCTION_KEYWORDS,
    PURE_CV_SPEECH_KEYWORDS,
)

_TECH_INDUSTRIES = {
    "technology", "software", "ai", "saas", "internet", "fintech",
    "e-commerce", "ecommerce", "edtech", "healthtech", "proptech",
    "media technology", "it services", "information technology",
}


def _actual_months(role: dict) -> int:
    """Compute months from start/end dates as a sanity check on duration_months."""
    try:
        start = datetime.strptime(role["start_date"], "%Y-%m-%d")
        end_str = role.get("end_date")
        end = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime.today()
        return max(0, (end.year - start.year) * 12 + (end.month - start.month))
    except Exception:
        return role.get("duration_months", 0)


def _is_consulting(company: str, industry: str) -> bool:
    co = company.lower()
    ind = industry.lower()
    if any(firm in co for firm in CONSULTING_FIRMS):
        return True
    if any(kw in ind for kw in ("consulting", "outsourcing", "it services", "bpo", "staffing")):
        return True
    return False


def _is_product_company(industry: str, is_consult: bool) -> bool:
    if is_consult:
        return False
    ind = industry.lower()
    return any(kw in ind for kw in _TECH_INDUSTRIES) or "product" in ind


def score_career(career_history: list[dict], profile: dict) -> float:
    """Returns 0–100 career quality score."""
    if not career_history:
        return 15.0

    score = 0.0
    ai_months = 0
    consulting_months = 0
    total_months = 0
    has_product_company = False
    production_evidence = 0

    all_titles = " ".join(r.get("title", "") for r in career_history).lower()

    for role in career_history:
        company = role.get("company", "")
        title = role.get("title", "").lower()
        desc = role.get("description", "").lower()
        industry = role.get("industry", "")
        duration = _actual_months(role)
        total_months += duration

        is_consult = _is_consulting(company, industry)
        if is_consult:
            consulting_months += duration
        elif _is_product_company(industry, is_consult):
            has_product_company = True

        if any(kw in title for kw in AI_TITLE_KEYWORDS):
            ai_months += duration

        prod_hits = sum(1 for kw in PRODUCTION_KEYWORDS if kw in desc)
        if prod_hits >= 2:
            production_evidence += 1

    # ── 1. AI role fraction (35 pts) ────────────────────────────────────────
    if total_months > 0:
        ai_ratio = min(ai_months / total_months, 1.0)
        score += ai_ratio * 35

    # ── 2. Consulting penalty (up to -40 pts) ───────────────────────────────
    if total_months > 0:
        consult_ratio = consulting_months / total_months
        if consult_ratio >= 0.95:
            score -= 40        # entire career at IT services
        elif consult_ratio >= 0.5:
            score -= 20
        elif consult_ratio >= 0.2:
            score -= 8

    # ── 3. Product company experience (+20 pts) ─────────────────────────────
    if has_product_company:
        score += 20

    # ── 4. Production evidence in descriptions (+up to 15 pts) ─────────────
    score += min(production_evidence * 5, 15)

    # ── 5. Current title bonus/penalty ──────────────────────────────────────
    current_title = profile.get("current_title", "").lower()
    if any(kw in current_title for kw in AI_TITLE_KEYWORDS):
        score += 15
    elif any(kw in current_title for kw in NON_FIT_TITLE_KEYWORDS):
        score -= 20

    # ── 6. Pure CV/speech disqualifier (JD explicit) ────────────────────────
    has_pure_cv = any(kw in all_titles for kw in PURE_CV_SPEECH_KEYWORDS)
    has_nlp_ir = any(kw in all_titles for kw in AI_TITLE_KEYWORDS
                      if kw not in ("computer vision",))
    if has_pure_cv and not has_nlp_ir:
        score -= 25

    # Base offset so a neutral career doesn't score 0
    return max(0.0, min(score + 15, 100.0))
