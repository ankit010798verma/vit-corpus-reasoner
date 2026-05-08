from pydantic import BaseModel
from src.config import BudgetMode


class QueryRequest(BaseModel):
    question: str
    budget_mode: BudgetMode = BudgetMode.MEDIUM


class Citation(BaseModel):
    paper_id: str
    title: str
    year: int | str | None = None
    section: str = ""
    quote: str = ""


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tier: int
    cost_usd: float
    reasoning_trace: str = ""


class EvalRequest(BaseModel):
    budget_mode: BudgetMode = BudgetMode.MEDIUM


class CostReport(BaseModel):
    total_usd: float
    by_model: dict[str, float]
    by_tier: dict[str, float]
    per_question: dict
    call_count: int
