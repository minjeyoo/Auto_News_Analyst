"""
Git-backed AutoResearch controller for Auto-News-Analyst.

This file is the loop runner. The agent's editable arena is intentionally small:
`candidate_pipeline.py`, `prompts/candidate_prompt.md`, and `news_keywords.json`.
The evaluator and cached data stay outside the arena.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import json
import logging
from pathlib import Path
import subprocess
from typing import Protocol

try:
    from .eval_harness import assert_no_news_leakage, evaluate_predictions
    from .domain_types import EvaluationResult, NewsRecord, PipelineState, PricePoint
except ImportError:  # Allows running tests from this directory without package install.
    from eval_harness import assert_no_news_leakage, evaluate_predictions
    from domain_types import EvaluationResult, NewsRecord, PipelineState, PricePoint


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutoResearchConfig:
    repo_root: Path
    target_files: tuple[Path, ...] = (
        Path("candidate_pipeline.py"),
        Path("prompts/candidate_prompt.md"),
        Path("news_keywords.json"),
        Path("industry_themes.json"),
        Path("company_aliases.json"),
    )
    immutable_paths: tuple[Path, ...] = (
        Path("eval_harness.py"),
        Path("news_cache.py"),
        Path("news_fetchers"),
        Path("prepare_data.py"),
        Path("price_provider.py"),
        Path("tests"),
        Path("cached_news"),
        Path("cached_prices"),
    )
    knowledge_files: tuple[Path, ...] = (Path("COMBAT_LOG.md"), Path("RESEARCH_LOG.md"))
    metric_name: str = "composite_score"
    metric_direction: str = "higher"
    min_metric_delta: float = 0.0001
    backcast_days: int = 30
    forecast_days: int = 7
    min_score_to_trade: float = 0.15
    flat_return_threshold: float = 0.005
    transaction_cost: float = 0.001
    min_evaluated_count: int = 20


@dataclass(frozen=True)
class ExperimentRecord:
    run_id: str
    status: str
    metric: float
    previous_best: float
    commit_sha: str = ""
    notes: str = ""
    errors: list[str] = field(default_factory=list)


class NewsFetcher(Protocol):
    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        """Fetch only news published inside [start, end]."""


class PriceProvider(Protocol):
    def get_close_points(self, tickers: list[str], start: date, end: date) -> dict[str, list[PricePoint]]:
        """Return adjusted close points for the evaluation window."""


class CandidatePipeline(Protocol):
    def analyze(self, news: list[NewsRecord], as_of_date: date, prompt: str) -> list:
        """Produce ticker-level predictions from supplied historical news only."""


class GitExperimentStore:
    def __init__(self, repo_root: Path, history_path: Path | None = None) -> None:
        self.repo_root = repo_root
        self.history_path = history_path or repo_root / ".autoresearch" / "experiments.jsonl"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def is_git_repo(self) -> bool:
        result = self._git("rev-parse", "--is-inside-work-tree", check=False)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def head_sha(self) -> str:
        return self._git("rev-parse", "--short", "HEAD").stdout.strip()

    def changed_files(self) -> set[Path]:
        result = self._git("diff", "--name-only")
        return {Path(line.strip()) for line in result.stdout.splitlines() if line.strip()}

    def validate_mutation_scope(self, config: AutoResearchConfig) -> None:
        changed = self.changed_files()
        immutable_hits = [
            path for path in changed if any(_is_relative_to(path, immutable) for immutable in config.immutable_paths)
        ]
        if immutable_hits:
            joined = ", ".join(str(path) for path in immutable_hits)
            raise ValueError(f"immutable files changed: {joined}")

        allowed = config.target_files + config.knowledge_files
        illegal = [path for path in changed if not any(_is_relative_to(path, prefix) for prefix in allowed)]
        if illegal:
            joined = ", ".join(str(path) for path in illegal)
            raise ValueError(f"files outside autoresearch arena changed: {joined}")

    def commit_success(self, record: ExperimentRecord, config: AutoResearchConfig) -> str:
        paths = [str(path) for path in config.target_files + config.knowledge_files]
        self._git("add", *paths)
        self._git("commit", "-m", f"research: keep {record.run_id} {config.metric_name}={record.metric:.6f}")
        return self.head_sha()

    def commit_knowledge(self, record: ExperimentRecord, config: AutoResearchConfig) -> str:
        paths = [str(path) for path in config.knowledge_files]
        self._git("add", *paths)
        self._git("commit", "-m", f"research: record failed experiment {record.run_id}")
        return self.head_sha()

    def revert_candidate_changes(self, config: AutoResearchConfig) -> None:
        paths = [str(path) for path in config.target_files]
        if paths:
            self._git("checkout", "--", *paths)

    def append_history(self, record: ExperimentRecord) -> None:
        row = {
            "run_id": record.run_id,
            "status": record.status,
            "metric": record.metric,
            "previous_best": record.previous_best,
            "commit_sha": record.commit_sha,
            "notes": record.notes,
            "errors": record.errors,
        }
        with self.history_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result


class AutoNewsAnalystController:
    def __init__(
        self,
        config: AutoResearchConfig,
        store: GitExperimentStore,
        news_fetcher: NewsFetcher,
        price_provider: PriceProvider,
        tickers: list[str],
    ) -> None:
        self.config = config
        self.store = store
        self.news_fetcher = news_fetcher
        self.price_provider = price_provider
        self.tickers = tickers

    def evaluate_candidate(
        self,
        pipeline: CandidatePipeline,
        *,
        run_id: str,
        today: date,
        prompt: str,
        keywords: list[str],
    ) -> EvaluationResult:
        forecast_start = today - timedelta(days=self.config.forecast_days)
        news_start = today - timedelta(days=self.config.backcast_days)
        news = self.news_fetcher.fetch(self.tickers, news_start, forecast_start, keywords)
        assert_no_news_leakage(news, forecast_start)
        predictions = pipeline.analyze(news, as_of_date=forecast_start, prompt=prompt)
        prices = self.price_provider.get_close_points(self.tickers, forecast_start, today)
        return evaluate_predictions(
            predictions=predictions,
            prices_by_ticker=prices,
            run_id=run_id,
            forecast_start=forecast_start,
            forecast_end=today,
            min_score_to_trade=self.config.min_score_to_trade,
            flat_return_threshold=self.config.flat_return_threshold,
            transaction_cost=self.config.transaction_cost,
            min_evaluated_count=self.config.min_evaluated_count,
        )

    def keep_or_discard(
        self,
        *,
        state: PipelineState,
        result: EvaluationResult,
        best_metric: float,
    ) -> PipelineState:
        self.store.validate_mutation_scope(self.config)
        improved = result.passed and result.composite_score > best_metric + self.config.min_metric_delta
        record = ExperimentRecord(
            run_id=result.run_id,
            status="kept" if improved else "discarded",
            metric=result.composite_score,
            previous_best=best_metric,
            errors=result.errors,
        )

        if improved:
            commit_sha = self.store.commit_success(record, self.config)
            kept = PipelineState(
                version=result.run_id,
                target_path=state.target_path,
                prompt_path=state.prompt_path,
                metric=result.composite_score,
                commit_sha=commit_sha,
            )
            self.store.append_history(record)
            return kept

        self.store.revert_candidate_changes(self.config)
        self.store.append_history(record)
        return state


def _is_relative_to(path: Path, prefix: Path) -> bool:
    return path == prefix or prefix in path.parents
