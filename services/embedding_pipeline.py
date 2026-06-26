"""Sentence-transformer embedding + FAISS index builder (from garv branch)."""
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype="float32")
    vecs = get_model().encode(texts, convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(vecs)
    return vecs


def build_index(vecs: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    return index


def is_model_loaded() -> bool:
    return _model is not None
