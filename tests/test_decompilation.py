import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from yaml2genie import compile_definition
from yaml2genie.cli import app
from yaml2genie.errors import ErrorExitCode

FIXTURE_ROOT = Path(__file__).parent
runner = CliRunner()


def test_decompile_writes_yaml_that_round_trips_to_normalized_json(
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/phase1_supported.json"
    output_path = tmp_path / "definition.yaml"
    expected = json.loads(input_path.read_text(encoding="utf-8"))

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert output_path.is_file()
    assert compile_definition(output_path).model_dump(exclude_none=True) == expected


def test_decompile_accepts_escaped_serialized_object(tmp_path: Path) -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/phase1_supported.json").read_text(
            encoding="utf-8",
        ),
    )
    input_path = tmp_path / "serialized.json"
    input_path.write_text(json.dumps(json.dumps(expected)), encoding="utf-8")
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert compile_definition(output_path).model_dump(exclude_none=True) == expected


def test_decompile_renders_readable_yaml(tmp_path: Path) -> None:
    input_path = tmp_path / "serialized.json"
    input_path.write_text(
        json.dumps(
            {
                "version": 2,
                "instructions": {
                    "text_instructions": [
                        {
                            "id": "00000000000000000000000000000001",
                            "content": [
                                "Answer with totals.\nDo not include tax.",
                            ],
                        },
                    ],
                },
            },
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    rendered = output_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert rendered.startswith("version: 2\ninstructions:\n")
    block_scalar = (
        "content: |-\n        Answer with totals.\n        Do not include tax.\n"
    )
    assert block_scalar in rendered


def test_decompile_renders_single_string_lists_as_scalars(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "artifacts/phase1_supported.json"
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    rendered = output_path.read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "question: What is total revenue?\n" in rendered
    assert "sql: SELECT SUM(order_amount) FROM sales.analytics.orders\n" in rendered
    assert "sql:\n        -" in rendered


@pytest.mark.parametrize(
    ("fixture_name", "category", "exit_code"),
    [
        ("malformed.json", "source parse", ErrorExitCode.SOURCE_PARSE),
        ("missing_version.json", "schema", ErrorExitCode.SCHEMA),
        ("missing_item_id.json", "schema", ErrorExitCode.SCHEMA),
        ("unsupported_version.json", "schema", ErrorExitCode.SCHEMA),
        ("unsupported_field.json", "schema", ErrorExitCode.SCHEMA),
    ],
)
def test_decompile_rejects_invalid_json_without_creating_output(
    fixture_name: str,
    category: str,
    exit_code: ErrorExitCode,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        [
            "decompile",
            str(FIXTURE_ROOT / "inputs" / fixture_name),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == exit_code
    assert f"Error [{category}]" in result.stderr
    assert not output_path.exists()


def test_decompile_requires_overwrite_and_replaces_atomically(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"
    output_path = tmp_path / "definition.yaml"
    original = "hand-edited YAML\n"
    output_path.write_text(original, encoding="utf-8")

    rejected = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )
    assert rejected.exit_code == ErrorExitCode.OUTPUT
    assert output_path.read_text(encoding="utf-8") == original

    accepted = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path), "--overwrite"],
    )

    assert accepted.exit_code == 0
    assert compile_definition(output_path).model_dump(exclude_none=True) == json.loads(
        input_path.read_text(encoding="utf-8"),
    )
