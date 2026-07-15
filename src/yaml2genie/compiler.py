from pathlib import Path

import yaml

from yaml2genie.models import DefinitionDocument, DefinitionInput
from yaml2genie.normalization import normalize


def compile_definition(path: Path) -> DefinitionDocument:
    source: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    candidate = DefinitionInput.model_validate(source)
    return normalize(candidate)
