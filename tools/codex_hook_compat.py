#!/usr/bin/env python3
"""Generate upgrade-tolerant hooks and repair paths held by existing Codex threads."""

import argparse
import json
import shlex
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = "hooks/scripts/track-telemetry.sh"
MARKER = "# Azure Codex stale-cache compatibility shim"

# Embedded in the command itself: a helper in a deleted cache cannot rescue it.
# Only real plugin roots qualify; shim-only directories must never recurse.
RESOLVER = r'''requested=$1
selected=
if [ -f "$requested/.claude-plugin/plugin.json" ] && [ -f "$requested/hooks/scripts/track-telemetry.sh" ]; then
  selected=$requested
else
  for candidate in "${requested%/*}"/*; do
    [ -f "$candidate/.claude-plugin/plugin.json" ] || continue
    [ -f "$candidate/hooks/scripts/track-telemetry.sh" ] || continue
    if [ -z "$selected" ] || [ "$candidate/.claude-plugin/plugin.json" -nt "$selected/.claude-plugin/plugin.json" ]; then
      selected=$candidate
    fi
  done
fi
if [ -z "$selected" ]; then
  printf 'Azure hook: no installed plugin found for %s\n' "$requested" >&2
  exit 127
fi
exec /bin/bash "$selected/hooks/scripts/track-telemetry.sh"
'''


def command():
    return '/bin/bash -c ' + shlex.quote(RESOLVER) + ' _ "${CLAUDE_PLUGIN_ROOT}"'


def generate():
    paths = [REPO / "hooks/claude-hooks.json"]
    paths += sorted((REPO / ".github/plugins").glob("*/hooks/claude-hooks.json"))
    for path in paths:
        data = json.loads(path.read_text())
        for event in data["hooks"].values():
            for group in event:
                for hook in group["hooks"]:
                    if hook.get("type") == "command" and SCRIPT in hook["command"]:
                        hook["command"] = command()
        path.write_text(json.dumps(data, indent=2) + "\n")
    return paths


def repair(cache, old_roots):
    cache = cache.expanduser().resolve()
    repaired = []
    for root in old_roots:
        root = root.expanduser().absolute()
        # Accept only a version directory directly under this marketplace/plugin.
        if root.parent.parent.resolve() != cache:
            raise ValueError(f"Not a plugin version under {cache}: {root}")
        if not any((p / ".claude-plugin/plugin.json").is_file()
                   and (p / SCRIPT).is_file() for p in root.parent.iterdir()):
            raise ValueError(f"No current installed plugin for {root}")
        target = root / SCRIPT
        shim = ("#!/bin/bash\n" + MARKER + "\n"
                + 'set -- "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"\n'
                + RESOLVER)
        if target.exists():
            if target.read_text() == shim:
                continue
            if (root / ".claude-plugin/plugin.json").is_file():
                continue  # Never overwrite a genuine installed script.
            raise ValueError(f"Refusing to replace unknown file: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x") as stream:
            stream.write(shim)
        target.chmod(0o755)
        repaired.append(str(target))
    return repaired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("generate", help="Regenerate packaged Claude/Codex hook commands")
    fix = sub.add_parser("repair", help="Restore forwarding scripts for old open threads")
    fix.add_argument("--cache-root", type=Path, required=True)
    fix.add_argument("old_roots", type=Path, nargs="+")
    args = parser.parse_args()
    result = generate() if args.action == "generate" else repair(args.cache_root, args.old_roots)
    print(json.dumps([str(p) for p in result], indent=2))


if __name__ == "__main__":
    main()
