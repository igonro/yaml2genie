import json
from pathlib import Path

import pytest

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
    Path("artifacts/minimal.json"),
    Path("artifacts/phase1_supported.json"),
    Path("artifacts/phase1_supported.provenance.md"),
)
JSON_ARTIFACTS = (
    Path("artifacts/minimal.json"),
    Path("artifacts/phase1_supported.json"),
)


@pytest.mark.parametrize("relative_path", PHASE_0_FIXTURES, ids=str)
def test_phase_0_fixture_exists(relative_path: Path) -> None:
    assert (FIXTURE_ROOT / relative_path).is_file()


def test_phase_0_inventory_declares_every_fixture() -> None:
    actual = {
        path.relative_to(FIXTURE_ROOT)
        for directory in (FIXTURE_ROOT / "inputs", FIXTURE_ROOT / "artifacts")
        for path in directory.iterdir()
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
