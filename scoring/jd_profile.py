"""
Hardcoded JD profile for the Redrob hackathon target role:
Senior AI Engineer — Founding Team, Redrob AI (Pune/Noida, Hybrid).
"""

# Core required skills from the JD — any substring match in skill name (lowercase)
REQUIRED_SKILL_KEYWORDS: list[str] = [
    # Embeddings & semantic search
    "embedding", "sentence-transformer", "sentence transformer", "bge", "e5",
    "text-embedding", "all-minilm", "semantic search", "semantic similarity",
    "dense retrieval", "bi-encoder", "cohere embed",
    # Vector databases / ANN
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
    "elasticsearch", "vector database", "vector db", "vector store",
    "vector search", "ann", "hnsw", "approximate nearest neighbor",
    # Retrieval & hybrid search
    "retrieval", "information retrieval", "bm25", "hybrid search",
    "sparse retrieval", "neural retrieval", "rag",
    "retrieval augmented", "reranking", "reranker", "cross-encoder",
    "two-tower",
    # Ranking & evaluation
    "learning to rank", "learning-to-rank", "ltr", "ndcg", "mrr",
    "search ranking", "ranking system", "recommendation", "recommender",
    "a/b testing", "ab testing", "offline evaluation",
    # LLMs & NLP
    "llm", "large language model", "fine-tuning", "fine tuning",
    "finetuning", "lora", "qlora", "peft", "transformers", "huggingface",
    "hugging face", "bert", "gpt", "nlp", "natural language processing",
    "text generation", "language model",
    # Core language
    "python",
]

# Nice-to-have skills (bonus, not required)
NICE_TO_HAVE_KEYWORDS: list[str] = [
    "lightgbm", "xgboost", "gradient boosting", "catboost",
    "distributed systems", "spark", "kafka", "ray",
    "mlflow", "kubeflow", "triton", "onnx", "torchserve",
    "open source", "open-source", "arxiv", "research paper",
    "pytorch", "tensorflow", "cuda",
]

# Consulting/services firms — entire career there = heavy penalty
CONSULTING_FIRMS: set[str] = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl technologies", "tech mahindra",
    "mphasis", "hexaware", "l&t infotech", "ltimindtree",
    "mindtree", "birlasoft", "coforge", "niit technologies",
    "sasken", "mastech", "igate", "patni", "syntel",
}

# Title patterns that indicate an AI/ML role
AI_TITLE_KEYWORDS: list[str] = [
    "ml engineer", "machine learning", "ai engineer", "nlp",
    "data scientist", "search engineer", "recommendation",
    "applied scientist", "research engineer", "applied ml",
    "senior ai", "staff ml", "lead ai", "applied researcher",
    "information retrieval", "ranking engineer", "deep learning",
    "computer vision",  # CV is ok if also NLP
    "llm", "language model", "generative ai",
]

# Titles that are clear non-fits (marketing, admin, etc.)
NON_FIT_TITLE_KEYWORDS: list[str] = [
    "marketing", "sales", "accountant", "hr ", "human resource",
    "graphic design", "civil engineer", "mechanical engineer",
    "operations manager", "content writer",
    "customer support", "business analyst",
]

# Titles that are PURE CV/speech/robotics without NLP — disqualifier per JD
PURE_CV_SPEECH_KEYWORDS: list[str] = [
    "computer vision engineer", "vision engineer",
    "speech recognition", "speech engineer",
    "robotics engineer", "autonomous driving",
    "image recognition engineer",
]

# Preferred India locations (city keywords in location string)
INDIA_CITY_KEYWORDS: set[str] = {
    "pune", "noida", "hyderabad", "mumbai", "bangalore", "bengaluru",
    "delhi", "gurugram", "gurgaon", "ncr", "delhi ncr",
    "chennai", "kolkata", "ahmedabad", "india",
}

# Career description keywords that signal production AI/ML deployment
PRODUCTION_KEYWORDS: set[str] = {
    "production", "deployed", "ship", "shipped", "users", "scale", "product",
    "real-world", "million", "billion", "customer", "latency",
    "serving", "inference", "search", "ranking", "recommendation",
    "retrieval", "embedding", "rag", "fine-tun", "a/b test",
    "eval", "metric", "ndcg", "precision", "recall",
}
