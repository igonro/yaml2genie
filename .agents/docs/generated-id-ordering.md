# Generated ID ordering

Generated IDs use two hexadecimal prefix fields: the normalized collection rank
and the item's zero-based position in its source collection. The remaining 24
hexadecimal characters are a deterministic digest of the item's stable identity
or content. Explicit IDs are unchanged. Because Databricks sorts ID-bearing
collections lexically, omitted IDs retain YAML order within a category and
generated instruction categories remain grouped.
