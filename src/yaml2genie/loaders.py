from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict

from yaml2genie.errors import DefinitionError

JsonObject = dict[str, Any]
SourceLocations = dict[tuple[str, ...], list[str]]


class LayoutManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[2]
    layout: Literal["grouped", "category-split", "fully-split", "mixed"]
    categories: dict[str, Literal["file", "items"]] | None = None


@dataclass(frozen=True)
class LoadedYamlSource:
    candidate: object
    source_locations: SourceLocations


GROUPED_FILES: dict[str, dict[str, tuple[str, ...]]] = {
    "config.yaml": {"sample_questions": ("config", "sample_questions")},
    "sources.yaml": {
        "tables": ("data_sources", "tables"),
        "metric_views": ("data_sources", "metric_views"),
    },
    "instructions.yaml": {
        "text_instructions": ("instructions", "text_instructions"),
        "sql_functions": ("instructions", "sql_functions"),
    },
    "examples.yaml": {
        "joins": ("instructions", "join_specs"),
        "queries": ("instructions", "example_question_sqls"),
        "filters": ("instructions", "sql_snippets", "filters"),
        "expressions": ("instructions", "sql_snippets", "expressions"),
        "measures": ("instructions", "sql_snippets", "measures"),
    },
    "benchmarks.yaml": {"questions": ("benchmarks", "questions")},
}
CATEGORY_FILES: dict[str, tuple[str, ...]] = {
    "config/sample_questions.yaml": ("config", "sample_questions"),
    "sources/tables.yaml": ("data_sources", "tables"),
    "sources/metric_views.yaml": ("data_sources", "metric_views"),
    "instructions/text_instructions.yaml": ("instructions", "text_instructions"),
    "instructions/sql_functions.yaml": ("instructions", "sql_functions"),
    "examples/joins.yaml": ("instructions", "join_specs"),
    "examples/queries.yaml": ("instructions", "example_question_sqls"),
    "examples/filters.yaml": ("instructions", "sql_snippets", "filters"),
    "examples/expressions.yaml": (
        "instructions",
        "sql_snippets",
        "expressions",
    ),
    "examples/measures.yaml": ("instructions", "sql_snippets", "measures"),
    "benchmarks/questions.yaml": ("benchmarks", "questions"),
}


def load_yaml_source(path: Path) -> LoadedYamlSource:
    if path.is_file():
        return LoadedYamlSource(_read_yaml(path), {})
    return _load_layout(path)


def _load_layout(root: Path) -> LoadedYamlSource:
    manifest_path = root / "genie.yaml"
    if not manifest_path.is_file():
        msg = f"{manifest_path}: required layout manifest does not exist"
        raise FileNotFoundError(msg)
    manifest = LayoutManifest.model_validate(_read_mapping(manifest_path))
    if manifest.layout == "grouped":
        return _load_grouped(root, manifest)
    if manifest.layout == "category-split":
        return _load_category_split(root, manifest)
    if manifest.layout == "fully-split":
        return _load_fully_split(root, manifest)
    return _load_mixed(root, manifest)


def _load_grouped(root: Path, manifest: LayoutManifest) -> LoadedYamlSource:
    _reject_unknown_yaml_files(root, {"genie.yaml", *GROUPED_FILES})
    candidate: JsonObject = {"version": manifest.version}
    locations: SourceLocations = {}
    for relative_path, categories in GROUPED_FILES.items():
        path = root / relative_path
        if not path.is_file():
            continue
        contents = _read_mapping(path)
        _reject_unknown_categories(relative_path, contents, set(categories))
        for category, destination in categories.items():
            if category not in contents:
                continue
            _append_collection(
                candidate,
                destination,
                _require_collection(relative_path, category, contents[category]),
                locations,
                relative_path,
            )
    return LoadedYamlSource(candidate, locations)


def _load_category_split(root: Path, manifest: LayoutManifest) -> LoadedYamlSource:
    _reject_unknown_yaml_files(root, {"genie.yaml", *CATEGORY_FILES})
    candidate: JsonObject = {"version": manifest.version}
    locations: SourceLocations = {}
    for relative_path, destination in CATEGORY_FILES.items():
        path = root / relative_path
        if not path.is_file():
            continue
        _append_collection(
            candidate,
            destination,
            _require_collection(relative_path, None, _read_yaml(path)),
            locations,
            relative_path,
        )
    return LoadedYamlSource(candidate, locations)


def _load_fully_split(root: Path, manifest: LayoutManifest) -> LoadedYamlSource:
    _reject_unknown_item_files(root, set(CATEGORY_FILES))
    candidate: JsonObject = {"version": manifest.version}
    locations: SourceLocations = {}
    for relative_path, destination in CATEGORY_FILES.items():
        _append_item_files(candidate, destination, locations, root, relative_path)
    return LoadedYamlSource(candidate, locations)


def _load_mixed(root: Path, manifest: LayoutManifest) -> LoadedYamlSource:
    if not manifest.categories:
        msg = "genie.yaml.categories: must declare source modes for mixed layouts"
        raise DefinitionError(msg)
    unknown = sorted(set(manifest.categories) - set(CATEGORY_FILES))
    if unknown:
        msg = f"genie.yaml.categories: unknown categories: {', '.join(unknown)}"
        raise DefinitionError(msg)
    missing = sorted(set(CATEGORY_FILES) - set(manifest.categories))
    if missing:
        msg = f"genie.yaml.categories: missing source modes: {', '.join(missing)}"
        raise DefinitionError(msg)
    file_categories = {
        relative_path
        for relative_path, mode in manifest.categories.items()
        if mode == "file"
    }
    item_categories = set(manifest.categories) - file_categories
    _reject_unknown_mixed_files(root, file_categories, item_categories)
    candidate: JsonObject = {"version": manifest.version}
    locations: SourceLocations = {}
    for relative_path, mode in manifest.categories.items():
        destination = CATEGORY_FILES[relative_path]
        path = root / relative_path
        if mode == "file":
            if path.is_file():
                _append_collection(
                    candidate,
                    destination,
                    _require_collection(relative_path, None, _read_yaml(path)),
                    locations,
                    relative_path,
                )
            continue
        _append_item_files(candidate, destination, locations, root, relative_path)
    return LoadedYamlSource(candidate, locations)


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _read_mapping(path: Path) -> JsonObject:
    source = _read_yaml(path)
    if not isinstance(source, dict):
        msg = f"{path.name}: expected a mapping"
        raise DefinitionError(msg)
    return source


def _require_collection(
    relative_path: str,
    category: str | None,
    value: object,
) -> list[JsonObject]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        location = f"{relative_path}.{category}" if category else relative_path
        msg = f"{location}: expected a list of mappings"
        raise DefinitionError(msg)
    return value


def _reject_unknown_yaml_files(root: Path, expected: set[str]) -> None:
    actual = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.yaml")
        if path.is_file()
    )
    unknown = sorted(set(actual) - expected)
    if unknown:
        msg = f"unknown layout category files: {', '.join(unknown)}"
        raise DefinitionError(msg)


def _reject_unknown_item_files(root: Path, categories: set[str]) -> None:
    _reject_unknown_mixed_files(root, set(), categories)


def _reject_unknown_mixed_files(
    root: Path,
    file_categories: set[str],
    item_categories: set[str],
) -> None:
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.yaml")
        if path.is_file()
    }
    allowed = {"genie.yaml", *file_categories}
    for relative_path in item_categories:
        directory = Path(relative_path).with_suffix("")
        allowed.update(
            path.relative_to(root).as_posix()
            for path in (root / directory).rglob("*.yaml")
            if path.is_file()
        )
    unknown = sorted(actual - allowed)
    if unknown:
        msg = f"unknown layout category files: {', '.join(unknown)}"
        raise DefinitionError(msg)


def _append_item_files(
    candidate: JsonObject,
    destination: tuple[str, ...],
    locations: SourceLocations,
    root: Path,
    relative_path: str,
) -> None:
    directory = root / Path(relative_path).with_suffix("")
    if not directory.is_dir():
        return
    for path in sorted(directory.rglob("*.yaml")):
        item = _read_mapping(path)
        _append_collection(
            candidate,
            destination,
            [item],
            locations,
            path.relative_to(root).as_posix(),
        )


def _reject_unknown_categories(
    relative_path: str,
    contents: JsonObject,
    expected: set[str],
) -> None:
    unknown = sorted(set(contents) - expected)
    if unknown:
        msg = f"{relative_path}: unknown categories: {', '.join(unknown)}"
        raise DefinitionError(msg)


def _append_collection(
    candidate: JsonObject,
    destination: tuple[str, ...],
    items: list[JsonObject],
    locations: SourceLocations,
    relative_path: str,
) -> None:
    container = candidate
    for segment in destination[:-1]:
        next_value = container.setdefault(segment, {})
        if not isinstance(next_value, dict):
            msg = f"{relative_path}: incompatible collection destination"
            raise DefinitionError(msg)
        container = next_value
    collection = container.setdefault(destination[-1], [])
    if not isinstance(collection, list):
        msg = f"{relative_path}: incompatible collection destination"
        raise DefinitionError(msg)
    collection.extend(items)
    locations.setdefault(destination, []).extend(
        f"{relative_path}[{index}]" for index in range(len(items))
    )
