"""Shared immutable data types for Auto-News-Analyst."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path


class Direction(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class NewsRecord:
    ticker: str
    title: str
    body: str
    published_at: datetime
    source: str
    url: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InsightPrediction:
    ticker: str
    as_of_date: date
    score: float
    confidence: float
    thesis: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PricePoint:
    ticker: str
    trading_date: date
    close: float


@dataclass(frozen=True)
class PredictionEvaluation:
    ticker: str
    predicted_direction: Direction
    actual_direction: Direction
    score: float
    confidence: float
    start_price: float
    end_price: float
    realized_return: float
    strategy_return: float
    hit: bool
    skipped_reason: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    run_id: str
    evaluated_count: int
    skipped_count: int
    hit_rate: float
    virtual_return: float
    benchmark_return: float
    alpha_return: float
    coverage_score: float
    direction_imbalance: float
    composite_score: float
    long_count: int
    short_count: int
    neutral_count: int
    min_evaluated_count: int
    details: list[PredictionEvaluation]
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors and self.evaluated_count >= self.min_evaluated_count


@dataclass(frozen=True)
class PipelineState:
    version: str
    target_path: Path
    prompt_path: Path
    metric: float = 0.0
    commit_sha: str = ""

