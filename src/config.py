from pathlib import Path
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class BudgetMode(str, Enum):
    LOW = "low"       # ~$1 for 40 questions: BM25 only + Haiku
    MEDIUM = "medium" # ~$5 for 40 questions: BM25 + semantic + mixed models
    HIGH = "high"     # ~$20 for 40 questions: full pipeline + Sonnet for complex tiers


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    semantic_scholar_api_key: str = ""

    data_dir: Path = Path("./data")
    corpus_dir: Path = Path("./corpus")
    budget_mode: BudgetMode = BudgetMode.MEDIUM

    # Derived paths
    @property
    def db_path(self) -> Path:
        return self.data_dir / "db" / "knowledge.db"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "embeddings" / "chroma"

    @property
    def bm25_path(self) -> Path:
        return self.data_dir / "bm25" / "index.pkl"

    @property
    def pdfs_dir(self) -> Path:
        return self.corpus_dir / "pdfs"

    @property
    def manifest_path(self) -> Path:
        return self.corpus_dir / "manifest.csv"


settings = Settings()
