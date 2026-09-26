# Finance workstation evidence

This repository uses fictional holdings, issuers, analyst reports, and scenarios in [`sample_data`](../src/finance_workstation/sample_data). The two captured Hermes sessions read those bundled CSV files through the finance tools. A separate Google Sheet contains matching demo rows, but neither session made an authenticated Sheets read. The model did not place an order or write to the portfolio.

## Captured sessions

| Session | Observed action and result | Record |
| --- | --- | --- |
| Direct Hermes, `20260926_124340_3f8174` | Bonsai made four model calls. Hermes read the portfolio and analyst reports, then called `compare_scenarios` twice. The answer compared current weights of 45% Harbor, 35% Orbit, and 20% Reserve with a feasible 35%/45%/20% candidate. The assumed base case rose from 7.75% to 8.65%; the downside moved from -14.5% to -16.7%. It named the low-confidence Orbit report and disclosed the CSV source. No draft was saved. | [Session](../evidence/sessions/live-run-evidence.json) · [six output checks](../evidence/evaluations/live-run-result.json), MLflow run `e05c98815de04e799a35c92111fa07fa` |
| Slack DM, `20260926_142835_a3f42516` | The existing A+ Client Commitments bot used its Hermes profile with the same finance tools and local Bonsai endpoint. Four main model calls produced a source-cited allocation comparison in 101.5 seconds. Hermes repeated `compare_scenarios` with identical arguments; it reused the first tool result. The answer disclosed local CSV sources and did not call the draft writer or an order tool. | [Session](../evidence/sessions/slack-live-evidence.json) · [ten output checks](../evidence/evaluations/slack-live-result.json), MLflow run `0944b153dd22461796832768a3aba8a5` |

The candidate is the result of arithmetic under the fictional [mandate](../src/finance_workstation/sample_data/mandate.json). The base and downside percentages are scenario assumptions, not forecasts or evidence of investment performance. The repeated comparison added a model round trip without new data; [the measured call breakdown](performance.md) identifies the latency contribution and a matched test to try next. No speedup has been measured.

## Checks and their scope

The current test suite has **seven passing tests**: four core tool tests for weights, scenario arithmetic, source IDs, mandate constraints, stale snapshots, and draft isolation, plus three Sheet-import parser tests. The parser tests exercise supplied API-shaped rows, title/header handling, and formatted values; they do not perform an authenticated Google API call.

MLflow experiment 41 also contains a historical **5/5 deterministic tool evaluation** in run `d02a8818609841f5a548a0a1a83cda0b` ([result](../evidence/evaluations/eval-result.json)). The direct session's **6/6** and Slack session's **10/10** are narrow checks of those saved sessions. Successful tool spans and passing output checks show what happened in these examples. They do not establish reliability across new portfolios or prompts, investment judgment, a held-out evaluation, or human approval. No human review is recorded.

The optional Sheets importer can download and validate `Portfolio` and `Analyst Reports` tabs into a local snapshot when given a workbook ID and OAuth token. The tools then read that snapshot; they do not read live cells on each question. This path is implemented but unverified with an authenticated Hermes session. No Sheets write is implemented. Screenshots of the demo Sheet show its rows, not an agent read.

The MLflow records were read back through the local API. An attempted lab backup lost its MongoDB GridFS connection, and Docker Desktop could not be reached afterward, so this run has no new archive restore verification. That limits durability claims for the trace archive; the checked-in session and evaluation exports above remain available for review.

## Optional screenshot index

- [Direct-run MLflow checks](../evidence/screenshots/mlflow-live-run.png), [Slack-run MLflow checks](../evidence/screenshots/mlflow-slack-checks.jpg), and [tool traces](../evidence/screenshots/mlflow-traces.png)
- [Slack allocation reply](../evidence/screenshots/slack-allocation-review.jpg) and [Slack scenario reply](../evidence/screenshots/slack-scenario-review.jpg)
- [Demo Sheet portfolio](../evidence/screenshots/google-sheet-portfolio.jpg) and [demo Sheet reports](../evidence/screenshots/google-sheet-reports.jpg)
