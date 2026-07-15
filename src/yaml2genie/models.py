from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints


def _as_string_list(value: object) -> object:
    if isinstance(value, str):
        return [value]
    return value


StringList = Annotated[list[str], BeforeValidator(_as_string_list)]
GenieId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SampleQuestionInput(StrictModel):
    id: GenieId | None = None
    question: StringList


class ConfigInput(StrictModel):
    sample_questions: list[SampleQuestionInput] | None = None


class ColumnConfigInput(StrictModel):
    column_name: str
    description: StringList | None = None
    exclude: bool | None = None
    enable_format_assistance: bool | None = None
    enable_entity_matching: bool | None = None


class TableInput(StrictModel):
    identifier: str
    description: StringList | None = None
    column_configs: list[ColumnConfigInput] | None = None


class DataSourcesInput(StrictModel):
    tables: list[TableInput] | None = None


class TextInstructionInput(StrictModel):
    id: GenieId | None = None
    content: StringList | None = None


class ExampleQuestionSqlInput(StrictModel):
    id: GenieId | None = None
    question: StringList | None = None
    sql: StringList | None = None


class JoinSideInput(StrictModel):
    identifier: str
    alias: str


class JoinSpecInput(StrictModel):
    id: GenieId | None = None
    left: JoinSideInput
    right: JoinSideInput
    sql: list[str] = Field(min_length=2, max_length=2)


class SqlSnippetInput(StrictModel):
    id: GenieId | None = None
    sql: StringList = Field(min_length=1)


class SqlSnippetsInput(StrictModel):
    filters: list[SqlSnippetInput] | None = None
    expressions: list[SqlSnippetInput] | None = None
    measures: list[SqlSnippetInput] | None = None


class InstructionsInput(StrictModel):
    text_instructions: list[TextInstructionInput] | None = None
    example_question_sqls: list[ExampleQuestionSqlInput] | None = None
    join_specs: list[JoinSpecInput] | None = None
    sql_snippets: SqlSnippetsInput | None = None


class DefinitionInput(StrictModel):
    version: Literal[2]
    config: ConfigInput | None = None
    data_sources: DataSourcesInput | None = None
    instructions: InstructionsInput | None = None


class SampleQuestion(StrictModel):
    id: GenieId
    question: list[str]


class Config(StrictModel):
    sample_questions: list[SampleQuestion] | None = None


class ColumnConfig(StrictModel):
    column_name: str
    description: list[str] | None = None
    exclude: bool | None = None
    enable_format_assistance: bool | None = None
    enable_entity_matching: bool | None = None


class Table(StrictModel):
    identifier: str
    description: list[str] | None = None
    column_configs: list[ColumnConfig] | None = None


class DataSources(StrictModel):
    tables: list[Table] | None = None


class TextInstruction(StrictModel):
    id: GenieId
    content: list[str] | None = None


class ExampleQuestionSql(StrictModel):
    id: GenieId
    question: list[str] | None = None
    sql: list[str] | None = None


class JoinSide(StrictModel):
    identifier: str
    alias: str


class JoinSpec(StrictModel):
    id: GenieId
    left: JoinSide
    right: JoinSide
    sql: list[str] = Field(min_length=2, max_length=2)


class SqlSnippet(StrictModel):
    id: GenieId
    sql: list[str] = Field(min_length=1)


class SqlSnippets(StrictModel):
    filters: list[SqlSnippet] | None = None
    expressions: list[SqlSnippet] | None = None
    measures: list[SqlSnippet] | None = None


class Instructions(StrictModel):
    text_instructions: list[TextInstruction] | None = None
    example_question_sqls: list[ExampleQuestionSql] | None = None
    join_specs: list[JoinSpec] | None = None
    sql_snippets: SqlSnippets | None = None


class DefinitionDocument(StrictModel):
    version: Literal[2]
    config: Config | None = None
    data_sources: DataSources | None = None
    instructions: Instructions | None = None
