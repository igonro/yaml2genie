import hashlib
import json
from typing import Any, cast

from yaml2genie.errors import DefinitionError
from yaml2genie.models import DefinitionDocument, DefinitionInput

ID_COLLECTIONS = (
    ("config", "sample_questions"),
    ("instructions", "text_instructions"),
    ("instructions", "example_question_sqls"),
    ("instructions", "join_specs"),
    ("instructions", "sql_snippets", "filters"),
    ("instructions", "sql_snippets", "expressions"),
    ("instructions", "sql_snippets", "measures"),
)
JsonObject = dict[str, Any]


def _collection(document: JsonObject, path: tuple[str, ...]) -> list[JsonObject]:
    value: object = document
    for segment in path:
        if not isinstance(value, dict) or segment not in value:
            return []
        value = value[segment]
    return cast("list[JsonObject]", value) if isinstance(value, list) else []


def _generated_id(path: tuple[str, ...], item: JsonObject) -> str:
    identity = {
        "category": ".".join(path),
        "content": {key: value for key, value in item.items() if key != "id"},
    }
    canonical = json.dumps(
        identity,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.blake2b(canonical.encode(), digest_size=16).hexdigest()


def _require_unique(
    values: list[str],
    path: str,
) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            msg = f"{path}: duplicate value {value!r}"
            raise DefinitionError(msg)
        seen.add(value)


def normalize(candidate: DefinitionInput) -> DefinitionDocument:
    document = candidate.model_dump(exclude_none=True)

    for path in ID_COLLECTIONS:
        items = _collection(document, path)
        for item in items:
            item["id"] = item.get("id") or _generated_id(path, item)
        items.sort(key=lambda item: item["id"])

    question_ids = [
        item["id"] for item in _collection(document, ("config", "sample_questions"))
    ]
    _require_unique(question_ids, "config.sample_questions")

    instruction_ids = [
        item["id"]
        for path in ID_COLLECTIONS[1:]
        for item in _collection(document, path)
    ]
    _require_unique(instruction_ids, "instructions")

    tables = _collection(document, ("data_sources", "tables"))
    for table in tables:
        columns = table.get("column_configs", [])
        _require_unique(
            [column["column_name"] for column in columns],
            f"data_sources.tables[{table['identifier']!r}].column_configs",
        )
        columns.sort(key=lambda column: column["column_name"])
    tables.sort(key=lambda table: table["identifier"])

    return DefinitionDocument.model_validate(document)
