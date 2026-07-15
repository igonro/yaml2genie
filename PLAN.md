# yaml2genie Implementation Roadmap

**Status:** Proposed

**Goal:** Build a production-quality Typer CLI that turns human-friendly YAML representations of Databricks Genie Agents into valid, deterministic `serialized_space` JSON, and converts that JSON back to YAML. The tool must support a readable centralized document first, then several explicitly defined decentralized directory layouts, while keeping all layouts on one validated domain model.

This roadmap is deliberately incremental. Each phase has a narrow deliverable, tests, and a review checkpoint. A checkpoint means: finish the listed tests, create a conventional commit, and pause for user review before starting the next phase. No checkpoint commit is part of this planning task.

## Working Contract

- The canonical content contract is Databricks `serialized_space` version 2. It is separate from the outer Genie deployment resource and its title, warehouse, permissions, lifecycle, and parent path.
- The first JSON output is the raw serialized definition object, not an escaped API response. It must be usable as the `file_path` content of a Declarative Automation Bundle Genie resource.
- Bundle `file_path` and inline `serialized_space` are mutually exclusive inputs. The Databricks CLI inlines file content during deployment and rejects a resource that sets both.
- Use “Genie Agent” in yaml2genie-facing language while retaining service-owned names such as `genie_space`, `space_id`, and `serialized_space` exactly where Databricks still exposes them.
- YAML may omit IDs and may use a scalar where Databricks represents a one-element string array. The source order is author-facing; exported JSON applies Databricks' required ordering.
- Explicit valid IDs are preserved. Missing IDs use deterministic lowercase hexadecimal IDs, preferably derived from a stable YAML key or source identity and otherwise from canonical item content. This makes repeated builds stable and reviewable.
- Invalid YAML, invalid JSON, unsupported schema versions, duplicate identities, malformed joins, and non-repairable limits fail with human-readable errors that identify the input path and field.
- Official prose validation rules outrank examples when Databricks' own examples conflict with those rules. Example presence establishes shape, not requiredness; every field in the contract matrix must be marked documented, example-only, inferred, or unknown.
- Initial releases do not deploy to Databricks or make network calls. They produce and validate files that another Declarative Automation Bundle or API client can deploy.

See [CONTEXT.md](CONTEXT.md), the [Databricks contract note](.agents/docs/databricks-genie-contract.md), and the proposed decisions in [ADR 0001](docs/adr/0001-schema-first-serialized-core.md) and [ADR 0002](docs/adr/0002-deterministic-generated-ids.md).

## Current Baseline

- The repository is a Python 3.12 package skeleton with a placeholder `main`, one dummy test, and `uv`/Ruff/Pyright/pytest conventions.
- Package metadata still contains template dependencies, extras, descriptions, and stale `genie2yaml` README commands. These are baseline cleanup, not product requirements.
- The preliminary `genie-pnl` repository demonstrates useful patterns: strict Pydantic models, safe YAML loading, scalar-to-list normalization, deterministic UUID5-style IDs, reference validation, canonical JSON rendering, atomic writes, diffs, and Typer tests.
- That preliminary project is intentionally incomplete for this universal tool. It omits `config`, sample questions, metric views, SQL functions, benchmarks, and several documented fields. Its mandatory column configs, snippet fields, CRLF splitting, grouped path conventions, and content-derived IDs are POC choices, not Databricks contract facts. Reuse patterns only after a focused test proves they match this roadmap.

## Target Shape

Keep the public seam small and deep:

- `DefinitionDocument`: the validated serialized Agent content.
- `SourceLoader`: an adapter that reads one centralized file or one declared source tree and returns a document candidate.
- `Normalizer`: pure technical fulfillment for IDs, sorting, uniqueness, references, and limits.
- `Renderer`: deterministic JSON and human-friendly YAML output.
- Typer commands: thin orchestration that selects a loader, invokes normalization, writes output, and maps domain errors to stable exit codes.

The planned CLI interface is `validate` and `build` in Phase 1, `decompile` in Phase 3, and `check` in Phase 7. Later phases extend accepted layouts and fields without creating parallel command families.

Suggested package areas are `models`, `loaders`, `normalization`, `rendering`, `errors`, and `cli` under `src/yaml2genie`. Do not expose every internal Pydantic class as a public CLI contract. Tests should cross the loader/normalizer/renderer seam and use direct unit tests only for genuinely pure rules.

## Phase 0: Freeze the Contract and Fixtures

**Outcome:** A small, reviewable contract matrix and fixture strategy exist before feature work begins.

- [x] Convert `.agents/docs/databricks-genie-contract.md` into a field-by-field v2 matrix with source URL, source retrieval date, JSON path, observed type, explicit requiredness, limits, sort key, uniqueness scope, allowed YAML shorthand, Phase 1 support status, and confidence (`documented`, `example-only`, `inferred`, or `unknown`).
- [x] Record upstream contradictions as test/design inputs: current v2 guidance coexists with stale v1 examples; some examples contain non-hex IDs; SQL functions participate in ID sorting and uniqueness but are omitted from the prose list of ID-required fields.
- [x] Define whether each field is explicitly required, explicitly optional, or unresolved, and whether it is a scalar, string-list, object-list, or bounded collection. Do not infer requiredness from an example or the preliminary POC. For unresolved fields, state the conservative Phase 1 behavior instead of guessing.
- [x] Create fixture directories under `tests/inputs/` and `tests/artifacts/`. Include a minimal supported centralized YAML, its expected JSON, malformed YAML, an invalid ID, unsorted input, duplicate IDs in each uniqueness scope, duplicate column identity, malformed join, unsupported field, and unsupported version.
- [x] Add one small v2 JSON fixture containing every field Phase 1 claims to support and annotate its provenance. Keep the large Databricks example and business-specific POC data out of unit tests.
- [x] Audit `CONTEXT.md` against the matrix, add only missing domain terms, and link the two architectural decisions in `docs/adr/`; do not duplicate field specifications in the glossary.
- [x] Decide the supported JSON input forms for the first release: raw serialized object and escaped serialized string; defer automatic extraction from a full Get API response until the import phase.
- [x] Freeze the Phase 1 unknown/unsupported-field behavior. Default to strict rejection with an exact path; do not silently discard fields that only Phase 4 will support.

**Tests and acceptance:** `tests/test_fixture_inventory.py` enumerates every Phase 0 fixture by relative path and asserts it exists; every matrix row has a support state and confidence; every normative rule has a primary-source URL; requiredness is `unknown` unless the source states it; the bundle note says `file_path` and inline `serialized_space` are mutually exclusive.

**Checkpoint 0:** Commit `docs: define Genie contract and roadmap`; user reviews the contract matrix and the meaning of centralized YAML.

## Phase 1: Centralized YAML to JSON MVP

**Outcome:** One YAML file whose keys mirror the supported serialized definition compiles to deterministic JSON.

This phase starts only after Checkpoint 0 accepts the matrix. The matrix is authoritative if its approved field list differs from the provisional list below.

- [x] Replace the placeholder package entry point with a Typer application and a testable application factory or command object. Keep command functions thin.
- [x] Remove placeholder runtime dependencies/extras and stale package metadata, then add Typer, Pydantic v2, and a safe YAML loader with `uv add`/`uv remove`. Keep development/test tools in the existing dependency groups; do not hand-edit dependency lists.
- [x] Implement separate strict input and normalized-output models for `version`, `config.sample_questions`, `data_sources.tables`, column configurations, `instructions.text_instructions`, `example_question_sqls`, `join_specs`, and `sql_snippets.filters`, `expressions`, and `measures`. Enforce `version == 2`. Metric views, SQL functions, and benchmarks are explicitly deferred to Phase 4 and fail with an unsupported-field path rather than disappearing.
- [x] Normalize only the string-list fields approved in the Phase 0 matrix from scalar YAML strings. Define newline handling as a yaml2genie policy and test LF, CRLF, trailing newline, blank lines, and multi-element arrays; do not copy the POC's CRLF splitting as an undocumented Databricks requirement.
- [x] Make IDs optional at the YAML boundary. Preserve explicit valid IDs; generate deterministic valid IDs for omissions; reject collisions; and require IDs in the normalized model. Do not emit `null` values.
- [x] Sort every supported collection by the documented key in normalized output and enforce the supported portion of each uniqueness scope. Phase 1 covers sample-question IDs and its implemented instruction categories; Phase 4 extends those same scopes with benchmarks and SQL functions. Preserve source order in memory and on disk.
- [x] Implement `yaml2genie validate INPUT` and `yaml2genie build INPUT --output OUTPUT`. `validate` must never write; `build` must use UTF-8, stable indentation, stable newline behavior, and atomic replacement.
- [x] Define output behavior before implementation: repeated `build` updates the requested artifact atomically; failures leave an existing artifact unchanged. Add `--stdout` only after file output and stderr/error behavior are covered. Avoid a configuration language or deployment command.

**Tests and acceptance:** A centralized example compiles to an expected artifact whose collections match every Phase 1 sort key in the matrix; omitted IDs are stable across separate processes; explicit IDs survive unchanged; version 1 and unknown versions fail; unsorted YAML produces sorted JSON without changing the YAML; repeated builds are byte-for-byte identical; invalid syntax, deferred fields, collisions, and Pydantic errors exit non-zero; failed builds do not alter output; CLI tests use `typer.testing.CliRunner`; the dummy test is removed.

**Checkpoint 1:** Commit `feat: compile centralized Genie YAML`; user reviews the first YAML shape and generated JSON.

## Phase 2: Technical Normalization and Human-Friendly Errors

**Outcome:** The deployable MVP's technical normalization is complete, centrally owned, and reports precise semantic failures.

- [x] Extend the pure identity module introduced in Phase 1 with optional YAML-only stable keys/source identities. Use canonical item content as fallback; exclude generated IDs and presentation-only metadata from the identity; document which edits change fallback IDs; rerun all Phase 1 stability tests unchanged.
- [x] Detect duplicate stable keys, generated-ID collisions, and explicit/generated collisions with both source locations in the error. Never silently add a random suffix. UUID v7 remains out of scope while deterministic rebuilds are the accepted requirement.
- [x] Centralize collection descriptors for sort key, ID requirement, uniqueness scope, and source path so later schema categories do not duplicate normalization logic. Sort only normalized output and never rewrite source files.
- [x] Validate explicit IDs as exactly 32 lowercase hexadecimal characters with no hyphens. Reject duplicate IDs across all supported instruction categories and enforce the separate question-ID scope; expand these scopes as Phase 4 adds categories.
- [x] Validate unique data-source identifiers, unique `(data_source_identifier, column_name)` pairs, and duplicate logical items across decentralized inputs when those loaders arrive.
- [x] Enforce documented bounds: 25,000 characters per string element, 10,000 items per repeated field, one text instruction, required non-empty snippet SQL, and any numeric SQL/data-source limits that become documented. Do not invent numeric limits for current workspace-specific or unspecified constraints. Report path, limit, and measured value.
- [x] Validate three-level data-source identifiers. Validate join endpoints, alias references, exactly two SQL elements, and the supported relationship annotation values. Use a small parser/grammar for the documented join envelope; do not attempt to parse arbitrary SQL in the CLI.
- [x] Define a structured error taxonomy for source parse errors, schema errors, semantic validation errors, and output errors. Typer should render concise messages and stable non-zero exit codes without leaking tracebacks by default.

**Tests and acceptance:** Each documented automatic repair has a before/after fixture; each non-repairable violation has an assertion on the useful field path; generated IDs remain stable across processes; all output collections are verified sorted and unique.

**Checkpoint 2:** Commit `feat: normalize and validate Genie definitions`; user reviews ID identity rules, sorting, and error wording.

## Phase 3: JSON to Centralized YAML

**Outcome:** A valid serialized definition can be inspected and edited as one readable YAML document.

- [x] Implement `yaml2genie decompile INPUT --output OUTPUT`, rejecting malformed JSON and model-invalid JSON with the same structured errors as the YAML path.
- [x] Accept the raw JSON object and a JSON string containing the serialized object. Keep full API-response extraction behind an explicit mode or a later phase so ambiguous objects are not silently interpreted.
- [x] Preserve explicit and generated IDs by default. Preserve all supported optional fields and never silently drop data during decompilation.
- [x] Render human-friendly YAML: use block scalars for multiline content, concise scalars for one-element string lists where safe, stable field ordering, and explicit lists when scalar coercion would be ambiguous.
- [x] Verify semantic round trips rather than textual equality: `normalize(compile(decompile(json)))` must equal the normalized source JSON. Add invalid JSON, missing version, and unsupported-version fixtures.
- [x] Reject valid-v2-but-not-yet-supported fields before creating output. Write atomically and require an explicit overwrite option when replacing hand-edited YAML.

**Tests and acceptance:** Official-shape fixtures decompile into YAML that follows the documented block-scalar, scalar/list, field-order, indentation, and newline policy, then compile back to identical normalized JSON; malformed or unsupported JSON fails before any output file is created.

**Checkpoint 3:** Commit `feat: decompile Genie JSON to centralized YAML`; user reviews the round-trip output and scalar/block-scalar conventions.

## Phase 4: Complete Documented Version-2 Coverage

**Outcome:** The centralized model covers the full documented v2 definition rather than the preliminary POC subset.

- [x] Add `data_sources.metric_views` using the documented source and column configuration shape, with separate identifiers and sorting checks.
- [x] Add `instructions.sql_functions`, including `(id, identifier)` ordering and duplicate checks.
- [x] Add all documented example SQL parameter fields, default values, usage guidance, comments, aliases, display names, synonyms, and instruction fields without inventing output keys.
- [x] Add `benchmarks.questions` and benchmark answers. Enforce one answer per question and `format: SQL`, and extend the existing sample-question ID uniqueness scope across both categories.
- [x] Compare the model against current Create/Get/Update examples. Per owner direction, exclude the incomplete external POC from Phase 4 acceptance. Add a fixture for every field that was previously omitted or discarded.
- [x] Keep version 2 as an explicit model invariant. Add a version-dispatch registry only when a second supported version or a real migration adapter exists.
- [x] Revisit the Phase 0 unknown-field policy against schema-drift evidence. Keep strict rejection as the default; add preservation/warning mode only if round-trip tests prove it cannot hide typos or silently bypass validation.

**Tests and acceptance:** No documented v2 field is silently dropped; model dumps and re-loads preserve supported fields; all documented validation rules have focused tests; version errors name the supported versions.

**Checkpoint 4:** Commit `feat: support documented Genie schema v2`; user reviews the compatibility matrix and unknown-field policy.

## Phase 5: Explicit Decentralized YAML Layouts

**Outcome:** The same domain model can be populated from progressively more granular YAML without hidden merge behavior.

- [x] Define a required root manifest, for example `genie.yaml`, containing the serialized version and explicit layout metadata. Do not infer meaning from arbitrary filenames when a manifest can state it.
- [x] Implement layout level 1: grouped files such as `sources.yaml`, `instructions.yaml`, `examples.yaml`, and optional `benchmarks.yaml`.
- [x] Implement layout level 2: category files such as `sources/tables.yaml`, `sources/metric_views.yaml`, `examples/joins.yaml`, `examples/queries.yaml`, `examples/filters.yaml`, `examples/expressions.yaml`, and `examples/measures.yaml`. Use contract names such as `metric_views`, not ambiguous aliases such as `views` or POC-only `calculated_fields`.
- [x] Define collection semantics precisely: collection files concatenate into one category; singleton values come from the manifest; missing optional files mean empty collections; duplicate identifiers/IDs are errors; no deep merge or last-file-wins behavior.
- [x] Make discovery deterministic and independent of filesystem enumeration. Include source-relative paths in errors and in fallback stable identities.
- [x] Keep level 1 and level 2 loaders as adapters that return the same candidate document consumed by Phase 2. Do not duplicate semantic validation in each loader.
- [x] Add representative fixtures named `centralized_genie.yaml`, `grouped_genie/`, and `category_split_genie/`, including unsorted filenames and cross-file references.

**Tests and acceptance:** Each decentralized fixture produces the same normalized JSON as its centralized equivalent; missing optional files, duplicate items, unknown categories, and broken references have focused tests.

**Checkpoint 5:** Commit `feat: load grouped Genie YAML layouts`; user reviews manifest names and merge semantics.

## Phase 6: Fully Split Layouts and JSON Export to Source Trees

**Outcome:** Users can choose one-file-per-item layouts and can decompile JSON into any supported source organization.

- [x] Implement layout level 3: one YAML file per data source or content item under declared category directories. Require a stable key or derive one from the relative path; never use a fragile list index as identity.
- [x] Implement layout level 4 mixed trees, where some categories are grouped and others are split. The manifest must declare each category's source mode so the loader remains predictable.
- [x] Add `decompile --layout central|grouped|category-split|fully-split|mixed` with an explicit manifest template. Use safe deterministic filenames and report collisions instead of overwriting.
- [x] Preserve IDs when splitting; do not use filenames as output JSON identifiers. Ensure two distinct items cannot collapse to one filename.
- [x] Add staged directory replacement, overwrite protection, and a dry-run file plan before changing a source tree. A failure must leave both existing files and the manifest unchanged.
- [x] Add all four decentralization levels under `tests/inputs/` and compare their normalized output to one artifact. Include a mixed-layout round trip.

**Tests and acceptance:** Every supported layout can compile and decompile; all layouts are semantically equivalent; file names and manifests are deterministic; collision and overwrite tests are present.

**Checkpoint 6:** Commit `feat: support fully decentralized Genie layouts`; user reviews the generated tree and overwrite behavior.

## Phase 7: Production CLI Experience

**Outcome:** The tool feels like a dependable CLI rather than a collection of library entry points.

- [ ] Finalize commands and help text: `validate`, `build`, `decompile`, and `check` are the core set. `check` compares generated output with a committed artifact and prints a focused diff without writing.
- [ ] Support explicit `--layout`/`--format` options plus safe auto-detection where it is unambiguous. Define stdin/stdout behavior, path handling, exit codes, and overwrite flags in the help and README.
- [ ] Add version output, quiet mode, optional verbose diagnostics, and readable Rich/Typer errors while keeping non-interactive CI output stable. Do not make color or network access mandatory.
- [ ] Add shell-level CLI integration tests for success, invalid input, stale artifact, dry run, and output path failures. Keep pure model tests separate from command tests.
- [ ] Update the package entry point, README installation/examples, Makefile targets, and CI instructions to use `yaml2genie` consistently. Remove skeleton references such as the placeholder greeting and stale `genie2yaml` command names.

**Tests and acceptance:** `uv run pytest`, Ruff, Pyright, and the documented Make targets pass in a clean environment; every command has useful `--help`; stale output fails `check` with a non-zero exit code and a reviewable diff.

**Checkpoint 7:** Commit `feat: ship production yaml2genie CLI`; user reviews command UX and README examples.

## Phase 8: Bundle Compatibility and Future Schema Changes

**Outcome:** The generated artifact is easy to place in a Declarative Automation Bundle and the project can evolve when Databricks changes the contract.

- [ ] Add a small bundle fixture showing `resources.genie_spaces.<name>.file_path` with `title` and `warehouse_id`, clearly separating it from the serialized content. Do not require Databricks credentials in tests.
- [ ] Document that `file_path` and inline `serialized_space` are mutually exclusive, that file content is inlined during deployment, and that the resource uses the direct deployment engine.
- [ ] Add a schema compatibility check against a checked-in official-shape fixture and, when available in CI, a non-destructive `databricks bundle validate` smoke test. Keep the package usable without the Databricks CLI.
- [ ] Re-read the primary Databricks references before every schema-version feature. Update the contract note, compatibility matrix, fixtures, and migration adapter together.
- [ ] Define a deprecation policy for old names such as Genie Space and for fields removed or renamed by Databricks. Never silently reinterpret a versioned document.

**Tests and acceptance:** A generated JSON fixture can be referenced by a bundle example; offline tests remain deterministic; version and migration behavior is covered without network calls.

**Checkpoint 8:** Commit `docs: document bundle compatibility and schema policy`; user reviews deployment assumptions.

## Phase 9: Release Hardening

**Outcome:** The project is publishable and maintainable by contributors who did not design the first version.

- [ ] Add coverage reporting and enforce a sensible minimum only after the fixture matrix is complete; prioritize behavior coverage over line-count chasing.
- [ ] Add regression tests for every bug found during implementation, especially ID stability, line endings, JSON escaping, source-tree ordering, and no-partial-write failures.
- [ ] Run the full quality gate through `make check`, `make test`, `make lint`, `make typecheck`, `make build`, and `make format-check` using `uv`.
- [ ] Document supported Python versions, installation, command examples, centralized and all decentralized layouts, error handling, bundle integration, and schema-version limitations.
- [ ] Add a concise contributor guide for adding a new Databricks field: update the model, fixture, normalizer if needed, renderer, docs, and focused tests in one change.
- [ ] Prepare a release checklist and changelog entry. Do not publish or commit from an implementation agent without the repository owner’s review at the final checkpoint.

**Final acceptance:** A clean checkout can install the package, validate all example inputs, build deterministic JSON artifacts, decompile them, reproduce equivalent output from every supported YAML layout, and explain every deliberate compatibility limitation.

## Review of This Plan

The roadmap covers every requested capability without making the first implementation depend on later layout machinery:

- Typer CLI: Phases 1 and 7.
- Pydantic validation: Phases 1, 2, and 4.
- YAML to JSON: Phases 1, 2, 5, and 6.
- JSON to YAML: Phases 3 and 6.
- Technical fulfillment: deployable ID/sort/uniqueness basics in Phase 1, semantic hardening in Phase 2, and complete v2 category scopes in Phase 4.
- Centralized to fully decentralized progression: Phases 1, 5, and 6.
- Fixtures and meaningful unit/CLI tests: every phase, with the required `tests/inputs/` and `tests/artifacts/` structure.
- Databricks bundle compatibility: Phase 8, with no unnecessary deployment client in the core tool.
- Documentation and domain decisions: `CONTEXT.md`, `.agents/docs/databricks-genie-contract.md`, and `docs/adr/`.

### Risks to keep visible

- Databricks does not publish a single stable JSON Schema for all Genie Agent versions. The official examples and validation rules must remain pinned in fixtures and revisited when the docs change.
- Deterministic IDs need a stable identity rule. The implementation must make that rule visible rather than pretending content-based fallback IDs never change.
- A full API response, a bundle resource, an escaped `serialized_space` string, and a raw serialized object are different representations. Auto-detection must not silently merge their fields.
- Strict unknown-field rejection protects against typos but can delay adoption of new Databricks fields. The compatibility matrix and schema-version policy must govern that trade-off; no supported field may be silently dropped.
- Current Databricks documentation is internally inconsistent: v2 rules coexist with stale v1 and invalid-ID examples. Fixture provenance and confidence labels are required to keep examples from overriding explicit validation rules.
- A successful local build proves shape and normalization, not that a particular workspace accepts every business-specific SQL expression. Deployment validation remains an external integration concern.
