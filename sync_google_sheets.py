"""Download two explicitly named Google Sheets tabs into an atomic local snapshot.

Credentials are supplied through environment variables and are never persisted.
The tool does not write to Google Sheets.
"""
import csv
import io
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA = {
    "Portfolio": ("portfolio.csv", ["asset_id", "asset_name", "sleeve", "units", "price_usd", "as_of", "source_ref"]),
    "Analyst Reports": ("analyst_reports.csv", ["report_id", "asset_id", "analyst", "as_of", "base_return_pct", "upside_return_pct", "downside_return_pct", "confidence", "thesis", "risk"]),
}


def fetch_tab(spreadsheet_id, token, tab):
    span = urllib.parse.quote(f"'{tab}'!A1:Z1000", safe="")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{urllib.parse.quote(spreadsheet_id, safe='')}/values/{span}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["values"]


def main():
    spreadsheet_id = os.environ.get("FINANCE_SPREADSHEET_ID")
    token = os.environ.get("FINANCE_GOOGLE_TOKEN")
    if not spreadsheet_id or not token:
        raise SystemExit("Set FINANCE_SPREADSHEET_ID and FINANCE_GOOGLE_TOKEN to read the two Google Sheets tabs.")
    downloaded = {}
    for tab, (filename, expected) in SCHEMA.items():
        values = fetch_tab(spreadsheet_id, token, tab)
        if not values or values[0][:len(expected)] != expected:
            raise ValueError(f"{tab} header differs from the expected schema")
        rows = [row + [""] * (len(expected) - len(row)) for row in values[1:] if any(cell.strip() for cell in row)]
        if not rows or any(len(row) != len(expected) for row in rows):
            raise ValueError(f"{tab} contains no rows or has extra columns")
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(expected)
        writer.writerows(rows)
        downloaded[filename] = stream.getvalue()
    target = Path(os.environ.get("FINANCE_DATA_DIR", ROOT / "sheets_snapshot"))
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target) as temp:
        stage = Path(temp)
        for filename, body in downloaded.items():
            (stage / filename).write_text(body)
        (stage / "mandate.json").write_bytes((ROOT / "data" / "mandate.json").read_bytes())
        import subprocess
        result = subprocess.run(["python3", "-c", "import finance; finance.snapshot()"],
                                cwd=ROOT, env={**os.environ, "FINANCE_DATA_DIR": str(stage)},
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError(f"Downloaded workbook failed validation: {result.stderr.strip()}")
        for filename in ["portfolio.csv", "analyst_reports.csv", "mandate.json"]:
            (stage / filename).replace(target / filename)
    (target / "source.json").write_text(json.dumps({"integration": "google_sheets_download",
                                               "spreadsheet_id": spreadsheet_id,
                                               "synced_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
    print(f"Downloaded validated tabs to {target}. Set FINANCE_DATA_DIR={target} for Hermes.")


if __name__ == "__main__":
    main()
