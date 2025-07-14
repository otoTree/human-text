"""
DSL Compiler Exception Classes
"""

from typing import Optional, Dict, Any, List


class CompilerError(Exception):
    """Base compiler exception"""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None, 
                 source_file: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.source_file = source_file
        self.context = context or {}
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.source_file:
            parts.append(f"File: {self.source_file}")
        if self.line is not None:
            if self.column is not None:
                parts.append(f"Position: {self.line}:{self.column}")
            else:
                parts.append(f"Line: {self.line}")
        return " - ".join(parts)


class ParseError(CompilerError):
    """Parse error"""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None,
                 source_file: Optional[str] = None, token: Optional[str] = None):
        super().__init__(message, line, column, source_file)
        self.token = token
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.token:
            result += f" - Token: {self.token}"
        return result


class ValidationError(CompilerError):
    """Validation error"""
    
    def __init__(self, message: str, rule: Optional[str] = None, 
                 line: Optional[int] = None, column: Optional[int] = None,
                 source_file: Optional[str] = None, suggestions: Optional[List[str]] = None):
        super().__init__(message, line, column, source_file)
        self.rule = rule
        self.suggestions = suggestions or []
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.rule:
            result += f" - Rule: {self.rule}"
        if self.suggestions:
            result += f" - Suggestions: {', '.join(self.suggestions)}"
        return result


class SemanticError(CompilerError):
    """Semantic error"""
    
    def __init__(self, message: str, node_id: Optional[str] = None,
                 line: Optional[int] = None, column: Optional[int] = None,
                 source_file: Optional[str] = None):
        super().__init__(message, line, column, source_file)
        self.node_id = node_id
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.node_id:
            result += f" - Node: {self.node_id}"
        return result


class LLMError(CompilerError):
    """LLM invocation error"""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 model: Optional[str] = None, retry_count: int = 0):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.retry_count = retry_count
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.provider:
            result += f" - Provider: {self.provider}"
        if self.model:
            result += f" - Model: {self.model}"
        if self.retry_count > 0:
            result += f" - Retry count: {self.retry_count}"
        return result


class TimeoutError(CompilerError):
    """Timeout error"""
    
    def __init__(self, message: str, timeout: int, operation: Optional[str] = None):
        super().__init__(message)
        self.timeout = timeout
        self.operation = operation
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.operation:
            result += f" - Operation: {self.operation}"
        result += f" - Timeout: {self.timeout}s"
        return result


class ConfigurationError(CompilerError):
    """Configuration error"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message)
        self.config_key = config_key
    
    def __str__(self) -> str:
        result = super().__str__()
        if self.config_key:
            result += f" - Config key: {self.config_key}"
        return result 