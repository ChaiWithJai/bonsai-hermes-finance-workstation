"""Run deterministic finance-tool checks and log their evidence in local MLflow.

This is not an evaluation of Bonsai's tool choice or answer quality.
"""
import json
import os
import tempfile
from pathlib import Path

import mlflow

from finance_workstation import tools as finance

ROOT = Path(__file__).resolve().parents[1]


def main():
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("bonsai-finance-workstation")

    @mlflow.trace(name="finance_eval_case", span_type="EVALUATOR")
    def case(name, callback):
        result = callback()
        return {"case": name, "passed": bool(result)}

    initial = finance.execute("read_portfolio", {})
    reports = finance.execute("read_analyst_reports", {})
    comparison = finance.execute("compare_scenarios", {})
    candidate = comparison["candidate"]
    checks = [
        case("portfolio_totals", lambda: initial["portfolio_value_usd"] == 1_000_000 and
             sum(h["weight_pct"] for h in initial["holdings"]) == 100),
        case("report_provenance", lambda: {r["report_id"] for r in reports["reports"]} ==
             {h["source_ref"] for h in initial["holdings"]}),
        case("scenario_arithmetic", lambda: initial["scenario_returns_pct"] ==
             {"base": 7.75, "upside": 13.75, "downside": -14.5}),
        case("candidate_feasible", lambda: sum(candidate["weights_pct"].values()) == 100 and
             candidate["one_way_turnover_pct"] <= 15 and
             candidate["scenario_returns_pct"]["downside"] >= -18),
        case("candidate_nontrivial", lambda: candidate["weights_pct"] != comparison["current_weights_pct"]),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "finance-eval.json"
        out.write_text(json.dumps({"evaluation_scope": "deterministic_tool_behavior_only",
                                   "model_evaluated": False, "slack_evaluated": False,
                                   "integration": initial["integration"],
                                   "snapshot_sha256": initial["snapshot_sha256"],
                                   "checks": checks, "comparison": comparison}, indent=2) + "\n")
        with mlflow.start_run(run_name="fictional-finance-tool-checks") as run:
            mlflow.log_metric("checks_passed", sum(c["passed"] for c in checks))
            mlflow.log_metric("checks_total", len(checks))
            mlflow.log_metric("feasible_candidates", comparison["feasible_grid_candidates"])
            mlflow.log_metric("candidate_one_way_turnover_pct", candidate["one_way_turnover_pct"])
            mlflow.log_artifact(str(out))
            run_id = run.info.run_id
    result = {"run_id": run_id, "tracking_uri": mlflow.get_tracking_uri(),
              "checks_passed": sum(c["passed"] for c in checks), "checks_total": len(checks),
              "evaluation_scope": "deterministic_tool_behavior_only", "model_evaluated": False}
    (ROOT / "evidence/evaluations/eval-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if any(not c["passed"] for c in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
