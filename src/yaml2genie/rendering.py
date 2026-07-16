import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast, override

import yaml

from yaml2genie.loaders import CATEGORY_FILES, GROUPED_FILES
from yaml2genie.models import MAX_STRING_LENGTH, DefinitionDocument

type YamlValue = (
    str | int | float | bool | None | list["YamlValue"] | dict[str, "YamlValue"]
)
Layout = Literal["central", "grouped", "category-split", "fully-split", "mixed"]
YamlPath = tuple[str, ...]

TEXTUAL_STRING_LIST_PATHS = frozenset(
    {
        ("config", "sample_questions", "[]", "question"),
        ("data_sources", "tables", "[]", "description"),
        ("data_sources", "tables", "[]", "column_configs", "[]", "description"),
        ("data_sources", "metric_views", "[]", "description"),
        (
            "data_sources",
            "metric_views",
            "[]",
            "column_configs",
            "[]",
            "description",
        ),
        ("instructions", "text_instructions", "[]", "content"),
        ("instructions", "example_question_sqls", "[]", "question"),
        ("instructions", "example_question_sqls", "[]", "sql"),
        (
            "instructions",
            "example_question_sqls",
            "[]",
            "parameters",
            "[]",
            "description",
        ),
        ("instructions", "example_question_sqls", "[]", "usage_guidance"),
        ("instructions", "join_specs", "[]", "comment"),
        ("instructions", "join_specs", "[]", "instruction"),
        ("instructions", "sql_snippets", "filters", "[]", "sql"),
        ("instructions", "sql_snippets", "filters", "[]", "comment"),
        ("instructions", "sql_snippets", "filters", "[]", "instruction"),
        ("instructions", "sql_snippets", "expressions", "[]", "sql"),
        ("instructions", "sql_snippets", "expressions", "[]", "comment"),
        ("instructions", "sql_snippets", "expressions", "[]", "instruction"),
        ("instructions", "sql_snippets", "measures", "[]", "sql"),
        ("instructions", "sql_snippets", "measures", "[]", "comment"),
        ("instructions", "sql_snippets", "measures", "[]", "instruction"),
        ("benchmarks", "questions", "[]", "question"),
        ("benchmarks", "questions", "[]", "answer", "[]", "content"),
    },
)
GENERATED_ID_PATHS = frozenset(
    {
        ("config", "sample_questions", "[]", "id"),
        ("benchmarks", "questions", "[]", "id"),
        ("instructions", "text_instructions", "[]", "id"),
        ("instructions", "example_question_sqls", "[]", "id"),
        ("instructions", "sql_functions", "[]", "id"),
        ("instructions", "join_specs", "[]", "id"),
        ("instructions", "sql_snippets", "filters", "[]", "id"),
        ("instructions", "sql_snippets", "expressions", "[]", "id"),
        ("instructions", "sql_snippets", "measures", "[]", "id"),
    },
)


@dataclass(frozen=True)
class YamlRenderOptions:
    pretty: bool = True
    omit_ids: bool = False


DEFAULT_YAML_RENDER_OPTIONS = YamlRenderOptions()


@dataclass(frozen=True)
class PlannedFile:
    relative_path: Path
    contents: str
    source_identity: str | None = None


MIXED_CATEGORY_MODES: dict[str, Literal["file", "items"]] = {
    "config/sample_questions.yaml": "file",
    "sources/tables.yaml": "items",
    "sources/metric_views.yaml": "items",
    "instructions/text_instructions.yaml": "file",
    "instructions/sql_functions.yaml": "items",
    "examples/joins.yaml": "file",
    "examples/queries.yaml": "file",
    "examples/filters.yaml": "items",
    "examples/expressions.yaml": "items",
    "examples/measures.yaml": "items",
    "benchmarks/questions.yaml": "items",
}


def render_json(definition: DefinitionDocument) -> str:
    payload = definition.model_dump(exclude_none=True)
    return f"{json.dumps(payload, ensure_ascii=False, indent=4)}\n"


class _HumanFriendlyDumper(yaml.SafeDumper):
    @override
    def analyze_scalar(self, scalar: str) -> yaml.emitter.ScalarAnalysis:
        analysis = super().analyze_scalar(scalar)
        if "\n" in scalar and "\r" not in scalar:
            analysis.allow_block = True
        return analysis

    @override
    def increase_indent(
        self,
        flow: bool = False,
        indentless: bool = False,
    ) -> None:
        super().increase_indent(flow=flow, indentless=False)


def _represent_string(
    dumper: _HumanFriendlyDumper,
    value: str,
) -> yaml.nodes.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_HumanFriendlyDumper.add_representer(str, _represent_string)


def _present_yaml_value(
    value: YamlValue,
    path: YamlPath,
    options: YamlRenderOptions,
) -> YamlValue:
    if isinstance(value, dict):
        return {
            key: _present_yaml_value(nested_value, (*path, key), options)
            for key, nested_value in value.items()
            if not (options.omit_ids and (*path, key) in GENERATED_ID_PATHS)
        }
    if isinstance(value, list):
        presented = [
            _present_yaml_value(item, (*path, "[]"), options) for item in value
        ]
        if options.pretty and path in TEXTUAL_STRING_LIST_PATHS:
            return _simplify_textual_list(presented)
        return presented
    return value


def _simplify_textual_list(value: list[YamlValue]) -> YamlValue:
    if not all(isinstance(item, str) for item in value):
        return value
    strings = cast("list[str]", value)
    normalized = [item.replace("\r\n", "\n").replace("\r", "\n") for item in strings]
    if len(normalized) == 1:
        return normalized[0]
    if all(item.endswith("\n") for item in normalized[:-1]):
        merged = "".join(normalized)
        if len(merged) <= MAX_STRING_LENGTH:
            return merged
    return cast("YamlValue", normalized)


def render_yaml(
    definition: DefinitionDocument,
    *,
    options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
) -> str:
    document = cast("dict[str, YamlValue]", definition.model_dump(exclude_none=True))
    return _render_yaml_payload(document, options=options)


def _render_yaml_payload(
    document: YamlValue,
    *,
    options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
    root_path: YamlPath = (),
) -> str:
    payload = _present_yaml_value(document, root_path, options)
    return _dump_yaml(payload)


def _dump_yaml(payload: YamlValue) -> str:
    return yaml.dump(
        payload,
        Dumper=_HumanFriendlyDumper,
        allow_unicode=True,
        default_flow_style=False,
        line_break="\n",
        sort_keys=False,
        width=1_000_000_000,
    )


def write_json_atomic(definition: DefinitionDocument, output_path: Path) -> None:
    _write_atomic(render_json(definition), output_path)


def write_yaml_atomic(
    definition: DefinitionDocument,
    output_path: Path,
    *,
    overwrite: bool,
    options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
) -> None:
    if output_path.exists() and not overwrite:
        msg = "output already exists; pass --overwrite to replace it"
        raise FileExistsError(msg)
    _write_atomic(render_yaml(definition, options=options), output_path)


def write_text_atomic(contents: str, output_path: Path) -> None:
    _write_atomic(contents, output_path)


def plan_source_tree(
    definition: DefinitionDocument,
    layout: Layout,
    *,
    options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
) -> list[PlannedFile]:
    document = cast("dict[str, YamlValue]", definition.model_dump(exclude_none=True))
    if layout == "grouped":
        planned = _plan_grouped(document, options)
    elif layout == "category-split":
        planned = _plan_category_split(document, options)
    elif layout == "fully-split":
        planned = _plan_fully_split(document, options)
    elif layout == "mixed":
        planned = _plan_mixed(document, options)
    else:
        msg = f"unsupported source-tree layout {layout!r}"
        raise ValueError(msg)
    _require_unique_paths(planned)
    return sorted(
        planned,
        key=lambda item: (
            item.relative_path.name != "genie.yaml",
            item.relative_path.as_posix(),
        ),
    )


def write_source_tree_atomic(
    planned_files: list[PlannedFile],
    output_path: Path,
    *,
    overwrite: bool,
) -> None:
    validate_source_tree_output(output_path, overwrite=overwrite)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path = Path(
        tempfile.mkdtemp(
            dir=output_path.parent,
            prefix=f".{output_path.name}.staging-",
        ),
    )
    backup_path: Path | None = None
    try:
        for planned_file in planned_files:
            staged_file = staging_path / planned_file.relative_path
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_text(
                planned_file.contents,
                encoding="utf-8",
                newline="\n",
            )
        if output_path.exists():
            backup_path = Path(
                tempfile.mkdtemp(
                    dir=output_path.parent,
                    prefix=f".{output_path.name}.backup-",
                ),
            )
            backup_path.rmdir()
            output_path.replace(backup_path)
        try:
            staging_path.replace(output_path)
        except OSError:
            if backup_path is not None:
                backup_path.replace(output_path)
                backup_path = None
            raise
        if backup_path is not None:
            try:
                shutil.rmtree(backup_path)
            except OSError:
                shutil.rmtree(output_path)
                backup_path.replace(output_path)
                backup_path = None
                raise
            backup_path = None
    finally:
        if staging_path.exists():
            shutil.rmtree(staging_path)
        if (
            backup_path is not None
            and backup_path.exists()
            and not output_path.exists()
        ):
            backup_path.replace(output_path)


def validate_source_tree_output(output_path: Path, *, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        msg = "output already exists; pass --overwrite to replace it"
        raise FileExistsError(msg)
    if output_path.exists() and not output_path.is_dir():
        msg = "source-tree output must be a directory"
        raise FileExistsError(msg)


def _plan_grouped(
    document: dict[str, YamlValue],
    options: YamlRenderOptions,
) -> list[PlannedFile]:
    planned = [_manifest_file("grouped")]
    for relative_path, categories in GROUPED_FILES.items():
        payload = cast(
            "dict[str, YamlValue]",
            {
                category: _present_yaml_value(
                    cast("YamlValue", collection),
                    destination,
                    options,
                )
                for category, destination in categories.items()
                if (collection := _collection(document, destination))
            },
        )
        if payload:
            planned.append(
                PlannedFile(Path(relative_path), _dump_yaml(payload)),
            )
    return planned


def _plan_category_split(
    document: dict[str, YamlValue],
    options: YamlRenderOptions,
) -> list[PlannedFile]:
    planned = [_manifest_file("category-split")]
    for relative_path, destination in CATEGORY_FILES.items():
        if collection := _collection(document, destination):
            planned.append(
                _planned_yaml(
                    relative_path,
                    cast("YamlValue", collection),
                    options,
                    root_path=destination,
                ),
            )
    return planned


def _plan_fully_split(
    document: dict[str, YamlValue],
    options: YamlRenderOptions,
) -> list[PlannedFile]:
    planned = [_manifest_file("fully-split")]
    for relative_path, destination in CATEGORY_FILES.items():
        planned.extend(
            _item_files(relative_path, _collection(document, destination), options),
        )
    return planned


def _plan_mixed(
    document: dict[str, YamlValue],
    options: YamlRenderOptions,
) -> list[PlannedFile]:
    manifest = cast(
        "dict[str, YamlValue]",
        {
            "version": 2,
            "layout": "mixed",
            "categories": MIXED_CATEGORY_MODES,
        },
    )
    planned = [_planned_yaml("genie.yaml", manifest, options)]
    for relative_path, destination in CATEGORY_FILES.items():
        collection = _collection(document, destination)
        if not collection:
            continue
        if MIXED_CATEGORY_MODES[relative_path] == "file":
            planned.append(
                _planned_yaml(
                    relative_path,
                    cast("YamlValue", collection),
                    options,
                    root_path=destination,
                ),
            )
        else:
            planned.extend(_item_files(relative_path, collection, options))
    return planned


def _manifest_file(layout: str) -> PlannedFile:
    return _planned_yaml("genie.yaml", {"version": 2, "layout": layout})


def _planned_yaml(
    relative_path: str,
    payload: YamlValue,
    options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
    *,
    root_path: YamlPath = (),
) -> PlannedFile:
    return PlannedFile(
        Path(relative_path),
        _render_yaml_payload(payload, options=options, root_path=root_path),
    )


def _collection(
    document: dict[str, YamlValue],
    destination: tuple[str, ...],
) -> list[dict[str, YamlValue]]:
    value: YamlValue = document
    for segment in destination:
        if not isinstance(value, dict):
            return []
        value = value.get(segment)
        if value is None:
            return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _item_files(
    category_path: str,
    items: list[dict[str, YamlValue]],
    options: YamlRenderOptions,
) -> list[PlannedFile]:
    directory = Path(category_path).with_suffix("")
    planned_files = []
    for item in items:
        source_identity = _item_source_identity(item)
        planned_files.append(
            PlannedFile(
                directory / f"{_safe_item_filename(item)}.yaml",
                _render_yaml_payload(
                    item,
                    options=options,
                    root_path=(*CATEGORY_FILES[category_path], "[]"),
                ),
                source_identity,
            ),
        )
    return planned_files


def _safe_item_filename(item: dict[str, YamlValue]) -> str:
    value = _item_source_identity(item)
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    if filename:
        return filename
    msg = f"cannot derive a safe filename from {value!r}"
    raise ValueError(msg)


def _item_source_identity(item: dict[str, YamlValue]) -> str:
    value = item.get("id") or item.get("identifier")
    if not isinstance(value, str):
        msg = "cannot derive a deterministic item filename"
        raise TypeError(msg)
    return value


def _require_unique_paths(planned_files: list[PlannedFile]) -> None:
    files_by_path: dict[Path, list[PlannedFile]] = {}
    for planned_file in planned_files:
        files_by_path.setdefault(planned_file.relative_path, []).append(planned_file)
    duplicates = {
        path: files for path, files in files_by_path.items() if len(files) > 1
    }
    if duplicates:
        details = "; ".join(
            f"{path.as_posix()} from "
            f"{', '.join(repr(file.source_identity) for file in files)}"
            for path, files in sorted(duplicates.items())
        )
        msg = f"source-tree filename collisions: {details}"
        raise FileExistsError(msg)


def _write_atomic(contents: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(contents)
            temporary_path = Path(temporary.name)
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
