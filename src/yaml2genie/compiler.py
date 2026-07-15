import json
from pathlib import Path

import yaml

from yaml2genie.loaders import load_yaml_source
from yaml2genie.models import DefinitionDocument, DefinitionInput
from yaml2genie.normalization import normalize


def compile_definition(path: Path) -> DefinitionDocument:
    source = load_yaml_source(path)
    return _compile_candidate(source.candidate, source.source_locations)


def compile_yaml_text(contents: str) -> DefinitionDocument:
    return _compile_candidate(yaml.safe_load(contents), {})


def _compile_candidate(
    candidate_source: object,
    source_locations: dict[tuple[str, ...], list[str]],
) -> DefinitionDocument:
    candidate = DefinitionInput.model_validate(candidate_source)
    return normalize(candidate, source_locations=source_locations)


def decompile_definition(path: Path) -> DefinitionDocument:
    return decompile_json_text(path.read_text(encoding="utf-8"))


def decompile_json_text(contents: str) -> DefinitionDocument:
    source: object = json.loads(contents)
    if isinstance(source, str):
        source = json.loads(source)
    serialized = DefinitionDocument.model_validate(source)
    candidate = DefinitionInput.model_validate(serialized.model_dump(exclude_none=True))
    return normalize(candidate)
