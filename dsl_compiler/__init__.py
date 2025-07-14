"""
Human-Text DSL Compiler

A powerful compiler that converts human-readable text into structured DSL,
supporting both controlled scripts and natural language input with LLM enhancement.

Key Features:
- Dual input modes: controlled scripts and natural language
- Multi-format output: YAML, JSON, Protocol Buffers
- LLM integration with multiple providers
- Advanced validation and optimization
- Command-line and library interfaces

Example usage:
    from dsl_compiler import compile, CompilerConfig
    
    config = CompilerConfig(llm_enabled=True, output_format="yaml")
    result = compile("input.txt", config)
    print(result.to_yaml())
"""

from .compiler import compile, CompilerConfig
from .exceptions import CompilerError, ParseError, ValidationError
from .models import TaskNode, ConditionalNext, DSLOutput

__version__ = "1.0.0"
__all__ = [
    "compile",
    "CompilerConfig", 
    "CompilerError",
    "ParseError",
    "ValidationError",
    "TaskNode",
    "ConditionalNext",
    "DSLOutput",
] 