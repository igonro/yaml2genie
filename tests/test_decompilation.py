import json
import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from yaml2genie import compile_definition, rendering
from yaml2genie.cli import app
from yaml2genie.errors import ErrorExitCode
from yaml2genie.models import DefinitionDocument
from yaml2genie.rendering import PlannedFile, write_source_tree_atomic

FIXTURE_ROOT = Path(__file__).parent
runner = CliRunner()


def test_yaml_presentation_is_schema_aware_and_raw_is_lossless() -> None:
    document = DefinitionDocument.model_validate(
        {
            "version": 2,
            "config": {
                "sample_questions": [
                    {
                        "id": "00000000000000000000000000000001",
                        "question": ["First line\r\n", "Second line\n", "Last line"],
                    },
                ],
            },
            "data_sources": {
                "tables": [
                    {
                        "identifier": "catalog.schema.table",
                        "column_configs": [
                            {"column_name": "category", "synonyms": ["kind"]},
                        ],
                    },
                ],
            },
            "instructions": {
                "text_instructions": [
                    {
                        "id": "00000000000000000000000000000003",
                        "content": ["Keep this space \r\n", "and this line."],
                    },
                ],
                "join_specs": [
                    {
                        "id": "00000000000000000000000000000002",
                        "left": {
                            "identifier": "catalog.schema.left",
                            "alias": "left",
                        },
                        "right": {
                            "identifier": "catalog.schema.right",
                            "alias": "right",
                        },
                        "sql": [
                            "SELECT " + "x" * 1_000,
                            "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
                        ],
                    },
                ],
            },
        },
    )

    pretty = rendering.render_yaml(document)
    raw = rendering.render_yaml(
        document,
        options=rendering.YamlRenderOptions(pretty=False),
    )
    pretty_payload = yaml.safe_load(pretty)
    raw_payload = yaml.safe_load(raw)

    assert pretty_payload["config"]["sample_questions"][0]["question"] == (
        "First line\nSecond line\nLast line"
    )
    assert pretty_payload["data_sources"]["tables"][0]["column_configs"][0][
        "synonyms"
    ] == ["kind"]
    assert pretty_payload["instructions"]["join_specs"][0]["sql"] == [
        "SELECT " + "x" * 1_000,
        "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
    ]
    assert pretty_payload["instructions"]["text_instructions"][0]["content"] == (
        "Keep this space \nand this line."
    )
    assert "content: |-\n        Keep this space \n" in pretty
    assert "\\\n" not in pretty
    assert raw_payload["config"]["sample_questions"][0]["question"] == [
        "First line\r\n",
        "Second line\n",
        "Last line",
    ]
    assert raw_payload["data_sources"]["tables"][0]["column_configs"][0][
        "synonyms"
    ] == ["kind"]


def test_decompile_cli_pretty_raw_and_json_modes_are_independent(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "definition.json"
    input_path.write_text(
        json.dumps(
            {
                "version": 2,
                "config": {
                    "sample_questions": [
                        {
                            "id": "00000000000000000000000000000001",
                            "question": ["First\r\n", "Last"],
                        },
                    ],
                },
            },
        ),
        encoding="utf-8",
    )

    pretty = runner.invoke(app, ["decompile", str(input_path), "--output", "-"])
    raw = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", "-", "--raw"],
    )
    rendered_json = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            "-",
            "--format",
            "json",
            "--omit-ids",
        ],
    )

    assert pretty.exit_code == 0
    assert (
        yaml.safe_load(pretty.stdout)["config"]["sample_questions"][0]["question"]
        == "First\nLast"
    )
    assert raw.exit_code == 0
    assert yaml.safe_load(raw.stdout)["config"]["sample_questions"][0]["question"] == [
        "First\r\n",
        "Last",
    ]
    assert rendered_json.exit_code == 0
    assert (
        json.loads(rendered_json.stdout)["config"]["sample_questions"][0]["id"]
        == "00000000000000000000000000000001"
    )


@pytest.mark.parametrize(
    "layout",
    ["central", "grouped", "category-split", "fully-split", "mixed"],
)
def test_decompile_omit_ids_preserves_item_filenames_and_regenerates_ids(
    layout: str,
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "definition.json"
    input_path.write_text(
        json.dumps(
            {
                "version": 2,
                "config": {
                    "sample_questions": [
                        {
                            "id": "00000000000000000000000000000001",
                            "question": ["How many orders?"],
                        },
                    ],
                },
                "instructions": {
                    "sql_snippets": {
                        "filters": [
                            {
                                "id": "00000000000000000000000000000002",
                                "sql": ["status = 'open'"],
                            },
                        ],
                    },
                },
            },
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / (
        "definition.yaml" if layout == "central" else "definition"
    )
    arguments = [
        "decompile",
        str(input_path),
        "--output",
        str(output_path),
        "--omit-ids",
    ]
    if layout != "central":
        arguments.extend(["--layout", layout])

    result = runner.invoke(app, arguments)

    assert result.exit_code == 0
    contents = (
        output_path.read_text(encoding="utf-8")
        if layout == "central"
        else "\n".join(
            path.read_text(encoding="utf-8") for path in output_path.rglob("*.yaml")
        )
    )
    assert "id:" not in contents
    if layout == "fully-split":
        assert (
            output_path
            / "config/sample_questions/00000000000000000000000000000001.yaml"
        ).is_file()
    if layout == "mixed":
        assert (
            output_path / "examples/filters/00000000000000000000000000000002.yaml"
        ).is_file()
    compiled = compile_definition(output_path).model_dump(exclude_none=True)
    assert re.fullmatch(
        r"[0-9a-f]{32}",
        compiled["config"]["sample_questions"][0]["id"],
    )


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


def test_decompile_preserves_all_supported_v2_fields(tmp_path: Path) -> None:
    input_path = FIXTURE_ROOT / "artifacts/phase4_supported.json"
    output_path = tmp_path / "definition.yaml"
    expected = json.loads(input_path.read_text(encoding="utf-8"))

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    rendered = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert (
        rendered["benchmarks"]["questions"][0]["evaluation_note"] == "Make no errors."
    )
    assert compile_definition(output_path).model_dump(exclude_none=True) == expected


def test_version_error_names_the_supported_version(tmp_path: Path) -> None:
    input_path = tmp_path / "definition.json"
    input_path.write_text('{"version": 3}', encoding="utf-8")
    output_path = tmp_path / "definition.yaml"

    result = runner.invoke(
        app,
        ["decompile", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == ErrorExitCode.SCHEMA
    assert "version" in result.stderr
    assert "Input should be 2" in result.stderr
    assert not output_path.exists()


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


def test_decompile_accepts_databricks_get_space_response(tmp_path: Path) -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/phase1_supported.json").read_text(
            encoding="utf-8",
        ),
    )
    input_path = tmp_path / "get-space-response.json"
    input_path.write_text(
        json.dumps(
            {
                "etag": "test-etag",
                "parent_path": "/Users/test@example.com",
                "serialized_space": json.dumps(expected),
                "space_id": "01f17f784c701bce84a1415424937544",
                "title": "Sales Assistant",
                "warehouse_id": "1234567890123456",
            },
        ),
        encoding="utf-8",
    )
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


def test_decompile_fully_split_dry_run_prints_deterministic_file_plan(
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"
    output_path = tmp_path / "definition"

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "CREATE genie.yaml",
        "CREATE config/sample_questions/00000000000000000000000000000001.yaml",
        "CREATE instructions/text_instructions/00000000000000000000000000000002.yaml",
        "CREATE sources/tables/sales.analytics.orders.yaml",
    ]
    assert not output_path.exists()


def test_decompile_fully_split_plan_is_sorted_by_relative_path(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "definition.json"
    input_path.write_text(
        json.dumps(
            {
                "version": 2,
                "config": {
                    "sample_questions": [
                        {
                            "id": "00000000000000000000000000000002",
                            "question": ["Second"],
                        },
                        {
                            "id": "00000000000000000000000000000001",
                            "question": ["First"],
                        },
                    ],
                },
            },
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "definition"

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "CREATE genie.yaml",
        "CREATE config/sample_questions/00000000000000000000000000000001.yaml",
        "CREATE config/sample_questions/00000000000000000000000000000002.yaml",
    ]


def test_source_tree_write_failure_preserves_existing_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "definition"
    output_path.mkdir()
    (output_path / "genie.yaml").write_text(
        "version: 2\nlayout: grouped\n",
        encoding="utf-8",
    )
    planned_files = [
        PlannedFile(Path("genie.yaml"), "version: 2\nlayout: fully-split\n"),
        PlannedFile(Path("sources/tables.yaml"), "- identifier: broken\n"),
    ]
    original_write_text = Path.write_text

    def fail_on_tables(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path.name == "tables.yaml":
            message = "simulated staging failure"
            raise OSError(message)
        return original_write_text(
            path,
            data,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

    monkeypatch.setattr(Path, "write_text", fail_on_tables)

    with pytest.raises(OSError, match="simulated staging failure"):
        write_source_tree_atomic(planned_files, output_path, overwrite=True)

    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        "version: 2\nlayout: grouped\n"
    )
    assert not (output_path / "sources").exists()


def test_decompile_fully_split_writes_tree_that_round_trips(
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/phase4_supported.json"
    output_path = tmp_path / "definition"
    expected = json.loads(input_path.read_text(encoding="utf-8"))

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
        ],
    )

    assert result.exit_code == 0
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        "version: 2\nlayout: fully-split\n"
    )
    assert compile_definition(output_path).model_dump(exclude_none=True) == expected


@pytest.mark.parametrize("layout", ["grouped", "category-split", "mixed"])
def test_decompile_layout_writes_tree_that_round_trips(
    layout: str,
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/phase4_supported.json"
    output_path = tmp_path / "definition"
    expected = json.loads(input_path.read_text(encoding="utf-8"))

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            layout,
        ],
    )

    assert result.exit_code == 0
    assert compile_definition(output_path).model_dump(exclude_none=True) == expected


def test_decompile_rejects_filename_collisions_without_replacing_tree(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "definition.json"
    input_path.write_text(
        json.dumps(
            {
                "version": 2,
                "data_sources": {
                    "tables": [
                        {"identifier": "sales.analytics.a/b"},
                        {"identifier": "sales.analytics.a?b"},
                    ],
                },
            },
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "definition"
    output_path.mkdir()
    original_manifest = "version: 2\nlayout: grouped\n"
    (output_path / "genie.yaml").write_text(original_manifest, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--overwrite",
        ],
    )

    assert result.exit_code == ErrorExitCode.OUTPUT
    assert "filename collisions" in result.stderr
    assert "sales.analytics.a/b" in result.stderr
    assert "sales.analytics.a?b" in result.stderr
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        original_manifest
    )


def test_decompile_source_tree_requires_overwrite_and_replaces_tree(
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"
    output_path = tmp_path / "definition"
    output_path.mkdir()
    original_manifest = "version: 2\nlayout: grouped\n"
    (output_path / "genie.yaml").write_text(original_manifest, encoding="utf-8")
    (output_path / "hand-edited.yaml").write_text("keep me\n", encoding="utf-8")

    rejected = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
        ],
    )

    assert rejected.exit_code == ErrorExitCode.OUTPUT
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        original_manifest
    )
    assert (output_path / "hand-edited.yaml").is_file()

    accepted = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--overwrite",
        ],
    )

    assert accepted.exit_code == 0
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        "version: 2\nlayout: fully-split\n"
    )
    assert not (output_path / "hand-edited.yaml").exists()


def test_decompile_source_tree_dry_run_respects_overwrite_protection(
    tmp_path: Path,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"
    output_path = tmp_path / "definition"
    output_path.mkdir()
    original_manifest = "version: 2\nlayout: grouped\n"
    (output_path / "genie.yaml").write_text(original_manifest, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--dry-run",
        ],
    )

    assert result.exit_code == ErrorExitCode.OUTPUT
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        original_manifest
    )


def test_decompile_source_tree_restores_existing_tree_after_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = FIXTURE_ROOT / "artifacts/minimal.json"
    output_path = tmp_path / "definition"
    output_path.mkdir()
    original_manifest = "version: 2\nlayout: grouped\n"
    (output_path / "genie.yaml").write_text(original_manifest, encoding="utf-8")
    original_rmtree = rendering.shutil.rmtree
    calls = 0

    def fail_first_cleanup(path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            msg = "simulated cleanup failure"
            raise OSError(msg)
        original_rmtree(path)

    monkeypatch.setattr(rendering.shutil, "rmtree", fail_first_cleanup)

    result = runner.invoke(
        app,
        [
            "decompile",
            str(input_path),
            "--output",
            str(output_path),
            "--layout",
            "fully-split",
            "--overwrite",
        ],
    )

    assert result.exit_code == ErrorExitCode.OUTPUT
    assert (output_path / "genie.yaml").read_text(encoding="utf-8") == (
        original_manifest
    )
    assert not (output_path / "config").exists()
