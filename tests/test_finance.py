import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from finance_workstation import tools as finance


class FinanceDemoTests(unittest.TestCase):
    def test_weights_and_scenarios(self):
        result = finance.execute("read_portfolio", {})
        self.assertEqual(result["portfolio_value_usd"], 1_000_000)
        self.assertEqual(sum(row["weight_pct"] for row in result["holdings"]), 100)
        self.assertEqual(result["scenario_returns_pct"], {"base": 7.75, "upside": 13.75, "downside": -14.5})
        self.assertEqual(result["integration"], "local_csv_fixture")

    def test_candidate_is_feasible_and_scored(self):
        result = finance.execute("compare_scenarios", {})
        candidate = result["candidate"]
        self.assertEqual(candidate["weights_pct"], {
            "FCT-HARBOR": 35, "FCT-ORBIT": 45, "FCT-RESERVE": 20})
        self.assertEqual(sum(candidate["weights_pct"].values()), 100)
        self.assertLessEqual(candidate["one_way_turnover_pct"], 15)
        self.assertGreaterEqual(candidate["scenario_returns_pct"]["downside"], -18)
        self.assertEqual(result["feasible_grid_candidates"], 20)

    def test_draft_requires_fresh_snapshot_and_does_not_change_holdings(self):
        before = finance.execute("read_portfolio", {})
        with tempfile.TemporaryDirectory() as temp:
            old_out = finance.OUT
            finance.OUT = Path(temp)
            try:
                with self.assertRaisesRegex(ValueError, "snapshot changed"):
                    finance.execute("write_review_draft", {"expected_snapshot_sha256": "stale", "reviewer": "A reviewer"})
                result = finance.execute("write_review_draft", {
                    "expected_snapshot_sha256": before["snapshot_sha256"], "reviewer": "A reviewer"})
                saved = json.loads(Path(result["path"]).read_text())
                self.assertEqual(saved["status"], "pending_human_review")
                self.assertFalse(saved["order_submitted"])
                self.assertEqual(finance.execute("read_portfolio", {})["holdings"], before["holdings"])
            finally:
                finance.OUT = old_out

    def test_report_source_ids_are_exact(self):
        reports = finance.execute("read_analyst_reports", {})["reports"]
        self.assertEqual({r["report_id"] for r in reports},
                         {r["source_ref"] for r in finance.execute("read_portfolio", {})["holdings"]})
        with self.assertRaisesRegex(ValueError, "Unknown asset_id"):
            finance.execute("read_analyst_reports", {"asset_id": "AAPL"})


if __name__ == "__main__":
    unittest.main()
