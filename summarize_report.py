"""Summarize long research reports into concise morning briefs with Anthropic."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_PROMPT_PATH = Path("prompts/morning_brief_prompt.md")


class AnthropicLikeClient(Protocol):
    class messages(Protocol):
        @staticmethod
        def create(**kwargs):
            ...


@dataclass(frozen=True)
class SummaryRequest:
    input_path: Path
    output_path: Path
    prompt_path: Path = DEFAULT_PROMPT_PATH
    model: str = DEFAULT_MODEL
    max_tokens: int = 3200
    report_date: str = ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a strategic report into a morning brief.")
    parser.add_argument("--input", required=True, type=Path, help="Input markdown report.")
    parser.add_argument("--output", required=True, type=Path, help="Output markdown brief.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_PATH, type=Path, help="Prompt template path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model name.")
    parser.add_argument("--max-tokens", default=3200, type=int)
    parser.add_argument("--report-date", default="", help="Report date shown in the brief.")
    return parser.parse_args(argv)


def summarize_report(request: SummaryRequest, client: AnthropicLikeClient | None = None) -> str:
    load_dotenv()
    report = request.input_path.read_text(encoding="utf-8")
    prompt = load_prompt(request.prompt_path, request.report_date or _infer_report_date(request.input_path))
    client = client or _build_anthropic_client()
    response = client.messages.create(
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=0.2,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "다음 리포트를 morning brief로 요약해줘.\n\n"
                    "<report>\n"
                    f"{report}\n"
                    "</report>"
                ),
            }
        ],
    )
    summary = _extract_text(response).strip()
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(summary + "\n", encoding="utf-8")
    return summary


def load_prompt(path: Path, report_date: str) -> str:
    template = path.read_text(encoding="utf-8")
    return template.replace("{report_date}", report_date)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    request = SummaryRequest(
        input_path=args.input,
        output_path=args.output,
        prompt_path=args.prompt,
        model=args.model,
        max_tokens=args.max_tokens,
        report_date=args.report_date,
    )
    summary = summarize_report(request)
    print(summary)
    return 0


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
    name = path.name
    candidate = name[:10]
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return date.today().isoformat()
    return candidate


if __name__ == "__main__":
    raise SystemExit(main())
