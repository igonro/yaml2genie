# Generate stable IDs for omitted definition items

**Status: accepted**

When a YAML item omits an ID, yaml2genie will generate a deterministic 32-character lowercase hexadecimal ID and preserve explicit valid IDs. Stable IDs make repeated builds reviewable and keep references from changing merely because the CLI was run again. A stable YAML key or source identity will be preferred; canonical item content is the fallback. UUID v7 remains an option only if Databricks later requires time-ordered random IDs, because the current contract only requires the lowercase hexadecimal format.
