import json
import tempfile
from pathlib import Path
from typing import cast, override

import yaml

from yaml2genie.models import DefinitionDocument

type YamlValue = (
    str | int | float | bool | None | list["YamlValue"] | dict[str, "YamlValue"]
)


def render_json(definition: DefinitionDocument) -> str:
    payload = definition.model_dump(exclude_none=True)
    return f"{json.dumps(payload, ensure_ascii=False, indent=4)}\n"


class _HumanFriendlyDumper(yaml.SafeDumper):
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


def _simplify_string_lists(value: YamlValue) -> YamlValue:
    if isinstance(value, dict):
        return {
            key: _simplify_string_lists(nested_value)
            for key, nested_value in value.items()
        }
    if isinstance(value, list):
        simplified = [_simplify_string_lists(item) for item in value]
        if len(simplified) == 1 and isinstance(simplified[0], str):
            return simplified[0]
        return simplified
    return value


def render_yaml(definition: DefinitionDocument) -> str:
    document = cast("dict[str, YamlValue]", definition.model_dump(exclude_none=True))
    payload = _simplify_string_lists(document)
    return yaml.dump(
        payload,
        Dumper=_HumanFriendlyDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def write_json_atomic(definition: DefinitionDocument, output_path: Path) -> None:
    _write_atomic(render_json(definition), output_path)


def write_yaml_atomic(
    definition: DefinitionDocument,
    output_path: Path,
    *,
    overwrite: bool,
) -> None:
    if output_path.exists() and not overwrite:
        msg = "output already exists; pass --overwrite to replace it"
        raise FileExistsError(msg)
    _write_atomic(render_yaml(definition), output_path)


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
