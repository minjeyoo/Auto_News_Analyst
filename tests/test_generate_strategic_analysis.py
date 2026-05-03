from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from generate_strategic_analysis import StrategicAnalysisRequest, generate_strategic_analysis, parse_args


class FakeBlock:
    def __init__(self, text):
        self.text = text


class FakeResponse:
    def __init__(self, text):
        self.content = [FakeBlock(text)]


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse("# 전략적 글로벌 산업 분석 - 2026-05-03\n\n## 1. 오늘의 핵심 결론\n분석")


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


class GenerateStrategicAnalysisTest(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(["--local-report", "local.md", "--global-report", "global.md", "--output", "out.md"])

        self.assertEqual(args.local_report, Path("local.md"))
        self.assertEqual(args.global_report, Path("global.md"))
        self.assertEqual(args.output, Path("out.md"))

    def test_generate_strategic_analysis_writes_output_and_sends_evidence_pack(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "local.md"
            global_report = root / "global.md"
            keywords = root / "keywords.json"
            themes = root / "themes.json"
            aliases = root / "aliases.json"
            prompt = root / "prompt.md"
            output = root / "out.md"
            local.write_text("국내 뉴스", encoding="utf-8")
            global_report.write_text("글로벌 맵", encoding="utf-8")
            keywords.write_text('{"global":["HBM"]}', encoding="utf-8")
            themes.write_text("{}", encoding="utf-8")
            aliases.write_text("{}", encoding="utf-8")
            prompt.write_text("날짜 {report_date}", encoding="utf-8")
            client = FakeClient()

            analysis = generate_strategic_analysis(
                StrategicAnalysisRequest(
                    local_report_path=local,
                    global_report_path=global_report,
                    derived_keywords_path=keywords,
                    industry_themes_path=themes,
                    company_aliases_path=aliases,
                    prompt_path=prompt,
                    output_path=output,
                    report_date="2026-05-03",
                    model="fake-model",
                ),
                client=client,
            )

            self.assertIn("전략적 글로벌 산업 분석", analysis)
            self.assertEqual(output.read_text(encoding="utf-8"), analysis + "\n")
            call = client.messages.calls[0]
            self.assertEqual(call["model"], "fake-model")
            self.assertIn("국내 뉴스", call["messages"][0]["content"])
            self.assertIn("글로벌 맵", call["messages"][0]["content"])
            self.assertIn("2026-05-03", call["system"])


if __name__ == "__main__":
    unittest.main()
