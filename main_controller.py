"""
Backward-compatible imports for the first Auto-News-Analyst prototype.

The project has been refactored into:
- `controller.py` for the git-backed keep/discard loop
- `eval_harness.py` for immutable backtest scoring
- `domain_types.py` for shared data objects
"""

try:
    from .controller import (  # noqa: F401
        AutoNewsAnalystController,
        AutoResearchConfig,
        ExperimentRecord,
        GitExperimentStore,
    )
    from .domain_types import (  # noqa: F401
        Direction,
        EvaluationResult,
        InsightPrediction,
        NewsRecord,
        PipelineState,
        PredictionEvaluation,
        PricePoint,
    )
    from .eval_harness import assert_no_news_leakage, evaluate_predictions  # noqa: F401
except ImportError:
    from controller import (  # noqa: F401
        AutoNewsAnalystController,
        AutoResearchConfig,
        ExperimentRecord,
        GitExperimentStore,
    )
    from domain_types import (  # noqa: F401
        Direction,
        EvaluationResult,
        InsightPrediction,
        NewsRecord,
        PipelineState,
        PredictionEvaluation,
        PricePoint,
    )
    from eval_harness import assert_no_news_leakage, evaluate_predictions  # noqa: F401
