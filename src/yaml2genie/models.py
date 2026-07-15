from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
)

MAX_ITEMS = 10_000
MAX_STRING_LENGTH = 25_000
DATA_SOURCE_LEVELS = 3


def _as_string_list(value: object) -> object:
    if isinstance(value, str):
        return [value]
    return value


def _require_bounded_string(value: str) -> str:
    if len(value) > MAX_STRING_LENGTH:
        msg = f"string exceeds limit {MAX_STRING_LENGTH}; measured length {len(value)}"
        raise ValueError(msg)
    return value


def _require_non_blank_string(value: str) -> str:
    if not value.strip():
        msg = "string must not be empty or whitespace"
        raise ValueError(msg)
    return value


def _require_three_level_identifier(value: str) -> str:
    parts = value.split(".")
    if len(parts) != DATA_SOURCE_LEVELS or any(
        not part or part != part.strip() for part in parts
    ):
        msg = "identifier must use three-level namespace catalog.schema.object"
        raise ValueError(msg)
    return value


BoundedString = Annotated[str, AfterValidator(_require_bounded_string)]
NonEmptyBoundedString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(_require_non_blank_string),
    AfterValidator(_require_bounded_string),
]
DataSourceIdentifier = Annotated[
    BoundedString,
    AfterValidator(_require_three_level_identifier),
]
StringList = Annotated[
    list[BoundedString],
    BeforeValidator(_as_string_list),
    Field(max_length=MAX_ITEMS),
]
NonEmptyStringList = Annotated[
    list[NonEmptyBoundedString],
    BeforeValidator(_as_string_list),
    Field(min_length=1, max_length=MAX_ITEMS),
]
GenieId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SampleQuestionInput(StrictModel):
    id: GenieId | None = None
    stable_key: NonEmptyBoundedString | None = None
    question: StringList


class ConfigInput(StrictModel):
    sample_questions: list[SampleQuestionInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class ColumnConfigInput(StrictModel):
    column_name: BoundedString
    description: StringList | None = None
    exclude: bool | None = None
    enable_format_assistance: bool | None = None
    enable_entity_matching: bool | None = None


class TableInput(StrictModel):
    identifier: DataSourceIdentifier
    description: StringList | None = None
    column_configs: list[ColumnConfigInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class DataSourcesInput(StrictModel):
    tables: list[TableInput] | None = Field(default=None, max_length=MAX_ITEMS)


class TextInstructionInput(StrictModel):
    id: GenieId | None = None
    stable_key: NonEmptyBoundedString | None = None
    content: StringList | None = None


class ExampleQuestionSqlInput(StrictModel):
    id: GenieId | None = None
    stable_key: NonEmptyBoundedString | None = None
    question: StringList | None = None
    sql: StringList | None = None


class JoinSideInput(StrictModel):
    identifier: DataSourceIdentifier
    alias: NonEmptyBoundedString


class JoinSpecInput(StrictModel):
    id: GenieId | None = None
    stable_key: NonEmptyBoundedString | None = None
    left: JoinSideInput
    right: JoinSideInput
    sql: list[BoundedString] = Field(min_length=2, max_length=2)


class SqlSnippetInput(StrictModel):
    id: GenieId | None = None
    stable_key: NonEmptyBoundedString | None = None
    sql: NonEmptyStringList


class SqlSnippetsInput(StrictModel):
    filters: list[SqlSnippetInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    expressions: list[SqlSnippetInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    measures: list[SqlSnippetInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class InstructionsInput(StrictModel):
    text_instructions: list[TextInstructionInput] | None = Field(
        default=None,
        max_length=1,
    )
    example_question_sqls: list[ExampleQuestionSqlInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    join_specs: list[JoinSpecInput] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    sql_snippets: SqlSnippetsInput | None = None


class DefinitionInput(StrictModel):
    version: Literal[2]
    config: ConfigInput | None = None
    data_sources: DataSourcesInput | None = None
    instructions: InstructionsInput | None = None


class SampleQuestion(StrictModel):
    id: GenieId
    question: list[BoundedString] = Field(max_length=MAX_ITEMS)


class Config(StrictModel):
    sample_questions: list[SampleQuestion] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class ColumnConfig(StrictModel):
    column_name: BoundedString
    description: list[BoundedString] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    exclude: bool | None = None
    enable_format_assistance: bool | None = None
    enable_entity_matching: bool | None = None


class Table(StrictModel):
    identifier: DataSourceIdentifier
    description: list[BoundedString] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    column_configs: list[ColumnConfig] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class DataSources(StrictModel):
    tables: list[Table] | None = Field(default=None, max_length=MAX_ITEMS)


class TextInstruction(StrictModel):
    id: GenieId
    content: list[BoundedString] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )


class ExampleQuestionSql(StrictModel):
    id: GenieId
    question: list[BoundedString] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    sql: list[BoundedString] | None = Field(default=None, max_length=MAX_ITEMS)


class JoinSide(StrictModel):
    identifier: DataSourceIdentifier
    alias: NonEmptyBoundedString


class JoinSpec(StrictModel):
    id: GenieId
    left: JoinSide
    right: JoinSide
    sql: list[BoundedString] = Field(min_length=2, max_length=2)


class SqlSnippet(StrictModel):
    id: GenieId
    sql: list[NonEmptyBoundedString] = Field(
        min_length=1,
        max_length=MAX_ITEMS,
    )


class SqlSnippets(StrictModel):
    filters: list[SqlSnippet] | None = Field(default=None, max_length=MAX_ITEMS)
    expressions: list[SqlSnippet] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    measures: list[SqlSnippet] | None = Field(default=None, max_length=MAX_ITEMS)


class Instructions(StrictModel):
    text_instructions: list[TextInstruction] | None = Field(
        default=None,
        max_length=1,
    )
    example_question_sqls: list[ExampleQuestionSql] | None = Field(
        default=None,
        max_length=MAX_ITEMS,
    )
    join_specs: list[JoinSpec] | None = Field(default=None, max_length=MAX_ITEMS)
    sql_snippets: SqlSnippets | None = None


class DefinitionDocument(StrictModel):
    version: Literal[2]
    config: Config | None = None
    data_sources: DataSources | None = None
    instructions: Instructions | None = None
