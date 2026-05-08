from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True)   # Semantic Scholar paper ID
    arxiv_id = Column(String, index=True)
    title = Column(Text, nullable=False)
    authors_json = Column(Text)             # JSON array of author names
    year = Column(Integer, index=True)
    venue = Column(String)
    citation_count = Column(Integer, default=0, index=True)
    source_url = Column(Text)
    pdf_path = Column(Text)
    abstract = Column(Text)

    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete-orphan")
    model_facts = relationship("ModelFact", back_populates="paper", cascade="all, delete-orphan")
    dataset_uses = relationship("DatasetUse", back_populates="paper", cascade="all, delete-orphan")
    benchmark_results = relationship("BenchmarkResult", back_populates="paper", cascade="all, delete-orphan")
    method_claims = relationship("MethodClaim", back_populates="paper", cascade="all, delete-orphan")
    citations_made = relationship("CitationEdge", foreign_keys="CitationEdge.citer_id", back_populates="citer")
    citations_received = relationship("CitationEdge", foreign_keys="CitationEdge.cited_id", back_populates="cited")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)   # f"{paper_id}_{section}_{chunk_idx}"
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    section = Column(String)                # abstract, introduction, method, results, etc.
    chunk_type = Column(String, default="text")  # text | table | figure_caption
    text = Column(Text, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)
    chunk_idx = Column(Integer)

    paper = relationship("Paper", back_populates="chunks")


class ModelFact(Base):
    __tablename__ = "model_facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    model_name = Column(String)
    param_count_millions = Column(Float)    # null if not reported
    architecture_type = Column(String)      # transformer | cnn | hybrid | other
    training_dataset = Column(String)
    raw_text = Column(Text)
    chunk_id = Column(String, ForeignKey("chunks.id"))

    paper = relationship("Paper", back_populates="model_facts")


class DatasetUse(Base):
    __tablename__ = "dataset_uses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    dataset_name = Column(String, nullable=False, index=True)   # normalized via resolver
    use_type = Column(String)              # pretraining | training | finetuning | evaluation
    uses_augmentation = Column(Boolean)
    dataset_size_k_samples = Column(Float) # thousands of samples; enables T8 correlation
    raw_text = Column(Text)
    chunk_id = Column(String, ForeignKey("chunks.id"))

    paper = relationship("Paper", back_populates="dataset_uses")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    benchmark_name = Column(String, nullable=False, index=True)
    metric_name = Column(String)           # Top-1 Accuracy, mAP, mIoU, etc.
    value = Column(Float)                  # numeric result
    is_sota_claim = Column(Boolean, default=False)
    training_conditions = Column(Text)     # e.g. "pretrained ImageNet-21K, finetuned 1K" — for T3 conflict detection
    year = Column(Integer)                 # denormalized from paper for fast T4 queries
    raw_text = Column(Text)
    chunk_id = Column(String, ForeignKey("chunks.id"))

    paper = relationship("Paper", back_populates="benchmark_results")


class MethodClaim(Base):
    __tablename__ = "method_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    method_name = Column(String)
    claim_type = Column(String)            # novel | improvement | sota | ablation | negative
    description = Column(Text)
    raw_text = Column(Text)
    chunk_id = Column(String, ForeignKey("chunks.id"))

    paper = relationship("Paper", back_populates="method_claims")


class CitationEdge(Base):
    """Inner-corpus citation: citer_id cites cited_id. Only stored when both papers are in corpus."""
    __tablename__ = "citation_edges"
    __table_args__ = (UniqueConstraint("citer_id", "cited_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    citer_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    cited_id = Column(String, ForeignKey("papers.id"), nullable=False, index=True)
    context_text = Column(Text)            # sentence where citation appears

    citer = relationship("Paper", foreign_keys=[citer_id], back_populates="citations_made")
    cited = relationship("Paper", foreign_keys=[cited_id], back_populates="citations_received")


def create_all_tables(db_url: str) -> None:
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
