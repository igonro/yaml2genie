import json
from pathlib import Path

from yaml2genie.loaders import load_yaml_source
from yaml2genie.models import DefinitionDocument, DefinitionInput
from yaml2genie.normalization import normalize


def compile_definition(path: Path) -> DefinitionDocument:
    source = load_yaml_source(path)
    candidate = DefinitionInput.model_validate(source.candidate)
    return normalize(candidate, source_locations=source.source_locations)


def decompile_definition(path: Path) -> DefinitionDocument:
    source: object = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(source, str):
        source = json.loads(source)
    serialized = DefinitionDocument.model_validate(source)
    candidate = DefinitionInput.model_validate(serialized.model_dump(exclude_none=True))
    return normalize(candidate)
