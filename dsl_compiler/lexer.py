"""
DSL Compiler Lexical Analyzer
Generates Token stream (DirectiveToken / TextToken)
"""

import re
from typing import List, Iterator, Optional, Tuple, Union, cast, Literal
from .config import CompilerConfig
from .models import Token, ParseContext
from .exceptions import ParseError, CompilerError


class Lexer:
    """Lexical Analyzer"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        
        # Define regex patterns for token types
        self.token_patterns = [
            # Directive tokens
            ('DIRECTIVE', r'^\s*@(task|tool|var|if|else|endif|include|agent|lang|next)(?:\s+(.*))?$'),
            # Code block markers
            ('CODE_BLOCK_START', r'^\s*```(\w+)?$'),
            ('CODE_BLOCK_END', r'^\s*```$'),
            # Comments
            ('COMMENT', r'^\s*#.*$'),
            # Empty lines
            ('EMPTY_LINE', r'^\s*$'),
            # Plain text
            ('TEXT', r'^.*$'),
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [(name, re.compile(pattern)) for name, pattern in self.token_patterns]
        
        # Directive parameter parsers
        self.directive_parsers = {
            'task': self._parse_task_directive,
            'tool': self._parse_tool_directive,
            'var': self._parse_var_directive,
            'if': self._parse_if_directive,
            'else': self._parse_else_directive,
            'endif': self._parse_endif_directive,
            'include': self._parse_include_directive,
            'agent': self._parse_agent_directive,
            'lang': self._parse_lang_directive,
            'next': self._parse_next_directive,
        }
    
    def tokenize(self, content: str, context: ParseContext) -> List[Token]:
        """
        Tokenize content into Token stream
        
        Args:
            content: Preprocessed content
            context: Parse context
            
        Returns:
            List[Token]: Token list
            
        Raises:
            ParseError: Lexical analysis error
        """
        tokens = []
        lines = content.split('\n')
        
        current_line = 1
        indent_stack = [0]  # Indentation stack
        in_code_block = False
        code_block_lang = None
        
        for line_num, line in enumerate(lines, 1):
            context.current_line = line_num
            context.current_column = 1
            
            try:
                # Handle code blocks
                if in_code_block:
                    if self._is_code_block_end(line):
                        tokens.append(Token(
                            type="directive",
                            value="```",
                            line=line_num,
                            column=1
                        ))
                        in_code_block = False
                        code_block_lang = None
                    else:
                        tokens.append(Token(
                            type="text",
                            value=line,
                            line=line_num,
                            column=1
                        ))
                    continue
                
                # Check code block start
                if self._is_code_block_start(line):
                    match = re.match(r'^\s*```(\w+)?$', line)
                    if match:
                        code_block_lang = match.group(1)
                        tokens.append(Token(
                            type="directive",
                            value=f"```{code_block_lang or ''}",
                            line=line_num,
                            column=1
                        ))
                        in_code_block = True
                        continue
                
                # Handle indentation
                indent_level = len(line) - len(line.lstrip())
                
                # Generate indent/dedent tokens
                if line.strip():  # Non-empty lines
                    while indent_level > indent_stack[-1]:
                        indent_stack.append(indent_level)
                        tokens.append(Token(
                            type="indent",
                            value=" " * indent_level,
                            line=line_num,
                            column=1
                        ))
                    
                    while indent_level < indent_stack[-1]:
                        indent_stack.pop()
                        tokens.append(Token(
                            type="dedent",
                            value="",
                            line=line_num,
                            column=1
                        ))
                
                # Match token type
                token_type, token_value = self._match_line(line, line_num)
                
                if token_type:
                    # Ensure token_type is correct type
                    valid_types = ["directive", "text", "indent", "dedent", "newline", "eof"]
                    if token_type not in valid_types:
                        token_type = "text"
                    
                    tokens.append(Token(
                        type=cast(Literal["directive", "text", "indent", "dedent", "newline", "eof"], token_type),
                        value=token_value,
                        line=line_num,
                        column=1
                    ))
                
                # Add newline token
                if line_num < len(lines):
                    tokens.append(Token(
                        type="newline",
                        value="\n",
                        line=line_num,
                        column=len(line) + 1
                    ))
                
            except Exception as e:
                raise ParseError(
                    f"Lexical analysis error: {str(e)}",
                    line=line_num,
                    source_file=context.source_file
                )
        
        # Handle remaining indentation
        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(
                type="dedent",
                value="",
                line=len(lines),
                column=1
            ))
        
        # Add EOF token
        tokens.append(Token(
            type="eof",
            value="",
            line=len(lines) + 1,
            column=1
        ))
        
        return tokens
    
    def _match_line(self, line: str, line_num: int) -> Tuple[str, str]:
        """Match line token type"""
        for token_type, pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                if token_type == 'DIRECTIVE':
                    return "directive", line.strip()
                elif token_type == 'COMMENT':
                    return "text", line.strip()  # Treat comments as text
                elif token_type == 'EMPTY_LINE':
                    return "text", ""
                elif token_type == 'TEXT':
                    return "text", line
                else:
                    return token_type.lower(), line.strip()
        
        return "text", line
    
    def _is_code_block_start(self, line: str) -> bool:
        """Check if line is code block start"""
        return bool(re.match(r'^\s*```(\w+)?$', line))
    
    def _is_code_block_end(self, line: str) -> bool:
        """Check if line is code block end"""
        return bool(re.match(r'^\s*```$', line))
    
    def _parse_task_directive(self, directive_text: str) -> dict:
        """Parse @task directive"""
        # @task [id] [title]
        parts = directive_text.split(None, 2)
        
        result = {'type': 'task'}
        if len(parts) > 1:
            result['id'] = parts[1]
        if len(parts) > 2:
            result['title'] = parts[2]
        
        return result
    
    def _parse_tool_directive(self, directive_text: str) -> dict:
        """Parse @tool directive"""
        # @tool [name] [description]
        parts = directive_text.split(None, 2)
        
        result = {'type': 'tool'}
        if len(parts) > 1:
            result['name'] = parts[1]
        if len(parts) > 2:
            result['description'] = parts[2]
        
        return result
    
    def _parse_var_directive(self, directive_text: str) -> dict:
        """Parse @var directive"""
        # @var name = value
        parts = directive_text.split(None, 1)
        
        result = {'type': 'var'}
        if len(parts) > 1:
            var_def = parts[1]
            if '=' in var_def:
                name, value = var_def.split('=', 1)
                result['name'] = name.strip()
                result['value'] = value.strip()
            else:
                result['name'] = var_def.strip()
        
        return result
    
    def _parse_if_directive(self, directive_text: str) -> dict:
        """Parse @if directive"""
        # @if condition
        parts = directive_text.split(None, 1)
        
        result = {'type': 'if'}
        if len(parts) > 1:
            result['condition'] = parts[1]
        
        return result
    
    def _parse_else_directive(self, directive_text: str) -> dict:
        """Parse @else directive"""
        return {'type': 'else'}
    
    def _parse_endif_directive(self, directive_text: str) -> dict:
        """Parse @endif directive"""
        return {'type': 'endif'}
    
    def _parse_include_directive(self, directive_text: str) -> dict:
        """Parse @include directive"""
        # @include file_path
        parts = directive_text.split(None, 1)
        
        result = {'type': 'include'}
        if len(parts) > 1:
            result['file_path'] = parts[1]
        
        return result
    
    def _parse_agent_directive(self, directive_text: str) -> dict:
        """Parse @agent directive"""
        # @agent AgentName(param1=value1, param2=value2)
        import re
        
        # Match agent name and parameters
        match = re.match(r'^\s*@agent\s+(\w+)(?:\((.*)\))?', directive_text)
        result = {'type': 'agent'}
        
        if match:
            result['name'] = match.group(1)
            if match.group(2):
                result['parameters'] = match.group(2).strip()
        
        return result
    
    def _parse_lang_directive(self, directive_text: str) -> dict:
        """Parse @lang directive"""
        # @lang en-US
        parts = directive_text.split(None, 1)
        
        result = {'type': 'lang'}
        if len(parts) > 1:
            result['language'] = parts[1]
        
        return result
    
    def _parse_next_directive(self, directive_text: str) -> dict:
        """Parse @next directive"""
        # @next TaskName
        parts = directive_text.split(None, 1)
        
        result = {'type': 'next'}
        if len(parts) > 1:
            result['target'] = parts[1]
        
        return result
    
    def parse_directive(self, directive_text: str) -> dict:
        """Parse directive content"""
        # Extract directive type
        match = re.match(r'^\s*@(\w+)', directive_text)
        if not match:
            raise ParseError(f"Invalid directive format: {directive_text}")
        
        directive_type = match.group(1)
        
        # Use corresponding parser
        if directive_type in self.directive_parsers:
            return self.directive_parsers[directive_type](directive_text)
        else:
            raise ParseError(f"Unsupported directive type: {directive_type}")
    
    def tokenize_expression(self, expression: str) -> List[Token]:
        """Tokenize expression (for conditional expressions, etc.)"""
        tokens = []
        
        # Simple expression tokenization
        # More complex expression parsing can be implemented here as needed
        operators = ['==', '!=', '<=', '>=', '<', '>', '&&', '||', '!']
        
        i = 0
        current_token = ""
        
        while i < len(expression):
            char = expression[i]
            
            if char.isspace():
                if current_token:
                    tokens.append(Token(
                        type="text",
                        value=current_token,
                        line=1,
                        column=i - len(current_token)
                    ))
                    current_token = ""
                i += 1
                continue
            
            # Check operators
            found_operator = False
            for op in operators:
                if expression[i:i+len(op)] == op:
                    if current_token:
                        tokens.append(Token(
                            type="text",
                            value=current_token,
                            line=1,
                            column=i - len(current_token)
                        ))
                        current_token = ""
                    
                    tokens.append(Token(
                        type="text",
                        value=op,
                        line=1,
                        column=i
                    ))
                    
                    i += len(op)
                    found_operator = True
                    break
            
            if not found_operator:
                current_token += char
                i += 1
        
        # Handle last token
        if current_token:
            tokens.append(Token(
                type="text",
                value=current_token,
                line=1,
                column=len(expression) - len(current_token)
            ))
        
        return tokens
    
    def get_token_statistics(self, tokens: List[Token]) -> dict:
        """Get token statistics"""
        stats = {
            'total_tokens': len(tokens),
            'directive_tokens': 0,
            'text_tokens': 0,
            'indent_tokens': 0,
            'dedent_tokens': 0,
            'newline_tokens': 0,
            'eof_tokens': 0
        }
        
        for token in tokens:
            if token.type == 'directive':
                stats['directive_tokens'] += 1
            elif token.type == 'text':
                stats['text_tokens'] += 1
            elif token.type == 'indent':
                stats['indent_tokens'] += 1
            elif token.type == 'dedent':
                stats['dedent_tokens'] += 1
            elif token.type == 'newline':
                stats['newline_tokens'] += 1
            elif token.type == 'eof':
                stats['eof_tokens'] += 1
        
        return stats 