from pathlib import Path
import unittest

from controller import AutoResearchConfig, GitExperimentStore


class FakeGitStore(GitExperimentStore):
    def __init__(self, changed):
        self._changed = {Path(item) for item in changed}

    def changed_files(self):
        return self._changed


class MutationScopeTest(unittest.TestCase):
    def test_allows_only_candidate_prompt_keywords_and_logs(self):
        config = AutoResearchConfig(repo_root=Path("."))
        store = FakeGitStore(
            [
                "candidate_pipeline.py",
                "prompts/candidate_prompt.md",
                "news_keywords.json",
                "COMBAT_LOG.md",
            ]
        )

        store.validate_mutation_scope(config)

    def test_rejects_immutable_evaluation_changes(self):
        config = AutoResearchConfig(repo_root=Path("."))
        store = FakeGitStore(["eval_harness.py"])

        with self.assertRaisesRegex(ValueError, "immutable files changed"):
            store.validate_mutation_scope(config)

    def test_rejects_files_outside_autoresearch_arena(self):
        config = AutoResearchConfig(repo_root=Path("."))
        store = FakeGitStore(["random_helper.py"])

        with self.assertRaisesRegex(ValueError, "outside autoresearch arena"):
            store.validate_mutation_scope(config)


if __name__ == "__main__":
    unittest.main()
