"""Run the MCP server or inspect the portfolio calculation without a model."""
import argparse

from . import tools


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "example"])
    args = parser.parse_args()
    if args.command == "serve":
        tools.main()
        return
    result = tools.execute("compare_scenarios", {})
    candidate = result["candidate"]
    current = result["current_scenario_returns_pct"]
    revised = candidate["scenario_returns_pct"]
    print("Portfolio scenario calculation (sample data; no model call)")
    print(f"Feasible allocations: {result['feasible_grid_candidates']}")
    print("Candidate weights: " + ", ".join(
        f"{asset} {weight}%" for asset, weight in candidate["weights_pct"].items()))
    print(f"Base scenario: {current['base']:.2f}% -> {revised['base']:.2f}%")
    print(f"Downside scenario: {current['downside']:.2f}% -> {revised['downside']:.2f}%")
    print(f"One-way turnover: {candidate['one_way_turnover_pct']}%")


if __name__ == "__main__":
    main()
