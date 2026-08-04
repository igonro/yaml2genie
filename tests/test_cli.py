import json
import re
from importlib.metadata import version as package_version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from yaml2genie.cli import app
from yaml2genie.errors import ErrorExitCode

FIXTURE_ROOT = Path(__file__).parent
runner = CliRunner()


def test_validate_accepts_definition_without_writing(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "inputs/minimal.yaml"

    result = runner.invoke(app, ["validate", str(input_path)])

    assert result.exit_code == 0
    assert result.stdout == "Valid Genie Agent definition.\n"
    assert list(tmp_path.iterdir()) == []


def test_validate_accepts_grouped_definition_directory() -> None:
    input_path = FIXTURE_ROOT / "inputs/grouped_genie"

    result = runner.invoke(app, ["validate", str(input_path)])

    assert result.exit_code == 0
    assert result.stdout == "Valid Genie Agent definition.\n"


def test_build_writes_expected_deterministic_json(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "inputs/minimal.yaml"
    expected = (FIXTURE_ROOT / "artifacts/minimal.json").read_bytes()
    output_path = tmp_path / "nested" / "definition.json"

    first = runner.invoke(
        app,
        ["build", str(input_path), "--output", str(output_path)],
    )
    first_bytes = output_path.read_bytes()
    second = runner.invoke(
        app,
        ["build", str(input_path), "--output", str(output_path)],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first_bytes == expected
    assert output_path.read_bytes() == first_bytes


def test_check_accepts_current_artifact(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "inputs/minimal.yaml"
    artifact_path = tmp_path / "definition.json"
    artifact_path.write_bytes((FIXTURE_ROOT / "artifacts/minimal.json").read_bytes())

    result = runner.invoke(
        app,
        ["check", str(input_path), "--artifact", str(artifact_path)],
    )

    assert result.exit_code == 0
    assert result.stdout == f"Artifact is up to date: {artifact_path}\n"
    assert result.stderr == ""


def test_check_reports_reviewable_diff_for_stale_artifact(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "inputs/minimal.yaml"
    artifact_path = tmp_path / "definition.json"
    artifact_path.write_text('{"version": 1}\n', encoding="utf-8")

    result = runner.invoke(
        app,
        ["check", str(input_path), "--artifact", str(artifact_path)],
    )

    assert result.exit_code == ErrorExitCode.STALE
    assert "--- " in result.stderr
    assert "+++ generated" in result.stderr
    assert '-{"version": 1}' in result.stderr
    assert '+    "version": 2' in result.stderr
    assert "Error [stale]" in result.stderr


def test_build_supports_stdin_stdout_and_yaml_format() -> None:
    result = runner.invoke(
        app,
        ["build", "-", "--output", "-", "--format", "yaml"],
        input="version: 2\n",
    )

    assert result.exit_code == 0
    assert result.stdout == "version: 2\n"


def test_example_writes_complete_supported_definition(tmp_path: Path) -> None:
    output_path = tmp_path / "genie.example.json"
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/phase4_supported.json").read_text(
            encoding="utf-8",
        ),
    )

    result = runner.invoke(app, ["example", "--output", str(output_path)])

    assert result.exit_code == 0
    assert json.loads(output_path.read_text(encoding="utf-8")) == expected


def test_decompile_supports_stdout() -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"

    result = runner.invoke(app, ["decompile", str(input_path), "--output", "-"])

    assert result.exit_code == 0
    assert result.stdout.startswith("version: 2\n")
    assert "config:" in result.stdout


def test_build_infers_yaml_format_from_output_suffix(tmp_path: Path) -> None:
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        [
            "build",
            str(FIXTURE_ROOT / "inputs/minimal.yaml"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.read_text(encoding="utf-8").startswith("version: 2\n")
    assert "config:" in output_path.read_text(encoding="utf-8")


def test_build_replaces_existing_output_atomically(tmp_path: Path) -> None:
    output_path = tmp_path / "definition.json"
    output_path.write_text("hand edited\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "build",
            str(FIXTURE_ROOT / "inputs/minimal.yaml"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert (
        output_path.read_bytes()
        == (FIXTURE_ROOT / "artifacts/minimal.json").read_bytes()
    )


def test_build_escapes_json_content_deterministically(tmp_path: Path) -> None:
    input_path = tmp_path / "definition.yaml"
    input_path.write_text(
        "version: 2\nconfig:\n  sample_questions:\n    - question: 'Qué ventas\\n'\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "definition.json"

    result = runner.invoke(
        app,
        ["build", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    rendered = output_path.read_text(encoding="utf-8")
    assert '"Qué ventas\\\\n"' in rendered
    assert json.loads(rendered)["config"]["sample_questions"][0]["question"] == [
        "Qué ventas\\n",
    ]


def test_build_normalizes_yaml_line_endings(tmp_path: Path) -> None:
    input_path = tmp_path / "definition.yaml"
    input_path.write_bytes(b"version: 2\r\n")
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        ["build", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert output_path.read_bytes() == b"version: 2\n"


@pytest.mark.parametrize(
    "arguments",
    [
        ["--help"],
        ["validate", "--help"],
        ["build", "--help"],
        ["example", "--help"],
        ["decompile", "--help"],
        ["check", "--help"],
    ],
)
def test_every_command_has_help(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_root_help_describes_each_command() -> None:
    result = runner.invoke(app, ["--help"])
    unstyled_help = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout)
    help_text = " ".join(unstyled_help.split())

    assert result.exit_code == 0
    assert "validate Validate a Genie Agent definition." in help_text
    assert "build Compile a definition into Genie Agent JSON or YAML." in help_text
    assert "example Write a complete supported Genie Agent JSON example." in help_text
    assert "decompile Convert Genie Agent JSON to YAML source." in help_text
    assert "check Compare a generated artifact with its source." in help_text


def test_version_output() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout == f"yaml2genie {package_version('yaml2genie')}\n"


def test_quiet_suppresses_success_message() -> None:
    result = runner.invoke(
        app,
        ["--quiet", "validate", str(FIXTURE_ROOT / "inputs/minimal.yaml")],
    )

    assert result.exit_code == 0
    assert result.stdout == ""


def test_verbose_prints_diagnostic_context() -> None:
    result = runner.invoke(
        app,
        ["--verbose", "validate", str(FIXTURE_ROOT / "inputs/minimal.yaml")],
    )

    assert result.exit_code == 0
    assert "[verbose] compile input" in result.stderr
    assert result.stdout == "Valid Genie Agent definition.\n"


def test_failed_build_preserves_existing_output(tmp_path: Path) -> None:
    output_path = tmp_path / "definition.json"
    original = b"existing artifact\n"
    output_path.write_bytes(original)

    result = runner.invoke(
        app,
        [
            "build",
            str(FIXTURE_ROOT / "inputs/malformed.yaml"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code != 0
    assert "malformed.yaml" in result.stderr
    assert output_path.read_bytes() == original


def test_validation_error_is_concise_and_has_field_path() -> None:
    result = runner.invoke(
        app,
        ["validate", str(FIXTURE_ROOT / "inputs/unsupported_field.yaml")],
    )

    assert result.exit_code != 0
    assert "data_sources.future_sources" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "fixture_name",
    [
        "malformed.yaml",
        "invalid_id.yaml",
        "unsupported_version.yaml",
        "unsupported_field.yaml",
        "malformed_join.yaml",
        "duplicate_question_ids.yaml",
        "duplicate_instruction_ids.yaml",
        "duplicate_column_identity.yaml",
    ],
)
def test_validate_rejects_invalid_fixture(fixture_name: str) -> None:
    result = runner.invoke(
        app,
        ["validate", str(FIXTURE_ROOT / "inputs" / fixture_name)],
    )

    assert result.exit_code != 0
    assert fixture_name in result.stderr


@pytest.mark.parametrize(
    ("fixture_name", "category", "exit_code", "path"),
    [
        ("malformed.yaml", "source parse", 2, "malformed.yaml"),
        ("invalid_id.yaml", "schema", 3, "config.sample_questions[0].id"),
        (
            "duplicate_instruction_ids.yaml",
            "semantic",
            4,
            "instructions.text_instructions[0].id",
        ),
    ],
)
def test_validate_uses_structured_error_exit_codes(
    fixture_name: str,
    category: str,
    exit_code: int,
    path: str,
) -> None:
    result = runner.invoke(
        app,
        ["validate", str(FIXTURE_ROOT / "inputs" / fixture_name)],
    )

    assert result.exit_code == exit_code
    assert f"Error [{category}]" in result.stderr
    assert path in result.stderr
    assert "Traceback" not in result.stderr


def test_build_reports_output_errors_with_stable_exit_code(tmp_path: Path) -> None:
    blocking_parent = tmp_path / "not-a-directory"
    blocking_parent.write_text("file", encoding="utf-8")
    output_path = blocking_parent / "definition.json"

    result = runner.invoke(
        app,
        [
            "build",
            str(FIXTURE_ROOT / "inputs/minimal.yaml"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == ErrorExitCode.OUTPUT
    assert "Error [output]" in result.stderr
    assert str(output_path) in result.stderr
    assert "Traceback" not in result.stderr
