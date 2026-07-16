import difflib
import json
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Annotated, Literal, Never

import typer
import yaml
from pydantic import ValidationError

from yaml2genie.compiler import (
    compile_definition,
    compile_yaml_text,
    decompile_definition,
    decompile_json_text,
)
from yaml2genie.errors import DefinitionError, ErrorReport
from yaml2genie.examples import complete_example
from yaml2genie.models import DefinitionDocument
from yaml2genie.rendering import (
    DEFAULT_YAML_RENDER_OPTIONS,
    YamlRenderOptions,
    plan_source_tree,
    render_json,
    render_yaml,
    validate_source_tree_output,
    write_json_atomic,
    write_source_tree_atomic,
    write_text_atomic,
    write_yaml_atomic,
)

VERSION = package_version("yaml2genie")
Format = Literal["auto", "json", "yaml"]
app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
InputPath = Annotated[
    str,
    typer.Argument(help="YAML/JSON path, or '-' for standard input."),
]
OutputPath = Annotated[
    Path,
    typer.Option("--output", "-o", help="Output path, or '-' for standard output."),
]
LayoutOption = Annotated[
    Literal["central", "grouped", "category-split", "fully-split", "mixed"],
    typer.Option(
        "--layout",
        help="Source-tree layout for decompile output; central is the default.",
    ),
]
FormatOption = Annotated[
    Format,
    typer.Option(
        "--format",
        help="Output format. 'auto' uses the output suffix, or JSON for stdout.",
    ),
]
PrettyOption = Annotated[
    bool,
    typer.Option(
        "--pretty/--raw",
        help=(
            "Pretty YAML normalizes newlines and combines newline-chunked "
            "text arrays; raw retains imported string-array boundaries and CRLF."
        ),
    ),
]
OmitIdsOption = Annotated[
    bool,
    typer.Option(
        "--omit-ids",
        help="Omit generated item IDs from YAML; build regenerates deterministic IDs.",
    ),
]


def _version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        typer.echo(f"yaml2genie {VERSION}")
        raise typer.Exit


@app.callback()
def configure(
    ctx: typer.Context,
    version: Annotated[  # noqa: ARG001, FBT002
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
    quiet: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--quiet", help="Suppress successful-operation messages."),
    ] = False,
    verbose: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--verbose", help="Print diagnostic context to stderr."),
    ] = False,
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet
    ctx.obj["verbose"] = verbose


def _exit_with_error(path: Path, report: ErrorReport) -> Never:
    typer.echo(f"Error [{report.category}]: {path}: {report.detail}", err=True)
    raise typer.Exit(code=report.exit_code)


def _compile_or_exit(input_path: str, ctx: typer.Context) -> DefinitionDocument:
    _diagnose(ctx, f"compile input {input_path}")
    try:
        if input_path == "-":
            return compile_yaml_text(typer.get_text_stream("stdin").read())
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(input_path)
        return compile_definition(path)
    except (OSError, yaml.YAMLError) as error:
        _exit_with_error(Path(input_path), ErrorReport.source_parse(error))
    except ValidationError as error:
        _exit_with_error(Path(input_path), ErrorReport.schema(error))
    except DefinitionError as error:
        _exit_with_error(Path(input_path), ErrorReport.semantic(error))


def _decompile_or_exit(input_path: str, ctx: typer.Context) -> DefinitionDocument:
    _diagnose(ctx, f"decompile input {input_path}")
    try:
        if input_path == "-":
            return decompile_json_text(typer.get_text_stream("stdin").read())
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(input_path)
        return decompile_definition(path)
    except (OSError, json.JSONDecodeError) as error:
        _exit_with_error(Path(input_path), ErrorReport.source_parse(error))
    except ValidationError as error:
        _exit_with_error(Path(input_path), ErrorReport.schema(error))
    except DefinitionError as error:
        _exit_with_error(Path(input_path), ErrorReport.semantic(error))


@app.command(help="Validate a Genie Agent definition.")
def validate(ctx: typer.Context, input_path: InputPath) -> None:
    _compile_or_exit(input_path, ctx)
    _success(ctx, "Valid Genie Agent definition.")


@app.command(help="Compile a definition into Genie Agent JSON or YAML.")
def build(
    ctx: typer.Context,
    input_path: InputPath,
    output_path: OutputPath,
    output_format: FormatOption = "auto",
) -> None:
    definition = _compile_or_exit(input_path, ctx)
    output_format = _resolve_format(output_format, output_path, default="json")
    contents = _render_definition(definition, output_format)
    if str(output_path) == "-":
        typer.echo(contents, nl=False)
        return
    try:
        if output_format == "json":
            write_json_atomic(definition, output_path)
        else:
            write_text_atomic(contents, output_path)
    except OSError as error:
        _exit_with_error(output_path, ErrorReport.output(error))
    _success(ctx, f"Built {output_path}")


@app.command(help="Write a complete supported Genie Agent JSON example.")
def example(
    ctx: typer.Context,
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output path, or '-' for standard output."),
    ] = Path("-"),
) -> None:
    definition = complete_example()
    if str(output_path) == "-":
        typer.echo(_render_definition(definition, "json"), nl=False)
        return
    try:
        write_json_atomic(definition, output_path)
    except OSError as error:
        _exit_with_error(output_path, ErrorReport.output(error))
    _success(ctx, f"Wrote example to {output_path}")


@app.command(help="Convert Genie Agent JSON to YAML source.")
def decompile(  # noqa: PLR0913
    ctx: typer.Context,
    input_path: InputPath,
    output_path: OutputPath,
    overwrite: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--overwrite"),
    ] = False,
    layout: LayoutOption = "central",
    output_format: FormatOption = "auto",
    pretty: PrettyOption = True,  # noqa: FBT002
    omit_ids: OmitIdsOption = False,  # noqa: FBT002
    dry_run: Annotated[  # noqa: FBT002
        bool,
        typer.Option("--dry-run"),
    ] = False,
) -> None:
    definition = _decompile_or_exit(input_path, ctx)
    yaml_options = YamlRenderOptions(pretty=pretty, omit_ids=omit_ids)
    if str(output_path) == "-":
        if layout != "central":
            _exit_with_error(
                output_path,
                ErrorReport.output(
                    OSError("source-tree layouts require an output directory"),
                ),
            )
        typer.echo(
            _render_definition(
                definition,
                _resolve_format(output_format, output_path, default="yaml"),
                yaml_options=yaml_options,
            ),
            nl=False,
        )
        return
    try:
        if layout == "central":
            if dry_run:
                _success(ctx, f"CREATE {output_path.name}")
                return
            write_yaml_atomic(
                definition,
                output_path,
                overwrite=overwrite,
                options=yaml_options,
            )
            _success(ctx, f"Decompiled {output_path}")
            return
        planned_files = plan_source_tree(definition, layout, options=yaml_options)
        if dry_run:
            validate_source_tree_output(output_path, overwrite=overwrite)
            for planned_file in planned_files:
                _success(ctx, f"CREATE {planned_file.relative_path.as_posix()}")
            return
        write_source_tree_atomic(planned_files, output_path, overwrite=overwrite)
    except OSError as error:
        _exit_with_error(output_path, ErrorReport.output(error))
    _success(ctx, f"Decompiled {output_path}")


@app.command(help="Compare a generated artifact with its source.")
def check(
    ctx: typer.Context,
    input_path: InputPath,
    artifact_path: Annotated[
        Path,
        typer.Option(
            "--artifact",
            "-a",
            help="Committed generated artifact to compare.",
        ),
    ],
    output_format: FormatOption = "auto",
) -> None:
    definition = _compile_or_exit(input_path, ctx)
    output_format = _resolve_format(output_format, artifact_path, default="json")
    generated = _render_definition(definition, output_format)
    try:
        expected = artifact_path.read_text(encoding="utf-8")
    except OSError as error:
        _exit_with_error(artifact_path, ErrorReport.output(error))
    if generated == expected:
        _success(ctx, f"Artifact is up to date: {artifact_path}")
        return
    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        generated.splitlines(keepends=True),
        fromfile=str(artifact_path),
        tofile="generated",
    )
    typer.echo("".join(diff), err=True, nl=False)
    _exit_with_error(artifact_path, ErrorReport.stale())


def _resolve_format(
    requested_format: Format,
    output_path: Path,
    *,
    default: Format,
) -> Literal["json", "yaml"]:
    if requested_format == "json":
        return "json"
    if requested_format == "yaml":
        return "yaml"
    if str(output_path) == "-":
        return "json" if default == "json" else "yaml"
    return "yaml" if output_path.suffix.lower() in {".yaml", ".yml"} else "json"


def _render_definition(
    definition: DefinitionDocument,
    output_format: Literal["json", "yaml"],
    *,
    yaml_options: YamlRenderOptions = DEFAULT_YAML_RENDER_OPTIONS,
) -> str:
    return (
        render_json(definition)
        if output_format == "json"
        else render_yaml(definition, options=yaml_options)
    )


def _diagnose(ctx: typer.Context, message: str) -> None:
    if ctx.obj and ctx.obj.get("verbose"):
        typer.echo(f"[verbose] {message}", err=True)


def _success(ctx: typer.Context, message: str) -> None:
    if not ctx.obj or not ctx.obj.get("quiet"):
        typer.echo(message)


def main() -> None:
    app()
