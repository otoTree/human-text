"""
DSL Compiler CLI Tool
"""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import CompilerConfig
from .compiler import DSLCompiler
from .exceptions import CompilerError, ValidationError, LLMError

app = typer.Typer(
    name="dslc",
    help="Human-Text DSL Compiler",
    context_settings={"help_option_names": ["-h", "--help"]}
)

console = Console()


@app.command()
def compile(
    input_file: Path = typer.Argument(..., help="Input file path"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file path"),
    format: str = typer.Option("yaml", "-f", "--format", help="Output format (yaml, json, proto)"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM enhancement"),
    compact: bool = typer.Option(False, "--compact", help="Compact output format"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Strict mode"),
    config_file: Optional[Path] = typer.Option(None, "-c", "--config", help="Configuration file path"),
    debug: bool = typer.Option(False, "--debug", help="Debug mode"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
):
    """Compile Human-Text script to DSL"""
    
    # Validate input file
    if not input_file.exists():
        console.print(f"[red]Error: Input file does not exist: {input_file}[/red]")
        raise typer.Exit(1)
    
    # Create configuration
    config = _create_config(
        format=format,
        no_llm=no_llm,
        compact=compact,
        strict=strict,
        debug=debug,
        config_file=config_file
    )
    
    # Determine output path
    if not output:
        output = input_file.with_suffix(_get_format_extension(format))
    
    try:
        # Show compilation progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Compiling...", total=None)
            
            # Create compiler and compile
            compiler = DSLCompiler(config)
            dsl_output = compiler.compile(input_file)
            
            progress.update(task, description="Writing output...")
            
            # Write output file
            compiler.compile_to_file(input_file, output)
        
        # Show success message
        console.print(f"[green]✓ Compilation successful![/green]")
        console.print(f"Input file: {input_file}")
        console.print(f"Output file: {output}")
        console.print(f"Format: {format}")
        
        # Show statistics
        if verbose:
            _show_statistics(dsl_output)
        
    except ValidationError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except LLMError as e:
        console.print(f"[red]LLM error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except CompilerError as e:
        console.print(f"[red]Compilation error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Unknown error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def validate(
    input_file: Path = typer.Argument(..., help="Input file path"),
    config_file: Optional[Path] = typer.Option(None, "-c", "--config", help="Configuration file path"),
    debug: bool = typer.Option(False, "--debug", help="Debug mode"),
):
    """Validate Human-Text script syntax"""
    
    if not input_file.exists():
        console.print(f"[red]Error: Input file does not exist: {input_file}[/red]")
        raise typer.Exit(1)
    
    # Create configuration
    config = _create_config(
        no_llm=True,  # Disable LLM during validation
        debug=debug,
        config_file=config_file
    )
    
    try:
        # Create compiler and validate
        compiler = DSLCompiler(config)
        result = compiler.validate_syntax(input_file)
        
        if result["valid"]:
            console.print(f"[green]✓ Syntax validation passed[/green]")
        else:
            console.print(f"[red]✗ Syntax validation failed: {result['message']}[/red]")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information"""
    console.print("Human-Text DSL Compiler v1.0.0")
    console.print("Copyright (c) 2024")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    list_formats: bool = typer.Option(False, "--list-formats", help="List supported formats"),
    check_llm: bool = typer.Option(False, "--check-llm", help="Check LLM configuration"),
):
    """Configuration management"""
    
    if show:
        _show_config()
    elif list_formats:
        _list_formats()
    elif check_llm:
        _check_llm_config()
    else:
        console.print("Please use --help to see available options")


def _create_config(
    format: str = "yaml",
    no_llm: bool = False,
    compact: bool = False,
    strict: bool = True,
    debug: bool = False,
    config_file: Optional[Path] = None
) -> CompilerConfig:
    """Create compiler configuration"""
    
    # Create base configuration from environment variables
    config = CompilerConfig.from_env()
    
    # Load configuration from file if available
    if config_file and config_file.exists():
        # Configuration file loading logic can be added here
        pass
    
    # Apply command line arguments
    config.output_format = format
    config.llm_enabled = not no_llm
    config.compact_mode = compact
    config.strict_mode = strict
    config.debug = debug
    
    return config


def _get_format_extension(format: str) -> str:
    """Get file extension for format"""
    extensions = {
        "yaml": ".yaml",
        "json": ".json",
        "proto": ".proto"
    }
    return extensions.get(format, ".yaml")


def _show_statistics(dsl_output):
    """Show statistics"""
    table = Table(title="Compilation Statistics")
    table.add_column("Item", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Task count", str(len(dsl_output.tasks)))
    table.add_row("Tool count", str(len(dsl_output.tools)))
    table.add_row("Variable count", str(len(dsl_output.variables)))
    table.add_row("Entry point", dsl_output.entry_point or "None")
    
    console.print(table)


def _show_config():
    """Show current configuration"""
    config = CompilerConfig.from_env()
    
    table = Table(title="Current Configuration")
    table.add_column("Configuration Item", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Output format", config.output_format)
    table.add_row("LLM enabled", "Yes" if config.llm_enabled else "No")
    table.add_row("LLM provider", config.llm_provider)
    table.add_row("LLM model", config.llm_model)
    table.add_row("Compact mode", "Yes" if config.compact_mode else "No")
    table.add_row("Strict mode", "Yes" if config.strict_mode else "No")
    table.add_row("Debug mode", "Yes" if config.debug else "No")
    
    console.print(table)


def _list_formats():
    """List supported formats"""
    formats = [
        ("yaml", "YAML format", ".yaml"),
        ("json", "JSON format", ".json"),
        ("proto", "Protocol Buffers", ".proto")
    ]
    
    table = Table(title="Supported Output Formats")
    table.add_column("Format", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Extension", style="green")
    
    for format_name, description, extension in formats:
        table.add_row(format_name, description, extension)
    
    console.print(table)


def _check_llm_config():
    """Check LLM configuration"""
    config = CompilerConfig.from_env()
    
    console.print(f"[bold]LLM Configuration Check[/bold]")
    console.print(f"Enabled status: {'✓' if config.llm_enabled else '✗'}")
    console.print(f"Provider: {config.llm_provider}")
    console.print(f"Model: {config.llm_model}")
    console.print(f"API Key: {'✓ Configured' if config.llm_api_key else '✗ Not configured'}")
    
    if config.llm_enabled:
        try:
            config.validate_llm_config()
            console.print("[green]✓ LLM configuration is valid[/green]")
        except ValueError as e:
            console.print(f"[red]✗ LLM configuration error: {e}[/red]")


def main():
    """Main function"""
    app()


if __name__ == "__main__":
    main() 