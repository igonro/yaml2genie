# Centralized JSON decompilation

- `yaml2genie decompile INPUT --output OUTPUT` accepts either the raw v2
  serialized definition object or a JSON string containing it. It deliberately
  does not inspect full API responses or bundle resources.
- JSON must validate as a normalized `DefinitionDocument`: required serialized
  IDs cannot be synthesized during decompilation. Shared semantic validation
  still rejects duplicate IDs, invalid joins, and unsupported content.
- YAML preserves supported data and source field order. One-item string lists
  are rendered as scalars, multiline strings as block scalars, and multi-item
  lists remain explicit. Nested mappings and lists use two-space indentation
  and files use UTF-8 with LF line endings and one trailing newline.
- Output uses a sibling temporary file and atomic replacement. Existing YAML
  requires the command's explicit `--overwrite` option.
