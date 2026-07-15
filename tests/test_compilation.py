import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from yaml2genie import compile_definition
from yaml2genie.errors import DefinitionError

FIXTURE_ROOT = Path(__file__).parent
GENIE_ID_LENGTH = 32


def test_minimal_yaml_compiles_to_expected_definition() -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/minimal.json").read_text(encoding="utf-8"),
    )

    definition = compile_definition(FIXTURE_ROOT / "inputs/minimal.yaml")

    assert definition.model_dump(exclude_none=True) == expected


def test_all_supported_fields_compile_to_expected_definition() -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/phase1_supported.json").read_text(
            encoding="utf-8",
        ),
    )

    definition = compile_definition(FIXTURE_ROOT / "inputs/phase1_supported.yaml")

    assert definition.model_dump(exclude_none=True) == expected


def test_normalized_output_is_sorted_without_rewriting_source() -> None:
    source_path = FIXTURE_ROOT / "inputs/unsorted.yaml"
    original_source = source_path.read_text(encoding="utf-8")

    definition = compile_definition(source_path)

    assert definition.config is not None
    assert definition.config.sample_questions is not None
    assert [item.id for item in definition.config.sample_questions] == [
        "00000000000000000000000000000001",
        "00000000000000000000000000000002",
    ]
    assert definition.data_sources is not None
    assert definition.data_sources.tables is not None
    assert [item.identifier for item in definition.data_sources.tables] == [
        "sales.analytics.customers",
        "sales.analytics.orders",
    ]
    assert source_path.read_text(encoding="utf-8") == original_source


def test_omitted_ids_are_valid_stable_and_explicit_ids_survive(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"question": "How many orders?"},
                {
                    "id": "00000000000000000000000000000001",
                    "question": "What is revenue?",
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    first = compile_definition(source_path)
    second = compile_definition(source_path)
    assert first.config is not None
    assert first.config.sample_questions is not None
    ids_by_question = {
        item.question[0]: item.id for item in first.config.sample_questions
    }
    generated_id = ids_by_question["How many orders?"]

    assert ids_by_question["What is revenue?"] == ("00000000000000000000000000000001")
    assert len(generated_id) == GENIE_ID_LENGTH
    assert generated_id.isascii()
    assert generated_id.islower()
    assert int(generated_id, 16) >= 0
    assert second == first


@pytest.mark.parametrize(
    ("fixture_name", "error_type", "message"),
    [
        ("invalid_id.yaml", ValidationError, "config.sample_questions.0.id"),
        ("unsupported_version.yaml", ValidationError, "version"),
        ("unsupported_field.yaml", ValidationError, "data_sources.metric_views"),
        ("malformed_join.yaml", ValidationError, "instructions.join_specs.0.sql"),
        ("duplicate_question_ids.yaml", DefinitionError, "config.sample_questions"),
        ("duplicate_instruction_ids.yaml", DefinitionError, "instructions"),
        ("duplicate_column_identity.yaml", DefinitionError, "column_configs"),
    ],
)
def test_invalid_definitions_report_the_relevant_path(
    fixture_name: str,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        compile_definition(FIXTURE_ROOT / "inputs" / fixture_name)


@pytest.mark.parametrize(
    "value",
    [
        "line one\nline two",
        "line one\r\nline two",
        "line one\n",
        "line one\n\nline three",
    ],
)
def test_scalar_string_lists_preserve_newlines_as_one_element(
    tmp_path: Path,
    value: str,
) -> None:
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(
        yaml.safe_dump(
            {
                "version": 2,
                "instructions": {"text_instructions": [{"content": value}]},
            },
        ),
        encoding="utf-8",
    )

    definition = compile_definition(source_path)

    assert definition.instructions is not None
    assert definition.instructions.text_instructions is not None
    assert definition.instructions.text_instructions[0].content == [value]


def test_string_list_input_remains_multiple_elements(tmp_path: Path) -> None:
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(
        yaml.safe_dump(
            {
                "version": 2,
                "instructions": {
                    "text_instructions": [{"content": ["first", "second"]}],
                },
            },
        ),
        encoding="utf-8",
    )

    definition = compile_definition(source_path)

    assert definition.instructions is not None
    assert definition.instructions.text_instructions is not None
    assert definition.instructions.text_instructions[0].content == [
        "first",
        "second",
    ]


def test_omitted_id_is_stable_across_processes(tmp_path: Path) -> None:
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(
        "version: 2\nconfig:\n  sample_questions:\n    - question: Stable?\n",
        encoding="utf-8",
    )
    script = (
        "from pathlib import Path; "
        "from yaml2genie import compile_definition; "
        "document = compile_definition(Path(__import__('sys').argv[1])); "
        "print(document.config.sample_questions[0].id)"
    )

    ids = [
        subprocess.run(  # noqa: S603
            [sys.executable, "-c", script, str(source_path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        for _ in range(2)
    ]

    assert ids[0] == ids[1]


def test_stable_key_keeps_generated_id_when_content_changes(tmp_path: Path) -> None:
    source_path = tmp_path / "definition.yaml"
    source = {
        "version": 2,
        "config": {
            "sample_questions": [
                {
                    "stable_key": "monthly-orders",
                    "question": "How many orders this month?",
                },
            ],
        },
    }
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    before = compile_definition(source_path)
    source["config"]["sample_questions"][0]["question"] = (
        "How many completed orders this month?"
    )
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")
    after = compile_definition(source_path)

    assert before.config is not None
    assert before.config.sample_questions is not None
    assert after.config is not None
    assert after.config.sample_questions is not None
    assert before.config.sample_questions[0].id == after.config.sample_questions[0].id
    assert "stable_key" not in after.model_dump_json()


def test_id_collision_reports_both_source_locations(tmp_path: Path) -> None:
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(
        """version: 2
instructions:
  text_instructions:
    - id: "00000000000000000000000000000001"
      content: Be concise.
  example_question_sqls:
    - id: "00000000000000000000000000000001"
      question: How many orders?
""",
        encoding="utf-8",
    )

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "instructions.text_instructions[0].id" in message
    assert "instructions.example_question_sqls[0].id" in message


def test_duplicate_stable_keys_report_both_source_locations(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"stable_key": "orders", "question": "How many orders?"},
                {"stable_key": "orders", "question": "What is revenue?"},
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "config.sample_questions[0].stable_key" in message
    assert "config.sample_questions[1].stable_key" in message


def test_generated_id_collision_reports_both_source_locations(tmp_path: Path) -> None:
    question = {"question": "How many orders?"}
    source = {
        "version": 2,
        "config": {"sample_questions": [question, question.copy()]},
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "config.sample_questions[0].id" in message
    assert "config.sample_questions[1].id" in message


def test_explicit_generated_collision_reports_both_locations(tmp_path: Path) -> None:
    source_path = tmp_path / "definition.yaml"
    generated_source = {
        "version": 2,
        "config": {"sample_questions": [{"question": "How many orders?"}]},
    }
    source_path.write_text(yaml.safe_dump(generated_source), encoding="utf-8")
    generated = compile_definition(source_path)
    assert generated.config is not None
    assert generated.config.sample_questions is not None
    generated_id = generated.config.sample_questions[0].id
    generated_source["config"]["sample_questions"].append(
        {"id": generated_id, "question": "What is revenue?"},
    )
    source_path.write_text(yaml.safe_dump(generated_source), encoding="utf-8")

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "config.sample_questions[0].id" in message
    assert "config.sample_questions[1].id" in message


def test_all_normalized_collections_are_sorted_and_unique(tmp_path: Path) -> None:
    def identified(identifier: int, **content: object) -> dict[str, object]:
        return {"id": f"{identifier:032x}", **content}

    join = {
        "left": {"identifier": "sales.analytics.orders", "alias": "orders"},
        "right": {
            "identifier": "sales.analytics.customers",
            "alias": "customers",
        },
        "sql": [
            "`orders`.`customer_id` = `customers`.`customer_id`",
            "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
        ],
    }
    source = {
        "version": 2,
        "config": {
            "sample_questions": [
                identified(2, question="Second"),
                identified(1, question="First"),
            ],
        },
        "data_sources": {
            "tables": [
                {
                    "identifier": "sales.analytics.orders",
                    "column_configs": [
                        {"column_name": "order_date"},
                        {"column_name": "customer_id"},
                    ],
                },
                {"identifier": "sales.analytics.customers"},
            ],
        },
        "instructions": {
            "text_instructions": [identified(3, content="Guidance")],
            "example_question_sqls": [
                identified(5, question="Second"),
                identified(4, question="First"),
            ],
            "join_specs": [identified(7, **join), identified(6, **join)],
            "sql_snippets": {
                "filters": [
                    identified(9, sql="second_filter"),
                    identified(8, sql="first_filter"),
                ],
                "expressions": [
                    identified(11, sql="second_expression"),
                    identified(10, sql="first_expression"),
                ],
                "measures": [
                    identified(13, sql="second_measure"),
                    identified(12, sql="first_measure"),
                ],
            },
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    document = compile_definition(source_path).model_dump(exclude_none=True)

    id_collections = [
        document["config"]["sample_questions"],
        document["instructions"]["text_instructions"],
        document["instructions"]["example_question_sqls"],
        document["instructions"]["join_specs"],
        document["instructions"]["sql_snippets"]["filters"],
        document["instructions"]["sql_snippets"]["expressions"],
        document["instructions"]["sql_snippets"]["measures"],
    ]
    for collection in id_collections:
        identifiers = [item["id"] for item in collection]
        assert identifiers == sorted(set(identifiers))

    tables = document["data_sources"]["tables"]
    table_identifiers = [table["identifier"] for table in tables]
    assert table_identifiers == sorted(set(table_identifiers))
    order_columns = tables[1]["column_configs"]
    column_names = [column["column_name"] for column in order_columns]
    assert column_names == sorted(set(column_names))
