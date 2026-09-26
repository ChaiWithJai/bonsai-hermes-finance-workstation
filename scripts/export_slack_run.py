"""Export and check the completed, read-only finance turn in the Slack gateway."""

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import mlflow


ROOT = Path(__file__).resolve().parents[1]
DB = Path.home() / ".hermes/profiles/commitments/state.db"
SESSION_ID = "20260926_142835_a3f42516"
TOOLS = {
    "mcp__finance_workstation__read_portfolio",
    "mcp__finance_workstation__read_analyst_reports",
    "mcp__finance_workstation__compare_scenarios",
}


def tool_result(text):
    """Extract the JSON response nested in Hermes's untrusted-data wrapper."""
    start = text.find('{"result": ')
    end = text.rfind("\n</untrusted_tool_result>")
    if start < 0 or end < 0:
        raise ValueError("Unexpected tool result wrapper")
    return json.loads(json.loads(text[start:end])["result"])


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    session = con.execute(
        "SELECT id,source,started_at,model FROM sessions WHERE id=?", (SESSION_ID,)
    ).fetchone()
    if not session:
        raise SystemExit("The recorded Slack session does not exist")
    rows = con.execute(
        "SELECT role,content,tool_calls,tool_name,timestamp FROM messages "
        "WHERE session_id=? ORDER BY id", (SESSION_ID,)
    ).fetchall()
    usage = con.execute(
        "SELECT model,api_call_count,input_tokens,output_tokens,reasoning_tokens "
        "FROM session_model_usage WHERE session_id=? ORDER BY api_call_count DESC LIMIT 1",
        (SESSION_ID,),
    ).fetchone()
    prompt = next(r["content"] for r in rows if r["role"] == "user")
    answer = next(r["content"] for r in reversed(rows) if r["role"] == "assistant" and not r["tool_calls"] and r["content"])
    tool_rows = [r for r in rows if r["role"] == "tool"]
    names = [r["tool_name"] for r in tool_rows]
    parsed = [tool_result(r["content"]) for r in tool_rows if "byte-identical" not in r["content"]]
    portfolio, reports, comparison = parsed
    same_snapshot = len({x["snapshot_sha256"] for x in parsed}) == 1
    candidate = comparison["candidate"]
    weights = candidate["weights_pct"]
    report_ids = {r["report_id"]: r for r in reports["reports"]}
    checks = {
        "required_finance_tools_used": TOOLS.issubset(names),
        "no_write_tool_called": "mcp__finance_workstation__write_review_draft" not in names,
        "one_source_snapshot": same_snapshot,
        "current_weights_match_tool": all(
            f'{comparison["current_weights_pct"][asset]:.1f}%' in answer
            for asset in weights
        ),
        "candidate_weights_match_tool": all(
            f'{pct}%' in answer for pct in weights.values()
        ),
        "downside_tradeoff_matches_tool": (
            str(comparison["current_scenario_returns_pct"]["downside"]) in answer
            and str(candidate["scenario_returns_pct"]["downside"]) in answer
            and "2.2 percentage points worse" in answer
        ),
        "report_ids_dates_confidence_cited": all(
            rid in answer and row["as_of"] in answer and row["confidence"] in answer.lower()
            for rid, row in report_ids.items() if rid in {"FIC-REPORT-01", "FIC-REPORT-02"}
        ),
        "local_fixture_disclosed": "local CSV fixture" in answer,
        "no_live_sheet_claim": "There was no Google Sheets download or live Sheet read" in answer,
        "no_order_or_draft_claim": "No draft saved, no order placed" in answer,
    }
    evidence = {
        "scope": "one completed Slack DM through Hermes to local Bonsai; fictional CSV data",
        "human_reviewed": False,
        "sheet_read_by_hermes": False,
        "session": dict(session),
        "usage_main_turn": dict(usage) if usage else None,
        "prompt": prompt,
        "answer": answer,
        "tool_names": names,
        "tool_result_sha256": [hashlib.sha256(r["content"].encode()).hexdigest() for r in tool_rows],
        "snapshot_sha256": portfolio["snapshot_sha256"],
        "candidate": candidate,
        "checks": checks,
        "duplicate_comparison_call": names.count("mcp__finance_workstation__compare_scenarios") - 1,
        "slack_message_url": "https://app.slack.com/client/T09PDJJ3U95/D0C4B99LSRZ",
    }
    out = ROOT / "evidence/sessions/slack-live-evidence.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("bonsai-finance-workstation")
    with mlflow.start_run(run_name="slack-finance-observable-checks") as run:
        mlflow.log_metric("checks_passed", sum(checks.values()))
        mlflow.log_metric("checks_total", len(checks))
        mlflow.log_metric("model_api_calls", usage["api_call_count"] if usage else 0)
        mlflow.log_metric("duplicate_comparison_calls", evidence["duplicate_comparison_call"])
        mlflow.log_artifact(str(out))
        mlflow.set_tags({
            "evidence_scope": "one_slack_finance_session",
            "human_reviewed": "false",
            "sheet_read_by_hermes": "false",
            "session_id": SESSION_ID,
        })
        run_id = run.info.run_id
    result = {"session_id": SESSION_ID, "mlflow_run_id": run_id,
              "checks_passed": sum(checks.values()), "checks_total": len(checks),
              "duplicate_comparison_call": evidence["duplicate_comparison_call"]}
    (ROOT / "evidence/evaluations/slack-live-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
