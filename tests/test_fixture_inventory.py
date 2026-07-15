import json
from pathlib import Path

import pytest
import yaml

from yaml2genie import compile_definition

SERIALIZED_VERSION = 2
MATRIX_COLUMN_COUNT = 10
FIXTURE_ROOT = Path(__file__).parent
CONTRACT_PATH = FIXTURE_ROOT.parent / ".agents/docs/databricks-genie-contract.md"
PHASE_0_FIXTURES = (
    Path("inputs/minimal.yaml"),
    Path("inputs/malformed.yaml"),
    Path("inputs/invalid_id.yaml"),
    Path("inputs/unsorted.yaml"),
    Path("inputs/duplicate_question_ids.yaml"),
    Path("inputs/duplicate_instruction_ids.yaml"),
    Path("inputs/duplicate_column_identity.yaml"),
    Path("inputs/malformed_join.yaml"),
    Path("inputs/unsupported_field.yaml"),
    Path("inputs/unsupported_version.yaml"),
    Path("inputs/phase1_supported.yaml"),
    Path("inputs/phase4_supported.yaml"),
    Path("inputs/centralized_genie.yaml"),
    Path("inputs/grouped_genie/genie.yaml"),
    Path("inputs/grouped_genie/config.yaml"),
    Path("inputs/grouped_genie/sources.yaml"),
    Path("inputs/grouped_genie/instructions.yaml"),
    Path("inputs/grouped_genie/examples.yaml"),
    Path("inputs/grouped_genie/benchmarks.yaml"),
    Path("inputs/category-split_genie/genie.yaml"),
    Path("inputs/category-split_genie/config/sample_questions.yaml"),
    Path("inputs/category-split_genie/sources/tables.yaml"),
    Path("inputs/category-split_genie/sources/metric_views.yaml"),
    Path("inputs/category-split_genie/instructions/text_instructions.yaml"),
    Path("inputs/category-split_genie/instructions/sql_functions.yaml"),
    Path("inputs/category-split_genie/examples/joins.yaml"),
    Path("inputs/category-split_genie/examples/queries.yaml"),
    Path("inputs/category-split_genie/examples/filters.yaml"),
    Path("inputs/category-split_genie/benchmarks/questions.yaml"),
    Path("inputs/fully-split_genie/genie.yaml"),
    Path("inputs/fully-split_genie/config/sample_questions/revenue.yaml"),
    Path("inputs/fully-split_genie/sources/tables/orders.yaml"),
    Path("inputs/fully-split_genie/sources/metric_views/revenue_metrics.yaml"),
    Path("inputs/fully-split_genie/instructions/text_instructions/fiscal_periods.yaml"),
    Path("inputs/fully-split_genie/instructions/sql_functions/fiscal_quarter.yaml"),
    Path("inputs/fully-split_genie/examples/joins/orders_customers.yaml"),
    Path("inputs/fully-split_genie/examples/queries/region_sales.yaml"),
    Path("inputs/fully-split_genie/examples/filters/high_value.yaml"),
    Path("inputs/fully-split_genie/benchmarks/questions/average_order_value.yaml"),
    Path("inputs/mixed_genie/genie.yaml"),
    Path("inputs/mixed_genie/config/sample_questions.yaml"),
    Path("inputs/mixed_genie/sources/tables/orders.yaml"),
    Path("inputs/mixed_genie/sources/metric_views.yaml"),
    Path("inputs/mixed_genie/instructions/text_instructions/fiscal_periods.yaml"),
    Path("inputs/mixed_genie/instructions/sql_functions.yaml"),
    Path("inputs/mixed_genie/examples/joins/orders_customers.yaml"),
    Path("inputs/mixed_genie/examples/queries.yaml"),
    Path("inputs/mixed_genie/examples/filters/high_value.yaml"),
    Path("inputs/mixed_genie/benchmarks/questions/average_order_value.yaml"),
    Path("inputs/malformed.json"),
    Path("inputs/missing_version.json"),
    Path("inputs/missing_item_id.json"),
    Path("inputs/unsupported_version.json"),
    Path("inputs/unsupported_field.json"),
    Path("inputs/bundle/databricks.yml"),
    Path("artifacts/minimal.json"),
    Path("artifacts/phase1_supported.json"),
    Path("artifacts/phase4_supported.json"),
    Path("artifacts/phase1_supported.provenance.md"),
    Path("artifacts/phase4_supported.provenance.md"),
)
JSON_ARTIFACTS = (
    Path("artifacts/minimal.json"),
    Path("artifacts/phase1_supported.json"),
    Path("artifacts/phase4_supported.json"),
)


@pytest.mark.parametrize("relative_path", PHASE_0_FIXTURES, ids=str)
def test_phase_0_fixture_exists(relative_path: Path) -> None:
    assert (FIXTURE_ROOT / relative_path).is_file()


def test_phase_0_inventory_declares_every_fixture() -> None:
    actual = {
        path.relative_to(FIXTURE_ROOT)
        for directory in (FIXTURE_ROOT / "inputs", FIXTURE_ROOT / "artifacts")
        for path in directory.rglob("*")
        if path.is_file()
    }

    assert actual == set(PHASE_0_FIXTURES)


@pytest.mark.parametrize("relative_path", JSON_ARTIFACTS, ids=str)
def test_json_artifact_is_version_2(relative_path: Path) -> None:
    artifact = json.loads((FIXTURE_ROOT / relative_path).read_text(encoding="utf-8"))

    assert artifact["version"] == SERIALIZED_VERSION


def test_contract_matrix_rows_have_acceptance_metadata() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    matrix = contract.split("<!-- matrix:start -->", maxsplit=1)[1].split(
        "<!-- matrix:end -->",
        maxsplit=1,
    )[0]
    rows = [line for line in matrix.splitlines() if line.startswith("| `")]

    assert rows
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == MATRIX_COLUMN_COUNT
        assert cells[2] in {"required", "optional", "unknown"}
        assert cells[7] in {"supported", "deferred"}
        assert cells[8] in {"documented", "example-only", "inferred", "unknown"}
        assert "https://" in cells[9]


def test_contract_freezes_phase_1_boundary_decisions() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "raw serialized object" in contract
    assert "escaped serialized string" in contract
    assert "full Get API response" in contract
    assert "deferred" in contract
    assert "Strict rejection reports the exact JSON path" in contract
    mutual_exclusion_rule = (
        "`file_path` and inline `serialized_space` are mutually exclusive"
    )
    assert mutual_exclusion_rule in contract


def test_bundle_fixture_references_generated_serialized_definition() -> None:
    bundle_path = FIXTURE_ROOT / "inputs/bundle/databricks.yml"
    bundle = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))

    resource = bundle["resources"]["genie_spaces"]["sales_assistant"]
    artifact_path = (bundle_path.parent / resource["file_path"]).resolve()
    generated = compile_definition(FIXTURE_ROOT / "inputs/minimal.yaml")

    assert bundle["bundle"]["engine"] == "direct"
    assert resource["title"] == "Sales Assistant"
    assert resource["warehouse_id"] == "${var.warehouse_id}"
    assert "serialized_space" not in resource
    assert json.loads(
        artifact_path.read_text(encoding="utf-8")
    ) == generated.model_dump(
        exclude_none=True,
    )


def test_official_shape_fixture_remains_compatible_with_generated_json() -> None:
    official_shape = json.loads(
        (FIXTURE_ROOT / "artifacts/phase4_supported.json").read_text(
            encoding="utf-8",
        ),
    )
    generated = compile_definition(FIXTURE_ROOT / "inputs/phase4_supported.yaml")

    assert official_shape["version"] == SERIALIZED_VERSION
    assert {"config", "data_sources", "instructions", "benchmarks"} <= set(
        official_shape,
    )
    assert generated.model_dump(exclude_none=True) == official_shape
