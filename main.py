from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.embedding_pipeline import get_model
from ml.ranker import _load_or_train
from routers import ranking, jobs, candidates


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Loading embedding model...")
    get_model()
    print("[startup] Initializing ML ranker...")
    _load_or_train()
    print("[startup] Ready.")
    yield


app = FastAPI(
    title="TalentOS — Unified AI Recruitment Engine",
    description=(
        "Integrates semantic matching (garv), verification scoring (poojit), "
        "gap analysis + decision intelligence (noel), and job/candidate parsing (harshith) "
        "into a single LightGBM-powered ranking pipeline."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ranking.router)
app.include_router(jobs.router)
app.include_router(candidates.router)


@app.get("/health", tags=["System"])
def health():
    from services.embedding_pipeline import is_model_loaded
    return {"status": "healthy", "embedding_model_loaded": is_model_loaded()}


if __name__ == "__main__":
    import uvicorn
    from config import PORT
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
