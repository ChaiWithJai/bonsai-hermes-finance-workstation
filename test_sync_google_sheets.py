import unittest
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import sync_google_sheets
from sync_google_sheets import SCHEMA, normalize_tab


class SheetImportTests(unittest.TestCase):
    def test_native_demo_sheet_layout_and_formatted_values(self):
        portfolio_header = SCHEMA["Portfolio"][1]
        report_header = SCHEMA["Analyst Reports"][1]
        portfolio = normalize_tab(
            [["FICTIONAL PORTFOLIO"], [], portfolio_header,
             ["FCT-HARBOR", "Harbor Infrastructure Notes", "defensive", "450", "$1,000", "2026-09-25", "FIC-REPORT-01"]],
            "Portfolio", portfolio_header)
        reports = normalize_tab(
            [["FICTIONAL ANALYST REPORTS"], [], report_header,
             ["FIC-REPORT-01", "FCT-HARBOR", "Fictional Credit Desk", "2026-09-25", "5.0%", "8.0%", "-9.0%", "medium", "thesis", "risk"]],
            "Analyst Reports", report_header)
        self.assertEqual(portfolio[0][3:5], ["450", "1000"])
        self.assertEqual(reports[0][4:7], ["5.0", "8.0", "-9.0"])

    def test_rejects_wrong_header_and_extra_data(self):
        expected = SCHEMA["Portfolio"][1]
        with self.assertRaisesRegex(ValueError, "header"):
            normalize_tab([["wrong"]], "Portfolio", expected)
        with self.assertRaisesRegex(ValueError, "beyond"):
            normalize_tab([expected, ["FCT-HARBOR", "", "", "450", "$1,000", "2026-09-25", "FIC-REPORT-01", "extra"]], "Portfolio", expected)

    def test_downloaded_native_values_make_valid_snapshot(self):
        portfolio = [SCHEMA["Portfolio"][1]]
        portfolio.extend([
            ["FCT-HARBOR", "Harbor Infrastructure Notes", "defensive", "450", "$1,000", "2026-09-25", "FIC-REPORT-01"],
            ["FCT-ORBIT", "Orbit Clinical Software Basket", "growth", "350", "$1,000", "2026-09-25", "FIC-REPORT-02"],
            ["FCT-RESERVE", "Reserve Treasury Proxy", "liquidity", "200", "$1,000", "2026-09-25", "FIC-REPORT-03"],
        ])
        reports = [SCHEMA["Analyst Reports"][1]]
        reports.extend([
            ["FIC-REPORT-01", "FCT-HARBOR", "Fictional Credit Desk", "2026-09-25", "5.0%", "8.0%", "-9.0%", "medium", "Contracted infrastructure revenue supports coupon coverage", "Refinancing costs could compress coverage"],
            ["FIC-REPORT-02", "FCT-ORBIT", "Fictional Software Desk", "2026-09-25", "14.0%", "27.0%", "-31.0%", "low", "Enterprise renewal growth could support expansion", "Concentration and implementation delays could reduce renewals"],
            ["FIC-REPORT-03", "FCT-RESERVE", "Fictional Treasury Desk", "2026-09-25", "3.0%", "3.5%", "2.0%", "high", "Short duration limits price sensitivity", "Reinvestment yield could fall"],
        ])
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"FINANCE_SPREADSHEET_ID": "fictional-sheet-id", "FINANCE_GOOGLE_TOKEN": "test-token", "FINANCE_DATA_DIR": tmp}):
                with patch.object(sync_google_sheets, "fetch_tab", side_effect=lambda _id, _token, tab: [["FICTIONAL SOURCE"], [], *(portfolio if tab == "Portfolio" else reports)]):
                    sync_google_sheets.main()
            with (Path(tmp) / "portfolio.csv").open() as stream:
                saved = list(csv.DictReader(stream))
            self.assertEqual(saved[0]["price_usd"], "1000")
            with (Path(tmp) / "analyst_reports.csv").open() as stream:
                saved_reports = list(csv.DictReader(stream))
            self.assertEqual(saved_reports[1]["downside_return_pct"], "-31.0")


if __name__ == "__main__":
    unittest.main()
