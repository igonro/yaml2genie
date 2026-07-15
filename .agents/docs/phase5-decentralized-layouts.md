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

## Fully split and mixed layouts

Phase 6 adds `fully-split`, which uses one YAML mapping per item below the
directory corresponding to each `category-split` collection path with its
`.yaml` suffix removed. For example, sample questions live at
`config/sample_questions/<item>.yaml`. Item files are read in lexical relative
path order. An author-supplied `stable_key` controls a generated ID across a
file rename; otherwise the source-relative item path is its fallback identity.

`mixed` requires the manifest to list every canonical category path under
`categories`, choosing `file` for the category's list file or `items` for its
per-item directory. This makes omitted optional content unambiguous and rejects
unknown or undeclared YAML files. An absent declared list file or item directory
means that optional category is empty.

`decompile --layout` accepts `central`, `grouped`, `category-split`,
`fully-split`, and `mixed`. Tree layouts produce a manifest first and then
deterministically ordered content files. A split filename comes from the
normalized item ID, or its identifier for ID-less data sources; it is never an
input to JSON identity. Colliding safe filenames are rejected before writes.
`--dry-run` prints the planned relative paths. Directory output stages the full
tree and replaces an existing tree only with `--overwrite`; rejected plans and
write failures preserve the old manifest and files.
