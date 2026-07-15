# yaml2genie

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat)](https://docs.astral.sh/ruff/)
[![uv](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOnyx-Nostalgia%2Fuv%2Frefs%2Fheads%2Ffix%2Flogo-badge%2Fassets%2Fbadge%2Fv0.json&style=flat)](https://docs.astral.sh/uv/)
[![CI](https://github.com/igonro/yaml2genie/actions/workflows/ci.yml/badge.svg)](https://github.com/igonro/yaml2genie/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/igonro/yaml2genie?style=flat)](LICENSE)
<!--
Once configured, add dynamic project badges such as:
![Coverage](https://img.shields.io/codecov/...)]
-->

Compile centralized or explicitly decentralized YAML definitions into
deterministic Databricks Genie Agent `serialized_space` version 2 JSON.

---

## Overview

The compiler supports the documented version 2 fields and rejects unknown
fields instead of discarding them. A source may be one YAML file or a directory
with a required `genie.yaml` manifest that declares `layout: grouped`,
`category-split`, `fully-split`, or `mixed`.

Generated JSON is stable across repeated builds. Explicit valid IDs are
preserved, omitted IDs are generated deterministically, and service-required
collections are sorted without rewriting the source YAML.

## Usage

```bash
# Validate without writing files
uv run yaml2genie validate tests/inputs/minimal.yaml

# Build deterministic JSON; existing files are replaced atomically
uv run yaml2genie build tests/inputs/minimal.yaml --output definition.json
uv run yaml2genie build tests/inputs/grouped_genie --output definition.json

# Check a committed artifact; stale output returns exit code 6
uv run yaml2genie check tests/inputs/minimal.yaml --artifact tests/artifacts/minimal.json

# Convert JSON back to centralized YAML
uv run yaml2genie decompile definition.json --output definition.yaml

# Convert JSON to a source tree or inspect its write plan
uv run yaml2genie decompile definition.json --output genie --layout fully-split
uv run yaml2genie decompile definition.json --output genie --layout mixed --dry-run

# Stream centralized YAML/JSON through stdin/stdout
cat tests/inputs/minimal.yaml | uv run yaml2genie build - --output - --format json
```

The core commands are `validate`, `build`, `decompile`, and `check`. Use
`yaml2genie --help` or `<command> --help` for the complete option list.
`--version` prints the installed version, `--quiet` suppresses successful
operation messages, and `--verbose` prints diagnostic context to stderr.

`build` accepts YAML files or declared source trees and writes JSON by default.
Use `--format yaml` or a `.yaml`/`.yml` output suffix for YAML. `decompile`
accepts a raw serialized definition object or a JSON string that contains that
object, and writes YAML by default. Both commands accept `-` for centralized
stdin/stdout. Source-tree layouts require a directory output and cannot be
streamed.

`--layout central|grouped|category-split|fully-split|mixed` selects the
decompile output organization. `fully-split` writes one item per declared
category directory. `mixed` writes a manifest that explicitly declares every
category as `file` or `items`. Generated item filenames are safe and
deterministic, but identifiers and IDs remain document content rather than
filename-derived data.

The supported source organizations are:

| Layout | Source organization | Manifest requirement |
| --- | --- | --- |
| `central` | One YAML document | None |
| `grouped` | One file per top-level category group | `genie.yaml` with `layout: grouped` |
| `category-split` | One file per serialized category | `genie.yaml` with `layout: category-split` |
| `fully-split` | One YAML file per item under category directories | `genie.yaml` with `layout: fully-split` |
| `mixed` | A declared combination of grouped and split categories | `genie.yaml` with per-category modes |

Missing optional collection files are treated as empty. Files are concatenated
within a declared category; yaml2genie does not deep-merge mappings or apply
last-file-wins behavior. Source paths are part of diagnostics and fallback
identity generation, while explicit IDs remain authoritative.

For source-tree outputs, `--dry-run` prints the complete deterministic file plan
without writing. Existing YAML files or trees are protected; pass `--overwrite`
to replace the requested output atomically. Filename collisions fail before the
existing tree or manifest is changed.

`check` renders the candidate using the selected format and compares it with a
committed artifact without writing. It returns zero when the artifact is current
and exit code 6 with a focused unified diff when it is stale. Source errors use
exit code 2, schema errors 3, semantic errors 4, and output errors 5.

Input errors are reported with their source path and field path, without a
traceback by default. Unknown fields and unsupported schema versions are
rejected; the current release supports serialized definition version 2 only.
The tool validates shape, IDs, ordering, references, documented collection
limits, and output determinism. SQL expressions themselves are not parsed or
validated against a Databricks workspace.

---

## Bundle Integration

Use generated JSON as the `file_path` for a Declarative Automation Bundle Genie
resource. Deployment metadata such as `title` and `warehouse_id` belongs to the
bundle resource, not the serialized Agent definition:

```yaml
resources:
    genie_spaces:
        sales_assistant:
            title: Sales Assistant
            warehouse_id: ${var.warehouse_id}
            file_path: resources/sales_assistant.geniespace.json
```

`file_path` and inline `serialized_space` are mutually exclusive. The
Databricks CLI reads and inlines `file_path` content during deployment; Genie
resources use the direct deployment engine. yaml2genie does not require the
Databricks CLI or workspace credentials. When it is installed in CI, run the
non-destructive `databricks bundle validate` as a deployment smoke test.

---

## Local Development

Follow these steps to get the project running on your machine.

### 1. Prerequisites

Before you begin, make sure you have the following tools installed:

* **`uv`**: The package installer. If you don't have it, install it [here](https://docs.astral.sh/uv/getting-started/installation/).
* **`git`**: To clone the repository.
* **`make`**: To run the project's development commands.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <REPOSITORY_URL>
    cd yaml2genie
    ```

2.  **Set up the project:**
    The Makefile creates the `.venv` environment, installs all development and test dependencies, and installs the `prek` Git hooks.
    ```bash
    make setup
    ```

    Activate the environment if you want commands available directly in your shell:
    ```bash
    # macOS / Linux
    source .venv/bin/activate

    # Windows
    .venv\Scripts\activate
    ```

## Development Workflow

### Makefile Commands

The Makefile provides the main commands for day-to-day development. Run `make help` to see the available targets.

```bash
# Run all configured prek hooks against every file
make check

# Run tests with coverage
make test

# Lint, format, or type-check the project
make lint
make format
make typecheck
make check-cli

# Check formatting without changing files
make format-check

# Build the package distributions
make build

# Remove generated artifacts and caches without touching .venv
make clean

# Upgrade dependencies and prek hook versions
make upgrade
```

Individual tools can also be run through the project environment, for example `uv run prek run --all-files` or `uv run ruff check .`.

### Adding a supported field

Use the checklist in [CONTRIBUTING.md](CONTRIBUTING.md) for changes that extend
the serialized definition. A new field is complete only when its contract
evidence, model shape, normalization behavior, renderer round trip, fixture,
focused tests, and user-facing documentation agree.

---

## Continuous Integration

This project uses [GitHub Actions](https://docs.github.com/en/actions) for
automation. The [CI workflow](.github/workflows/ci.yml) runs on every push and
pull request, with quality checks and unit tests running in parallel. It
installs the locked dependencies with `uv`, runs all `prek` hooks, verifies the
committed CLI artifact, and executes the full test suite with coverage.
