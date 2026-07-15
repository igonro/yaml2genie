import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, cast

from yaml2genie.errors import SemanticValidationError
from yaml2genie.models import DefinitionDocument, DefinitionInput

JsonObject = dict[str, Any]
CollectionKey = str | tuple[str, ...]
LocatedValue = tuple[CollectionKey, str]


@dataclass(frozen=True)
class CollectionDescriptor:
    path: tuple[str, ...]
    sort_key: tuple[str, ...]
    id_required: bool = False
    uniqueness_scope: str | None = None
    uniqueness_key: tuple[str, ...] | None = None

    @property
    def source_path(self) -> str:
        path = ""
        for segment in self.path:
            separator = "" if not path or segment.startswith("[") else "."
            path += f"{separator}{segment}"
        return path


COLLECTIONS = (
    CollectionDescriptor(
        ("config", "sample_questions"),
        ("id",),
        id_required=True,
        uniqueness_scope="question IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("benchmarks", "questions"),
        ("id",),
        id_required=True,
        uniqueness_scope="question IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("data_sources", "tables"),
        ("identifier",),
        uniqueness_scope="data source identifiers",
        uniqueness_key=("identifier",),
    ),
    CollectionDescriptor(
        ("data_sources", "metric_views"),
        ("identifier",),
        uniqueness_scope="metric view identifiers",
        uniqueness_key=("identifier",),
    ),
    CollectionDescriptor(
        ("instructions", "text_instructions"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "example_question_sqls"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "sql_functions"),
        ("id", "identifier"),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "join_specs"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "sql_snippets", "filters"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "sql_snippets", "expressions"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
    CollectionDescriptor(
        ("instructions", "sql_snippets", "measures"),
        ("id",),
        id_required=True,
        uniqueness_scope="instruction IDs",
        uniqueness_key=("id",),
    ),
)
COLUMN_CONFIGS = CollectionDescriptor(
    ("data_sources", "tables", "[]", "column_configs"),
    ("column_name",),
    uniqueness_scope="column identities",
    uniqueness_key=("column_name",),
)
METRIC_VIEW_COLUMN_CONFIGS = CollectionDescriptor(
    ("data_sources", "metric_views", "[]", "column_configs"),
    ("column_name",),
)
JOIN_ALIAS_REFERENCE = re.compile(r"`([^`]+)`\s*\.\s*`[^`]+`")
RELATIONSHIP_ANNOTATIONS = {
    f"--rt=FROM_RELATIONSHIP_TYPE_{cardinality}--"
    for cardinality in ("MANY_TO_ONE", "ONE_TO_MANY", "ONE_TO_ONE", "MANY_TO_MANY")
}


def _collection(document: JsonObject, path: tuple[str, ...]) -> list[JsonObject]:
    value: object = document
    for segment in path:
        if not isinstance(value, dict) or segment not in value:
            return []
        value = value[segment]
    return cast("list[JsonObject]", value) if isinstance(value, list) else []


def _generated_id(path: tuple[str, ...], item: JsonObject) -> str:
    stable_key = item.get("stable_key")
    identity = {
        "category": ".".join(path),
        "identity": (
            {"stable_key": stable_key}
            if stable_key is not None
            else {
                "content": {
                    key: value
                    for key, value in item.items()
                    if key not in {"id", "stable_key"}
                },
            }
        ),
    }
    canonical = json.dumps(
        identity,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.blake2b(canonical.encode(), digest_size=16).hexdigest()


def _item_key(item: JsonObject, fields: tuple[str, ...]) -> CollectionKey:
    values = tuple(cast("str", item[field]) for field in fields)
    return values[0] if len(values) == 1 else values


def _require_unique(values: list[LocatedValue], scope: str) -> None:
    seen: dict[CollectionKey, str] = {}
    for value, location in values:
        if value in seen:
            msg = f"{scope}: duplicate value {value!r} at {seen[value]} and {location}"
            raise SemanticValidationError(msg)
        seen[value] = location


def _normalize_collection(
    items: list[JsonObject],
    descriptor: CollectionDescriptor,
    values_by_scope: dict[str, list[LocatedValue]],
) -> None:
    stable_keys: list[LocatedValue] = []
    for index, item in enumerate(items):
        location = f"{descriptor.source_path}[{index}]"
        if "stable_key" in item:
            stable_keys.append((item["stable_key"], f"{location}.stable_key"))
        if descriptor.id_required:
            item["id"] = item.get("id") or _generated_id(descriptor.path, item)
        item.pop("stable_key", None)
        if descriptor.uniqueness_scope and descriptor.uniqueness_key:
            values_by_scope.setdefault(descriptor.uniqueness_scope, []).append(
                (
                    _item_key(item, descriptor.uniqueness_key),
                    f"{location}.{'.'.join(descriptor.uniqueness_key)}",
                ),
            )
    _require_unique(stable_keys, descriptor.source_path)
    items.sort(key=lambda item: _item_key(item, descriptor.sort_key))


def _validate_joins(document: JsonObject) -> None:
    joins = _collection(document, ("instructions", "join_specs"))
    for index, join in enumerate(joins):
        path = f"instructions.join_specs[{index}]"
        left_alias = join["left"]["alias"]
        right_alias = join["right"]["alias"]
        if left_alias == right_alias:
            msg = f"{path}.right.alias: join aliases must be distinct"
            raise SemanticValidationError(msg)

        referenced_aliases = set(JOIN_ALIAS_REFERENCE.findall(join["sql"][0]))
        expected_aliases = {left_alias, right_alias}
        missing_aliases = expected_aliases - referenced_aliases
        unknown_aliases = referenced_aliases - expected_aliases
        if missing_aliases or unknown_aliases:
            details = []
            if missing_aliases:
                details.append(f"missing aliases {sorted(missing_aliases)!r}")
            if unknown_aliases:
                details.append(f"unknown aliases {sorted(unknown_aliases)!r}")
            msg = f"{path}.sql[0]: {'; '.join(details)}"
            raise SemanticValidationError(msg)

        relationship = join["sql"][1]
        if relationship not in RELATIONSHIP_ANNOTATIONS:
            msg = f"{path}.sql[1]: unsupported relationship annotation {relationship!r}"
            raise SemanticValidationError(msg)


def normalize(candidate: DefinitionInput) -> DefinitionDocument:
    document = candidate.model_dump(exclude_none=True)
    values_by_scope: dict[str, list[LocatedValue]] = {}
    _validate_joins(document)

    for descriptor in COLLECTIONS:
        if descriptor.path in {
            ("data_sources", "tables"),
            ("data_sources", "metric_views"),
        }:
            continue
        _normalize_collection(
            _collection(document, descriptor.path),
            descriptor,
            values_by_scope,
        )

    tables = _collection(document, ("data_sources", "tables"))
    for table_index, table in enumerate(tables):
        columns = table.get("column_configs", [])
        column_descriptor = CollectionDescriptor(
            (
                "data_sources",
                "tables",
                f"[{table_index}]",
                "column_configs",
            ),
            COLUMN_CONFIGS.sort_key,
            uniqueness_scope=COLUMN_CONFIGS.uniqueness_scope,
            uniqueness_key=("identifier", "column_name"),
        )
        columns_with_identifiers = [
            {"identifier": table["identifier"], **column} for column in columns
        ]
        _normalize_collection(
            columns_with_identifiers,
            column_descriptor,
            values_by_scope,
        )
        columns[:] = [
            {key: value for key, value in column.items() if key != "identifier"}
            for column in columns_with_identifiers
        ]

    table_descriptor = next(
        descriptor
        for descriptor in COLLECTIONS
        if descriptor.path == ("data_sources", "tables")
    )
    _normalize_collection(tables, table_descriptor, values_by_scope)

    metric_views = _collection(document, ("data_sources", "metric_views"))
    for metric_view in metric_views:
        columns = cast(
            "list[JsonObject] | None",
            metric_view.get("column_configs"),
        )
        if columns is not None:
            columns.sort(
                key=lambda column: _item_key(
                    column,
                    METRIC_VIEW_COLUMN_CONFIGS.sort_key,
                ),
            )
    metric_view_descriptor = next(
        descriptor
        for descriptor in COLLECTIONS
        if descriptor.path == ("data_sources", "metric_views")
    )
    _normalize_collection(metric_views, metric_view_descriptor, values_by_scope)

    for scope, values in values_by_scope.items():
        _require_unique(values, scope)

    return DefinitionDocument.model_validate(document)
