# Tests and MLflow

Run the regression suite from the installed checkout:

```sh
python -m unittest discover -s tests -v
```

The suite checks portfolio weights, scenario arithmetic, the allocation constraints, report references, draft revision checks and Sheet parsing. The calculation can also be inspected with `python -m finance_workstation example` without using a model.

To log the deterministic tool checks to MLflow, install the optional dependency and start a local tracking server in a separate terminal:

```sh
python -m pip install -r requirements-eval.txt
mlflow server --host 127.0.0.1 --port 5210
```

Then run:

```sh
export MLFLOW_TRACKING_URI=http://127.0.0.1:5210
python scripts/evaluate.py
```

Open the tracking URI on your machine and select the `bonsai-finance-workstation` experiment. The script logs five code-behavior checks and a comparison artifact. It evaluates the tools directly, so its passing count does not measure the model's answer quality.

For tool traces during a Hermes run, install MLflow before creating the profile. Setup enables tracing when it can import MLflow through the selected tool interpreter; otherwise it disables tracing so the local example still runs. Set `MLFLOW_TRACKING_URI` in `mcp_servers.finance.env` if the tracking server uses a different address. Tool traces do not by themselves capture model latency or token usage.

The [execution record](evidence.md) links portable captures from the direct and Slack sessions, including their prompts, answers and check results. The exporter scripts under `scripts/` preserve those original sessions from the author's local Hermes databases. They are archival utilities, and their recorded session IDs will not exist in a new installation. Use your own session capture to evaluate a new run.
