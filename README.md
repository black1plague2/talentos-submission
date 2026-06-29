# TalentOS

> *Finding the needle in a haystack of 100,000 candidates — without any AI.*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Fully Offline](https://img.shields.io/badge/Runs-Fully%20Offline-22c55e?style=flat-square)](https://github.com/black1plague2/talentos-submission)
[![No API Calls](https://img.shields.io/badge/API%20Calls-Zero-f97316?style=flat-square)](https://github.com/black1plague2/talentos-submission)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)

**[▶ Watch it rank 100,000 candidates in real-time →](https://black1plague2.github.io/talentos-submission/demo.html)**

---

## The problem

Redrob dropped 100,000 candidate profiles on us and said: *"Find us the best Senior AI Engineers. You have 5 minutes, a regular laptop, no internet, and no GPU."*

Most people's instinct: run embeddings, call GPT, train a model. None of that works here — 100K candidates through a sentence-transformer takes 30+ minutes on CPU, and the rules explicitly ban API calls.

So we built something different.

---

## The solution

TalentOS reads every candidate in one pass, scores them across five dimensions, filters out ~80 fake "honeypot" profiles, and writes a ranked CSV — all in under 2 minutes using nothing but Python's standard library.

No heavy models. No internet. No GPU. Just careful scoring logic built directly from the job description.

---

## How scoring works

We read the JD closely. It says five things matter:

**1. Can they actually do the AI work? (35%)**

We match each candidate's skill list against 40+ role-specific keywords: embeddings, FAISS, Qdrant, BM25, RAG, NDCG, fine-tuning, etc. But we don't just count matches — we weight them. A skill you've used for 18 months with 20 endorsements counts more than one you listed but never used. The Redrob platform even provides skill assessment scores, which we factor in.

**2. Have they built real AI products — not just consulted? (30%)**

The JD explicitly says: *no pure consulting backgrounds*. So we look at where candidates have worked, what fraction of their career was in actual AI roles, and whether their job descriptions mention production systems. Someone who spent 10 years at TCS doing Java migrations gets penalised, even if they took an ML course last year.

**3. Are they actually reachable right now? (20%)**

The Redrob dataset includes 23 behavioral signals about each candidate. We use them: Are they open to work? When did they last log in? What's their recruiter response rate? What's their notice period? A candidate who hasn't been active in 6 months and responds to 5% of recruiter messages isn't really available — and the JD says so explicitly.

**4. Do their years match the role? (10%)**

The JD wants 5–9 years, ideally 6–8. We score experience on a curve that peaks right there, then slowly drops off for people with too little or too much experience.

**5. Are they in India? (5%)**

Pune or Noida are preferred. Anywhere in India gets full credit. Willing-to-relocate gets partial credit. The rest gets less.

---

## The honeypot problem

Hidden in the 100K candidates are about 80 "honeypot" profiles — subtly fake candidates designed to trap naive rankers. An example: someone with 10 "Expert"-level skills, all with 0 months of usage and 0 endorsements. Or a career history where the total months of work is physically impossible given their age and experience.

We run 5 impossibility checks before ranking. Any candidate that fails gets scored zero and excluded. This protects our Stage 3 evaluation score.

---

## Run it yourself

```bash
# Clone the repo
git clone https://github.com/black1plague2/talentos-submission.git
cd talentos-submission

# No pip install needed — uses Python stdlib only
# (Python 3.10+ required)

# Put candidates.jsonl in this folder (from the hackathon bundle)
# Gzipped input also works: candidates.jsonl.gz

# Run
python rank.py --candidates candidates.jsonl --out submission.csv

# Verify your output format
python validate_submission.py submission.csv
```

**Runtime:** 60–120 seconds for all 100K candidates.
**Memory:** Under 200 MB peak (streams the file, never loads it all at once).

---

## Reproduce with Docker (Stage 3)

```bash
docker build -t talentos-submission .

docker run --rm \
  -v /path/to/candidates.jsonl:/data/candidates.jsonl \
  talentos-submission \
  python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv
```

---

## What's in the repo

```
rank.py                    # The whole ranker — start here
scoring/
  jd_profile.py            # All the JD requirements as constants
  skills.py                # AI skill matching with proficiency/duration weighting
  career.py                # Career quality — consulting penalty, AI role ratio
  availability.py          # 23 behavioral signals → availability score
  honeypot.py              # Fake profile detection
  reasoning.py             # Human-readable explanation per candidate (Stage 4)
Dockerfile                 # For Stage 3 sandboxed reproduction
demo.html                  # Interactive visualisation (GitHub Pages)
submission_metadata.yaml   # Team info + reproduce command
```

---

## Why not use embeddings?

We considered it. The JD literally lists FAISS and vector search as required skills — wouldn't it make sense to use them for ranking?

The constraint is time: embedding 100K candidates through `sentence-transformers` takes 25–45 minutes on CPU. Even with batching, we'd blow past the 5-minute limit. And calling a hosted embedding API is banned.

The skills field in the dataset is already structured — candidates list their skills explicitly, with proficiency levels, durations, and endorsements attached. Matching against those directly is both faster and more accurate than comparing embedding vectors.

We build the search index; we don't need to infer it.

---

## Why 30% on career quality?

Because the JD says so, directly. It lists these as automatic disqualifiers:

- "Pure consulting firm backgrounds (TCS, Infosys, Wipro, Accenture, etc.)"
- "CV/speech-only AI engineers without NLP or search experience"
- "AI experience limited to LangChain wrappers, <12 months"

A Marketing Manager with a perfect skill list is not a fit. Career context matters nearly as much as skills, so we gave it 30%.

---

## Team

**TalentOS** — Redrob AI India Runs Challenge 2026

| Person | Role |
|---|---|
| Garv Bansal | Offline ranker architecture, scoring pipeline |
| Harshith | Candidate embedding research, data analysis |
| Noel Ninan Sheri | Backend infrastructure, system design |
| Poojit | Career quality scoring, evaluation metrics |

---

<div align="center">
  Built for the <b>India Runs: Data & AI Challenge</b> · Redrob AI · 2026
</div>
