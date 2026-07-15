# Keep the serialized definition as the core contract

**Status: accepted**

yaml2genie will model the Databricks `serialized_space` version 2 definition as its canonical content contract. Centralized YAML and every decentralized YAML layout will load into that same definition, while API and Declarative Automation Bundle metadata remain a separate deployment wrapper. This keeps validation, JSON export, and YAML round-trips on one seam and prevents deployment-specific fields from leaking into Agent content.
