#!/usr/bin/env python3
"""
Redrob Hackathon — Senior AI Engineer ranker.

Reads candidates.jsonl (100K candidates) and writes a top-100 submission CSV.
Fully offline: no API calls, no GPU, no network. Designed to run in <5 minutes
on a 16 GB CPU-only machine.

Usage:
    python rank.py --candidates candidates.jsonl --out submission.csv
    python rank.py --candidates candidates.jsonl.gz --out submission.csv
"""
import argparse
import csv
import gzip
import heapq
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

from scoring.skills import score_skills
from scoring.career import score_career
from scoring.availability import score_availability
from scoring.honeypot import is_honeypot
from scoring.reasoning import generate_reasoning
from scoring.jd_profile import INDIA_CITY_KEYWORDS

# ── Scoring weights ──────────────────────────────────────────────────────────
# skill:        how well they match the AI/IR JD requirements
# career:       product company history, AI roles, production evidence
# availability: behavioral signals (open_to_work, recency, response rate, notice)
# experience:   years fit — JD peak is 6–8 years
# location:     India-based / willing to relocate preferred
_WEIGHTS = {
    "skill": 0.35,
    "career": 0.30,
    "availability": 0.20,
    "experience": 0.10,
    "location": 0.05,
}


def _experience_fit(years: float) -> float:
    """Piecewise score peaking at 6–8 yrs matching the JD's preferred range."""
    if years < 2:
        return max(0.0, years * 12)
    if years <= 5:
        return 24.0 + (years - 2) * 17.0
    if years <= 9:
        return 75.0 + (years - 5) * 5.5
    return max(45.0, 97.0 - (years - 9) * 4.0)


def _location_fit(profile: dict, signals: dict) -> float:
    loc = (profile.get("location", "") + " " + profile.get("country", "")).lower()
    in_india = any(kw in loc for kw in INDIA_CITY_KEYWORDS)
    willing = signals.get("willing_to_relocate", False)
    if in_india:
        return 100.0
    if willing:
        return 55.0   # JD says case-by-case for non-India; relocation helps
    return 25.0


def _score_one(c: dict) -> tuple[float, dict]:
    """Score a single candidate. Returns (final_score_0_to_100, breakdown)."""
    if is_honeypot(c):
        return 0.0, {}

    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    assessment = signals.get("skill_assessment_scores", {})

    breakdown = {
        "skill": score_skills(c.get("skills", []), assessment),
        "career": score_career(c.get("career_history", []), profile),
        "availability": score_availability(signals),
        "experience": _experience_fit(profile.get("years_of_experience", 0)),
        "location": _location_fit(profile, signals),
    }
    final = sum(_WEIGHTS[k] * v for k, v in breakdown.items())
    return round(final, 6), breakdown


def _open_file(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def rank_candidates(cand_path: Path, top_n: int = 100) -> list[tuple[float, str, dict, dict]]:
    """
    Stream through candidates.jsonl, keep top_n*10 in a min-heap,
    return top_n sorted by (score DESC, candidate_id ASC).
    Memory: O(top_n * 10) candidate objects in RAM at any time.
    """
    HEAP_SIZE = top_n * 10
    heap: list[tuple[float, str, dict, dict]] = []   # (score, cid, candidate, breakdown)
    total = 0
    honeypots = 0
    t0 = time.time()

    with _open_file(cand_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1
            score, bd = _score_one(c)

            if score == 0.0:
                honeypots += 1
                continue

            cid = c.get("candidate_id", "")
            entry = (score, cid, c, bd)

            if len(heap) < HEAP_SIZE:
                heapq.heappush(heap, entry)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, entry)

            if total % 10_000 == 0:
                elapsed = time.time() - t0
                print(f"  {total:,} processed | {elapsed:.1f}s elapsed | heap top={heap[0][0]:.4f}", flush=True)

    elapsed = time.time() - t0
    print(f"[ranker] Done: {total:,} candidates in {elapsed:.1f}s | honeypots filtered: {honeypots}")

    # Sort descending by score, break ties by candidate_id ascending (spec rule)
    top = sorted(heap, key=lambda x: (-x[0], x[1]))[:top_n]
    return top


def write_csv(results: list[tuple[float, str, dict, dict]], out_path: Path) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (raw_score, cid, c, bd) in enumerate(results, start=1):
            # Normalise to 0-1 range for the submission (spec shows scores like 0.987)
            norm_score = round(raw_score / 100.0, 4)
            reasoning = generate_reasoning(c, rank, norm_score, bd)
            writer.writerow([cid, rank, norm_score, reasoning])

    print(f"[ranker] Wrote {len(results)} rows to {out_path}")
    if results:
        top_score = results[0][0] / 100
        bot_score = results[-1][0] / 100
        print(f"[ranker] Score range: {top_score:.4f} (rank 1) → {bot_score:.4f} (rank {len(results)})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Redrob hackathon candidate ranker")
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates.jsonl or candidates.jsonl.gz",
    )
    parser.add_argument(
        "--out",
        default="submission.csv",
        help="Output CSV path (default: submission.csv)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of candidates to output (default: 100)",
    )
    args = parser.parse_args()

    cand_path = Path(args.candidates)
    if not cand_path.exists():
        sys.exit(f"Error: '{cand_path}' not found. "
                 f"Download candidates.jsonl from the hackathon bundle first.")

    print(f"[ranker] Scoring {cand_path.name} for: Senior AI Engineer @ Redrob AI")
    print(f"[ranker] Weights: {_WEIGHTS}")

    results = rank_candidates(cand_path, top_n=args.top)
    write_csv(results, Path(args.out))
    print("[ranker] Done. Run validate_submission.py to check format before submitting.")


if __name__ == "__main__":
    main()
