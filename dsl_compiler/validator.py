"""
DSL Compiler Validator
DAG detection, type checking, variable scope, conflict checking
"""

from typing import List, Dict, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import ValidationError, CompilerError


class Validator:
    """Validator"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def validate(self, ast_root: ASTNode, context: ParseContext) -> List[ValidationError]:
        """
        Validate AST
        
        Args:
            ast_root: Root AST node
            context: Parse context
            
        Returns:
            List[ValidationError]: Validation error list
        """
        self.errors = []
        self.warnings = []
        
        try:
            # 1. DAG detection
            self._validate_dag(ast_root, context)
            
            # 2. Type checking
            self._validate_types(ast_root, context)
            
            # 3. Variable scope checking
            self._validate_scopes(ast_root, context)
            
            # 4. Conflict checking
            self._validate_conflicts(ast_root, context)
            
            # 5. Reference checking
            self._validate_references(ast_root, context)
            
            # 6. Semantic consistency checking
            self._validate_consistency(ast_root, context)
            
            return self.errors
            
        except Exception as e:
            error = ValidationError(f"Error occurred during validation: {str(e)}")
            self.errors.append(error)
            return self.errors
    
    def _validate_dag(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate DAG structure"""
        # Collect all task nodes
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # Build task graph
        task_graph: Dict[str, List[str]] = {}
        task_map: Dict[str, ASTNode] = {}
        
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                task_map[task_id] = task_node
                task_graph[task_id] = []
        
        # Analyze task dependency relationships
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                # Find next relationships
                next_tasks = self._extract_next_tasks(task_node)
                task_graph[task_id].extend(next_tasks)
        
        # Check circular dependencies
        self._detect_cycles(task_graph, task_map)
        
        # Check isolated nodes
        self._detect_isolated_nodes(task_graph, task_map)
    
    def _validate_types(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate types"""
        # Validate variable types
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            self._validate_variable_type(var_node, context)
        
        # Validate task types
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            self._validate_task_type(task_node, context)
        
        # Validate tool types
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            self._validate_tool_type(tool_node, context)
    
    def _validate_scopes(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate scopes"""
        # Build scope tree
        scope_stack = [{}]  # Global scope
        
        self._validate_node_scope(ast_root, scope_stack, context)
    
    def _validate_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate conflicts"""
        # Check ID conflicts
        self._check_id_conflicts(ast_root, context)
        
        # Check name conflicts
        self._check_name_conflicts(ast_root, context)
        
        # Check resource conflicts
        self._check_resource_conflicts(ast_root, context)
    
    def _validate_references(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate references"""
        # Collect all symbols
        symbols = self._collect_symbols(ast_root)
        
        # Check references
        self._check_references(ast_root, symbols, context)
    
    def _validate_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Validate semantic consistency"""
        # Check task flow consistency
        self._check_task_flow_consistency(ast_root, context)
        
        # Check tool parameter consistency
        self._check_tool_parameter_consistency(ast_root, context)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """Find nodes of specified type"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _extract_next_tasks(self, task_node: ASTNode) -> List[str]:
        """Extract next tasks from task"""
        next_tasks = []
        
        # Extract references from task content
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # Simple reference extraction
                import re
                matches = re.findall(r'@\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
                next_tasks.extend(matches)
        
        return next_tasks
    
    def _detect_cycles(self, graph: Dict[str, List[str]], task_map: Dict[str, ASTNode]) -> None:
        """Detect circular dependencies"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph and dfs(neighbor):
                    # Found cycle
                    task_node = task_map.get(node)
                    if task_node:
                        self.errors.append(ValidationError(
                            f"Circular dependency detected: {node} -> {neighbor}",
                            rule="no_cycles",
                            line=task_node.line,
                            suggestions=["Check task flow, remove circular references"]
                        ))
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
    
    def _detect_isolated_nodes(self, graph: Dict[str, List[str]], task_map: Dict[str, ASTNode]) -> None:
        """Detect isolated nodes"""
        # Find all referenced nodes
        referenced = set()
        for node, neighbors in graph.items():
            referenced.update(neighbors)
        
        # Check if any node is neither entry nor referenced
        for node in graph:
            if node not in referenced and not graph[node]:
                task_node = task_map.get(node)
                if task_node:
                    self.warnings.append(f"Task '{node}' may be an isolated node")
    
    def _validate_variable_type(self, var_node: ASTNode, context: ParseContext) -> None:
        """Validate variable type"""
        var_name = var_node.get_attribute("name")
        var_value = var_node.get_attribute("value")
        inferred_type = var_node.get_attribute("inferred_type")
        
        if not var_name:
            self.errors.append(ValidationError(
                "Variable missing name",
                rule="variable_name_required",
                line=var_node.line,
                suggestions=["Specify a name for the variable"]
            ))
        
        # Relaxed type validation: only perform type checking in strict mode
        if self.config.strict_mode and var_value is not None and inferred_type:
            actual_type = self._get_actual_type(var_value)
            # Allow compatible type conversions
            if not self._is_type_compatible(actual_type, inferred_type):
                self.warnings.append(
                    f"Variable '{var_name}' type may not match: expected {inferred_type}, actual {actual_type}"
                )
    
    def _is_type_compatible(self, actual_type: str, expected_type: str) -> bool:
        """Check type compatibility"""
        if actual_type == expected_type:
            return True
        
        # Relaxed type compatibility rules
        compatible_types = {
            "integer": ["string", "float"],  # Numbers can come from strings or floats
            "float": ["string", "integer"],   # Floats can come from strings or integers
            "string": ["integer", "float", "boolean"],  # Strings can represent any type
            "boolean": ["string"],            # Boolean values can come from strings
        }
        
        return actual_type in compatible_types.get(expected_type, [])
    
    def _validate_task_type(self, task_node: ASTNode, context: ParseContext) -> None:
        """Validate task type"""
        task_id = task_node.get_attribute("id")
        
        if not task_id:
            self.errors.append(ValidationError(
                "Task missing ID",
                rule="task_id_required",
                line=task_node.line,
                suggestions=["Specify a unique ID for the task"]
            ))
        
        # Check if task has content
        if not task_node.children:
            self.warnings.append(f"Task '{task_id}' has no content")
    
    def _validate_tool_type(self, tool_node: ASTNode, context: ParseContext) -> None:
        """Validate tool type"""
        tool_name = tool_node.get_attribute("name")
        
        if not tool_name:
            self.errors.append(ValidationError(
                "Tool missing name",
                rule="tool_name_required",
                line=tool_node.line,
                suggestions=["Specify a name for the tool"]
            ))
    
    def _validate_node_scope(self, node: ASTNode, scope_stack: List[Dict[str, Any]], context: ParseContext) -> None:
        """Validate node scope"""
        # Enter new scope
        if node.node_type in ["task", "tool", "if", "else"]:
            scope_stack.append({})
        
        # Handle variable definitions
        if node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name:
                # Check if already defined in current scope
                if var_name in scope_stack[-1]:
                    self.errors.append(ValidationError(
                        f"Variable '{var_name}' redefined in current scope",
                        rule="variable_redefinition",
                        line=node.line,
                        suggestions=["Use a different variable name or check scope"]
                    ))
                else:
                    scope_stack[-1][var_name] = node
        
        # Recursively process child nodes
        for child in node.children:
            self._validate_node_scope(child, scope_stack, context)
        
        # Exit scope
        if node.node_type in ["task", "tool", "if", "else"]:
            scope_stack.pop()
    
    def _check_id_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Check ID conflicts"""
        # Collect all IDs
        ids = {}
        
        # Task IDs
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                if task_id in ids:
                    self.errors.append(ValidationError(
                        f"Task ID '{task_id}' duplicate definition",
                        rule="unique_task_id",
                        line=task_node.line,
                        suggestions=["Use a unique task ID"]
                    ))
                else:
                    ids[task_id] = task_node
        
        # Tool IDs
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_id = tool_node.get_attribute("id")
            if tool_id:
                if tool_id in ids:
                    self.errors.append(ValidationError(
                        f"Tool ID '{tool_id}' conflicts with other elements",
                        rule="unique_id",
                        line=tool_node.line,
                        suggestions=["Use a unique tool ID"]
                    ))
                else:
                    ids[tool_id] = tool_node
    
    def _check_name_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Check name conflicts"""
        # Collect all names
        names = {}
        
        # Variable names
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            if var_name:
                if var_name in names:
                    self.errors.append(ValidationError(
                        f"Variable name '{var_name}' duplicate definition",
                        rule="unique_variable_name",
                        line=var_node.line,
                        suggestions=["Use a unique variable name"]
                    ))
                else:
                    names[var_name] = var_node
        
        # Tool names
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            if tool_name:
                if tool_name in names:
                    self.errors.append(ValidationError(
                        f"Tool name '{tool_name}' conflicts with variable name",
                        rule="unique_name",
                        line=tool_node.line,
                        suggestions=["Use a different tool name"]
                    ))
                else:
                    names[tool_name] = tool_node
    
    def _check_resource_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Check resource conflicts"""
        # Check port conflicts
        ports = {}
        
        # Check ports from tool parameters
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            parameters = tool_node.get_attribute("parameters", {})
            if isinstance(parameters, dict):
                port = parameters.get("port")
                if port:
                    if port in ports:
                        self.errors.append(ValidationError(
                            f"Port {port} conflict",
                            rule="unique_port",
                            line=tool_node.line,
                            suggestions=["Use a different port number"]
                        ))
                    else:
                        ports[port] = tool_node
    
    def _collect_symbols(self, ast_root: ASTNode) -> Dict[str, ASTNode]:
        """Collect all symbols"""
        symbols = {}
        
        # Collect task symbols
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                symbols[task_id] = task_node
        
        # Collect variable symbols
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            if var_name:
                symbols[var_name] = var_node
        
        # Collect tool symbols
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            if tool_name:
                symbols[tool_name] = tool_node
        
        return symbols
    
    def _check_references(self, node: ASTNode, symbols: Dict[str, ASTNode], context: ParseContext) -> None:
        """Check references"""
        if node.node_type == "text":
            content = node.get_attribute("content", "")
            # Find references
            import re
            refs = re.findall(r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
            
            for ref in refs:
                if ref not in symbols:
                    # Check if it's a built-in reference
                    if not self._is_builtin_reference(ref):
                        self.errors.append(ValidationError(
                            f"Undefined reference: {ref}",
                            rule="undefined_reference",
                            line=node.line,
                            suggestions=[f"Define variable or task '{ref}'", "Check reference name spelling"]
                        ))
        
        # Recursively check child nodes
        for child in node.children:
            self._check_references(child, symbols, context)
    
    def _check_task_flow_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Check task flow consistency"""
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # Check if there are entry tasks
        if not task_nodes:
            self.warnings.append("No tasks defined")
            return
        
        # Check task flow completeness
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                # Check if task has reasonable content
                if not task_node.children:
                    self.warnings.append(f"Task '{task_id}' has no content")
    
    def _check_tool_parameter_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """Check tool parameter consistency"""
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            parameters = tool_node.get_attribute("parameters", {})
            
            if tool_name and isinstance(parameters, dict):
                # Check parameter validity
                for param_name, param_value in parameters.items():
                    if not self._is_valid_parameter(param_name, param_value):
                        self.errors.append(ValidationError(
                            f"Tool '{tool_name}' parameter '{param_name}' is invalid",
                            rule="invalid_parameter",
                            line=tool_node.line,
                            suggestions=["Check parameter name and value"]
                        ))
    
    def _get_actual_type(self, value: Any) -> str:
        """Get actual type"""
        if value is None:
            return "none"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _is_builtin_reference(self, ref_name: str) -> bool:
        """Check if it's a built-in reference"""
        builtin_refs = ["env", "config", "context", "result", "input", "output", "this", "self"]
        return ref_name in builtin_refs
    
    def _is_valid_parameter(self, param_name: str, param_value: Any) -> bool:
        """Check if parameter is valid"""
        # Simple parameter validation
        if not param_name or not isinstance(param_name, str):
            return False
        
        # Check parameter name format
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param_name):
            return False
        
        return True
    
    def get_warnings(self) -> List[str]:
        """Get warning list"""
        return self.warnings.copy() 