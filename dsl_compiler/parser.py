"""
DSL Compiler Syntax Parser
Builds preliminary AST by indentation (TaskNode etc.)
"""

from typing import List, Dict, Any, Optional, Union
from .config import CompilerConfig
from .models import Token, ParseContext, TaskNode, ToolNode, VariableNode, Block, ConditionalNext
from .exceptions import ParseError, CompilerError


class ASTNode:
    """AST Node Base Class"""
    
    def __init__(self, node_type: str, line: int, column: int):
        self.node_type = node_type
        self.line = line
        self.column = column
        self.children: List['ASTNode'] = []
        self.parent: Optional['ASTNode'] = None
        self.attributes: Dict[str, Any] = {}
    
    def add_child(self, child: 'ASTNode') -> None:
        """Add child node"""
        child.parent = self
        self.children.append(child)
    
    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get attribute"""
        return self.attributes.get(name, default)
    
    def set_attribute(self, name: str, value: Any) -> None:
        """Set attribute"""
        self.attributes[name] = value


class Parser:
    """Syntax Parser"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.tokens: List[Token] = []
        self.current_token_index = 0
        self.current_token: Optional[Token] = None
        self.context: Optional[ParseContext] = None
    
    def parse(self, tokens: List[Token], context: ParseContext) -> ASTNode:
        """
        Parse Token stream to AST
        
        Args:
            tokens: Token list
            context: Parse context
            
        Returns:
            ASTNode: Root AST node
            
        Raises:
            ParseError: Syntax parsing error
        """
        self.tokens = tokens
        self.current_token_index = 0
        self.context = context
        
        if not tokens:
            raise ParseError("Empty Token stream", source_file=context.source_file)
        
        self.current_token = tokens[0] if tokens else None
        
        try:
            # Build root node
            root = ASTNode("root", 1, 1)
            
            # Parse top-level structure
            while not self._is_at_end():
                if self._match("eof"):
                    break
                
                node = self._parse_top_level()
                if node:
                    root.add_child(node)
            
            return root
            
        except Exception as e:
            if isinstance(e, ParseError):
                raise
            else:
                raise ParseError(
                    f"Syntax parsing error: {str(e)}",
                    line=self.current_token.line if self.current_token else 0,
                    column=self.current_token.column if self.current_token else 0,
                    source_file=context.source_file if context else None
                )
    
    def _parse_top_level(self) -> Optional[ASTNode]:
        """Parse top-level structure"""
        # Skip empty lines and newlines
        while self._match("newline", "text") and self.current_token and not self.current_token.value.strip():
            pass
        
        if self._is_at_end():
            return None
        
        # Handle directives
        if self._check("directive"):
            return self._parse_directive()
        
        # Handle text blocks
        if self._check("text"):
            return self._parse_text_block()
        
        # Handle indented blocks
        if self._check("indent"):
            return self._parse_indented_block()
        
        # Skip other tokens
        self._advance()
        return None
    
    def _parse_directive(self) -> Optional[ASTNode]:
        """Parse directive"""
        if not self._check("directive") or self.current_token is None:
            return None
        
        directive_token = self.current_token
        self._advance()
        
        # Parse directive content
        directive_text = directive_token.value
        
        # Extract directive type
        import re
        match = re.match(r'^\s*@(\w+)', directive_text)
        if not match:
            raise ParseError(f"Invalid directive format: {directive_text}", 
                           line=directive_token.line, 
                           column=directive_token.column,
                           source_file=self.context.source_file if self.context else None)
        
        directive_type = match.group(1)
        
        # Create corresponding AST node based on directive type
        if directive_type == "task":
            return self._parse_task_directive(directive_text, directive_token)
        elif directive_type == "tool":
            return self._parse_tool_directive(directive_text, directive_token)
        elif directive_type == "var":
            return self._parse_var_directive(directive_text, directive_token)
        elif directive_type == "if":
            return self._parse_if_directive(directive_text, directive_token)
        elif directive_type == "else":
            return self._parse_else_directive(directive_text, directive_token)
        elif directive_type == "endif":
            return self._parse_endif_directive(directive_text, directive_token)
        elif directive_type == "include":
            return self._parse_include_directive(directive_text, directive_token)
        elif directive_type == "agent":
            return self._parse_agent_directive(directive_text, directive_token)
        elif directive_type == "lang":
            return self._parse_lang_directive(directive_text, directive_token)
        elif directive_type == "next":
            return self._parse_next_directive(directive_text, directive_token)
        else:
            raise ParseError(f"Unsupported directive type: {directive_type}",
                           line=directive_token.line,
                           column=directive_token.column,
                           source_file=self.context.source_file if self.context else None)
    
    def _parse_task_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @task directive"""
        import re
        
        # Parse task parameters: @task task_id [title]
        match = re.match(r'^\s*@task\s+(\w+)(?:\s+(.*))?$', directive_text)
        if not match:
            raise ParseError(f"Invalid task definition: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        task_id = match.group(1)
        task_title = match.group(2).strip() if match.group(2) else None
        
        # Create task node
        task_node = ASTNode("task", token.line, token.column)
        task_node.set_attribute("id", task_id)
        task_node.set_attribute("title", task_title)
        
        # Parse task body
        self._parse_task_body(task_node)
        
        return task_node
    
    def _parse_tool_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @tool directive"""
        import re
        
        # Parse tool parameters: @tool tool_name
        match = re.match(r'^\s*@tool\s+(\w+)(?:\s+(.*))?$', directive_text)
        if not match:
            raise ParseError(f"Invalid tool definition: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        tool_name = match.group(1)
        tool_description = match.group(2).strip() if match.group(2) else None
        
        # Create tool node
        tool_node = ASTNode("tool", token.line, token.column)
        tool_node.set_attribute("name", tool_name)
        tool_node.set_attribute("description", tool_description)
        
        # Parse tool body
        self._parse_tool_body(tool_node)
        
        return tool_node
    
    def _parse_var_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @var directive"""
        import re
        
        # Parse variable parameters
        match = re.match(r'^\s*@var\s+(\w+)\s*(?:=\s*(.*))?$', directive_text)
        if not match:
            raise ParseError(f"Invalid variable definition: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        var_name = match.group(1)
        var_value_str = match.group(2) if match.group(2) else None
        
        # Basic type inference
        var_value = self._infer_variable_type(var_value_str) if var_value_str else None
        
        # Create variable node
        var_node = ASTNode("var", token.line, token.column)
        var_node.set_attribute("name", var_name)
        var_node.set_attribute("value", var_value)
        
        return var_node
    
    def _infer_variable_type(self, value_str: str) -> Any:
        """Infer variable type"""
        if not value_str:
            return None
        
        value_str = value_str.strip()
        
        # Try parsing as integer
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try parsing as float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Try parsing as boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        
        # Try parsing as null/None
        if value_str.lower() in ('null', 'none'):
            return None
        
        # Handle quoted strings
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Default to string
        return value_str
    
    def _parse_if_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @if directive"""
        import re
        
        # Parse condition
        match = re.match(r'^\s*@if\s+(.+)$', directive_text)
        if not match:
            raise ParseError(f"Invalid if condition: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        condition = match.group(1)
        
        # Create if node
        if_node = ASTNode("if", token.line, token.column)
        if_node.set_attribute("condition", condition)
        
        # Parse if body
        self._parse_conditional_body(if_node)
        
        return if_node
    
    def _parse_else_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @else directive"""
        else_node = ASTNode("else", token.line, token.column)
        
        # Parse else body
        self._parse_conditional_body(else_node)
        
        return else_node
    
    def _parse_endif_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @endif directive"""
        return ASTNode("endif", token.line, token.column)
    
    def _parse_include_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @include directive"""
        import re
        
        # Parse file path
        match = re.match(r'^\s*@include\s+(.+)$', directive_text)
        if not match:
            raise ParseError(f"Invalid include directive: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        file_path = match.group(1).strip('"\'')
        
        # Create include node
        include_node = ASTNode("include", token.line, token.column)
        include_node.set_attribute("file_path", file_path)
        
        return include_node
    
    def _parse_agent_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @agent directive"""
        import re
        
        # Parse agent name and parameters: @agent AgentName(param1=value1, param2=value2)
        match = re.match(r'^\s*@agent\s+(\w+)(?:\((.*)\))?', directive_text)
        if not match:
            raise ParseError(f"Invalid agent directive: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        agent_name = match.group(1)
        agent_params = match.group(2).strip() if match.group(2) else None
        
        # Create agent node
        agent_node = ASTNode("agent", token.line, token.column)
        agent_node.set_attribute("name", agent_name)
        if agent_params:
            agent_node.set_attribute("parameters", agent_params)
        
        return agent_node
    
    def _parse_lang_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @lang directive"""
        import re
        
        # Parse language setting: @lang en-US
        match = re.match(r'^\s*@lang\s+(.+)$', directive_text)
        if not match:
            raise ParseError(f"Invalid lang directive: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        language = match.group(1).strip()
        
        # Create lang node
        lang_node = ASTNode("lang", token.line, token.column)
        lang_node.set_attribute("language", language)
        
        return lang_node
    
    def _parse_next_directive(self, directive_text: str, token: Token) -> ASTNode:
        """Parse @next directive"""
        import re
        
        # Parse target task: @next TaskName
        match = re.match(r'^\s*@next\s+(.+)$', directive_text)
        if not match:
            raise ParseError(f"Invalid next directive: {directive_text}",
                           line=token.line, column=token.column,
                           source_file=self.context.source_file if self.context else None)
        
        target_task = match.group(1).strip()
        
        # Create next node
        next_node = ASTNode("next", token.line, token.column)
        next_node.set_attribute("target", target_task)
        
        return next_node
    
    def _parse_task_body(self, task_node: ASTNode) -> None:
        """Parse task body"""
        # Handle newlines
        self._skip_newlines()
        
        # Check if there's indented content
        if self._check("indent"):
            self._advance()  # Consume indent token
            
            # Parse indented content
            while not self._check("dedent") and not self._is_at_end():
                if self._match("newline"):
                    continue
                
                # Parse text blocks
                if self._check("text"):
                    text_node = self._parse_text_block()
                    if text_node:
                        task_node.add_child(text_node)
                elif self._check("directive"):
                    directive_node = self._parse_directive()
                    if directive_node:
                        task_node.add_child(directive_node)
                else:
                    self._advance()
            
            # Consume dedent token
            if self._check("dedent"):
                self._advance()
    
    def _parse_tool_body(self, tool_node: ASTNode) -> None:
        """Parse tool body"""
        # Handle newlines
        self._skip_newlines()
        
        # Check if there's indented content
        if self._check("indent"):
            self._advance()  # Consume indent token
            
            # Parse indented content
            while not self._check("dedent") and not self._is_at_end():
                if self._match("newline"):
                    continue
                
                # Parse text blocks
                if self._check("text"):
                    text_node = self._parse_text_block()
                    if text_node:
                        tool_node.add_child(text_node)
                else:
                    self._advance()
            
            # Consume dedent token
            if self._check("dedent"):
                self._advance()
    
    def _parse_conditional_body(self, parent_node: ASTNode) -> None:
        """Parse conditional body"""
        # Handle newlines
        self._skip_newlines()
        
        # Check if there's indented content
        if self._check("indent"):
            self._advance()  # Consume indent token
            
            # Parse indented content
            while not self._check("dedent") and not self._is_at_end():
                if self._match("newline"):
                    continue
                
                # Parse text blocks or directives, not top-level elements
                if self._check("text"):
                    text_node = self._parse_text_block()
                    if text_node:
                        parent_node.add_child(text_node)
                elif self._check("directive"):
                    directive_node = self._parse_directive()
                    if directive_node:
                        parent_node.add_child(directive_node)
                else:
                    self._advance()
            
            # Consume dedent token
            if self._check("dedent"):
                self._advance()
    
    def _parse_text_block(self) -> Optional[ASTNode]:
        """Parse text block"""
        if not self._check("text") or self.current_token is None:
            return None
        
        text_token = self.current_token
        self._advance()
        
        # Create text node
        text_node = ASTNode("text", text_token.line, text_token.column)
        text_node.set_attribute("content", text_token.value)
        
        return text_node
    
    def _parse_indented_block(self) -> Optional[ASTNode]:
        """Parse indented block"""
        if not self._check("indent") or self.current_token is None:
            return None
        
        indent_token = self.current_token
        self._advance()
        
        # Create indented block node
        block_node = ASTNode("block", indent_token.line, indent_token.column)
        
        # Parse indented content
        while not self._check("dedent") and not self._is_at_end():
            if self._match("newline"):
                continue
            
            node = self._parse_top_level()
            if node:
                block_node.add_child(node)
        
        # Consume dedent token
        if self._check("dedent"):
            self._advance()
        
        return block_node
    
    def _skip_newlines(self) -> None:
        """Skip newlines"""
        while self._match("newline"):
            pass
    
    def _check(self, token_type: str) -> bool:
        """Check current token type"""
        if self._is_at_end() or self.current_token is None:
            return False
        return self.current_token.type == token_type
    
    def _match(self, *token_types: str) -> bool:
        """Match token types"""
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False
    
    def _advance(self) -> Optional[Token]:
        """Advance to next token"""
        if not self._is_at_end():
            self.current_token_index += 1
            
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        else:
            self.current_token = None
            
        return self.current_token
    
    def _is_at_end(self) -> bool:
        """Check if at end"""
        return (self.current_token_index >= len(self.tokens) or 
                self.current_token is None or 
                self.current_token.type == "eof")
    
    def _peek(self, offset: int = 1) -> Optional[Token]:
        """Look ahead at token"""
        peek_index = self.current_token_index + offset
        if peek_index < len(self.tokens):
            return self.tokens[peek_index]
        return None
    
    def _previous(self) -> Optional[Token]:
        """Get previous token"""
        if self.current_token_index > 0:
            return self.tokens[self.current_token_index - 1]
        return None
    
    def ast_to_dsl_nodes(self, ast_root: ASTNode) -> List[Union[TaskNode, ToolNode, VariableNode]]:
        """Convert AST to DSL nodes"""
        dsl_nodes = []
        
        for child in ast_root.children:
            if child.node_type == "task":
                task_node = self._ast_to_task_node(child)
                if task_node:
                    dsl_nodes.append(task_node)
            elif child.node_type == "tool":
                tool_node = self._ast_to_tool_node(child)
                if tool_node:
                    dsl_nodes.append(tool_node)
            elif child.node_type == "var":
                var_node = self._ast_to_var_node(child)
                if var_node:
                    dsl_nodes.append(var_node)
        
        return dsl_nodes
    
    def _ast_to_task_node(self, ast_node: ASTNode) -> Optional[TaskNode]:
        """Convert AST task node to TaskNode"""
        task_id = ast_node.get_attribute("id")
        task_title = ast_node.get_attribute("title")
        
        if not task_id:
            return None
        
        # Collect all blocks (text and directives) from task body
        body_blocks = []
        next_targets = []
        
        for child in ast_node.children:
            if child.node_type == "text":
                block = Block(
                    type="text",
                    content=child.get_attribute("content", ""),
                    line_number=child.line
                )
                body_blocks.append(block)
            elif child.node_type in ["tool", "agent", "lang", "next", "if", "else", "endif"]:
                # Convert directives to directive type blocks
                block = self._ast_directive_to_block(child)
                if block:
                    body_blocks.append(block)
                
                # If it's a next directive, collect jump targets
                if child.node_type == "next":
                    target = child.get_attribute("target")
                    if target:
                        next_targets.append(target)
        
        return TaskNode(
            id=task_id,
            title=task_title,
            body=body_blocks,
            next=next_targets,
            dependencies=[]
        )
    
    def _ast_directive_to_block(self, directive_node: ASTNode) -> Optional[Block]:
        """Convert directive AST node to Block"""
        directive_type = directive_node.node_type
        
        # Generate content based on directive type
        if directive_type == "tool":
            name = directive_node.get_attribute("name", "")
            description = directive_node.get_attribute("description", "")
            content = f"@tool {name}"
            if description:
                content += f" - {description}"
                
        elif directive_type == "agent":
            name = directive_node.get_attribute("name", "")
            params = directive_node.get_attribute("parameters", "")
            content = f"@agent {name}"
            if params:
                content += f"({params})"
                
        elif directive_type == "lang":
            language = directive_node.get_attribute("language", "")
            content = f"@lang {language}"
            
        elif directive_type == "next":
            target = directive_node.get_attribute("target", "")
            content = f"@next {target}"
            
        elif directive_type == "if":
            condition = directive_node.get_attribute("condition", "")
            content = f"@if {condition}"
            
            # Handle nested content in if block
            nested_content = []
            for child in directive_node.children:
                if child.node_type == "text":
                    nested_content.append(f"    {child.get_attribute('content', '').strip()}")
                elif child.node_type in ["tool", "agent", "lang", "next"]:
                    nested_block = self._ast_directive_to_block(child)
                    if nested_block:
                        nested_content.append(f"    {nested_block.content}")
            
            if nested_content:
                content += "\n" + "\n".join(nested_content)
            
        elif directive_type == "else":
            content = "@else"
            
            # Handle nested content in else block
            nested_content = []
            for child in directive_node.children:
                if child.node_type == "text":
                    nested_content.append(f"    {child.get_attribute('content', '').strip()}")
                elif child.node_type in ["tool", "agent", "lang", "next"]:
                    nested_block = self._ast_directive_to_block(child)
                    if nested_block:
                        nested_content.append(f"    {nested_block.content}")
            
            if nested_content:
                content += "\n" + "\n".join(nested_content)
            
        elif directive_type == "endif":
            content = "@endif"
            
        else:
            return None
        
        return Block(
            type="directive",
            content=content,
            line_number=directive_node.line
        )
    
    def _ast_to_tool_node(self, ast_node: ASTNode) -> Optional[ToolNode]:
        """Convert AST tool node to ToolNode"""
        tool_name = ast_node.get_attribute("name")
        tool_description = ast_node.get_attribute("description")
        
        if not tool_name:
            return None
        
        return ToolNode(
            id=f"tool_{ast_node.line}",
            name=tool_name,
            description=tool_description,
            parameters={}
        )
    
    def _ast_to_var_node(self, ast_node: ASTNode) -> Optional[VariableNode]:
        """Convert AST variable node to VariableNode"""
        var_name = ast_node.get_attribute("name")
        var_value = ast_node.get_attribute("value")
        
        if not var_name:
            return None
        
        return VariableNode(
            name=var_name,
            value=var_value,
            scope="global"
        ) 