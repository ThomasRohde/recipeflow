# Release process

## Prepare

1. Start from a clean checkout on the release branch.
2. Reconcile package version, contract versions, and `CHANGELOG.md`.
3. Ensure the lockfile is committed and current.
4. Run the full gate in [AGENTS.md](../AGENTS.md) on Windows and Linux.
5. Regenerate schemas, TypeScript declarations, examples, and every golden artifact.
6. Complete the manual visual checklist and resolve critical or major findings.
7. Review compatibility, accessibility, security, and benchmark evidence.

## Build and inspect

```powershell
uv build
```

Inspect wheel and source archive contents. Install the wheel into a clean environment, then
run import, CLI help, schema export, validation, and SVG/PNG smoke checks. Verify artifact
hashes and ensure no credentials, caches, private keys, or local paths are included.

## Publish

Create a signed or protected `vX.Y.Z` tag from the reviewed commit. The release workflow
re-runs verification, builds once, records provenance, and attaches wheel, source archive,
schemas, declarations, hashes, and release notes. Package-index publication uses trusted
publishing where configured.

## Verify

Install the published version in a clean environment and repeat the public smoke tests.
Compare published hashes with workflow output. Record the release URL, tag, commit, workflow
run, artifacts, and any known limitation.

Never call an unverified local build a released artifact.
