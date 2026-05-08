"""FastAPI application with lifespan startup to load all indexes."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import settings
from src.knowledge.store import init_db
from src.knowledge.indexer import load_indexes

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db(settings.db_path)
    try:
        load_indexes()
        print("All indexes loaded.")
    except Exception as e:
        print(f"Warning: could not load indexes ({e}). Run scripts/03_build_index.py first.")
    yield
    # Shutdown — nothing to clean up


app = FastAPI(
    title="VIT Corpus Reasoner",
    description="Research comprehension system for top-100 Vision Transformer papers. Answers all 8 question tiers with cited, defensible answers.",
    version="0.1.0",
    lifespan=lifespan,
)

from src.api.routes import router
app.include_router(router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")
