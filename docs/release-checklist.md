# Release Checklist

## Before review

- [x] Confirm the version in `pyproject.toml`, `src/yaml2genie/cli.py`, and the changelog.
- [x] Read the current Databricks version 2 references and update the contract matrix if needed.
- [x] Run `make check`, `make test`, `make lint`, `make typecheck`, `make build`, and `make format-check`.
- [x] Run `make check-cli` and verify the committed artifacts are current.
- [x] Confirm centralized, grouped, category-split, fully-split, and mixed fixtures compile to equivalent normalized JSON.
- [x] Confirm malformed input, unsupported fields, unsupported versions, stale artifacts, and output failures have useful errors.
- [x] Inspect the built wheel and source distribution contents.
- [x] Review `CHANGELOG.md`, README examples, and compatibility limitations.

## Optional deployment smoke test

When the Databricks CLI is available, run `databricks bundle validate` against
the fixture under `tests/inputs/bundle/`. This is non-destructive and does not
replace the offline test suite.

## Owner approval

- [ ] Review the diff and release notes.
- [ ] Approve the release commit.
- [ ] Publish only through the repository's approved release process.

The implementation agent must not publish a package or create a release tag.
