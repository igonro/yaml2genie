# Decentralized YAML layouts

Phase 5 accepts a YAML directory only when its root contains `genie.yaml`:

```yaml
version: 2
layout: grouped # or category-split
```

`grouped` may contain these optional mapping files. Their keys are collection
names and every collection value is a list of item mappings.

| File | Keys |
| --- | --- |
| `config.yaml` | `sample_questions` |
| `sources.yaml` | `tables`, `metric_views` |
| `instructions.yaml` | `text_instructions`, `sql_functions` |
| `examples.yaml` | `joins`, `queries`, `filters`, `expressions`, `measures` |
| `benchmarks.yaml` | `questions` |

`category-split` uses optional list files at `config/sample_questions.yaml`,
`sources/tables.yaml`, `sources/metric_views.yaml`,
`instructions/text_instructions.yaml`, `instructions/sql_functions.yaml`,
`examples/joins.yaml`, `examples/queries.yaml`, `examples/filters.yaml`,
`examples/expressions.yaml`, `examples/measures.yaml`, and
`benchmarks/questions.yaml`.

The loader reads only these declared paths in a fixed order and rejects other
YAML category files or keys. Missing files mean empty collections. Collection
items are combined only at their declared category; mappings are never deeply
merged and there is no last-file-wins rule. `version` is currently the only
supported singleton and it comes from the manifest; all other supported v2
fields are collections. Existing validation remains shared with centralized
YAML. When an item has no explicit ID or `stable_key`, its
relative file path and list position provide a deterministic fallback identity;
semantic errors name those source-relative paths.
