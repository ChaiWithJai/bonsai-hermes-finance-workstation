import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ProfileSetupTest(unittest.TestCase):
    def test_selected_snapshot_is_used_outside_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder).resolve()
            data = home / "snapshot"
            shutil.copytree(ROOT / "src/finance_workstation/sample_data", data)
            source = {"integration": "local_csv_fixture", "test_marker": "selected_snapshot", "synced_at": "2026-09-26"}
            (data / "source.json").write_text(json.dumps(source))
            env = dict(os.environ, HOME=str(home), FINANCE_DATA_DIR=str(data),
                       FINANCE_DRAFT_DIR=str(home / "drafts"), FINANCE_PYTHON=sys.executable)
            subprocess.run([sys.executable, str(ROOT / "scripts/setup_profile.py"),
                            "--profile", "setup-check"], env=env, check=True, capture_output=True)
            profile = home / ".hermes/profiles/setup-check/config.yaml"
            server = json.loads(profile.read_text())["mcp_servers"]["finance"]
            self.assertEqual(server["command"], str(Path(sys.executable).absolute()))
            self.assertEqual(server["env"]["FINANCE_DATA_DIR"], str(data))
            self.assertEqual(server["env"]["FINANCE_DRAFT_DIR"], str(home / "drafts"))
            child_env = dict(os.environ)
            child_env.pop("FINANCE_DATA_DIR", None)
            child_env.update(server["env"])
            child_env["FINANCE_MLFLOW_TRACE"] = "0"
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "read_portfolio", "arguments": {}}}
            result = subprocess.run([server["command"], *server["args"]], cwd=home,
                                    env=child_env, input=json.dumps(request)+"\n",
                                    capture_output=True, text=True, check=True)
            reply = json.loads(result.stdout)["result"]
            self.assertFalse(reply.get("isError"), reply)
            self.assertIn("selected_snapshot", reply["content"][0]["text"])

    def test_web_research_is_explicit_and_keeps_finance_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            env = {**os.environ, 'HOME': folder, 'FINANCE_PYTHON': sys.executable}
            for name, flags in [('local-only', []), ('with-research', ['--web-research'])]:
                subprocess.run([sys.executable, str(ROOT / 'scripts/setup_profile.py'), '--profile', name, *flags], env=env, check=True, capture_output=True)
            profiles = Path(folder) / '.hermes/profiles'
            local = json.loads((profiles / 'local-only/config.yaml').read_text())
            research = json.loads((profiles / 'with-research/config.yaml').read_text())
            self.assertEqual(local['platform_toolsets']['cli'], ['finance'])
            self.assertNotIn('web', local)
            for platform in ('cli', 'slack'):
                self.assertEqual(research['platform_toolsets'][platform], ['finance', 'web'])
            self.assertEqual(research['web']['provider_tier'], {'exa': 'free', 'firecrawl': 'free'})
            self.assertEqual(research['web']['extract_backend'], 'firecrawl')
            self.assertEqual(research['mcp_servers']['finance'], local['mcp_servers']['finance'])
            self.assertIn('Public research does not change the mandate', (profiles / 'with-research/SOUL.md').read_text())
            self.assertNotIn('Public research does not change the mandate', (profiles / 'local-only/SOUL.md').read_text())
