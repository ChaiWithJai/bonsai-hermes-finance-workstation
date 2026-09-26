"""Create a new isolated Hermes profile without replacing another profile."""
import argparse
import json
import shutil
import sys
import re
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--profile", default="finance-workstation")
args = parser.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", args.profile):
    raise SystemExit("Use a simple profile name with letters, numbers and hyphens")
out = Path.home() / ".hermes" / "profiles" / args.profile
if out.exists():
    raise SystemExit(f"Refusing to overwrite {out}")
config = json.loads((root / "config" / "hermes.json").read_text())
tool_python = Path(os.environ.get("FINANCE_PYTHON", sys.executable)).expanduser().resolve()
if not tool_python.exists():
    raise SystemExit(f"Python interpreter does not exist: {tool_python}")
has_mlflow = subprocess.run([str(tool_python), "-c", "import mlflow"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
out.mkdir(parents=True)
config["mcp_servers"]["finance"]["command"] = str(tool_python)
config["mcp_servers"]["finance"]["args"] = [str(root / "src" / "finance_workstation" / "tools.py")]
if not has_mlflow:
    config["mcp_servers"]["finance"]["env"]["FINANCE_MLFLOW_TRACE"] = "0"
(out / "config.yaml").write_text(json.dumps(config, indent=2) + "\n")
shutil.copy2(root / "config" / "SOUL.md", out / "SOUL.md")
(out / ".env.example").write_text("SLACK_BOT_TOKEN=\nSLACK_APP_TOKEN=\nSLACK_ALLOWED_USERS=\n")
print(out)
