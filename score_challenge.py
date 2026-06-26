"""
Challenge submission generator for the Redrob AI Senior AI Engineer role.

Reads candidates.jsonl (the full 5000-candidate dataset), scores each candidate
against the job description, and outputs the top 100 as a valid submission CSV.

Run:
    python score_challenge.py
Output:
    output/submission.csv
"""

import csv
import json
import re
from datetime import datetime, date
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
DATASET_DIR = Path(
    r"C:\Users\GARV BANSAL\Downloads\challenge_dataset"
    r"\[PUB] India_runs_data_and_ai_challenge"
    r"\India_runs_data_and_ai_challenge"
)
CANDIDATES_FILE = DATASET_DIR / "candidates.jsonl"
OUTPUT_FILE = Path(__file__).parent / "output" / "submission.csv"
OUTPUT_FILE.parent.mkdir(exist_ok=True)

TODAY = date(2026, 6, 26)

# ── Job-specific AI skill vocabulary ─────────────────────────────────────────
AI_CORE_SKILLS = {
    # Vector / semantic search
    "embeddings", "embedding", "faiss", "pinecone", "weaviate", "qdrant",
    "milvus", "chroma", "vector database", "vector store", "vector search",
    "elasticsearch", "opensearch", "bm25", "hybrid search", "dense retrieval",
    "semantic search", "approximate nearest neighbor", "ann", "hnsw",
    # LLM / fine-tuning
    "llm", "large language model", "fine-tuning", "fine tuning", "lora",
    "qlora", "peft", "rlhf", "instruction tuning", "gpt", "claude", "llama",
    # Transformers / NLP
    "transformers", "sentence-transformers", "sentence transformers", "bert",
    "roberta", "t5", "nlp", "natural language processing", "information retrieval",
    "cross-encoder", "bi-encoder",
    # Ranking & Retrieval
    "learning to rank", "ltr", "ranking", "reranking", "re-ranking",
    "ndcg", "mrr", "map", "recommendation", "recommender", "retrieval",
    "rag", "retrieval augmented generation",
    # ML Frameworks
    "pytorch", "tensorflow", "jax", "huggingface", "hugging face", "keras",
    # Ops
    "mlops", "mlflow", "weights & biases", "model serving", "triton",
    # Skill assessment names that appear in the dataset
    "image classification", "speech recognition", "tts", "gans", "milvus",
}

CONSULTING_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl technologies", "tech mahindra", "mphasis", "hexaware",
    "ltimindtree", "mindtree", "ibm", "deloitte", "kpmg", "pwc",
    "ernst & young", "l&t infotech", "persistent systems",
}

RELEVANT_CAREER_KEYWORDS = {
    "ranking", "retrieval", "recommendation", "embedding", "vector", "search",
    "nlp", "natural language", "llm", "language model", "fine-tun",
    "semantic", "matching", "scoring", "inference", "machine learning",
    "recommendation system", "search engine", "faiss", "pinecone", "bert",
    "transformer", "pytorch", "tensorflow", "a/b test", "experiment",
    "production ml", "mlops", "feature store", "model serving", "rerank",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _lower(text: str) -> str:
    return text.lower() if text else ""


def _days_since(date_str: str | None) -> int:
    if not date_str:
        return 9999
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        return (TODAY - d).days
    except Exception:
        return 9999


def _is_consulting_only(career: list[dict]) -> bool:
    """True only if EVERY role is at a known consulting firm."""
    if not career:
        return False
    for role in career:
        company = _lower(role.get("company", ""))
        if not any(firm in company for firm in CONSULTING_FIRMS):
            return False  # at least one non-consulting role found
    return True


def _count_ai_skills(skills: list[dict]) -> tuple[int, float]:
    """Returns (count_of_ai_skills, avg_proficiency_weight)."""
    PROFICIENCY = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.85, "expert": 1.0}
    ai_skills = []
    for s in skills:
        name = _lower(s.get("name", ""))
        if any(k in name for k in AI_CORE_SKILLS):
            ai_skills.append(PROFICIENCY.get(s.get("proficiency", "beginner"), 0.25))
    if not ai_skills:
        return 0, 0.0
    return len(ai_skills), sum(ai_skills) / len(ai_skills)


def _career_relevance(career: list[dict]) -> float:
    """0-1 score based on how many career descriptions mention relevant systems."""
    if not career:
        return 0.0
    hits = 0
    for role in career:
        desc = _lower(role.get("description", ""))
        title = _lower(role.get("title", ""))
        combined = desc + " " + title
        kw_hits = sum(1 for k in RELEVANT_CAREER_KEYWORDS if k in combined)
        if kw_hits >= 2:
            hits += 1
    return min(hits / max(len(career), 1), 1.0)


def _assessment_score(signals: dict) -> float:
    """Average skill assessment score (0-100) for AI-relevant skills, normalized to 0-1."""
    assessments: dict = signals.get("skill_assessment_scores", {}) or {}
    if not assessments:
        return 0.0
    scores = []
    for skill, val in assessments.items():
        if any(k in _lower(skill) for k in AI_CORE_SKILLS):
            scores.append(val)
    if not scores:
        return 0.0
    return min(sum(scores) / len(scores) / 100.0, 1.0)


def _behavioral_score(signals: dict) -> float:
    """0-1 composite from platform engagement signals."""
    s = 0.0

    # Open to work
    if signals.get("open_to_work_flag"):
        s += 0.20

    # Recruiter response rate (strong signal per JD)
    rr = signals.get("recruiter_response_rate", 0)
    s += rr * 0.25

    # Recently active (last 90 days = full credit, fades)
    days = _days_since(signals.get("last_active_date"))
    if days <= 30:
        s += 0.20
    elif days <= 90:
        s += 0.15
    elif days <= 180:
        s += 0.05

    # GitHub activity (relevant for engineering role)
    gh = signals.get("github_activity_score", -1)
    if gh >= 0:
        s += (gh / 100.0) * 0.15

    # Interview reliability
    icr = signals.get("interview_completion_rate", 0)
    s += icr * 0.10

    # Profile completeness
    pc = signals.get("profile_completeness_score", 0) / 100.0
    s += pc * 0.10

    return min(s, 1.0)


def score_candidate(c: dict) -> tuple[float, str]:
    """Returns (raw_score_0_to_1, reasoning_string)."""
    profile = c.get("profile", {})
    career = c.get("career_history", [])
    skills = c.get("skills", [])
    certs = c.get("certifications", [])
    signals = c.get("redrob_signals", {})

    yoe = profile.get("years_of_experience", 0)
    current_title = _lower(profile.get("current_title", ""))

    # ── 1. Experience score (optimal 5-9 years) ────────────────────────────
    if 5 <= yoe <= 9:
        exp_score = 1.0
    elif 4 <= yoe < 5:
        exp_score = 0.80
    elif 9 < yoe <= 12:
        exp_score = 0.75  # slightly over but still fine
    elif 3 <= yoe < 4:
        exp_score = 0.55
    elif yoe > 12:
        exp_score = 0.55  # likely moved to architecture/management
    else:
        exp_score = max(0.1, yoe / 5.0 * 0.55)

    # ── 2. AI skill match ─────────────────────────────────────────────────
    ai_count, ai_prof_avg = _count_ai_skills(skills)
    # Normalize: 8+ AI skills = full score
    skill_score = min(ai_count / 8.0, 1.0) * 0.6 + ai_prof_avg * 0.4

    # ── 3. Career relevance (did they BUILD these systems?) ───────────────
    career_score = _career_relevance(career)

    # ── 4. Platform behavioral signals ───────────────────────────────────
    behavioral = _behavioral_score(signals)

    # ── 5. Assessment scores (actual test results) ────────────────────────
    assessment = _assessment_score(signals)

    # ── 6. Certification bonus ────────────────────────────────────────────
    cert_bonus = min(len(certs) * 0.02, 0.06)

    # ── Raw composite score ───────────────────────────────────────────────
    score = (
        exp_score     * 0.15 +
        skill_score   * 0.30 +
        career_score  * 0.30 +
        behavioral    * 0.15 +
        assessment    * 0.07 +
        cert_bonus
    )

    # ── Penalties ─────────────────────────────────────────────────────────

    # Consulting-only background is a hard disqualifier per JD
    if _is_consulting_only(career):
        score *= 0.35

    # Not open to work AND inactive for 6+ months — low hire probability
    if not signals.get("open_to_work_flag") and _days_since(signals.get("last_active_date")) > 180:
        score *= 0.60

    # Clearly wrong domain — CV/robotics/pure sales with zero AI skills
    if ai_count == 0 and not any(
        k in current_title for k in ("ml", "ai", "data", "engineer", "research", "nlp", "software")
    ):
        score *= 0.50

    score = max(0.0, min(1.0, round(score, 4)))

    # ── Reasoning string (matches sample format) ──────────────────────────
    reasoning = (
        f"{profile.get('current_title', 'N/A')} with {yoe} yrs; "
        f"{ai_count} AI core skills; "
        f"response rate {signals.get('recruiter_response_rate', 0):.2f}."
    )

    return score, reasoning


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading candidates from {CANDIDATES_FILE} ...")
    candidates = []

    with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
                raw_score, reasoning = score_candidate(c)
                candidates.append({
                    "candidate_id": c["candidate_id"],
                    "score": raw_score,
                    "reasoning": reasoning,
                })
            except Exception as e:
                print(f"  Skipping line {i+1}: {e}")

            if (i + 1) % 500 == 0:
                print(f"  Processed {i+1} candidates...")

    print(f"Total candidates scored: {len(candidates)}")

    # Sort by score desc; tie-break by candidate_id asc (per validation rules)
    candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    # Take top 100
    top100 = candidates[:100]

    # Assign non-increasing scores (required by validator)
    # Scores are already non-increasing after sort; just assign ranks
    for rank, c in enumerate(top100, start=1):
        c["rank"] = rank

    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for c in top100:
            writer.writerow([c["candidate_id"], c["rank"], c["score"], c["reasoning"]])

    print(f"\nTop 10 candidates:")
    for c in top100[:10]:
        print(f"  #{c['rank']:3d}  {c['candidate_id']}  score={c['score']:.4f}  {c['reasoning']}")

    print(f"\nSubmission written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
