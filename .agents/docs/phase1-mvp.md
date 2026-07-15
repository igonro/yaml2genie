# Centralized compiler implementation

- The public compile boundary is `compile_definition(path) -> DefinitionDocument`.
- Pydantic input models reject unknown fields. Normalized output models require
  every ID that Databricks requires.
- A scalar accepted for a string-list field becomes exactly one list element.
  Embedded LF or CRLF characters, trailing newlines, and blank lines are never
  split into additional elements.
- Missing IDs use a 16-byte BLAKE2b digest of their category and identity.
  Authors may set YAML-only `stable_key`; changing service-owned item content
  then preserves the ID, while changing the key or moving categories changes
  it. Without a key, all item content except `id` and YAML-only metadata is the
  fallback identity, so any content edit can change the generated ID.
- Stable keys are unique within their collection. Generated/generated and
  explicit/generated collisions fail with both indexed source locations; IDs
  never receive random suffixes.
- Collection descriptors own source paths, sort keys, ID requirements, and
  uniqueness scopes. Normalization sorts only exported collections and never
  modifies YAML. Decentralized source identities remain deferred to their
  loaders.
- Input and normalized models enforce the documented 25,000-character and
  10,000-item limits, one text instruction, non-empty snippet SQL, lowercase
  32-character hexadecimal IDs, and three-level table identifiers. No
  workspace-specific or undocumented SQL numeric limit is imposed.
- Join validation checks two endpoints, distinct and backtick-referenced
  aliases, exactly two SQL elements, and the four documented relationship
  annotations. It does not parse arbitrary SQL expressions.
- CLI errors are categorized with stable exit codes: source parse `2`, schema
  `3`, semantic `4`, and output `5`. The library compile boundary retains native
  Pydantic errors and semantic `DefinitionError` subclasses.
- JSON uses four-space indentation, UTF-8, and one trailing LF. Builds write a
  temporary sibling and atomically replace the requested output only on success.
