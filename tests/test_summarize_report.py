from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from summarize_report import SummaryRequest, load_prompt, parse_args, summarize_report


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
        return FakeResponse("# Morning Market Brief - 2026-05-03\n\n요약")


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


class SummarizeReportTest(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(["--input", "a.md", "--output", "b.md", "--model", "test-model"])

        self.assertEqual(args.input, Path("a.md"))
        self.assertEqual(args.output, Path("b.md"))
        self.assertEqual(args.model, "test-model")

    def test_load_prompt_replaces_report_date(self):
        with TemporaryDirectory() as tmp:
            prompt = Path(tmp) / "prompt.md"
            prompt.write_text("Date {report_date}", encoding="utf-8")

            self.assertEqual(load_prompt(prompt, "2026-05-03"), "Date 2026-05-03")

    def test_summarize_report_writes_output_and_calls_client(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "2026-05-03_report.md"
            output_path = root / "brief.md"
            prompt_path = root / "prompt.md"
            input_path.write_text("Long report", encoding="utf-8")
            prompt_path.write_text("Prompt {report_date}", encoding="utf-8")
            client = FakeClient()

            summary = summarize_report(
                SummaryRequest(
                    input_path=input_path,
                    output_path=output_path,
                    prompt_path=prompt_path,
                    model="fake-model",
                ),
                client=client,
            )

            self.assertIn("Morning Market Brief", summary)
            self.assertEqual(output_path.read_text(encoding="utf-8"), summary + "\n")
            call = client.messages.calls[0]
            self.assertEqual(call["model"], "fake-model")
            self.assertIn("2026-05-03", call["system"])
            self.assertIn("Long report", call["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()

