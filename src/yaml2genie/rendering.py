import json
import tempfile
from pathlib import Path

from yaml2genie.models import DefinitionDocument


def render_json(definition: DefinitionDocument) -> str:
    payload = definition.model_dump(exclude_none=True)
    return f"{json.dumps(payload, ensure_ascii=False, indent=4)}\n"


def write_json_atomic(definition: DefinitionDocument, output_path: Path) -> None:
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
            temporary.write(render_json(definition))
            temporary_path = Path(temporary.name)
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
