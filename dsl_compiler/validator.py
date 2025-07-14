"""
DSL 编译器验证器
DAG 检测、类型检查、变量作用域、冲突检查
"""

from typing import List, Dict, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import ValidationError, CompilerError


class Validator:
    """验证器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def validate(self, ast_root: ASTNode, context: ParseContext) -> List[ValidationError]:
        """
        验证 AST
        
        Args:
            ast_root: 根 AST 节点
            context: 解析上下文
            
        Returns:
            List[ValidationError]: 验证错误列表
        """
        self.errors = []
        self.warnings = []
        
        try:
            # 1. DAG 检测
            self._validate_dag(ast_root, context)
            
            # 2. 类型检查
            self._validate_types(ast_root, context)
            
            # 3. 变量作用域检查
            self._validate_scopes(ast_root, context)
            
            # 4. 冲突检查
            self._validate_conflicts(ast_root, context)
            
            # 5. 引用检查
            self._validate_references(ast_root, context)
            
            # 6. 语义一致性检查
            self._validate_consistency(ast_root, context)
            
            return self.errors
            
        except Exception as e:
            error = ValidationError(f"验证过程发生错误: {str(e)}")
            self.errors.append(error)
            return self.errors
    
    def _validate_dag(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证 DAG 结构"""
        # 收集所有任务节点
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # 构建任务图
        task_graph: Dict[str, List[str]] = {}
        task_map: Dict[str, ASTNode] = {}
        
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                task_map[task_id] = task_node
                task_graph[task_id] = []
        
        # 分析任务依赖关系
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                # 查找 next 关系
                next_tasks = self._extract_next_tasks(task_node)
                task_graph[task_id].extend(next_tasks)
        
        # 检查循环依赖
        self._detect_cycles(task_graph, task_map)
        
        # 检查孤立节点
        self._detect_isolated_nodes(task_graph, task_map)
    
    def _validate_types(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证类型"""
        # 验证变量类型
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            self._validate_variable_type(var_node, context)
        
        # 验证任务类型
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            self._validate_task_type(task_node, context)
        
        # 验证工具类型
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            self._validate_tool_type(tool_node, context)
    
    def _validate_scopes(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证作用域"""
        # 构建作用域树
        scope_stack = [{}]  # 全局作用域
        
        self._validate_node_scope(ast_root, scope_stack, context)
    
    def _validate_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证冲突"""
        # 检查 ID 冲突
        self._check_id_conflicts(ast_root, context)
        
        # 检查名称冲突
        self._check_name_conflicts(ast_root, context)
        
        # 检查资源冲突
        self._check_resource_conflicts(ast_root, context)
    
    def _validate_references(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证引用"""
        # 收集所有符号
        symbols = self._collect_symbols(ast_root)
        
        # 检查引用
        self._check_references(ast_root, symbols, context)
    
    def _validate_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证语义一致性"""
        # 检查任务流一致性
        self._check_task_flow_consistency(ast_root, context)
        
        # 检查工具参数一致性
        self._check_tool_parameter_consistency(ast_root, context)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """查找指定类型的节点"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _extract_next_tasks(self, task_node: ASTNode) -> List[str]:
        """提取任务的下一步任务"""
        next_tasks = []
        
        # 从任务内容中提取引用
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # 简单的引用提取
                import re
                matches = re.findall(r'@\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
                next_tasks.extend(matches)
        
        return next_tasks
    
    def _detect_cycles(self, graph: Dict[str, List[str]], task_map: Dict[str, ASTNode]) -> None:
        """检测循环依赖"""
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
                    # 找到循环
                    task_node = task_map.get(node)
                    if task_node:
                        self.errors.append(ValidationError(
                            f"检测到循环依赖: {node} -> {neighbor}",
                            rule="no_cycles",
                            line=task_node.line,
                            suggestions=["检查任务流程，移除循环引用"]
                        ))
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
    
    def _detect_isolated_nodes(self, graph: Dict[str, List[str]], task_map: Dict[str, ASTNode]) -> None:
        """检测孤立节点"""
        # 找到所有被引用的节点
        referenced = set()
        for node, neighbors in graph.items():
            referenced.update(neighbors)
        
        # 检查是否有节点既不是入口也不被引用
        for node in graph:
            if node not in referenced and not graph[node]:
                task_node = task_map.get(node)
                if task_node:
                    self.warnings.append(f"任务 '{node}' 可能是孤立节点")
    
    def _validate_variable_type(self, var_node: ASTNode, context: ParseContext) -> None:
        """验证变量类型"""
        var_name = var_node.get_attribute("name")
        var_value = var_node.get_attribute("value")
        inferred_type = var_node.get_attribute("inferred_type")
        
        if not var_name:
            self.errors.append(ValidationError(
                "变量缺少名称",
                rule="variable_name_required",
                line=var_node.line,
                suggestions=["为变量指定名称"]
            ))
        
        # 宽松的类型验证：只在严格模式下进行类型检查
        if self.config.strict_mode and var_value is not None and inferred_type:
            actual_type = self._get_actual_type(var_value)
            # 允许兼容的类型转换
            if not self._is_type_compatible(actual_type, inferred_type):
                self.warnings.append(
                    f"变量 '{var_name}' 类型可能不匹配: 期望 {inferred_type}, 实际 {actual_type}"
                )
    
    def _is_type_compatible(self, actual_type: str, expected_type: str) -> bool:
        """检查类型兼容性"""
        if actual_type == expected_type:
            return True
        
        # 宽松的类型兼容性规则
        compatible_types = {
            "integer": ["string", "float"],  # 数字可以来自字符串或浮点
            "float": ["string", "integer"],   # 浮点可以来自字符串或整数
            "string": ["integer", "float", "boolean"],  # 字符串可以表示任何类型
            "boolean": ["string"],            # 布尔值可以来自字符串
        }
        
        return actual_type in compatible_types.get(expected_type, [])
    
    def _validate_task_type(self, task_node: ASTNode, context: ParseContext) -> None:
        """验证任务类型"""
        task_id = task_node.get_attribute("id")
        
        if not task_id:
            self.errors.append(ValidationError(
                "任务缺少 ID",
                rule="task_id_required",
                line=task_node.line,
                suggestions=["为任务指定唯一的 ID"]
            ))
        
        # 检查任务是否有内容
        if not task_node.children:
            self.warnings.append(f"任务 '{task_id}' 没有内容")
    
    def _validate_tool_type(self, tool_node: ASTNode, context: ParseContext) -> None:
        """验证工具类型"""
        tool_name = tool_node.get_attribute("name")
        
        if not tool_name:
            self.errors.append(ValidationError(
                "工具缺少名称",
                rule="tool_name_required",
                line=tool_node.line,
                suggestions=["为工具指定名称"]
            ))
    
    def _validate_node_scope(self, node: ASTNode, scope_stack: List[Dict[str, Any]], context: ParseContext) -> None:
        """验证节点作用域"""
        # 进入新作用域
        if node.node_type in ["task", "tool", "if", "else"]:
            scope_stack.append({})
        
        # 处理变量定义
        if node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name:
                # 检查当前作用域是否已定义
                if var_name in scope_stack[-1]:
                    self.errors.append(ValidationError(
                        f"变量 '{var_name}' 在当前作用域重复定义",
                        rule="variable_redefinition",
                        line=node.line,
                        suggestions=["使用不同的变量名或检查作用域"]
                    ))
                else:
                    scope_stack[-1][var_name] = node
        
        # 递归处理子节点
        for child in node.children:
            self._validate_node_scope(child, scope_stack, context)
        
        # 退出作用域
        if node.node_type in ["task", "tool", "if", "else"]:
            scope_stack.pop()
    
    def _check_id_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """检查 ID 冲突"""
        # 收集所有 ID
        ids = {}
        
        # 任务 ID
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                if task_id in ids:
                    self.errors.append(ValidationError(
                        f"任务 ID '{task_id}' 重复定义",
                        rule="unique_task_id",
                        line=task_node.line,
                        suggestions=["使用唯一的任务 ID"]
                    ))
                else:
                    ids[task_id] = task_node
        
        # 工具 ID
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_id = tool_node.get_attribute("id")
            if tool_id:
                if tool_id in ids:
                    self.errors.append(ValidationError(
                        f"工具 ID '{tool_id}' 与其他元素冲突",
                        rule="unique_id",
                        line=tool_node.line,
                        suggestions=["使用唯一的工具 ID"]
                    ))
                else:
                    ids[tool_id] = tool_node
    
    def _check_name_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """检查名称冲突"""
        # 收集所有名称
        names = {}
        
        # 变量名
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            if var_name:
                if var_name in names:
                    self.errors.append(ValidationError(
                        f"变量名 '{var_name}' 重复定义",
                        rule="unique_variable_name",
                        line=var_node.line,
                        suggestions=["使用唯一的变量名"]
                    ))
                else:
                    names[var_name] = var_node
        
        # 工具名
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            if tool_name:
                if tool_name in names:
                    self.errors.append(ValidationError(
                        f"工具名 '{tool_name}' 与变量名冲突",
                        rule="unique_name",
                        line=tool_node.line,
                        suggestions=["使用不同的工具名"]
                    ))
                else:
                    names[tool_name] = tool_node
    
    def _check_resource_conflicts(self, ast_root: ASTNode, context: ParseContext) -> None:
        """检查资源冲突"""
        # 检查端口冲突
        ports = {}
        
        # 从工具参数中检查端口
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            parameters = tool_node.get_attribute("parameters", {})
            if isinstance(parameters, dict):
                port = parameters.get("port")
                if port:
                    if port in ports:
                        self.errors.append(ValidationError(
                            f"端口 {port} 冲突",
                            rule="unique_port",
                            line=tool_node.line,
                            suggestions=["使用不同的端口号"]
                        ))
                    else:
                        ports[port] = tool_node
    
    def _collect_symbols(self, ast_root: ASTNode) -> Dict[str, ASTNode]:
        """收集所有符号"""
        symbols = {}
        
        # 收集任务符号
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                symbols[task_id] = task_node
        
        # 收集变量符号
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            if var_name:
                symbols[var_name] = var_node
        
        # 收集工具符号
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            if tool_name:
                symbols[tool_name] = tool_node
        
        return symbols
    
    def _check_references(self, node: ASTNode, symbols: Dict[str, ASTNode], context: ParseContext) -> None:
        """检查引用"""
        if node.node_type == "text":
            content = node.get_attribute("content", "")
            # 查找引用
            import re
            refs = re.findall(r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
            
            for ref in refs:
                if ref not in symbols:
                    # 检查是否是内置引用
                    if not self._is_builtin_reference(ref):
                        self.errors.append(ValidationError(
                            f"未定义的引用: {ref}",
                            rule="undefined_reference",
                            line=node.line,
                            suggestions=[f"定义变量或任务 '{ref}'", "检查引用名称拼写"]
                        ))
        
        # 递归检查子节点
        for child in node.children:
            self._check_references(child, symbols, context)
    
    def _check_task_flow_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """检查任务流一致性"""
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # 检查是否有入口任务
        if not task_nodes:
            self.warnings.append("没有定义任何任务")
            return
        
        # 检查任务流的完整性
        for task_node in task_nodes:
            task_id = task_node.get_attribute("id")
            if task_id:
                # 检查任务是否有合理的内容
                if not task_node.children:
                    self.warnings.append(f"任务 '{task_id}' 没有内容")
    
    def _check_tool_parameter_consistency(self, ast_root: ASTNode, context: ParseContext) -> None:
        """检查工具参数一致性"""
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            parameters = tool_node.get_attribute("parameters", {})
            
            if tool_name and isinstance(parameters, dict):
                # 检查参数的有效性
                for param_name, param_value in parameters.items():
                    if not self._is_valid_parameter(param_name, param_value):
                        self.errors.append(ValidationError(
                            f"工具 '{tool_name}' 的参数 '{param_name}' 无效",
                            rule="invalid_parameter",
                            line=tool_node.line,
                            suggestions=["检查参数名称和值"]
                        ))
    
    def _get_actual_type(self, value: Any) -> str:
        """获取实际类型"""
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
        """检查是否是内置引用"""
        builtin_refs = ["env", "config", "context", "result", "input", "output", "this", "self"]
        return ref_name in builtin_refs
    
    def _is_valid_parameter(self, param_name: str, param_value: Any) -> bool:
        """检查参数是否有效"""
        # 简单的参数验证
        if not param_name or not isinstance(param_name, str):
            return False
        
        # 检查参数名格式
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param_name):
            return False
        
        return True
    
    def get_warnings(self) -> List[str]:
        """获取警告列表"""
        return self.warnings.copy() 