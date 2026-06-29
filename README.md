# TalentOS — Redrob AI Hackathon Submission

**India Runs: Data & AI Challenge — Intelligent Candidate Discovery & Ranking**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![No API calls](https://img.shields.io/badge/Offline-No%20API%20calls-success?style=for-the-badge)](https://github.com/black1plague2/talentos-submission)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

**[▶ Live Demo](https://black1plague2.github.io/talentos-submission/demo.html)**

---

## What it does

Ranks 100,000 candidates from the Redrob dataset against the **Senior AI Engineer — Founding Team** job description. Fully offline, no API calls, no GPU, runs in <5 minutes on CPU.

---

## Reproduce the submission

```bash
# 1. Clone and enter the repo
git clone https://github.com/black1plague2/talentos-submission.git
cd talentos-submission

# 2. No pip install needed — stdlib only
#    (Python 3.10+ required)

# 3. Place candidates.jsonl in this directory (from the hackathon bundle)
#    Gzipped input also works: candidates.jsonl.gz

# 4. Run the ranker
python rank.py --candidates candidates.jsonl --out submission.csv

# 5. Validate format before submitting
python validate_submission.py submission.csv
```

**Expected runtime:** 60–120 seconds for 100K candidates on a standard CPU.  
**Memory:** <200 MB peak.

---

## Scoring approach

Five components, weighted for NDCG@10 emphasis (top-10 quality = 50% of final score):

| Component | Weight | Signal |
|---|---|---|
| **AI Skill Match** | 35% | Embeddings, vector DBs (FAISS/Pinecone/Qdrant), retrieval, RAG, NLP, ranking eval — matched with proficiency/duration/endorsement weighting + `skill_assessment_scores` from Redrob |
| **Career Quality** | 30% | Product company history, fraction of career in AI/ML roles, production evidence in role descriptions; penalises pure consulting (TCS/Infosys/Wipro/Accenture etc.) |
| **Availability** | 20% | 23 Redrob behavioral signals: `open_to_work_flag`, `last_active_date`, `recruiter_response_rate`, `notice_period_days`, `interview_completion_rate`, `github_activity_score` |
| **Experience Fit** | 10% | Piecewise score peaking at 6–8 yrs (JD's stated preferred range) |
| **Location** | 5% | India-based (Pune/Noida/Hyderabad/Mumbai/Bangalore) preferred; non-India + `willing_to_relocate` gets partial credit |

**Honeypot detection** (Stage 3): expert skills with 0 months used and 0 endorsements, career duration inflation vs actual date spans, total skill-months exceeding what's physically possible → scored 0.

---

## Why no embeddings/LLMs?

The spec requires **<5 min on CPU-only, no network**. Running sentence-transformer embeddings on 100K candidates takes 20–40 min without GPU, and calling any hosted LLM is explicitly banned. Structured keyword matching on the skill fields achieves <2 min runtime and is fully reproducible.

---

## Repository structure

```
rank.py                    # Entry point: python rank.py --candidates X --out Y
scoring/
  jd_profile.py            # JD skill requirements + disqualifier lists (constants)
  skills.py                # AI/IR skill matching with proficiency/duration weighting
  career.py                # Career analysis: consulting penalty, AI role ratio
  availability.py          # Redrob behavioral signals → availability score
  honeypot.py              # Impossible profile detection
  reasoning.py             # Per-candidate reasoning for Stage 4 review
requirements.txt           # stdlib only; flask optional for demo
Dockerfile                 # Stage 3 sandboxed reproduction
demo.html                  # Sandbox/demo link (hosted on GitHub Pages)
submission_metadata.yaml   # Team + compute metadata
```

---

## Design decisions

**Why 35% skill / 30% career?**  
The JD explicitly disqualifies candidates at purely consulting firms or non-AI roles, regardless of their skill list. A Marketing Manager with perfect AI keywords is stated as "not a fit" in the JD. Career background is nearly as decisive as skill match.

**Why 20% availability?**  
The JD is explicit: "a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% recruiter response rate is not actually available." Availability is a first-class ranking signal.

**Honeypot avoidance**  
Detecting ~80 honeypots protects the Stage 3 score. Our checks flag: ghost-expert skills (expert proficiency + 0 months used + 0 endorsements ≥4 occurrences), career duration inconsistencies vs actual start/end dates, and total skill-months impossibly large for the claimed experience.

---

<div align="center">
Built for the <b>India Runs: Data & AI Challenge</b> — Redrob AI
</div>
