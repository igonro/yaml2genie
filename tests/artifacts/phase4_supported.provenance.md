# Official-shape compatibility fixture

`phase4_supported.json` is a compact version 2 serialized Agent definition
derived from the current first-party Create, Get, Update, and
serialized-definition examples. It covers every field currently marked
`supported` in the contract matrix.

It is an offline compatibility oracle: compiling
`tests/inputs/phase4_supported.yaml` must reproduce it exactly after
normalization. Source URLs and retrieval date are maintained in
`.agents/docs/databricks-genie-contract.md`.
