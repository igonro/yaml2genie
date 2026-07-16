# Generate stable IDs for omitted definition items

**Status: accepted**

When a YAML item omits an ID, yaml2genie will generate a deterministic 32-character lowercase hexadecimal ID and preserve explicit valid IDs. The generated ID starts with a collection rank and zero-padded source position, followed by a content/identity digest. This makes Databricks' lexical ID sort preserve YAML order within a collection and group generated instruction items by type. A stable YAML key or source identity will be preferred; canonical item content is the fallback. UUID v7 remains an option only if Databricks later requires time-ordered random IDs, because the current contract only requires the lowercase hexadecimal format.

`decompile --omit-ids` is an explicit presentation choice for editable YAML.
It produces source that recompiles to valid deterministic IDs, but cannot
preserve identity continuity from the imported Agent when an ID is absent.
Regeneration can therefore change IDs and service-required ordering, and it
can expose duplicate-content collisions when neither explicit IDs nor distinct
`stable_key` values identify otherwise identical centralized items. In split
layouts, imported IDs remain available during output planning so filenames stay
deterministic before IDs are omitted from file contents.
