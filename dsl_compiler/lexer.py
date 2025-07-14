"""
DSL 编译器词法分析器
生成 Token 流 (DirectiveToken / TextToken)
"""

import re
from typing import List, Iterator, Optional, Tuple, Union, cast, Literal
from .config import CompilerConfig
from .models import Token, ParseContext
from .exceptions import ParseError, CompilerError


class Lexer:
    """词法分析器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        
        # 定义 token 类型的正则表达式
        self.token_patterns = [
            # 指令 token
            ('DIRECTIVE', r'^\s*@(task|tool|var|if|else|endif|include|agent|lang|next)(?:\s+(.*))?$'),
            # 代码块标记
            ('CODE_BLOCK_START', r'^\s*```(\w+)?$'),
            ('CODE_BLOCK_END', r'^\s*```$'),
            # 注释
            ('COMMENT', r'^\s*#.*$'),
            # 空行
            ('EMPTY_LINE', r'^\s*$'),
            # 普通文本
            ('TEXT', r'^.*$'),
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [(name, re.compile(pattern)) for name, pattern in self.token_patterns]
        
        # 指令参数解析器
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
        将内容分词为 Token 流
        
        Args:
            content: 预处理后的内容
            context: 解析上下文
            
        Returns:
            List[Token]: Token 列表
            
        Raises:
            ParseError: 词法分析错误
        """
        tokens = []
        lines = content.split('\n')
        
        current_line = 1
        indent_stack = [0]  # 缩进栈
        in_code_block = False
        code_block_lang = None
        
        for line_num, line in enumerate(lines, 1):
            context.current_line = line_num
            context.current_column = 1
            
            try:
                # 处理代码块
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
                
                # 检查代码块开始
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
                
                # 处理缩进
                indent_level = len(line) - len(line.lstrip())
                
                # 生成缩进/反缩进 token
                if line.strip():  # 非空行
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
                
                # 匹配 token 类型
                token_type, token_value = self._match_line(line, line_num)
                
                if token_type:
                    # 确保 token_type 是正确的类型
                    valid_types = ["directive", "text", "indent", "dedent", "newline", "eof"]
                    if token_type not in valid_types:
                        token_type = "text"
                    
                    tokens.append(Token(
                        type=cast(Literal["directive", "text", "indent", "dedent", "newline", "eof"], token_type),
                        value=token_value,
                        line=line_num,
                        column=1
                    ))
                
                # 添加换行符 token
                if line_num < len(lines):
                    tokens.append(Token(
                        type="newline",
                        value="\n",
                        line=line_num,
                        column=len(line) + 1
                    ))
                
            except Exception as e:
                raise ParseError(
                    f"词法分析错误: {str(e)}",
                    line=line_num,
                    source_file=context.source_file
                )
        
        # 处理剩余的缩进
        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(
                type="dedent",
                value="",
                line=len(lines),
                column=1
            ))
        
        # 添加 EOF token
        tokens.append(Token(
            type="eof",
            value="",
            line=len(lines) + 1,
            column=1
        ))
        
        return tokens
    
    def _match_line(self, line: str, line_num: int) -> Tuple[str, str]:
        """匹配行的 token 类型"""
        for token_type, pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                if token_type == 'DIRECTIVE':
                    return "directive", line.strip()
                elif token_type == 'COMMENT':
                    return "text", line.strip()  # 注释作为文本处理
                elif token_type == 'EMPTY_LINE':
                    return "text", ""
                elif token_type == 'TEXT':
                    return "text", line
                else:
                    return token_type.lower(), line.strip()
        
        return "text", line
    
    def _is_code_block_start(self, line: str) -> bool:
        """检查是否是代码块开始"""
        return bool(re.match(r'^\s*```(\w+)?$', line))
    
    def _is_code_block_end(self, line: str) -> bool:
        """检查是否是代码块结束"""
        return bool(re.match(r'^\s*```$', line))
    
    def _parse_task_directive(self, directive_text: str) -> dict:
        """解析 @task 指令"""
        # @task [id] [title]
        parts = directive_text.split(None, 2)
        
        result = {'type': 'task'}
        if len(parts) > 1:
            result['id'] = parts[1]
        if len(parts) > 2:
            result['title'] = parts[2]
        
        return result
    
    def _parse_tool_directive(self, directive_text: str) -> dict:
        """解析 @tool 指令"""
        # @tool [name] [description]
        parts = directive_text.split(None, 2)
        
        result = {'type': 'tool'}
        if len(parts) > 1:
            result['name'] = parts[1]
        if len(parts) > 2:
            result['description'] = parts[2]
        
        return result
    
    def _parse_var_directive(self, directive_text: str) -> dict:
        """解析 @var 指令"""
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
        """解析 @if 指令"""
        # @if condition
        parts = directive_text.split(None, 1)
        
        result = {'type': 'if'}
        if len(parts) > 1:
            result['condition'] = parts[1]
        
        return result
    
    def _parse_else_directive(self, directive_text: str) -> dict:
        """解析 @else 指令"""
        return {'type': 'else'}
    
    def _parse_endif_directive(self, directive_text: str) -> dict:
        """解析 @endif 指令"""
        return {'type': 'endif'}
    
    def _parse_include_directive(self, directive_text: str) -> dict:
        """解析 @include 指令"""
        # @include file_path
        parts = directive_text.split(None, 1)
        
        result = {'type': 'include'}
        if len(parts) > 1:
            result['file_path'] = parts[1]
        
        return result
    
    def _parse_agent_directive(self, directive_text: str) -> dict:
        """解析 @agent 指令"""
        # @agent AgentName(param1=value1, param2=value2)
        import re
        
        # 匹配 agent 名称和参数
        match = re.match(r'^\s*@agent\s+(\w+)(?:\((.*)\))?', directive_text)
        result = {'type': 'agent'}
        
        if match:
            result['name'] = match.group(1)
            if match.group(2):
                result['parameters'] = match.group(2).strip()
        
        return result
    
    def _parse_lang_directive(self, directive_text: str) -> dict:
        """解析 @lang 指令"""
        # @lang en-US
        parts = directive_text.split(None, 1)
        
        result = {'type': 'lang'}
        if len(parts) > 1:
            result['language'] = parts[1]
        
        return result
    
    def _parse_next_directive(self, directive_text: str) -> dict:
        """解析 @next 指令"""
        # @next TaskName
        parts = directive_text.split(None, 1)
        
        result = {'type': 'next'}
        if len(parts) > 1:
            result['target'] = parts[1]
        
        return result
    
    def parse_directive(self, directive_text: str) -> dict:
        """解析指令内容"""
        # 提取指令类型
        match = re.match(r'^\s*@(\w+)', directive_text)
        if not match:
            raise ParseError(f"无效的指令格式: {directive_text}")
        
        directive_type = match.group(1)
        
        # 使用对应的解析器
        if directive_type in self.directive_parsers:
            return self.directive_parsers[directive_type](directive_text)
        else:
            raise ParseError(f"不支持的指令类型: {directive_type}")
    
    def tokenize_expression(self, expression: str) -> List[Token]:
        """为表达式分词（用于条件表达式等）"""
        tokens = []
        
        # 简单的表达式分词
        # 这里可以根据需要实现更复杂的表达式解析
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
            
            # 检查操作符
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
        
        # 处理最后一个 token
        if current_token:
            tokens.append(Token(
                type="text",
                value=current_token,
                line=1,
                column=len(expression) - len(current_token)
            ))
        
        return tokens
    
    def get_token_statistics(self, tokens: List[Token]) -> dict:
        """获取 token 统计信息"""
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