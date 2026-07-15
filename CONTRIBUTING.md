# Contributing

## Development setup

The project requires Python 3.12 and `uv`.

```bash
make setup
```

Run focused commands while working, then run the complete quality gate before
opening a change:

```bash
make test
make lint
make typecheck
make format-check
make build
make check
```

The test command enforces the coverage floor configured in `pyproject.toml`.
Tests should verify behavior at the compiler, renderer, loader, or CLI boundary;
avoid coupling them to private helper functions.

## Adding a Databricks field

Keep a field change in one reviewable change and follow this order:

1. Update the contract matrix in `.agents/docs/databricks-genie-contract.md`
   with primary-source evidence, requiredness, limits, ordering, and support
   state.
2. Add or update the strict input and normalized output models in
   `src/yaml2genie/models.py`.
3. Extend normalization only when the field has an explicit sorting,
   uniqueness, identity, reference, or limit rule.
4. Verify JSON and YAML rendering, including centralized and relevant source
   tree round trips.
5. Add or update an independent fixture or artifact for the documented shape.
6. Add focused tests for valid output, invalid input, and any regression or
   deterministic behavior introduced by the change.
7. Update `README.md`, `CONTEXT.md`, or an ADR when the public contract or
   domain vocabulary changes.

Unknown fields must remain rejected unless a reviewed schema policy changes
that behavior. Do not add deployment calls or workspace credentials to the
compiler.

## Commit and review

Use a conventional commit message such as `feat: support metric view fields`.
Keep generated artifacts deterministic and do not commit local build, coverage,
or virtual-environment files. A release requires owner review after the
checklist in `docs/release-checklist.md` is complete.
