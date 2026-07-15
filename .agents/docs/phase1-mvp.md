# Phase 1 MVP implementation

- The public compile boundary is `compile_definition(path) -> DefinitionDocument`.
- Pydantic input models reject unknown fields. Normalized output models require
  every ID that Databricks requires.
- A scalar accepted for a string-list field becomes exactly one list element.
  Embedded LF or CRLF characters, trailing newlines, and blank lines are never
  split into additional elements.
- Missing IDs use a 16-byte BLAKE2b digest of canonical item content and its
  instruction category. Phase 2 may add explicit YAML stable keys; changing
  fallback identity content changes the generated ID.
- Normalization sorts exported collections and checks the Phase 1 question,
  instruction, and column uniqueness scopes without modifying YAML.
- JSON uses four-space indentation, UTF-8, and one trailing LF. Builds write a
  temporary sibling and atomically replace the requested output only on success.
