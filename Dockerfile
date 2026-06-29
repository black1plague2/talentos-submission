FROM python:3.11-slim
WORKDIR /app

# No heavy dependencies — rank.py uses only stdlib
COPY requirements.txt .
RUN pip install --no-cache-dir flask>=3.0.0

COPY . .

# Stage 3 reproduction command:
#   docker run --rm -v /path/to/candidates.jsonl:/data/candidates.jsonl \
#     talentos-submission \
#     python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv
CMD ["python", "rank.py", "--help"]
