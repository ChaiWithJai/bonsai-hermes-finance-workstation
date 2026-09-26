import unittest

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


if __name__ == "__main__":
    unittest.main()
