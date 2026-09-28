"""Exercise actual shell commands without network or telemetry calls."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import codex_hook_compat as compat


class HookCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="azure hooks ")
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / "cache"
        self.plugin = self.cache / "azure"
        self.payload = '{"hook_event_name":"PostToolUse","tool_name":"Bash"}\n'

    def install(self, version, stamp=1, exit_code=0):
        root = self.plugin / version
        manifest = root / ".claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "azure", "version": version}))
        os.utime(manifest, (stamp, stamp))
        script = root / compat.SCRIPT
        script.parent.mkdir(parents=True)
        # Script proves stdin, the chosen version, script location, and exit status.
        script.write_text(f'#!/bin/bash\n/bin/cat\nprintf "%s\\n" "${{BASH_SOURCE[0]}}"\nexit {exit_code}\n')
        return root

    def run_hook(self, root):
        return subprocess.run(["/bin/bash", "-c", compat.command()],
                              env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(root), "PATH": "/usr/bin:/bin"},
                              input=self.payload, text=True, capture_output=True)

    def test_requested_root_and_spaces(self):
        old = self.install("1.0", 1)
        self.install("2.0", 2)
        result = self.run_hook(old)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.payload + str(old / compat.SCRIPT) + "\n")

    def test_deleted_root_uses_most_recent_manifest_and_preserves_status(self):
        old = self.install("1.0")
        shutil.rmtree(old)
        self.install("9.0", 2)
        current = self.install("10.0", 3, exit_code=7)
        result = self.run_hook(old)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, self.payload + str(current / compat.SCRIPT) + "\n")

    def test_old_script_shim_forwards_and_is_idempotent(self):
        current = self.install("2.0")
        old = self.plugin / "1.0"
        self.assertEqual(len(compat.repair(self.cache, [old])), 1)
        self.assertEqual(compat.repair(self.cache, [old, current]), [])
        result = subprocess.run(["/bin/bash", str(old / compat.SCRIPT)],
                                input=self.payload, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.payload + str(current / compat.SCRIPT) + "\n")
        self.assertEqual(self.run_hook(old).stdout, result.stdout)

    def test_missing_plugin_fails_clearly(self):
        result = self.run_hook(self.plugin / "1.0")
        self.assertEqual(result.returncode, 127)
        self.assertIn("no installed plugin", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_repair_preserves_unknown_files_and_rejects_other_paths(self):
        self.install("2.0")
        old = self.plugin / "1.0"
        target = old / compat.SCRIPT
        target.parent.mkdir(parents=True)
        target.write_text("custom script")
        with self.assertRaises(ValueError):
            compat.repair(self.cache, [old])
        self.assertEqual(target.read_text(), "custom script")
        with self.assertRaises(ValueError):
            compat.repair(self.cache, [self.cache.parent / "outside"])

    def test_all_distributed_commands_match_generator(self):
        paths = [compat.REPO / "hooks/claude-hooks.json"]
        paths += list((compat.REPO / ".github/plugins").glob("*/hooks/claude-hooks.json"))
        self.assertEqual(len(paths), 6)
        for path in paths:
            for event in json.loads(path.read_text())["hooks"].values():
                for group in event:
                    for hook in group["hooks"]:
                        self.assertEqual(hook["command"], compat.command(), str(path))


if __name__ == "__main__":
    unittest.main()
