import importlib.util
import os
import sys
import unittest

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


class MarketProfileTests(unittest.TestCase):
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
