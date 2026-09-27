"""Create a new isolated Hermes profile without replacing another profile."""
import argparse
import json
import sys
import re
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--profile", default="finance-workstation")
parser.add_argument("--web-research", action="store_true", help="Enable Hermes public web research using free Exa search and Firecrawl extraction")
args = parser.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", args.profile):
    raise SystemExit("Use a simple profile name with letters, numbers and hyphens")
out = Path.home() / ".hermes" / "profiles" / args.profile
if out.exists():
    raise SystemExit(f"Refusing to overwrite {out}")
config = json.loads((root / "config" / "hermes.json").read_text())
if args.web_research:
    for platform in ("cli", "slack"):
        config["platform_toolsets"][platform].append("web")
    config["web"] = {"search_backend": "exa", "extract_backend": "firecrawl", "provider_tier": {"exa": "free", "firecrawl": "free"}}
tool_python = Path(os.environ.get("FINANCE_PYTHON", sys.executable)).expanduser().absolute()
if not tool_python.exists():
    raise SystemExit(f"Python interpreter does not exist: {tool_python}")
has_mlflow = subprocess.run([str(tool_python), "-c", "import mlflow"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
out.mkdir(parents=True)
config["mcp_servers"]["finance"]["command"] = str(tool_python)
config["mcp_servers"]["finance"]["args"] = [str(root / "src" / "finance_workstation" / "tools.py")]
server_env = config["mcp_servers"]["finance"].setdefault("env", {})
for variable in ("FINANCE_DATA_DIR", "FINANCE_DRAFT_DIR"):
    if os.environ.get(variable):
        server_env[variable] = str(Path(os.environ[variable]).expanduser().resolve())
if not has_mlflow:
    config["mcp_servers"]["finance"]["env"]["FINANCE_MLFLOW_TRACE"] = "0"
(out / "config.yaml").write_text(json.dumps(config, indent=2) + "\n")
instructions = (root / "config" / "SOUL.md").read_text()
if args.web_research:
    instructions += "\n" + (root / "config" / "research.md").read_text()
(out / "SOUL.md").write_text(instructions)
(out / ".env.example").write_text("SLACK_BOT_TOKEN=\nSLACK_APP_TOKEN=\nSLACK_ALLOWED_USERS=\n")
print(out)
