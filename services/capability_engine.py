"""
LLM-based capability evaluation from project history (from garv branch).
Falls back to rule-based score when OpenAI key is absent.
"""
import json
from config import LLM_MODEL, OPENAI_API_KEY
from models.schemas import CandidateProfile, CapabilityResult, JobProfile

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _rule_based_score(job: JobProfile, candidate: CandidateProfile) -> tuple[float, str]:
    """Heuristic fallback when no OpenAI key is configured."""
    job_skills_lower = {s.lower() for s in job.required_skills}
    candidate_skills_lower = {s.lower() for s in candidate.skills}
    skill_overlap = len(job_skills_lower & candidate_skills_lower) / max(len(job_skills_lower), 1)

    project_bonus = min(len(candidate.projects) * 8, 30)
    exp_bonus = min(candidate.experience * 5, 25)
    base = round(skill_overlap * 45 + project_bonus + exp_bonus)
    score = min(max(base, 10), 95)
    return float(score), "Rule-based estimate (no LLM key configured)."


def run_capability_evaluation(job: JobProfile, candidate: CandidateProfile) -> CapabilityResult:
    if not OPENAI_API_KEY:
        score, feedback = _rule_based_score(job, candidate)
        return CapabilityResult(candidate_id=candidate.candidate_id,
                                capability_score=score, feedback=feedback)

    prompt_system = (
        "Given a job requirement and a candidate's project/experience data, "
        "estimate capability score (0-100). Focus on: project complexity, "
        "technology overlap, and problem-solving evidence. "
        'Return ONLY valid JSON: {"capabilityScore": <number>, "feedback": "<2-3 sentences>"}'
    )
    prompt_user = (
        f"Job: {job.title} requiring {', '.join(job.required_skills)}\n"
        f"Candidate projects: {json.dumps([p.model_dump() for p in candidate.projects])}\n"
        f"Candidate experience: {candidate.experience} years, skills: {candidate.skills}"
    )

    try:
        resp = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": prompt_system},
                      {"role": "user", "content": prompt_user}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        score = max(0, min(100, int(data.get("capabilityScore", 50))))
        feedback = str(data.get("feedback", ""))
    except Exception:
        score, feedback = _rule_based_score(job, candidate)

    return CapabilityResult(candidate_id=candidate.candidate_id,
                            capability_score=float(score), feedback=feedback)
