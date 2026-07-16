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

## First TestPyPI release

1. Configure the `testpypi` GitHub environment and TestPyPI trusted publisher.
2. Run `make release-dry-run`, then use `make release-patch` (or another
   increment) to create the release commit and `vX.Y.Z` tag.
3. Push the commit and tag to GitHub. The production workflow should pause at
   the `pypi` environment approval gate.
4. Run the `TestPyPI` workflow manually from the release tag. Do not run it
   from `main` or another branch.
5. Verify the package from TestPyPI in an isolated environment:

   ```bash
   uv run --isolated --no-project \
       --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ \
       --with yaml2genie -- yaml2genie --version
   ```

6. Configure the `pypi` GitHub environment with required reviewers and the
   PyPI trusted publisher, then approve the paused tag workflow to publish the
   version to PyPI.

TestPyPI and PyPI do not allow re-uploading the same version. Use a new
version for every retry.
