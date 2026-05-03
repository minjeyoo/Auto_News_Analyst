"""Generate a multi-axis strategic industry analysis with Anthropic."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PROMPT_PATH = Path("prompts/strategic_analysis_prompt.md")


class AnthropicLikeClient(Protocol):
    class messages(Protocol):
        @staticmethod
        def create(**kwargs):
            ...


@dataclass(frozen=True)
class StrategicAnalysisRequest:
    output_path: Path
    report_date: str
    local_report_path: Path = Path("reports/2026-05-03_daily_local_news_report.md")
    global_report_path: Path = Path("reports/2026-05-03_global_equity_theme_map.md")
    derived_keywords_path: Path = Path("derived_keywords.json")
    industry_themes_path: Path = Path("industry_themes.json")
    company_aliases_path: Path = Path("company_aliases.json")
    prompt_path: Path = DEFAULT_PROMPT_PATH
    model: str = DEFAULT_MODEL
    max_tokens: int = 6000


def generate_strategic_analysis(
    request: StrategicAnalysisRequest,
    client: AnthropicLikeClient | None = None,
) -> str:
    load_dotenv()
    prompt = _load_prompt(request.prompt_path, request.report_date)
    evidence_pack = _build_evidence_pack(request)
    client = client or _build_anthropic_client()
    response = client.messages.create(
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=0.25,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "아래 증거 패키지를 바탕으로 전략적 글로벌 산업 분석 리포트를 작성하세요.\n\n"
                    f"{evidence_pack}"
                ),
            }
        ],
    )
    analysis = _extract_text(response).strip()
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(analysis + "\n", encoding="utf-8")
    return analysis


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a strategic multi-axis industry analysis.")
    parser.add_argument("--local-report", type=Path, required=True)
    parser.add_argument("--global-report", type=Path, required=True)
    parser.add_argument("--derived-keywords", type=Path, default=Path("derived_keywords.json"))
    parser.add_argument("--industry-themes", type=Path, default=Path("industry_themes.json"))
    parser.add_argument("--company-aliases", type=Path, default=Path("company_aliases.json"))
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-date", default="")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=6000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_date = args.report_date or _infer_report_date(args.output)
    analysis = generate_strategic_analysis(
        StrategicAnalysisRequest(
            local_report_path=args.local_report,
            global_report_path=args.global_report,
            derived_keywords_path=args.derived_keywords,
            industry_themes_path=args.industry_themes,
            company_aliases_path=args.company_aliases,
            prompt_path=args.prompt,
            output_path=args.output,
            report_date=report_date,
            model=args.model,
            max_tokens=args.max_tokens,
        )
    )
    print(analysis)
    return 0


def _build_evidence_pack(request: StrategicAnalysisRequest) -> str:
    sections = [
        ("국내 뉴스 플로우", _read_text(request.local_report_path)),
        ("글로벌 산업/주식 맵", _read_text(request.global_report_path)),
        ("파생 검색 키워드", _read_text(request.derived_keywords_path)),
        ("산업 테마 유니버스", _read_text(request.industry_themes_path)),
        ("회사/사업부 alias 유니버스", _read_text(request.company_aliases_path)),
    ]
    return "\n\n".join(f"<{title}>\n{content}\n</{title}>" for title, content in sections)


def _read_text(path: Path) -> str:
    if not path.exists():
        return "(파일 없음)"
    return path.read_text(encoding="utf-8")


def _load_prompt(path: Path, report_date: str) -> str:
    return path.read_text(encoding="utf-8").replace("{report_date}", report_date)


def _build_anthropic_client():
    import anthropic

    return anthropic.Anthropic()


def _extract_text(response) -> str:
    parts = []
    for block in getattr(response, "content", []):
        text = getattr(block, "text", "")
        if text:
            parts.append(text)
    return "\n".join(parts)


def _infer_report_date(path: Path) -> str:
    candidate = path.name[:10]
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return date.today().isoformat()
    return candidate


if __name__ == "__main__":
    raise SystemExit(main())
