# Codex compatibility branch

`codex-compatible` is a repaired distribution of Microsoft Azure Skills 1.2.73, based on upstream commit `f07c05364353925f7c8b0e474aa95afa291bce54`.

The internal `azure-app-onboard` prepare, scaffold and deploy documents are named `PHASE.md`, with incoming references updated in both distributed copies. This prevents Codex from discovering them as malformed standalone skills. All workflow bodies, MCP configuration, hooks and other plugins are preserved. Azure plugin manifests carry matching `+codex.<timestamp>` version suffixes so Codex installs a fresh cache entry.

The maintained-source repair is submitted as [Microsoft PR #3279](https://github.com/microsoft/GitHub-Copilot-for-Azure/pull/3279), addressing [issue #3109](https://github.com/microsoft/GitHub-Copilot-for-Azure/issues/3109).

## Install and refresh

When replacing the existing Microsoft marketplace, remove its source registration first. This keeps the plugin configuration but removes the old marketplace snapshot. Then add the repaired source and reinstall:

```sh
codex plugin marketplace remove azure-skills
codex plugin marketplace add jtalk22/azure-skills --ref codex-compatible
codex plugin add azure@azure-skills
```

Subsequent refreshes use this repaired branch:

```sh
codex plugin marketplace upgrade azure-skills
codex plugin add azure@azure-skills
```

The marketplace and plugin retain their existing identities. Start a new Codex thread after reinstalling to load the refreshed skill and tool catalog.

## Future upstream updates

This branch deliberately does not follow Microsoft's `main` automatically. Before publishing an upstream update here, preserve the phase-document fix, validate every distributed `SKILL.md`, verify phase references resolve, and keep the root `skills/` projection identical to `.github/plugins/azure-skills/skills/`. Update the matching Azure manifest version suffixes before reinstalling. Do not publish an unvalidated upstream sync over this branch.

Once Microsoft's released marketplace includes the fix, remove the repaired marketplace registration with `codex plugin marketplace remove azure-skills`, add the official source with `codex plugin marketplace add microsoft/azure-skills --ref main`, then reinstall, and verify a fresh Codex `skills/list` response has no errors.

Reference: [OpenAI plugin marketplace documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).
