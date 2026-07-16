# YAML presentation policy

Decompile renders YAML with `YamlRenderOptions`: pretty mode is the default and raw mode retains validated string-array boundaries and embedded CRLF. Pretty mode applies CRLF/CR-to-LF normalization only to schema-whitelisted human-text fields. It collapses eligible singleton arrays and merges a multi-element array only when every element except the last ends in LF after normalization. It leaves semantic lists (`synonyms`, parameter default values, and two-element join SQL tuples) intact.

Merged text must remain within Databricks' 25,000-character string limit; otherwise the original normalized list is retained. LF-containing pretty values use literal block scalars, and the dumper uses an effectively unlimited width to avoid continuation wrapping. JSON rendering bypasses this presentation transform.

`--omit-ids` is independent of pretty/raw and runs only after source-tree item filenames are planned. Current Databricks documentation examples use LF; no CRLF output requirement is known.
