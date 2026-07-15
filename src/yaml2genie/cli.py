from pathlib import Path
from typing import Annotated, Never

import typer
import yaml
from pydantic import ValidationError

from yaml2genie.compiler import compile_definition
from yaml2genie.errors import DefinitionError, ErrorReport
from yaml2genie.models import DefinitionDocument
from yaml2genie.rendering import write_json_atomic

app = typer.Typer(no_args_is_help=True)
InputPath = Annotated[Path, typer.Argument(exists=True, dir_okay=False)]


def _exit_with_error(path: Path, report: ErrorReport) -> Never:
    typer.echo(f"Error [{report.category}]: {path}: {report.detail}", err=True)
    raise typer.Exit(code=report.exit_code)


def _compile_or_exit(input_path: Path) -> DefinitionDocument:
    try:
        return compile_definition(input_path)
    except (OSError, yaml.YAMLError) as error:
        _exit_with_error(input_path, ErrorReport.source_parse(error))
    except ValidationError as error:
        _exit_with_error(input_path, ErrorReport.schema(error))
    except DefinitionError as error:
        _exit_with_error(input_path, ErrorReport.semantic(error))


@app.command()
def validate(input_path: InputPath) -> None:
    _compile_or_exit(input_path)
    typer.echo("Valid Genie Agent definition.")


@app.command()
def build(
    input_path: InputPath,
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", dir_okay=False),
    ],
) -> None:
    definition = _compile_or_exit(input_path)
    try:
        write_json_atomic(definition, output_path)
    except OSError as error:
        _exit_with_error(output_path, ErrorReport.output(error))
    typer.echo(f"Built {output_path}")


def main() -> None:
    app()
