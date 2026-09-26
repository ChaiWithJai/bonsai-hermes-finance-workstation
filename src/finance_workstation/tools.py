"""Deterministic fictional portfolio analytics exposed as a narrow MCP server."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("FINANCE_DATA_DIR", ROOT / "sample_data"))
OUT = Path(os.environ.get("FINANCE_DRAFT_DIR", Path.cwd() / "drafts"))


def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(newline="") as f:
        return list(csv.DictReader(f))


def mandate() -> dict:
    return json.loads((DATA / "mandate.json").read_text())


def snapshot() -> dict:
    holdings = read_csv("portfolio.csv")
    reports = read_csv("analyst_reports.csv")
    names = {r["asset_id"] for r in holdings}
    if len(names) != len(holdings) or {r["asset_id"] for r in reports} != names:
        raise ValueError("Holdings and analyst reports must have one matching row per asset")
    if not names or any(not x.startswith("FCT-") for x in names):
        raise ValueError("Only fictional FCT asset IDs are accepted")
    if any(not r["report_id"].startswith("FIC-") for r in reports):
        raise ValueError("Only fictional FIC report IDs are accepted")
    if any(int(r["units"]) <= 0 or int(r["price_usd"]) <= 0 for r in holdings):
        raise ValueError("Units and prices must be positive integers")
    m = mandate()
    if not math.isclose(sum(m["scenario_probabilities"].values()), 1.0):
        raise ValueError("Scenario probabilities must sum to one")
    if any(not math.isfinite(float(r[f"{s}_return_pct"])) for r in reports
           for s in ("base", "upside", "downside")):
        raise ValueError("Scenario returns must be finite")
    if any(r["as_of"] != m["as_of"] for r in holdings + reports):
        raise ValueError("All source dates must match the mandate date")
    total = sum(int(r["units"]) * int(r["price_usd"]) for r in holdings)
    if total <= 0:
        raise ValueError("Portfolio value must be positive")
    enriched = []
    for h in holdings:
        value = int(h["units"]) * int(h["price_usd"])
        enriched.append({**h, "value_usd": value, "weight_pct": round(100 * value / total, 4)})
    payload = {"holdings": enriched, "reports": reports, "mandate": m}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    source_file = DATA / "source.json"
    source = json.loads(source_file.read_text()) if source_file.exists() else {"integration": "local_csv_fixture"}
    if source.get("integration") not in {"local_csv_fixture", "google_sheets_download"}:
        raise ValueError("Unknown source integration")
    return {"demo": True, "source": source, "integration": source["integration"], "snapshot_sha256": digest,
            "portfolio_value_usd": total, **payload}


def weighted_return(weights: dict[str, int], reports: list[dict], scenario: str) -> float:
    col = f"{scenario}_return_pct"
    return round(sum(weights[r["asset_id"]] * float(r[col]) / 100 for r in reports), 4)


def breakdown(state: dict) -> dict:
    weights = {r["asset_id"]: r["weight_pct"] for r in state["holdings"]}
    return {k: weighted_return(weights, state["reports"], k) for k in ("base", "upside", "downside")}


def candidates(state: dict) -> list[dict]:
    m = state["mandate"]
    by_sleeve = {r["sleeve"]: r["asset_id"] for r in state["holdings"]}
    if set(by_sleeve) != set(m["sleeve_bounds_pct"]) or len(by_sleeve) != len(state["holdings"]):
        raise ValueError("The demo expects one holding per named sleeve")
    current = {r["asset_id"]: r["weight_pct"] for r in state["holdings"]}
    step = int(m["grid_step_pct"])
    found = []
    for defensive in range(0, 101, step):
        for growth in range(0, 101 - defensive, step):
            liquidity = 100 - defensive - growth
            sleeves = {"defensive": defensive, "growth": growth, "liquidity": liquidity}
            if any(not (lo <= sleeves[s] <= hi) for s, (lo, hi) in m["sleeve_bounds_pct"].items()):
                continue
            weights = {by_sleeve[s]: w for s, w in sleeves.items()}
            turnover = sum(abs(weights[k] - current[k]) for k in weights) / 2
            if turnover > m["max_one_way_turnover_pct"]:
                continue
            returns = {k: weighted_return(weights, state["reports"], k) for k in ("base", "upside", "downside")}
            if returns["downside"] < m["downside_floor_pct"]:
                continue
            weighted = sum(returns[k] * p for k, p in m["scenario_probabilities"].items())
            objective = weighted - 0.1 * abs(min(returns["downside"], 0)) - 0.02 * turnover
            found.append({"weights_pct": weights, "scenario_returns_pct": returns,
                          "one_way_turnover_pct": turnover, "probability_weighted_return_pct": round(weighted, 4),
                          "objective_score": round(objective, 4)})
    return sorted(found, key=lambda c: (-c["objective_score"], c["one_way_turnover_pct"],
                                       tuple(c["weights_pct"][k] for k in sorted(c["weights_pct"]))))


def execute(name: str, args: dict) -> dict:
    state = snapshot()
    common = {"demo": True, "integration": state["integration"], "source": state["source"],
              "snapshot_sha256": state["snapshot_sha256"]}
    if name == "read_portfolio":
        return {**common, "as_of": state["mandate"]["as_of"], "portfolio_value_usd": state["portfolio_value_usd"],
                "holdings": state["holdings"], "scenario_returns_pct": breakdown(state)}
    if name == "read_analyst_reports":
        asset = args.get("asset_id")
        rows = [r for r in state["reports"] if not asset or r["asset_id"] == asset]
        if asset and not rows:
            raise ValueError("Unknown asset_id. Read the portfolio to get valid IDs.")
        return {**common, "reports": rows}
    if name == "compare_scenarios":
        current = breakdown(state)
        ranked = candidates(state)
        if not ranked:
            raise ValueError("No candidate satisfies the mandate constraints")
        best = ranked[0]
        return {**common, "current_scenario_returns_pct": current,
                "current_weights_pct": {r["asset_id"]: r["weight_pct"] for r in state["holdings"]},
                "candidate": best, "feasible_grid_candidates": len(ranked),
                "methodology": state["mandate"], "decision_state": "draft_for_human_review"}
    if name == "write_review_draft":
        expected = args.get("expected_snapshot_sha256")
        if expected != state["snapshot_sha256"]:
            raise ValueError("Source snapshot changed. Reread the portfolio and scenarios.")
        reviewer = args.get("reviewer", "").strip()
        if not reviewer or len(reviewer) > 80:
            raise ValueError("A reviewer name of at most 80 characters is required")
        candidate = candidates(state)[0]
        OUT.mkdir(parents=True, exist_ok=True)
        draft_id = f"DRAFT-{state['snapshot_sha256'][:12]}"
        record = {**common, "draft_id": draft_id, "reviewer": reviewer,
                  "created_at": datetime.now(timezone.utc).isoformat(), "candidate": candidate,
                  "status": "pending_human_review", "order_submitted": False,
                  "source_reports": [r["report_id"] for r in state["reports"]]}
        path = OUT / f"{draft_id}.json"
        if not path.exists():
            path.write_text(json.dumps(record, indent=2) + "\n")
        return {"draft_id": draft_id, "path": str(path), "status": record["status"],
                "order_submitted": False, "integration": "local_json_draft"}
    raise ValueError("Unknown finance tool")


def tool(name, description, properties, required=(), readonly=True):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": properties,
                            "required": list(required), "additionalProperties": False},
            "annotations": {"readOnlyHint": readonly, "destructiveHint": False, "openWorldHint": False}}


TOOLS = [
    tool("read_portfolio", "Read the fictional holdings, current weights, valuation date and scenario returns.", {}),
    tool("read_analyst_reports", "Read fictional analyst report assumptions with source IDs and confidence.",
         {"asset_id": {"type": "string"}}),
    tool("compare_scenarios", "Evaluate all 5 percent grid allocations that meet the fictional mandate. Return current and top candidate with constraints.", {}),
    tool("write_review_draft", "Save the top candidate for human review only. Never submits an order or changes the holdings.",
         {"expected_snapshot_sha256": {"type": "string"}, "reviewer": {"type": "string"}},
         ("expected_snapshot_sha256", "reviewer"), False),
]


def main():
    for line in sys.stdin:
        try:
            q = json.loads(line)
            if "id" not in q:
                continue
            method = q["method"]
            if method == "initialize":
                result = {"protocolVersion": q.get("params", {}).get("protocolVersion", "2024-11-05"),
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "bonsai-portfolio-review", "version": "0.1.0"}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                p = q["params"]
                try:
                    result = {"content": [{"type": "text", "text": json.dumps(execute(p["name"], p.get("arguments", {})))}]}
                except Exception as e:
                    result = {"isError": True, "content": [{"type": "text", "text": str(e)}]}
            else:
                result = {}
            print(json.dumps({"jsonrpc": "2.0", "id": q["id"], "result": result}), flush=True)
        except Exception as e:
            print(str(e), file=sys.stderr)


if os.environ.get("FINANCE_MLFLOW_TRACE") == "1":
    import mlflow
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("bonsai-finance-workstation")
    execute = mlflow.trace(name="finance_tool", span_type="TOOL")(execute)

if __name__ == "__main__":
    main()
