"""
DSL Compiler Semantic Analyzer
Directive semantic checking, default value completion, cross-node reference resolution
"""

from typing import Dict, List, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import SemanticError, CompilerError


class SemanticAnalyzer:
    """Semantic Analyzer"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.symbol_table: Dict[str, Any] = {}
        self.task_definitions: Dict[str, ASTNode] = {}
        self.tool_definitions: Dict[str, ASTNode] = {}
        self.variable_definitions: Dict[str, ASTNode] = {}
        self.references: Dict[str, List[ASTNode]] = {}
        self.scopes: List[Dict[str, Any]] = []
        
    def analyze(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """
        Perform semantic analysis
        
        Args:
            ast_root: Root AST node
            context: Parse context
            
        Returns:
            ASTNode: Analyzed AST
            
        Raises:
            SemanticError: Semantic error
        """
        try:
            # Clear previous state
            self.symbol_table.clear()
            self.task_definitions.clear()
            self.tool_definitions.clear()
            self.variable_definitions.clear()
            self.references.clear()
            self.scopes.clear()
            
            # 1. Build symbol table
            self._build_symbol_table(ast_root)
            
            # 2. Type checking
            self._type_check(ast_root, context)
            
            # 3. Reference resolution
            self._resolve_references(ast_root, context)
            
            # 4. Default value completion
            self._complete_defaults(ast_root, context)
            
            # 5. Scope checking
            self._check_scopes(ast_root, context)
            
            # 6. Semantic validation
            self._validate_semantics(ast_root, context)
            
            return ast_root
            
        except Exception as e:
            if isinstance(e, SemanticError):
                raise
            else:
                raise SemanticError(f"Semantic analysis failed: {str(e)}")
    
    def _build_symbol_table(self, node: ASTNode) -> None:
        """Build symbol table"""
        if node.node_type == "task":
            task_id = node.get_attribute("id")
            if task_id:
                if task_id in self.task_definitions:
                    raise SemanticError(f"Task ID duplicate definition: {task_id}", 
                                      node_id=task_id, line=node.line)
                self.task_definitions[task_id] = node
                self.symbol_table[task_id] = {"type": "task", "node": node}
        
        elif node.node_type == "tool":
            tool_name = node.get_attribute("name")
            if tool_name:
                if tool_name in self.tool_definitions:
                    raise SemanticError(f"Tool name duplicate definition: {tool_name}", 
                                      node_id=tool_name, line=node.line)
                self.tool_definitions[tool_name] = node
                self.symbol_table[tool_name] = {"type": "tool", "node": node}
        
        elif node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name:
                if var_name in self.variable_definitions:
                    raise SemanticError(f"Variable name duplicate definition: {var_name}", 
                                      node_id=var_name, line=node.line)
                self.variable_definitions[var_name] = node
                self.symbol_table[var_name] = {"type": "variable", "node": node}
        
        # Recursively process child nodes
        for child in node.children:
            self._build_symbol_table(child)
    
    def _type_check(self, node: ASTNode, context: ParseContext) -> None:
        """Type checking"""
        if node.node_type == "task":
            self._check_task_type(node, context)
        elif node.node_type == "tool":
            self._check_tool_type(node, context)
        elif node.node_type == "var":
            self._check_variable_type(node, context)
        elif node.node_type == "if":
            self._check_condition_type(node, context)
        
        # Recursively process child nodes
        for child in node.children:
            self._type_check(child, context)
    
    def _check_task_type(self, node: ASTNode, context: ParseContext) -> None:
        """Check task type"""
        task_id = node.get_attribute("id")
        if not task_id:
            raise SemanticError("Task missing ID", line=node.line)
        
        # Check task ID format
        if not self._is_valid_identifier(task_id):
            raise SemanticError(f"Invalid task ID format: {task_id}", 
                              node_id=task_id, line=node.line)
        
        # Check if task has content
        has_content = False
        for child in node.children:
            if child.node_type == "text" and child.get_attribute("content", "").strip():
                has_content = True
                break
        
        if not has_content:
            # Add default content for empty tasks
            node.set_attribute("_has_default_content", True)
    
    def _check_tool_type(self, node: ASTNode, context: ParseContext) -> None:
        """Check tool type"""
        tool_name = node.get_attribute("name")
        if not tool_name:
            raise SemanticError("Tool missing name", line=node.line)
        
        # Check tool name format
        if not self._is_valid_identifier(tool_name):
            raise SemanticError(f"Invalid tool name format: {tool_name}", 
                              node_id=tool_name, line=node.line)
    
    def _check_variable_type(self, node: ASTNode, context: ParseContext) -> None:
        """Check variable type"""
        var_name = node.get_attribute("name")
        if not var_name:
            raise SemanticError("Variable missing name", line=node.line)
        
        # Check variable name format
        if not self._is_valid_identifier(var_name):
            raise SemanticError(f"Invalid variable name format: {var_name}", 
                              node_id=var_name, line=node.line)
        
        # Check variable value
        var_value = node.get_attribute("value")
        if var_value is not None:
            # Simple type inference
            inferred_type = self._infer_type(var_value)
            node.set_attribute("inferred_type", inferred_type)
    
    def _check_condition_type(self, node: ASTNode, context: ParseContext) -> None:
        """Check condition type"""
        condition = node.get_attribute("condition")
        if not condition:
            raise SemanticError("Condition expression is empty", line=node.line)
        
        # Simple condition expression validation
        if not self._is_valid_condition(condition):
            raise SemanticError(f"Invalid condition expression: {condition}", line=node.line)
    
    def _resolve_references(self, node: ASTNode, context: ParseContext) -> None:
        """Resolve references"""
        # Collect references
        if node.node_type == "text":
            content = node.get_attribute("content", "")
            refs = self._extract_references(content)
            for ref in refs:
                if ref not in self.references:
                    self.references[ref] = []
                self.references[ref].append(node)
        
        # Recursively process child nodes
        for child in node.children:
            self._resolve_references(child, context)
        
        # Validate references
        self._validate_references(context)
    
    def _validate_references(self, context: ParseContext) -> None:
        """Validate reference validity"""
        for ref_name, ref_nodes in self.references.items():
            if ref_name not in self.symbol_table:
                # Check if it's a built-in reference
                if not self._is_builtin_reference(ref_name):
                    for ref_node in ref_nodes:
                        raise SemanticError(f"Undefined reference: {ref_name}", 
                                          node_id=ref_name, line=ref_node.line)
    
    def _complete_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """Complete default values"""
        if node.node_type == "task":
            self._complete_task_defaults(node, context)
        elif node.node_type == "tool":
            self._complete_tool_defaults(node, context)
        elif node.node_type == "var":
            self._complete_variable_defaults(node, context)
        
        # Recursively process child nodes
        for child in node.children:
            self._complete_defaults(child, context)
    
    def _complete_task_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """Complete task default values"""
        # If task has no title, use ID as title
        if not node.get_attribute("title"):
            task_id = node.get_attribute("id")
            if task_id:
                node.set_attribute("title", task_id.replace("_", " ").title())
        
        # If task has no content, add default content
        if node.get_attribute("_has_default_content"):
            from .parser import ASTNode as ParserASTNode
            default_content = ParserASTNode("text", node.line, node.column)
            default_content.set_attribute("content", f"Execute task: {node.get_attribute('title')}")
            node.add_child(default_content)
    
    def _complete_tool_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """Complete tool default values"""
        # If tool has no description, use name as description
        if not node.get_attribute("description"):
            tool_name = node.get_attribute("name")
            if tool_name:
                node.set_attribute("description", f"Tool: {tool_name}")
    
    def _complete_variable_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """Complete variable default values"""
        # If variable has no value, set to None
        if node.get_attribute("value") is None:
            node.set_attribute("value", None)
            node.set_attribute("inferred_type", "none")
    
    def _check_scopes(self, node: ASTNode, context: ParseContext) -> None:
        """Check scopes"""
        # Enter new scope
        if node.node_type in ["task", "tool", "if", "else"]:
            self.scopes.append({})
        
        # Process current node
        if node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name and self.scopes:
                # Check if already defined in current scope
                if var_name in self.scopes[-1]:
                    raise SemanticError(f"Variable redefined in current scope: {var_name}", 
                                      node_id=var_name, line=node.line)
                self.scopes[-1][var_name] = node
        
        # Recursively process child nodes
        for child in node.children:
            self._check_scopes(child, context)
        
        # Exit scope
        if node.node_type in ["task", "tool", "if", "else"]:
            self.scopes.pop()
    
    def _validate_semantics(self, node: ASTNode, context: ParseContext) -> None:
        """Semantic validation"""
        # Check conditional block matching
        if node.node_type == "if":
            self._validate_conditional_block(node, context)
        
        # Check task flow
        if node.node_type == "task":
            self._validate_task_flow(node, context)
        
        # Recursively process child nodes
        for child in node.children:
            self._validate_semantics(child, context)
    
    def _validate_conditional_block(self, node: ASTNode, context: ParseContext) -> None:
        """Validate conditional block"""
        # Check for matching endif
        # This needs to be checked at parent node level, simplified implementation
        pass
    
    def _validate_task_flow(self, node: ASTNode, context: ParseContext) -> None:
        """Validate task flow"""
        # Check for circular references in tasks
        task_id = node.get_attribute("id")
        if task_id:
            self._check_circular_references(task_id, set(), context)
    
    def _check_circular_references(self, task_id: str, visited: Set[str], context: ParseContext) -> None:
        """Check circular references"""
        if task_id in visited:
            raise SemanticError(f"Circular reference detected: {task_id}", node_id=task_id)
        
        visited.add(task_id)
        
        # Check task dependencies
        if task_id in self.task_definitions:
            task_node = self.task_definitions[task_id]
            # This needs to check actual dependency relationships
            # Simplified implementation, temporarily skip
        
        visited.remove(task_id)
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if it's a valid identifier"""
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
    
    def _infer_type(self, value: Any) -> str:
        """Infer type"""
        if value is None:
            return "none"
        
        # If already a concrete type, return directly
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        
        # Handle string-type values
        if isinstance(value, str):
            value = value.strip()
            
            # Boolean values
            if value.lower() in ["true", "false"]:
                return "boolean"
            
            # Numbers
            try:
                if '.' in value:
                    float(value)
                    return "float"
                else:
                    int(value)
                    return "integer"
            except ValueError:
                pass
        
        # Default string
        return "string"
    
    def _is_valid_condition(self, condition: str) -> bool:
        """Check if condition expression is valid"""
        # Simple condition expression validation
        if not condition.strip():
            return False
        
        # Check for dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$']
        for char in dangerous_chars:
            if char in condition:
                return False
        
        return True
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract references from text"""
        import re
        # Find references like ${variable} or @{task_id}
        pattern = r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        matches = re.findall(pattern, content)
        return matches
    
    def _is_builtin_reference(self, ref_name: str) -> bool:
        """Check if it's a built-in reference"""
        builtin_refs = ["env", "config", "context", "result", "input", "output"]
        return ref_name in builtin_refs
    
    def get_symbol_table(self) -> Dict[str, Any]:
        """Get symbol table"""
        return self.symbol_table.copy()
    
    def get_task_definitions(self) -> Dict[str, ASTNode]:
        """Get task definitions"""
        return self.task_definitions.copy()
    
    def get_tool_definitions(self) -> Dict[str, ASTNode]:
        """Get tool definitions"""
        return self.tool_definitions.copy()
    
    def get_variable_definitions(self) -> Dict[str, ASTNode]:
        """Get variable definitions"""
        return self.variable_definitions.copy()
    
    def get_references(self) -> Dict[str, List[ASTNode]]:
        """Get reference information"""
        return self.references.copy() 