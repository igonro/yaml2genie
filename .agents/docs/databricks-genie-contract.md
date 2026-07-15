# Databricks Genie Agent Contract

**Researched:** 2026-07-15 against documentation last updated 2026-07-14.

This is an evidence ledger for `PLAN.md`, not a substitute for the upstream
documentation. Databricks does not publish a standalone, stable JSON Schema for
the serialized definition. Examples establish shape, while prose validation
rules establish constraints; neither should be used to invent requiredness.

## Primary sources

- [Use the Genie Agents API](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
- [Create Genie Space](https://docs.databricks.com/api/workspace/genie/createspace)
- [Get Genie Space](https://docs.databricks.com/api/workspace/genie/getspace)
- [Update Genie Space](https://docs.databricks.com/api/workspace/genie/updatespace)
- [Bundle Genie resource](https://docs.databricks.com/gcp/en/dev-tools/bundles/resources#genie_space)
- [Official Genie bundle example](https://github.com/databricks/bundle-examples/tree/main/knowledge_base/genie_space_nyc_taxi)
- [Databricks CLI Genie resource implementation](https://github.com/databricks/cli/blob/main/bundle/config/mutator/resourcemutator/configure_genie_space_serialized_space.go)

## Documented rules

These statements are explicit in current first-party prose or API field
descriptions.

### Representations

- New definitions require `version: 2`.
- The management API carries `serialized_space` as an escaped JSON string.
	Create requires it; Update treats it as a full replacement when supplied; Get
	includes it only when `include_serialized_space=true`, which requires at least
	`CAN EDIT`.
- The raw, unescaped JSON object is the content expected by a bundle
	`.geniespace.json` `file_path`.
- API/deployment fields such as `title`, `description`, `warehouse_id`,
	`parent_path`, `etag`, lifecycle, and permissions are not members of the
	serialized definition.
- In bundles, `file_path` and inline `serialized_space` are two mutually
	exclusive inputs. The CLI reads the file and inlines its content during
	deployment. Setting both is rejected; neither takes precedence.
- Genie bundle resources require the direct deployment engine. It is the
	default for new deployments in Databricks CLI 1.3.0 and later.

### Shape and constraints

- Current examples contain `config.sample_questions`, `data_sources.tables`,
	`data_sources.metric_views`, `instructions.text_instructions`,
	`example_question_sqls`, `sql_functions`, `join_specs`, `sql_snippets`
	(`filters`, `expressions`, and `measures`), and `benchmarks.questions`.
- Every documented ID field is a 32-character lowercase hexadecimal string
	without hyphens.
- The ID validation list explicitly names sample questions, text instructions,
	example SQL questions, joins, all three SQL snippet categories, and benchmark
	questions. SQL-function examples contain IDs, and sorting/uniqueness rules
	include them, although the prose ID-required list omits them.
- Collections must arrive pre-sorted: tables and metric views by `identifier`;
	column configurations by `column_name`; question, instruction, join, snippet,
	and benchmark collections by `id`; SQL functions by `(id, identifier)`.
- Sample-question and benchmark-question IDs share one uniqueness scope. All
	instruction categories, including SQL functions and snippets, share another.
	Column configuration identity is `(table_identifier, column_name)`.
- Individual string elements are limited to 25,000 characters, repeated fields
	to 10,000 items, and an Agent to one text-instruction item. Data-source counts
	are workspace-specific. SQL content has limits, but the page does not state
	numeric values.
- Table identifiers use `catalog.schema.table`. The prose does not separately
	state whether metric-view and SQL-function identifiers follow the same rule.
- A join's `sql` has exactly two elements: a condition using backtick-quoted
	endpoint aliases and `--rt=FROM_RELATIONSHIP_TYPE_<CARDINALITY>--`, where the
	cardinality is `MANY_TO_ONE`, `ONE_TO_MANY`, `ONE_TO_ONE`, or `MANY_TO_MANY`.
	Multi-column relationships use separate join specs.
- Each benchmark question has exactly one answer with `format: SQL`. Filter,
	expression, and measure SQL fields cannot be empty.

## Shape evidence, not requiredness

The full v2 example shows the following fields, but the prose does not provide a
complete required/optional matrix:

- source `description` and `column_configs`; column `description`, `synonyms`,
	`exclude`, `enable_format_assistance`, and `enable_entity_matching`;
- example SQL `question`, `sql`, `parameters`, and `usage_guidance`; parameter
	`name`, `type_hint`, `description`, and `default_value.values`;
- join endpoints with `identifier` and `alias`, plus `comment` and `instruction`;
- snippet `alias`, `sql`, `display_name`, `synonyms`, `comment`, and
	`instruction`;
- benchmark answer `content`.

Phase 0 must classify each field as explicitly required, explicitly optional,
example-only/unknown, or deferred. An example's presence is not proof that a
field is required, and its absence is not proof that a field is forbidden.

## Upstream contradictions and unknowns

- The conversation page says to use version 2, but some request/retrieval
	examples on the same page still show version 1.
- Some narrative examples contain IDs with letters outside hexadecimal, despite
	the explicit lowercase-hex validation rule. The validation rule takes
	precedence for yaml2genie.
- SQL functions participate in ID sorting and uniqueness but are omitted from
	the explicit list of fields requiring IDs. Treat this as unresolved until a
	fixture is checked against a current export or API validation.
- Numeric SQL-length and workspace-specific data-source limits are not exposed.
- The docs describe the section shapes but do not clearly declare whether empty
	`config`, `data_sources`, or `instructions` containers are mandatory.
- The serialized schema is service-owned and can change without a separately
	versioned JSON Schema artifact. Checked-in provenance and fixtures are part of
	the compatibility strategy, not optional documentation.

## yaml2genie design choices

These are local product decisions, not Databricks requirements:

- accepting YAML scalars for selected one-element string-array fields;
- generating omitted IDs deterministically and supporting a YAML-only stable
	key/source identity;
- preserving author order in YAML while sorting only normalized output;
- newline and block-scalar rendering policy;
- strict rejection or preservation of unknown fields;
- decentralized layouts and their manifest/merge semantics.

The preliminary `genie-pnl` project is useful evidence for Pydantic, safe YAML,
atomic writes, deterministic rendering, and CLI testing. Its required column
configs, snippet fields, CRLF splitting, grouped directory discovery, and
content-derived UUID5 IDs are POC behavior and must not be promoted to the
external contract without a deliberate yaml2genie decision.
