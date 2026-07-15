# Phase 9 Release Hardening

- Coverage is reported by `make test` and must remain at least 90 percent.
- Regression tests cover deterministic JSON escaping, LF output, source-tree plan ordering, and preservation of an existing tree when staging fails.
- Contributor changes that add a Databricks field must update contract evidence, models, normalization, rendering, fixtures, focused tests, and docs together.
- Releases require owner review of `docs/release-checklist.md`; the implementation agent does not publish or tag releases.
