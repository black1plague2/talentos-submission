"""
Recruiter explanation generator.
Upgraded from noel's template string to an actual LLM call.
Falls back to a structured template when no OpenAI key is set.
"""
import json
from config import LLM_MODEL, OPENAI_API_KEY
from models.schemas import RankedCandidate


def _template_explanation(r: RankedCandidate) -> str:
    strengths, weaknesses = [], []
    if r.semantic_match_score >= 70:
        strengths.append("strong semantic skill alignment")
    if r.capability_score >= 70:
        strengths.append("high capability score from project evidence")
    if r.verification_score >= 70:
        strengths.append("well-verified credentials")
    if r.growth_score >= 70:
        strengths.append("consistent growth trajectory")
    if r.gap_score > 30:
        weaknesses.append(f"skill gaps in: {', '.join(r.missing_skills[:3])}")
    if not strengths:
        strengths.append("moderate overall profile")
    strong_str = ", ".join(strengths)
    weak_str = (f" Key gaps: {'; '.join(weaknesses)}." if weaknesses else "")
    return (
        f"{r.candidate_name} (Rank #{r.rank}, Score {r.final_score:.1f}/100): "
        f"Demonstrates {strong_str}.{weak_str}"
    )


def generate_explanation(ranked: RankedCandidate) -> str:
    if not OPENAI_API_KEY:
        return _template_explanation(ranked)

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = (
        "You are a senior recruiter. Write a concise 2-sentence hiring recommendation "
        "for this candidate based on their scores. Be specific and actionable.\n\n"
        f"Candidate: {ranked.candidate_name}\n"
        f"Role: {ranked.job_title}\n"
        f"Final Score: {ranked.final_score:.1f}/100 (Rank #{ranked.rank})\n"
        f"Semantic Match: {ranked.semantic_match_score:.0f}%\n"
        f"Capability Score: {ranked.capability_score:.0f}/100\n"
        f"Verification Score: {ranked.verification_score:.0f}/100\n"
        f"Growth Score: {ranked.growth_score:.0f}/100\n"
        f"Missing Skills: {ranked.missing_skills or 'None'}\n"
    )
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return _template_explanation(ranked)
