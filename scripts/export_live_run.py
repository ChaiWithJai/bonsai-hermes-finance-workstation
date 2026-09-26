"""Export one completed Hermes session and score narrow observable behaviors."""
import json
import os
import sqlite3
from pathlib import Path

import mlflow

ROOT = Path(__file__).resolve().parents[1]
PROFILE = Path.home() / ".hermes" / "profiles" / "finance-workstation"
SESSION_ID = os.environ.get("FINANCE_SESSION_ID", "20260926_124340_3f8174")


def main():
    con = sqlite3.connect(PROFILE / "state.db")
    con.row_factory = sqlite3.Row
    session = con.execute("SELECT id,source,started_at,model FROM sessions WHERE id=?", (SESSION_ID,)).fetchone()
    if not session:
        raise SystemExit("Requested Hermes session does not exist")
    rows = con.execute("SELECT role,content,tool_calls,tool_name,timestamp,finish_reason FROM messages WHERE session_id=? ORDER BY id", (SESSION_ID,)).fetchall()
    usage = con.execute("SELECT model,api_call_count,input_tokens,output_tokens,reasoning_tokens FROM session_model_usage WHERE session_id=?", (SESSION_ID,)).fetchone()
    messages = [{k: r[k] for k in r.keys()} for r in rows]
    final = next((r["content"] for r in reversed(rows) if r["role"] == "assistant" and r["content"]), "")
    tools = [r["tool_name"] for r in rows if r["role"] == "tool"]
    required = {"mcp__finance__read_portfolio", "mcp__finance__read_analyst_reports", "mcp__finance__compare_scenarios"}
    checks = {
        "used_required_tools": required.issubset(tools),
        "no_write_tool": "mcp__finance__write_review_draft" not in tools,
        "base_and_downside_numbers": "8.65%" in final and "-16.7%" in final,
        "cites_uncertain_report": "FIC-REPORT-02" in final and "low-confidence" in final.lower(),
        "names_fixture": "local CSV fixture" in final,
        "states_no_trade": "not a trade instruction" in final or "no draft has been saved" in final.lower(),
    }
    evidence = {"scope": "one live local Hermes and Bonsai session, deterministic output checks",
                "human_reviewed": False, "slack_evaluated": False,
                "session": dict(session), "usage": dict(usage) if usage else None,
                "tool_names": tools, "checks": checks, "messages": messages}
    out = ROOT / "evidence/sessions/live-run-evidence.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("bonsai-finance-workstation")
    with mlflow.start_run(run_name="live-hermes-finance-observable-checks") as run:
        mlflow.log_metric("checks_passed", sum(checks.values()))
        mlflow.log_metric("checks_total", len(checks))
        mlflow.log_metric("model_api_calls", usage["api_call_count"] if usage else 0)
        mlflow.log_metric("input_tokens", usage["input_tokens"] if usage else 0)
        mlflow.log_metric("output_tokens", usage["output_tokens"] if usage else 0)
        mlflow.log_artifact(str(out))
        mlflow.set_tags({"evidence_scope": "one_live_hermes_session", "human_reviewed": "false",
                         "slack_evaluated": "false", "session_id": SESSION_ID})
        run_id = run.info.run_id
    summary = {"session_id": SESSION_ID, "run_id": run_id, "checks": checks,
               "checks_passed": sum(checks.values()), "checks_total": len(checks),
               "model_api_calls": usage["api_call_count"] if usage else None}
    (ROOT / "evidence/evaluations/live-run-result.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
