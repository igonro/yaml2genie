from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from yaml2genie import compile_definition
from yaml2genie.errors import DefinitionError


def _write_yaml(tmp_path: Path, source: object) -> Path:
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")
    return source_path


def test_string_limit_reports_path_limit_and_measured_length(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "config": {"sample_questions": [{"question": "x" * 25_001}]},
    }

    with pytest.raises(ValidationError) as error:
        compile_definition(_write_yaml(tmp_path, source))

    message = str(error.value)
    assert "config.sample_questions.0.question.0" in message
    assert "25000" in message
    assert "25001" in message


def test_repeated_field_limit_reports_path_limit_and_item_count(
    tmp_path: Path,
) -> None:
    source = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"question": f"Question {index}"} for index in range(10_001)
            ],
        },
    }

    with pytest.raises(ValidationError) as error:
        compile_definition(_write_yaml(tmp_path, source))

    message = str(error.value)
    assert "config.sample_questions" in message
    assert "10000" in message
    assert "10001" in message


def test_only_one_text_instruction_is_allowed(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "instructions": {
            "text_instructions": [
                {"content": "First"},
                {"content": "Second"},
            ],
        },
    }

    with pytest.raises(ValidationError, match=r"instructions.text_instructions"):
        compile_definition(_write_yaml(tmp_path, source))


@pytest.mark.parametrize("sql", [[], [""], ["   "]])
def test_sql_snippet_content_must_not_be_empty(
    tmp_path: Path,
    sql: list[str],
) -> None:
    source = {
        "version": 2,
        "instructions": {"sql_snippets": {"filters": [{"sql": sql}]}},
    }

    with pytest.raises(
        ValidationError,
        match=r"instructions.sql_snippets.filters.0.sql",
    ):
        compile_definition(_write_yaml(tmp_path, source))


@pytest.mark.parametrize("identifier", ["schema.table", "catalog..table"])
def test_table_identifier_requires_three_levels(
    tmp_path: Path,
    identifier: str,
) -> None:
    source = {"version": 2, "data_sources": {"tables": [{"identifier": identifier}]}}

    with pytest.raises(
        ValidationError,
        match=r"data_sources.tables.0.identifier",
    ):
        compile_definition(_write_yaml(tmp_path, source))


def test_duplicate_table_identifiers_report_both_locations(tmp_path: Path) -> None:
    table = {"identifier": "sales.analytics.orders"}
    source = {
        "version": 2,
        "data_sources": {"tables": [table, table.copy()]},
    }

    with pytest.raises(DefinitionError) as error:
        compile_definition(_write_yaml(tmp_path, source))

    message = str(error.value)
    assert "data_sources.tables[0].identifier" in message
    assert "data_sources.tables[1].identifier" in message


def test_same_column_name_is_allowed_for_different_tables(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "data_sources": {
            "tables": [
                {
                    "identifier": "sales.analytics.orders",
                    "column_configs": [{"column_name": "created_at"}],
                },
                {
                    "identifier": "sales.analytics.customers",
                    "column_configs": [{"column_name": "created_at"}],
                },
            ],
        },
    }

    definition = compile_definition(_write_yaml(tmp_path, source))

    assert definition.data_sources is not None
    assert definition.data_sources.tables is not None
    assert [table.identifier for table in definition.data_sources.tables] == [
        "sales.analytics.customers",
        "sales.analytics.orders",
    ]


def _join_source(condition: str, relationship: str) -> dict[str, object]:
    return {
        "version": 2,
        "instructions": {
            "join_specs": [
                {
                    "left": {
                        "identifier": "sales.analytics.orders",
                        "alias": "orders",
                    },
                    "right": {
                        "identifier": "sales.analytics.customers",
                        "alias": "customers",
                    },
                    "sql": [condition, relationship],
                },
            ],
        },
    }


@pytest.mark.parametrize(
    "relationship",
    [
        "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
        "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_MANY--",
        "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_ONE--",
        "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--",
    ],
)
def test_join_accepts_documented_relationship_types(
    tmp_path: Path,
    relationship: str,
) -> None:
    source = _join_source(
        "`orders`.`customer_id` = `customers`.`customer_id`",
        relationship,
    )

    definition = compile_definition(_write_yaml(tmp_path, source))

    assert definition.instructions is not None
    assert definition.instructions.join_specs is not None
    assert definition.instructions.join_specs[0].sql[1] == relationship


def test_join_endpoint_requires_three_level_identifier(tmp_path: Path) -> None:
    source = _join_source(
        "`orders`.`customer_id` = `customers`.`customer_id`",
        "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
    )
    instructions = source["instructions"]
    assert isinstance(instructions, dict)
    join_specs = instructions["join_specs"]
    assert isinstance(join_specs, list)
    join_specs[0]["right"]["identifier"] = "analytics.customers"

    with pytest.raises(
        ValidationError,
        match=r"instructions.join_specs.0.right.identifier",
    ):
        compile_definition(_write_yaml(tmp_path, source))


def test_join_condition_must_reference_both_aliases(tmp_path: Path) -> None:
    source = _join_source(
        "`orders`.`customer_id` = `accounts`.`customer_id`",
        "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
    )

    with pytest.raises(DefinitionError, match=r"join_specs\[0\].sql\[0\].*customers"):
        compile_definition(_write_yaml(tmp_path, source))


def test_join_rejects_unsupported_relationship_annotation(tmp_path: Path) -> None:
    source = _join_source(
        "`orders`.`customer_id` = `customers`.`customer_id`",
        "--rt=FROM_RELATIONSHIP_TYPE_UNKNOWN--",
    )

    with pytest.raises(DefinitionError, match=r"join_specs\[0\].sql\[1\]"):
        compile_definition(_write_yaml(tmp_path, source))
