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


def test_all_documented_v2_fields_compile_to_expected_definition() -> None:
    expected = json.loads(
        (FIXTURE_ROOT / "artifacts/phase4_supported.json").read_text(
            encoding="utf-8",
        ),
    )

    definition = compile_definition(FIXTURE_ROOT / "inputs/phase4_supported.yaml")

    assert definition.model_dump(exclude_none=True) == expected


@pytest.mark.parametrize("layout", ["grouped", "category-split"])
def test_decentralized_layout_compiles_to_centralized_artifact(
    layout: str,
) -> None:
    expected = compile_definition(
        FIXTURE_ROOT / "inputs/centralized_genie.yaml",
    ).model_dump(exclude_none=True)

    definition = compile_definition(FIXTURE_ROOT / "inputs" / f"{layout}_genie")

    assert definition.model_dump(exclude_none=True) == expected


def test_decentralized_fallback_ids_do_not_depend_on_absolute_root(
    tmp_path: Path,
) -> None:
    roots = [tmp_path / "first/grouped_genie", tmp_path / "second/grouped_genie"]
    for root in roots:
        root.mkdir(parents=True)
        (root / "genie.yaml").write_text(
            "version: 2\nlayout: grouped\n",
            encoding="utf-8",
        )
        (root / "config.yaml").write_text(
            "sample_questions:\n  - question: How many orders?\n",
            encoding="utf-8",
        )

    documents = [compile_definition(root) for root in roots]

    assert documents[0] == documents[1]


def test_decentralized_omitted_ids_are_stable_for_each_relative_source_path(
    tmp_path: Path,
) -> None:
    root = tmp_path / "grouped_genie"
    root.mkdir()
    (root / "genie.yaml").write_text(
        "version: 2\nlayout: grouped\n",
        encoding="utf-8",
    )
    (root / "config.yaml").write_text(
        "sample_questions:\n  - question: How many orders?\n",
        encoding="utf-8",
    )

    first = compile_definition(root)
    second = compile_definition(root)

    assert first == second
    assert first.config is not None
    assert first.config.sample_questions is not None
    assert first.config.sample_questions[0].id


def test_decentralized_layout_treats_missing_optional_files_as_empty(
    tmp_path: Path,
) -> None:
    root = tmp_path / "grouped_genie"
    root.mkdir()
    (root / "genie.yaml").write_text(
        "version: 2\nlayout: grouped\n",
        encoding="utf-8",
    )

    definition = compile_definition(root)

    assert definition.model_dump(exclude_none=True) == {"version": 2}


def test_decentralized_duplicate_ids_name_both_source_files(tmp_path: Path) -> None:
    root = tmp_path / "category_split_genie"
    (root / "config").mkdir(parents=True)
    (root / "benchmarks").mkdir()
    (root / "genie.yaml").write_text(
        "version: 2\nlayout: category-split\n",
        encoding="utf-8",
    )
    shared_id = "00000000000000000000000000000001"
    (root / "config" / "sample_questions.yaml").write_text(
        f'- id: "{shared_id}"\n  question: Sample question\n',
        encoding="utf-8",
    )
    (root / "benchmarks" / "questions.yaml").write_text(
        '- id: "'
        f'{shared_id}"\n'
        "  question: Benchmark question\n"
        "  answer:\n"
        "    - format: SQL\n"
        "      content: SELECT 1\n",
        encoding="utf-8",
    )

    with pytest.raises(DefinitionError) as error:
        compile_definition(root)

    message = str(error.value)
    assert "config/sample_questions.yaml" in message
    assert "benchmarks/questions.yaml" in message


def test_decentralized_layout_rejects_unknown_category_file(tmp_path: Path) -> None:
    root = tmp_path / "category_split_genie"
    (root / "sources").mkdir(parents=True)
    (root / "genie.yaml").write_text(
        "version: 2\nlayout: category-split\n",
        encoding="utf-8",
    )
    (root / "sources" / "views.yaml").write_text("[]\n", encoding="utf-8")

    with pytest.raises(DefinitionError, match=r"sources/views\.yaml"):
        compile_definition(root)


def test_decentralized_broken_join_reference_names_source_file(tmp_path: Path) -> None:
    root = tmp_path / "category_split_genie"
    (root / "examples").mkdir(parents=True)
    (root / "genie.yaml").write_text(
        "version: 2\nlayout: category-split\n",
        encoding="utf-8",
    )
    (root / "examples" / "joins.yaml").write_text(
        "- left:\n"
        "    identifier: sales.analytics.orders\n"
        "    alias: orders\n"
        "  right:\n"
        "    identifier: sales.analytics.customers\n"
        "    alias: customers\n"
        "  sql:\n"
        "    - '`orders`.`customer_id` = `accounts`.`customer_id`'\n"
        "    - '--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--'\n",
        encoding="utf-8",
    )

    with pytest.raises(DefinitionError) as error:
        compile_definition(root)

    assert "examples/joins.yaml" in str(error.value)


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


def test_metric_views_compile_with_sorted_column_configuration(
    tmp_path: Path,
) -> None:
    source = {
        "version": 2,
        "data_sources": {
            "metric_views": [
                {
                    "identifier": "sales.analytics.revenue_metrics",
                    "description": "Revenue metrics by region.",
                    "column_configs": [
                        {"column_name": "revenue", "synonyms": ["sales"]},
                        {"column_name": "region", "exclude": False},
                    ],
                },
                {"identifier": "sales.analytics.customer_metrics"},
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    document = compile_definition(source_path).model_dump(exclude_none=True)

    metric_views = document["data_sources"]["metric_views"]
    assert [view["identifier"] for view in metric_views] == [
        "sales.analytics.customer_metrics",
        "sales.analytics.revenue_metrics",
    ]
    assert metric_views[0] == {
        "identifier": "sales.analytics.customer_metrics",
    }
    assert metric_views[1]["description"] == ["Revenue metrics by region."]
    assert metric_views[1]["column_configs"] == [
        {"column_name": "region", "exclude": False},
        {"column_name": "revenue", "synonyms": ["sales"]},
    ]


def test_sql_functions_compile_in_documented_order(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "instructions": {
            "sql_functions": [
                {
                    "id": "00000000000000000000000000000002",
                    "identifier": "sales.analytics.fiscal_year",
                },
                {
                    "id": "00000000000000000000000000000001",
                    "identifier": "sales.analytics.fiscal_quarter",
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    document = compile_definition(source_path).model_dump(exclude_none=True)

    assert document["instructions"]["sql_functions"] == [
        {
            "id": "00000000000000000000000000000001",
            "identifier": "sales.analytics.fiscal_quarter",
        },
        {
            "id": "00000000000000000000000000000002",
            "identifier": "sales.analytics.fiscal_year",
        },
    ]


def test_benchmark_questions_compile_in_id_order(tmp_path: Path) -> None:
    source = {
        "version": 2,
        "benchmarks": {
            "questions": [
                {
                    "id": "00000000000000000000000000000002",
                    "question": "Second question",
                    "answer": [{"format": "SQL", "content": "SELECT 2"}],
                },
                {
                    "id": "00000000000000000000000000000001",
                    "question": "First question",
                    "answer": [{"format": "SQL", "content": "SELECT 1"}],
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    document = compile_definition(source_path).model_dump(exclude_none=True)

    questions = document["benchmarks"]["questions"]
    assert [question["id"] for question in questions] == [
        "00000000000000000000000000000001",
        "00000000000000000000000000000002",
    ]


@pytest.mark.parametrize(
    "answer",
    [
        [],
        [
            {"format": "SQL", "content": "SELECT 1"},
            {"format": "SQL", "content": "SELECT 2"},
        ],
        [{"format": "CSV", "content": "not SQL"}],
    ],
)
def test_benchmark_question_requires_one_sql_answer(
    answer: list[dict[str, object]],
    tmp_path: Path,
) -> None:
    source = {
        "version": 2,
        "benchmarks": {
            "questions": [
                {
                    "id": "00000000000000000000000000000001",
                    "question": "Test question",
                    "answer": answer,
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match=r"benchmarks\.questions\.0\.answer"):
        compile_definition(source_path)


def test_benchmark_id_collision_reports_both_question_paths(tmp_path: Path) -> None:
    shared_id = "00000000000000000000000000000001"
    source = {
        "version": 2,
        "config": {
            "sample_questions": [{"id": shared_id, "question": "Sample?"}],
        },
        "benchmarks": {
            "questions": [
                {
                    "id": shared_id,
                    "question": "Benchmark?",
                    "answer": [{"format": "SQL", "content": "SELECT 1"}],
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "config.sample_questions[0].id" in message
    assert "benchmarks.questions[0].id" in message


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
        ("unsupported_field.yaml", ValidationError, "data_sources.future_sources"),
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


def test_sql_function_id_collision_reports_both_instruction_paths(
    tmp_path: Path,
) -> None:
    shared_id = "00000000000000000000000000000001"
    source = {
        "version": 2,
        "instructions": {
            "text_instructions": [{"id": shared_id, "content": "Be concise."}],
            "sql_functions": [
                {
                    "id": shared_id,
                    "identifier": "sales.analytics.fiscal_quarter",
                },
            ],
        },
    }
    source_path = tmp_path / "definition.yaml"
    source_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(DefinitionError) as error:
        compile_definition(source_path)

    message = str(error.value)
    assert "instructions.text_instructions[0].id" in message
    assert "instructions.sql_functions[0].id" in message


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
