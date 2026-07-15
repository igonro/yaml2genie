# yaml2genie Context

This context defines the project vocabulary for representing Databricks Genie Agents as maintainable YAML and exporting their deployable serialized definition.

## Representations

**Genie Agent**:
A Databricks AI/BI artifact configured with data sources, instructions, examples, and optional benchmarks. Databricks documentation and APIs still use the former name "Genie Space" in several resource names.
_Avoid_: Treating the deployment resource and its serialized content as the same thing.

**Serialized Agent Definition**:
The versioned JSON object carried by the Databricks `serialized_space` field. It describes the Agent's configuration and content; it is not the outer API response or bundle resource metadata.
_Avoid_: Serialized space when referring to the whole deployment resource.

**Deployment Resource**:
The outer Databricks API or Declarative Automation Bundle object that supplies metadata such as title, warehouse, parent path, permissions, and the serialized definition.
_Avoid_: Putting deployment metadata inside the serialized Agent definition.

**Centralized YAML**:
One YAML document whose structure mirrors the serialized Agent Definition closely enough to validate, round-trip, and export without layout-specific merging.
_Avoid_: Calling every YAML input a source tree.

**Decentralized YAML Source Tree**:
A directory layout that stores parts of one Agent Definition in multiple YAML files. The loader assembles it into the same logical definition used by centralized YAML.
_Avoid_: An arbitrary deep merge with undocumented precedence rules.

## Agent Content

**Data Source**:
A Unity Catalog table or metric view exposed to the Agent, identified by a three-level namespace and optionally annotated with column configuration.

**Instruction Item**:
An ID-bearing entry inside the Agent's instructions, such as text guidance, an example SQL question, a join specification, a SQL function reference, or a SQL snippet.

**Benchmark Question**:
A question and its expected SQL answer used to evaluate Agent quality. It is distinct from a user-facing sample question and must retain its own globally unique ID.

**Technical Normalization**:
The deterministic fulfillment applied before JSON export: generating missing IDs, sorting collections required by Databricks, and enforcing cross-item constraints without rewriting the author's YAML files.

**Question ID Scope**:
The shared uniqueness scope containing sample-question IDs and benchmark-question IDs.
_Avoid_: Validating those collections independently.

**Instruction ID Scope**:
The shared uniqueness scope containing text instructions, example SQL questions, SQL functions, joins, filters, expressions, and measures.
_Avoid_: Treating an ID as unique merely because it is unique within one instruction category.

**Contract Matrix**:
The source-linked evidence ledger in [.agents/docs/databricks-genie-contract.md](.agents/docs/databricks-genie-contract.md) that records observed version 2 fields, requiredness evidence, constraints, and release support. It governs schema implementation without replacing upstream documentation.
_Avoid_: Copying field specifications into this glossary.

## Architecture decisions

- [ADR 0001: Keep the serialized definition as the core contract](docs/adr/0001-schema-first-serialized-core.md)
- [ADR 0002: Generate stable IDs for omitted definition items](docs/adr/0002-deterministic-generated-ids.md)
