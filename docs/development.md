# Development

| Location | What to change |
| --- | --- |
| `src/finance_workstation/tools.py` | Scenario arithmetic, constraints and draft persistence. |
| `src/finance_workstation/sample_data/` | Holdings, analyst assumptions and the mandate. |
| `src/finance_workstation/sheets.py` | Import of a Google Sheets snapshot. |
| `config/` | Hermes instructions, tool access and Slack manifest. |
| `scripts/` | Model startup, profile setup and result export. |
| `tests/` | Calculation, source and persistence checks. |
| `docs/`, `evidence/` | Architecture, setup, captured sessions and screenshots. |

Run `python -m unittest discover -s tests -v` after changing the calculation or a tool. The [connected verification](../docs/google-verification.md) shows the Sheet import and saved Slack draft; the [performance record](../docs/performance.md) separates request time and repeated calls so you can identify work worth reducing.
