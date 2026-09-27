# Portfolio review with Bonsai and Hermes

Build a portfolio review agent that compares allocations against a written mandate and explains the tradeoff using analyst reports. Hermes chooses the tools and Ternary Bonsai 2 27B runs locally, while Python calculates scenario returns and checks the allocation constraints.

The example starts with a $1 million portfolio and asks whether shifting ten percentage points from Harbor to Orbit improves its outlook. The candidate improves the assumed base return from 7.75% to 8.65%, while worsening the downside from -14.50% to -16.70%. The agent must explain both changes and cite the report behind the more uncertain assumption.

The included holdings and reports are sample data. The tools can save a review draft, but they cannot submit an order. Local CLI and Slack sessions have been captured; an authenticated Sheet import and subsequent Slack review are recorded in the [connected verification](docs/google-verification.md).

## Run the portfolio calculation

You need Python 3.10 or newer. The calculation uses the standard library, so you can inspect the result before installing Hermes or downloading a model.

```sh
git clone https://github.com/ChaiWithJai/bonsai-hermes-finance-workstation.git
cd bonsai-hermes-finance-workstation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m finance_workstation example
```

The command runs the same calculation exposed to the agent, without making a model call:

```text
Portfolio scenario calculation (sample data; no model call)
Feasible allocations: 20
Candidate weights: FCT-HARBOR 35%, FCT-ORBIT 45%, FCT-RESERVE 20%
Base scenario: 7.75% -> 8.65%
Downside scenario: -14.50% -> -16.70%
One-way turnover: 10.0%
```

The candidate is selected by the scoring rule in [mandate.json](src/finance_workstation/sample_data/mandate.json). Change that rule or the analyst assumptions to examine a different tradeoff. The search uses a five-percentage-point grid, so it compares a finite set of feasible allocations rather than solving a continuous optimization problem.

## Run the agent locally

Install [Hermes](https://github.com/NousResearch/hermes-agent) and obtain the [Bonsai 2 GGUF and matching Prism runtime](https://github.com/PrismML-Eng/Bonsai-demo). The captured setup used an M5 Pro with 48 GiB of memory. See [model and harness setup](docs/setup.md) for the tested revisions, settings and troubleshooting.

In a separate terminal, start the model with your downloaded paths:

```sh
export LLAMA_SERVER=/absolute/path/to/llama-server
export BONSAI_MODEL=/absolute/path/to/Ternary-Bonsai-2-27B-PQ2_0.gguf
sh scripts/start_model.sh
```

Back in the activated Python environment, create a Hermes profile and ask for a review:

```sh
python scripts/setup_profile.py --profile finance-workstation
hermes --profile finance-workstation chat --oneshot -Q -q \
  "Compare the current portfolio with the best allocation under the mandate. Explain the change in base and downside returns, and cite the analyst assumptions that require review."
```

Hermes should call `read_portfolio`, `read_analyst_reports` and `compare_scenarios`. Its explanation should preserve the numbers above and identify the low-confidence Orbit report, `FIC-REPORT-02`. A [recorded Slack run](evidence/sessions/slack-live-evidence.json) shows this tool sequence using the A+ Client Commitments profile and bundled CSVs. It is separate from the local profile created above.

To save a candidate, ask the agent to prepare a review draft for a named reviewer. The `write_review_draft` tool checks the source snapshot before writing a JSON file under `drafts/`, with status `pending_human_review`. Changing the source requires a fresh comparison. The tool reads the saved file back before confirming it, and repeating the same request preserves the original draft. A different reviewer requires resolving the existing assignment; the tool rejects that request rather than silently changing reviewers.

## How the workflow is divided

| Component | Responsibility |
| --- | --- |
| [Portfolio and analyst reports](src/finance_workstation/sample_data/) | Supply positions, dates, report references and scenario assumptions. |
| [Mandate](src/finance_workstation/sample_data/mandate.json) | Defines allocation bounds, turnover, downside floor and candidate scoring. |
| [Python tools](src/finance_workstation/tools.py) | Validate inputs, calculate returns, search allocations and save review drafts. |
| [Hermes instructions](config/SOUL.md) | Govern tool use, source attribution and when the agent may save a draft. |
| Local Bonsai server | Selects tool calls and explains the result in the conversation. |

Slack is an optional entry point to the same agent. Google Sheets can supply a downloaded input snapshot. Follow the [integration guide](docs/integrations.md) after the local path works.

## Inspect and extend the example

```sh
python -m unittest discover -s tests -v
```

The tests cover scenario arithmetic, allocation constraints, report references, source revisions and Sheet parsing. For optional MLflow logging, install `requirements-eval.txt` and follow the [evaluation guide](docs/evaluation.md).

A captured Slack review took 101.5 seconds over four model calls, including a repeated comparison. The [latency breakdown](docs/performance.md) identifies the extra turn and the next controlled test. The [execution record](docs/evidence.md) links the sessions, check results and screenshots without treating a passing check count as a reliability estimate.

Source code lives in `src/`, agent configuration in `config/`, setup and evaluation commands in `scripts/`, and regression tests in `tests/`. The `evidence/` directory preserves the recorded sessions; `docs/` explains integration and measurement details.
