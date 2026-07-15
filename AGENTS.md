# AGENTS.md

## Dev environment
- Use `uv` instead of `python`. For example `uv run python -c "print('hello')"` instead of `python -c "print('hello')"` or `uv run my_script.py` instead of `python my_script.py`.
- Use `uv add ...` for adding dependencies to this repository instead of manually editing the `pyproject.toml` file.
- Use #context7 tool for reading documentation about libraries, platforms, services... instead of relying solely on your internal knowledge. If you don't have that tool available or you can't find something using that tool, fetch information directly from the web.

## Dev workflow
- After some work is done (e.g., implementing changes, doing research), write or edit documentation MD files in `.agents/docs` folder. Keep files short and only document what is worth for the future.
- Changes should be commited frequently. Ask the user for permission for a commit, specially when the task is large and should be splitted into several commits. Write short conventional commit messages.

## Relevant resources
- [Declarative Automation Bundles resources](https://docs.databricks.com/gcp/en/dev-tools/bundles/resources#genie_space): it includes the spec for genie_space
    * Note: Databricks is rebranding Genie Spaces to Genie Agents, so it's possible that the `genie_space` resource gets renamed in the future.
- [Use the Genie Agents API](https://docs.databricks.com/aws/en/genie/conversation-api): it includes useful information about Genie Agents (formerly known as Genie Spaces)
    * Understanding the serialized_space field: this section explains the content of the Genie Agent JSON. This JSON schema changes quite frequently so if there is an error with an older Genie Agent JSON, or if this repo does not cover some new features of Genie Agents it may be worth to take a look at the spec to see if something has changed. Current version is 2.
    * Validation rules for serialized_space: this section cover other additional and technical details about the JSON contents such as: version, ID format, sorting requirements, uniqueness constraints, size and length limits, join specs format, etc.
- [Get Genie Space - REST API reference](https://docs.databricks.com/api/workspace/genie/getspace): unfortunately, as of July 2026 the documentation of Databricks doesn't include a JSON schema for the Genie Agents, but between the "Use the Genie Agents API" and this resource there are a few examples that could be useful for understanding the technical definition.
