import importlib.util
import os
import sys
import unittest

import config as app_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

_SPEC = importlib.util.spec_from_file_location(
    "chatbot_tester",
    os.path.join(BASE_DIR, "chatbot_tester.py"),
)
ct = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ct)


class PromptCsvTests(unittest.TestCase):
    def test_load_prompts_from_csv(self):
        data = ct.load_prompts_from_csv(ct.PROMPTS_CSV)
        self.assertIsNotNone(data)
        rows, prompt_col, status_col, link_col, time_col, entries, header_row_idx, hi_col = data
        self.assertGreater(len(entries), 0)
        self.assertIsNotNone(prompt_col)
        self.assertIsNotNone(hi_col)
        self.assertEqual(ct._prompt_entry_prompt(entries[0]), "Show me ria in usa")

    def test_smoke_filter(self):
        data = ct.load_prompts_from_csv(ct.PROMPTS_CSV)
        entries = data[5]
        smoke = ct._filter_prompt_entries_for_smoke(entries, True)
        self.assertEqual(len(smoke), 3)
        for entry in smoke:
            self.assertEqual(ct._prompt_entry_marker(entry), "smoke")

    def test_run_mode_all(self):
        data = ct.load_prompts_from_csv(ct.PROMPTS_CSV)
        entries = data[5]
        all_entries = ct._filter_prompt_entries_for_run_mode(entries, "all")
        self.assertGreater(len(all_entries), len(
            ct._filter_prompt_entries_for_run_mode(entries, "smoke")
        ))

    def test_run_mode_test_prompts_file(self):
        test_csv = ct.project_path("Prompts.test.csv")
        data = ct.load_prompts_from_csv(test_csv)
        self.assertIsNotNone(data)
        entries = ct._filter_prompt_entries_for_run_mode(data[5], "all")
        self.assertEqual(len(entries), 1)
        self.assertEqual(ct._prompt_entry_prompt(entries[0]), "Show me ria in usa")

    def test_run_mode_test_on_marketplace_uses_test_csv(self):
        profile = ct.resolve_market_profile("marketplace")
        exec_cfg = app_config.resolve_prompt_execution(profile, "test")
        self.assertEqual(exec_cfg["prompts_file"], "Prompts.test.csv")
        self.assertEqual(exec_cfg["run_mode"], "all")
        self.assertEqual(exec_cfg["runs_per_object"], 1)

    def test_expand_prompt_runs(self):
        prompts = ["p1", "p2"]
        rows = [1, 2]
        types = ["Accounts", "Contacts"]
        exp_prompts, exp_rows, exp_types, samples = ct._expand_prompt_runs(
            prompts, rows, types
        )
        self.assertEqual(len(exp_prompts), ct.RUNS_PER_OBJECT * len(prompts))
        self.assertEqual(samples[:3], [1, 2, 3])
        self.assertEqual(exp_types[:3], ["Accounts"] * 3)


class BenchmarkKeyTests(unittest.TestCase):
    def test_normalize_object_key(self):
        self.assertEqual(ct._normalize_object_key("  Alumni  "), "alumni")

    def test_load_benchmarks_from_csv(self):
        benchmarks = ct._load_benchmarks_from_csv()
        self.assertIn("accounts", benchmarks)
        self.assertEqual(benchmarks["accounts"], 60.0)

    def test_load_all_benchmarks_includes_csv(self):
        merged = ct._load_all_benchmarks()
        self.assertIn("contacts", merged)
        self.assertGreaterEqual(len(merged), 2)


class MarketProfileTests(unittest.TestCase):
    def test_test_market_profile(self):
        profile = ct.resolve_market_profile("test")
        self.assertEqual(profile["key"], "test")
        self.assertEqual(profile["prompts_file"], "Prompts.test.csv")
        self.assertEqual(profile.get("runs_per_object"), 1)

    def test_marketplace_profile(self):
        profile = ct.resolve_market_profile("marketplace")
        self.assertEqual(profile["key"], "marketplace")
        self.assertIn("dakotaMarketplace", profile["base_url"])

    def test_custom_profile_requires_url(self):
        old = os.environ.pop("DAKOTA_BASE_URL", None)
        try:
            with self.assertRaises(ValueError):
                ct.resolve_market_profile("custom")
        finally:
            if old is not None:
                os.environ["DAKOTA_BASE_URL"] = old

    def test_custom_profile_with_override(self):
        profile = ct.resolve_market_profile(
            "custom", "https://example.test/community/s/"
        )
        self.assertEqual(profile["key"], "custom")
        self.assertTrue(profile["base_url"].startswith("https://example.test"))


if __name__ == "__main__":
    unittest.main()
