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
