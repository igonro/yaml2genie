import json
from dataclasses import dataclass
from enum import IntEnum, StrEnum

import yaml
from pydantic import ValidationError


class DefinitionError(ValueError):
    pass


class SemanticValidationError(DefinitionError):
    pass


class ErrorCategory(StrEnum):
    SOURCE_PARSE = "source parse"
    SCHEMA = "schema"
    SEMANTIC = "semantic"
    OUTPUT = "output"


class ErrorExitCode(IntEnum):
    SOURCE_PARSE = 2
    SCHEMA = 3
    SEMANTIC = 4
    OUTPUT = 5


@dataclass(frozen=True)
class ErrorReport:
    category: ErrorCategory
    exit_code: ErrorExitCode
    detail: str

    @classmethod
    def source_parse(
        cls,
        error: OSError | json.JSONDecodeError | yaml.YAMLError,
    ) -> "ErrorReport":
        if isinstance(error, yaml.MarkedYAMLError):
            problem = error.problem or "invalid YAML"
            if error.problem_mark is not None:
                mark = error.problem_mark
                problem = f"{problem} at line {mark.line + 1}, column {mark.column + 1}"
            detail = problem
        else:
            detail = str(error)
        return cls(ErrorCategory.SOURCE_PARSE, ErrorExitCode.SOURCE_PARSE, detail)

    @classmethod
    def schema(cls, error: ValidationError) -> "ErrorReport":
        messages = []
        for item in error.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        ):
            location = _format_location(item["loc"])
            messages.append(f"{location}: {item['msg']}")
        return cls(ErrorCategory.SCHEMA, ErrorExitCode.SCHEMA, "; ".join(messages))

    @classmethod
    def semantic(cls, error: DefinitionError) -> "ErrorReport":
        return cls(ErrorCategory.SEMANTIC, ErrorExitCode.SEMANTIC, str(error))

    @classmethod
    def output(cls, error: OSError) -> "ErrorReport":
        return cls(ErrorCategory.OUTPUT, ErrorExitCode.OUTPUT, str(error))


def _format_location(location: tuple[int | str, ...]) -> str:
    path = ""
    for segment in location:
        if isinstance(segment, int):
            path += f"[{segment}]"
        else:
            path += f"{'.' if path else ''}{segment}"
    return path
