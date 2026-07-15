# Databricks Genie Agent version 2 contract

**Retrieved:** 2026-07-15. The primary serialized-definition page was last
updated 2026-07-14.

This matrix is yaml2genie's evidence ledger for the service-owned
`serialized_space` version 2 format. Databricks does not publish a standalone,
stable JSON Schema for this object. Prose rules establish constraints; examples
establish observed shape but not requiredness.

## Sources

- [Use the Genie Agents API](https://docs.databricks.com/aws/en/genie-agents/conversation-api), retrieved 2026-07-15.
- [Create Genie Space](https://docs.databricks.com/api/workspace/genie/createspace), retrieved 2026-07-15.
- [Get Genie Space](https://docs.databricks.com/api/workspace/genie/getspace), retrieved 2026-07-15.
- [Update Genie Space](https://docs.databricks.com/api/workspace/genie/updatespace), retrieved 2026-07-15.
- [Bundle Genie resource](https://docs.databricks.com/gcp/en/dev-tools/bundles/resources#genie_space), retrieved 2026-07-15.
- [Official Genie bundle example](https://github.com/databricks/bundle-examples/tree/main/knowledge_base/genie_space_nyc_taxi), retrieved 2026-07-15.
- [Databricks CLI file inlining](https://github.com/databricks/cli/blob/main/bundle/config/mutator/resourcemutator/configure_genie_space_serialized_space.go), retrieved 2026-07-15.

## Matrix conventions

- Requiredness is `required` or `optional` only when first-party prose says so;
  otherwise it is `unknown`.
- Types describe observed JSON. A bounded collection is subject to the stated
  10,000-item general repeated-field limit.
- `supported` means accepted in Phase 1. `deferred` means known version 2 shape
  that Phase 1 rejects at its exact path and Phase 4 may add.
- YAML shorthand applies only at the YAML boundary. `scalar -> one item` means a
  scalar string is normalized to a one-element JSON string list.
- Confidence describes the evidence for the field or rule, not a guess about
  requiredness.

<!-- matrix:start -->
| JSON path | Observed type | Requiredness | Limits | Sort key | Uniqueness scope | Allowed YAML shorthand | Phase 1 | Confidence | Primary source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `version` | integer scalar | required | exactly `2` for new definitions | n/a | n/a | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `config` | object | unknown | n/a | n/a | n/a | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `config.sample_questions` | object-list (bounded) | unknown | at most 10,000 items | `id` | question IDs across sample and benchmark questions | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `config.sample_questions[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | question IDs across sample and benchmark questions | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `config.sample_questions[].question` | string-list (bounded) | required | at most 10,000 items; 25,000 characters each | n/a | none stated | scalar -> one item | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources` | object | unknown | workspace-specific source count | n/a | n/a | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables` | object-list (bounded) | unknown | at most 10,000 items; workspace-specific source count | `identifier` | none stated | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].identifier` | string scalar | required | 25,000 characters; three-level namespace | parent collection | none stated | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].description` | string-list (bounded) | optional | at most 10,000 items; 25,000 characters each | n/a | none stated | scalar -> one item | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs` | object-list (bounded) | optional | at most 10,000 items | `column_name` | `(table_identifier, column_name)` agent-wide | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].column_name` | string scalar | unknown | 25,000 characters | parent collection | `(table_identifier, column_name)` agent-wide | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].description` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | scalar -> one item | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].synonyms` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].exclude` | boolean scalar | unknown | n/a | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].enable_format_assistance` | boolean scalar | unknown | n/a | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.tables[].column_configs[].enable_entity_matching` | boolean scalar | unknown | n/a | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views` | object-list (bounded) | unknown | at most 10,000 items; workspace-specific source count | `identifier` | none stated | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].identifier` | string scalar | required | 25,000 characters; namespace format not stated | parent collection | none stated | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].description` | string-list (bounded) | optional | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs` | object-list (bounded) | optional | at most 10,000 items | `column_name` | `(table_identifier, column_name)` wording is unresolved for metric views | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].column_name` | string scalar | unknown | 25,000 characters | parent collection | metric-view scope unresolved | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].description` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].synonyms` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].exclude` | boolean scalar | unknown | n/a | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].enable_format_assistance` | boolean scalar | unknown | n/a | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `data_sources.metric_views[].column_configs[].enable_entity_matching` | boolean scalar | unknown | n/a | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions` | object | unknown | n/a | n/a | n/a | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.text_instructions` | object-list (bounded) | unknown | at most one item | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.text_instructions[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.text_instructions[].content` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | scalar -> one item | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls` | object-list (bounded) | unknown | at most 10,000 items | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].question` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | scalar -> one item | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].sql` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each; additional SQL limit unknown | n/a | none stated | scalar -> one item | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters` | object-list (bounded) | optional | at most 10,000 items | n/a | none stated | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters[].name` | string scalar | unknown | 25,000 characters | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters[].type_hint` | string scalar | unknown | 25,000 characters | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters[].description` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters[].default_value` | object | unknown | n/a | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].parameters[].default_value.values` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.example_question_sqls[].usage_guidance` | string-list (bounded) | optional | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_functions` | object-list (bounded) | unknown | at most 10,000 items | `(id, identifier)` | instruction IDs across every instruction category | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_functions[].id` | string scalar | unknown | ID format inferred from sorting and uniqueness rules | parent collection | instruction IDs across every instruction category | none | deferred | inferred | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_functions[].identifier` | string scalar | unknown | 25,000 characters; namespace format not stated | parent collection | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs` | object-list (bounded) | unknown | at most 10,000 items | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].left` | object | unknown | n/a | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].left.identifier` | string scalar | unknown | 25,000 characters | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].left.alias` | string scalar | unknown | 25,000 characters; referenced backtick-quoted in join SQL | n/a | alias within join | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].right` | object | unknown | n/a | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].right.identifier` | string scalar | unknown | 25,000 characters | n/a | none stated | none | supported | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].right.alias` | string scalar | unknown | 25,000 characters; referenced backtick-quoted in join SQL | n/a | alias within join | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].sql` | string-list (bounded) | required | exactly two items; condition then relationship annotation; SQL length unknown | n/a | none stated | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].comment` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.join_specs[].instruction` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets` | object | unknown | n/a | n/a | n/a | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.filters` | object-list (bounded) | unknown | at most 10,000 items | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.expressions` | object-list (bounded) | unknown | at most 10,000 items | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.measures` | object-list (bounded) | unknown | at most 10,000 items | `id` | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | instruction IDs across every instruction category | none | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].alias` | string scalar | unknown | 25,000 characters | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].sql` | string-list (bounded) | required | non-empty; at most 10,000 items; 25,000 characters each; SQL length unknown | n/a | none stated | scalar -> one item | supported | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].display_name` | string scalar | unknown | 25,000 characters | n/a | none stated | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].synonyms` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].comment` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `instructions.sql_snippets.{filters,expressions,measures}[].instruction` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks` | object | unknown | n/a | n/a | n/a | none | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions` | object-list (bounded) | unknown | at most 10,000 items | `id` | question IDs across sample and benchmark questions | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions[].id` | string scalar | required | 32 lowercase hexadecimal characters | parent collection | question IDs across sample and benchmark questions | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions[].question` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions[].answer` | object-list | required | exactly one item | n/a | none stated | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions[].answer[].format` | string scalar | required | exactly `SQL` | n/a | none stated | none | deferred | documented | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
| `benchmarks.questions[].answer[].content` | string-list (bounded) | unknown | at most 10,000 items; 25,000 characters each; SQL length unknown | n/a | none stated | no (deferred) | deferred | example-only | <https://docs.databricks.com/aws/en/genie-agents/conversation-api> |
<!-- matrix:end -->

## Upstream contradictions

- Current guidance requires version 2, while stale create and retrieval examples
  on the same [Genie Agents API page](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
  still contain version 1. yaml2genie follows the explicit version rule.
- Some examples on that [same primary page](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
  contain non-hexadecimal IDs. yaml2genie follows the explicit 32-character
  lowercase hexadecimal rule.
- SQL functions participate in sorting and instruction-ID uniqueness on the
  [primary page](https://docs.databricks.com/aws/en/genie-agents/conversation-api),
  but are omitted from its explicit ID-required list. Their ID requiredness
  remains `unknown`; Phase 1 rejects the entire deferred category.

## Frozen Phase 1 decisions

The first release accepts two JSON input forms: a raw serialized object and an
escaped serialized string whose decoded value is that object. Automatic
extraction from a full Get API response is deferred to the import phase because
the wrapper also contains deployment metadata.

Known fields marked `deferred` and genuinely unknown fields are both rejected in
Phase 1. Strict rejection reports the exact JSON path. No unsupported value is
silently discarded. Unresolved requiredness does not become a local requirement;
the model accepts omission unless another documented invariant makes the field
necessary for a supplied item.

YAML scalar shorthand is limited to matrix rows marked `scalar -> one item`.
Join SQL remains an explicit two-item list. Source order is author-facing;
rendered JSON uses the documented sort key.

## Representation boundary

The management API transports `serialized_space` as an escaped JSON string:
Create requires it, Update treats it as a full replacement when supplied, and
Get includes it only with `include_serialized_space=true`, which requires at
least `CAN EDIT` ([Create](https://docs.databricks.com/api/workspace/genie/createspace),
[Update](https://docs.databricks.com/api/workspace/genie/updatespace),
[Get](https://docs.databricks.com/api/workspace/genie/getspace)). The unescaped
object is the `.geniespace.json` file content used by bundles.

Deployment fields such as `title`, `description`, `warehouse_id`, `parent_path`,
`etag`, lifecycle, and permissions are outside the serialized definition. In a
[bundle Genie resource](https://docs.databricks.com/gcp/en/dev-tools/bundles/resources#genie_space),
`file_path` and inline `serialized_space` are mutually exclusive. The
[Databricks CLI](https://github.com/databricks/cli/blob/main/bundle/config/mutator/resourcemutator/configure_genie_space_serialized_space.go)
inlines file content during deployment and rejects a resource that supplies
both. Genie resources use the direct deployment engine, as shown by the
[official bundle example](https://github.com/databricks/bundle-examples/tree/main/knowledge_base/genie_space_nyc_taxi).

## Local policies, not service requirements

Deterministic generated IDs, YAML scalar shorthand, preservation of author
order, newline rendering, strict rejection of deferred fields, and decentralized
layout semantics are yaml2genie product decisions. Preliminary POC behavior is
not contract evidence.
