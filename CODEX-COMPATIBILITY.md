# Codex compatibility branch

`codex-compatible` is a repaired distribution of Microsoft Azure Skills 1.2.73, based on upstream commit `f07c05364353925f7c8b0e474aa95afa291bce54`.

The internal `azure-app-onboard` prepare, scaffold and deploy documents are named `PHASE.md`, with incoming references updated in both distributed copies. This prevents Codex from discovering them as malformed standalone skills. Workflow bodies, MCP configuration and telemetry behavior are preserved. Plugin manifests carry matching `+codex.<timestamp>` version suffixes so Codex installs a fresh cache entry.

The maintained-source repair is submitted as [Microsoft PR #3279](https://github.com/microsoft/GitHub-Copilot-for-Azure/pull/3279), addressing [issue #3109](https://github.com/microsoft/GitHub-Copilot-for-Azure/issues/3109).

## Install and refresh

When replacing the existing Microsoft marketplace, remove its source registration first. This keeps the plugin configuration but removes the old marketplace snapshot. Then add the repaired source and reinstall:

```sh
codex plugin marketplace remove azure-skills
codex plugin marketplace add jtalk22/azure-skills --ref codex-compatible
codex plugin add azure@azure-skills
codex plugin add azure-local-skills@azure-skills
codex plugin add foundry-iq-skills@azure-skills
```

Subsequent refreshes use this repaired branch:

```sh
codex plugin marketplace upgrade azure-skills
codex plugin add azure@azure-skills
codex plugin add azure-local-skills@azure-skills
codex plugin add foundry-iq-skills@azure-skills
```

The marketplace and plugin retain their existing identities. Start a new Codex thread after reinstalling to load the refreshed skill and tool catalog.

## Hooks surviving plugin updates

Older Codex threads can retain expanded hook commands pointing at deleted cache versions. For example, `bash ".../azure/1.2.72/hooks/scripts/track-telemetry.sh"` exits 127 after that directory disappears. Reinstalling the current plugin alone does not repair a command already held by an open thread.

All five distributed plugins now embed a small resolver in their Claude/Codex hook commands. It uses `/bin/bash`, prefers the requested installation when present, and otherwise selects a sibling plugin version with the most recently modified manifest. Both a genuine manifest and telemetry script must exist. The resolver executes the real script at its real path, preserving stdin, exit status and telemetry preferences. It reports failure if no installation remains. No background process is required. Cursor and Copilot hook formats are unchanged.

For threads that loaded the original commands, restore forwarding scripts at the specific missing version paths after reinstalling. From this repository, substitute the paths reported by the failed hooks:

```sh
python3 tools/codex_hook_compat.py repair \
  --cache-root "$HOME/.codex/plugins/cache/azure-skills" \
  "$HOME/.codex/plugins/cache/azure-skills/azure/1.2.72"
```

This adds only a forwarding script; it does not duplicate skill trees or overwrite installed plugin code. The same resolver serves both the packaged command and these temporary compatibility paths. A full marketplace removal can delete the forwarding paths again; restore them afterward if legacy threads are still open. New threads load the resilient command.

Codex requires changed hook definitions to be reviewed and trusted again. Review the installed command in `/hooks` and approve its exact definition; do not disable hooks or bypass trust globally. See [Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).

To regenerate and validate commands after editing the resolver:

```sh
python3 tools/codex_hook_compat.py generate
python3 -m unittest discover -s tools -p 'test_codex_hook_compat.py' -v
```

The tests exercise cache deletion, multiple replacements, paths containing spaces, actual stdin/exit-status forwarding, safe legacy repair, missing installations, and consistency across all six distributed hook files.

## Future upstream updates

This branch deliberately does not follow Microsoft's `main` automatically. Before publishing an upstream update here, preserve the phase-document fix and hook resolver, validate every distributed `SKILL.md`, verify phase references resolve, run the hook compatibility tests, and keep the root Azure projection identical to `.github/plugins/azure-skills/`. Update the matching manifest version suffixes for changed plugins before reinstalling. Do not publish an unvalidated upstream sync over this branch.

Once Microsoft's released marketplace includes the fix, remove the repaired marketplace registration with `codex plugin marketplace remove azure-skills`, add the official source with `codex plugin marketplace add microsoft/azure-skills --ref main`, then reinstall, and verify a fresh Codex `skills/list` response has no errors.

Reference: [OpenAI plugin marketplace documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).
