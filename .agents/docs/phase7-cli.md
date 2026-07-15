# Phase 7 CLI contract

The production command set is `validate`, `build`, `decompile`, and `check`.
Centralized commands accept `-` for stdin/stdout. `build` emits JSON by default;
`--format yaml` or a YAML output suffix selects YAML. `check` never writes and
returns exit code 6 when the generated artifact differs from the committed
artifact. Source, schema, semantic, and output failures use exit codes 2, 3, 4,
and 5 respectively.

Global `--version`, `--quiet`, and `--verbose` options are available. Source
tree decompilation remains directory-only and uses `--layout`; `--dry-run`
prints its deterministic file plan.
