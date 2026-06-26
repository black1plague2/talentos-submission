# TalentOS — Unified AI Recruitment Intelligence Engine

> **Branch:** `integration` | Combines all 4 team branches into a single ML-powered pipeline

---

## Architecture Overview

```
Job Description + Candidate Profiles
              │
              ▼
    ┌─────────────────────┐
    │  Semantic Matcher   │  ← sentence-transformers + FAISS (garv)
    │  all-MiniLM-L6-v2   │    Finds semantic skill overlap, not just keyword match
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │  Capability Engine  │  ← GPT-4o-mini (garv)
    │  (LLM evaluation)   │    Infers practical capability from project evidence
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │ Verification Scorer │  ← Multi-dimensional scoring (poojit)
    │  6 sub-scores       │    learning / growth / career / project / evidence
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │    Gap Engine       │  ← Semantic gap analysis (noel, enhanced)
    │  (FAISS-powered)    │    Skill / experience / certification gaps
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │  Feature Vector     │  15 features from all 4 modules
    │  (15 dimensions)    │
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │  LightGBM Ranker    │  ← ML model (trained on 1000 synthetic pairs)
    │  (auto-trained)     │    Learns non-linear feature interactions
    └─────────┬───────────┘
              │
    ┌─────────▼───────────┐
    │  Role Discovery     │  ← Semantic alternative role matching (noel)
    │  RecruiterCopilot   │  ← LLM-generated hiring explanation (noel, upgraded)
    └─────────────────────┘
              │
              ▼
    ranked_output.json  ✓
```

---

## Why LightGBM Over a Fixed Formula

The original system used:
```
Score = 0.35×match + 0.25×capability + 0.20×growth + 0.15×verification - 0.15×gap
```

This linear formula assumes features are independent and weights are known. They're not.

LightGBM (gradient-boosted trees) captures:
- **Multiplicative interactions**: a candidate needs BOTH high match AND high capability — not just one
- **Non-linear thresholds**: a 2-year experience gap matters much more than a 0.5-year gap
- **Optimal weights**: learned from data, not hand-tuned
- **Feature importance ranking** printed at startup

---

## Feature Vector (15 dimensions)

| Feature | Source | Description |
|---------|--------|-------------|
| `semantic_match_score` | garv | FAISS cosine score (0–100) |
| `capability_score` | garv | LLM project evaluation (0–100) |
| `matched_req_pct` | garv | % of required skills semantically matched |
| `matched_pref_pct` | garv | % of preferred skills matched |
| `verification_score` | poojit | Composite credential score |
| `learning_score` | poojit | Skills × certs × projects |
| `growth_score` | poojit | Total growth / experience years |
| `career_score` | poojit | Career progression levels × 25 |
| `project_score` | poojit | GitHub + readme + deployment signals |
| `evidence_score` | poojit | Certs + GitHub projects + platform verification |
| `skill_gap_pct` | noel | % required skills missing (semantic) |
| `experience_gap` | noel | Years of experience shortage |
| `cert_gap` | noel | Missing required certifications |
| `exp_years` | data | Candidate total years of experience |
| `cert_count` | data | Number of certifications held |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Add your OPENAI_API_KEY (optional — system works without it using rule-based fallback)
```

### 3. Generate ranked output (competition submission)
```bash
python run_ranking.py
# Output: output/ranked_output.json
```

### 4. Run as API server
```bash
python main.py
# API docs: http://localhost:8000/docs
```

### 5. Docker
```bash
docker-compose up
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/rank` | Rank candidates for a job (full pipeline) |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Get specific job |
| `GET` | `/candidates` | List all candidates |
| `GET` | `/candidates/{id}` | Get specific candidate |
| `GET` | `/health` | Health check |

### Example: Rank candidates

```bash
curl -X POST http://localhost:8000/rank \
  -H "Content-Type: application/json" \
  -d '{
    "job": {
      "job_id": "JOB001",
      "title": "Backend Engineer",
      "required_skills": ["Python", "FastAPI", "Docker", "AWS"],
      "required_experience": 3,
      "required_certifications": []
    },
    "candidates": [
      {
        "candidate_id": "C001",
        "name": "John Doe",
        "skills": ["Python", "FastAPI", "Docker"],
        "experience": 2,
        "certifications": [],
        "projects": []
      }
    ]
  }'
```

---

## Output Format (`ranked_output.json`)

```json
[
  {
    "rank": 1,
    "candidate_id": "C002",
    "candidate_name": "Sarah Wilson",
    "job_id": "JOB001",
    "job_title": "Backend Engineer",
    "final_score": 84.7,
    "semantic_match_score": 95.0,
    "capability_score": 88.0,
    "verification_score": 74.0,
    "growth_score": 67.5,
    "gap_score": 5.2,
    "missing_skills": [],
    "alternative_roles": [...],
    "explanation": "Sarah Wilson demonstrates exceptional semantic alignment..."
  }
]
```

---

## Technical Choices

| Decision | Choice | Why |
|----------|--------|-----|
| Embedding model | `all-MiniLM-L6-v2` | Fast, 384-dim, strong skill-domain semantics |
| Skill matching | FAISS `IndexFlatIP` (cosine) | Sub-millisecond exact search on small candidate sets |
| ML ranker | LightGBM regressor | Handles mixed feature types, captures non-linear interactions, trains in <5s |
| Training data | 1000 synthetic pairs | Generated from domain-expert rules, covers full feature space |
| LLM | GPT-4o-mini | Low latency, affordable, sufficient for capability/explanation tasks |
| API | FastAPI | Async, auto-docs, Pydantic validation |

---

## Team Integration Map

| Branch | Person | Integrated As |
|--------|--------|--------------|
| `harshith` | Person 1 | Data schemas, expanded candidate/job dataset |
| `poojit` | Person 2 | `services/verification_scorer.py` |
| `garv` | Person 3 | `services/semantic_matcher.py`, `capability_engine.py`, `embedding_pipeline.py` |
| `noel` | Person 4 | `services/gap_engine.py`, `role_discovery.py`, `recruiter_copilot.py` |
| `integration` | All | `ml/ranker.py`, unified `main.py`, `run_ranking.py` |
