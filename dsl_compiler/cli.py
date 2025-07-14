"""
DSL 编译器 CLI 工具
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
    help="Human-Text DSL 编译器",
    context_settings={"help_option_names": ["-h", "--help"]}
)

console = Console()


@app.command()
def compile(
    input_file: Path = typer.Argument(..., help="输入文件路径"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="输出文件路径"),
    format: str = typer.Option("yaml", "-f", "--format", help="输出格式 (yaml, json, proto)"),
    no_llm: bool = typer.Option(False, "--no-llm", help="禁用 LLM 增强"),
    compact: bool = typer.Option(False, "--compact", help="紧凑输出格式"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="严格模式"),
    config_file: Optional[Path] = typer.Option(None, "-c", "--config", help="配置文件路径"),
    debug: bool = typer.Option(False, "--debug", help="调试模式"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="详细输出"),
):
    """编译 Human-Text 脚本为 DSL"""
    
    # 验证输入文件
    if not input_file.exists():
        console.print(f"[red]错误: 输入文件不存在: {input_file}[/red]")
        raise typer.Exit(1)
    
    # 创建配置
    config = _create_config(
        format=format,
        no_llm=no_llm,
        compact=compact,
        strict=strict,
        debug=debug,
        config_file=config_file
    )
    
    # 确定输出路径
    if not output:
        output = input_file.with_suffix(_get_format_extension(format))
    
    try:
        # 显示编译进度
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("编译中...", total=None)
            
            # 创建编译器并编译
            compiler = DSLCompiler(config)
            dsl_output = compiler.compile(input_file)
            
            progress.update(task, description="写入输出...")
            
            # 写入输出文件
            compiler.compile_to_file(input_file, output)
        
        # 显示成功信息
        console.print(f"[green]✓ 编译成功![/green]")
        console.print(f"输入文件: {input_file}")
        console.print(f"输出文件: {output}")
        console.print(f"格式: {format}")
        
        # 显示统计信息
        if verbose:
            _show_statistics(dsl_output)
        
    except ValidationError as e:
        console.print(f"[red]验证错误: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except LLMError as e:
        console.print(f"[red]LLM 错误: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except CompilerError as e:
        console.print(f"[red]编译错误: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def validate(
    input_file: Path = typer.Argument(..., help="输入文件路径"),
    config_file: Optional[Path] = typer.Option(None, "-c", "--config", help="配置文件路径"),
    debug: bool = typer.Option(False, "--debug", help="调试模式"),
):
    """验证 Human-Text 脚本语法"""
    
    if not input_file.exists():
        console.print(f"[red]错误: 输入文件不存在: {input_file}[/red]")
        raise typer.Exit(1)
    
    # 创建配置
    config = _create_config(
        no_llm=True,  # 验证时禁用 LLM
        debug=debug,
        config_file=config_file
    )
    
    try:
        # 创建编译器并验证
        compiler = DSLCompiler(config)
        result = compiler.validate_syntax(input_file)
        
        if result["valid"]:
            console.print(f"[green]✓ 语法验证通过[/green]")
        else:
            console.print(f"[red]✗ 语法验证失败: {result['message']}[/red]")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[red]验证错误: {e}[/red]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def version():
    """显示版本信息"""
    console.print("Human-Text DSL 编译器 v1.0.0")
    console.print("Copyright (c) 2024")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="显示当前配置"),
    list_formats: bool = typer.Option(False, "--list-formats", help="列出支持的格式"),
    check_llm: bool = typer.Option(False, "--check-llm", help="检查 LLM 配置"),
):
    """配置管理"""
    
    if show:
        _show_config()
    elif list_formats:
        _list_formats()
    elif check_llm:
        _check_llm_config()
    else:
        console.print("请使用 --help 查看可用选项")


def _create_config(
    format: str = "yaml",
    no_llm: bool = False,
    compact: bool = False,
    strict: bool = True,
    debug: bool = False,
    config_file: Optional[Path] = None
) -> CompilerConfig:
    """创建编译器配置"""
    
    # 从环境变量创建基础配置
    config = CompilerConfig.from_env()
    
    # 如果有配置文件，加载配置
    if config_file and config_file.exists():
        # 这里可以添加配置文件加载逻辑
        pass
    
    # 应用命令行参数
    config.output_format = format
    config.llm_enabled = not no_llm
    config.compact_mode = compact
    config.strict_mode = strict
    config.debug = debug
    
    return config


def _get_format_extension(format: str) -> str:
    """获取格式对应的文件扩展名"""
    extensions = {
        "yaml": ".yaml",
        "json": ".json",
        "proto": ".proto"
    }
    return extensions.get(format, ".yaml")


def _show_statistics(dsl_output):
    """显示统计信息"""
    table = Table(title="编译统计")
    table.add_column("项目", style="cyan")
    table.add_column("数量", style="magenta")
    
    table.add_row("任务数", str(len(dsl_output.tasks)))
    table.add_row("工具数", str(len(dsl_output.tools)))
    table.add_row("变量数", str(len(dsl_output.variables)))
    table.add_row("入口点", dsl_output.entry_point or "无")
    
    console.print(table)


def _show_config():
    """显示当前配置"""
    config = CompilerConfig.from_env()
    
    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="magenta")
    
    table.add_row("输出格式", config.output_format)
    table.add_row("LLM 启用", "是" if config.llm_enabled else "否")
    table.add_row("LLM 提供商", config.llm_provider)
    table.add_row("LLM 模型", config.llm_model)
    table.add_row("紧凑模式", "是" if config.compact_mode else "否")
    table.add_row("严格模式", "是" if config.strict_mode else "否")
    table.add_row("调试模式", "是" if config.debug else "否")
    
    console.print(table)


def _list_formats():
    """列出支持的格式"""
    formats = [
        ("yaml", "YAML 格式", ".yaml"),
        ("json", "JSON 格式", ".json"),
        ("proto", "Protocol Buffers", ".proto")
    ]
    
    table = Table(title="支持的输出格式")
    table.add_column("格式", style="cyan")
    table.add_column("描述", style="magenta")
    table.add_column("扩展名", style="green")
    
    for format_name, description, extension in formats:
        table.add_row(format_name, description, extension)
    
    console.print(table)


def _check_llm_config():
    """检查 LLM 配置"""
    config = CompilerConfig.from_env()
    
    console.print(f"[bold]LLM 配置检查[/bold]")
    console.print(f"启用状态: {'✓' if config.llm_enabled else '✗'}")
    console.print(f"提供商: {config.llm_provider}")
    console.print(f"模型: {config.llm_model}")
    console.print(f"API Key: {'✓ 已配置' if config.llm_api_key else '✗ 未配置'}")
    
    if config.llm_enabled:
        try:
            config.validate_llm_config()
            console.print("[green]✓ LLM 配置有效[/green]")
        except ValueError as e:
            console.print(f"[red]✗ LLM 配置错误: {e}[/red]")


def main():
    """主函数"""
    app()


if __name__ == "__main__":
    main() 