"""
DSL 编译器语义分析器
指令语义检查、默认值补全、跨节点引用解析
"""

from typing import Dict, List, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import SemanticError, CompilerError


class SemanticAnalyzer:
    """语义分析器"""
    
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
        进行语义分析
        
        Args:
            ast_root: 根 AST 节点
            context: 解析上下文
            
        Returns:
            ASTNode: 分析后的 AST
            
        Raises:
            SemanticError: 语义错误
        """
        try:
            # 清除先前状态
            self.symbol_table.clear()
            self.task_definitions.clear()
            self.tool_definitions.clear()
            self.variable_definitions.clear()
            self.references.clear()
            self.scopes.clear()
            
            # 1. 构建符号表
            self._build_symbol_table(ast_root)
            
            # 2. 类型检查
            self._type_check(ast_root, context)
            
            # 3. 引用解析
            self._resolve_references(ast_root, context)
            
            # 4. 默认值补全
            self._complete_defaults(ast_root, context)
            
            # 5. 作用域检查
            self._check_scopes(ast_root, context)
            
            # 6. 语义验证
            self._validate_semantics(ast_root, context)
            
            return ast_root
            
        except Exception as e:
            if isinstance(e, SemanticError):
                raise
            else:
                raise SemanticError(f"语义分析失败: {str(e)}")
    
    def _build_symbol_table(self, node: ASTNode) -> None:
        """构建符号表"""
        if node.node_type == "task":
            task_id = node.get_attribute("id")
            if task_id:
                if task_id in self.task_definitions:
                    raise SemanticError(f"任务 ID 重复定义: {task_id}", 
                                      node_id=task_id, line=node.line)
                self.task_definitions[task_id] = node
                self.symbol_table[task_id] = {"type": "task", "node": node}
        
        elif node.node_type == "tool":
            tool_name = node.get_attribute("name")
            if tool_name:
                if tool_name in self.tool_definitions:
                    raise SemanticError(f"工具名称重复定义: {tool_name}", 
                                      node_id=tool_name, line=node.line)
                self.tool_definitions[tool_name] = node
                self.symbol_table[tool_name] = {"type": "tool", "node": node}
        
        elif node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name:
                if var_name in self.variable_definitions:
                    raise SemanticError(f"变量名称重复定义: {var_name}", 
                                      node_id=var_name, line=node.line)
                self.variable_definitions[var_name] = node
                self.symbol_table[var_name] = {"type": "variable", "node": node}
        
        # 递归处理子节点
        for child in node.children:
            self._build_symbol_table(child)
    
    def _type_check(self, node: ASTNode, context: ParseContext) -> None:
        """类型检查"""
        if node.node_type == "task":
            self._check_task_type(node, context)
        elif node.node_type == "tool":
            self._check_tool_type(node, context)
        elif node.node_type == "var":
            self._check_variable_type(node, context)
        elif node.node_type == "if":
            self._check_condition_type(node, context)
        
        # 递归处理子节点
        for child in node.children:
            self._type_check(child, context)
    
    def _check_task_type(self, node: ASTNode, context: ParseContext) -> None:
        """检查任务类型"""
        task_id = node.get_attribute("id")
        if not task_id:
            raise SemanticError("任务缺少 ID", line=node.line)
        
        # 检查任务 ID 格式
        if not self._is_valid_identifier(task_id):
            raise SemanticError(f"无效的任务 ID 格式: {task_id}", 
                              node_id=task_id, line=node.line)
        
        # 检查任务体
        has_content = False
        for child in node.children:
            if child.node_type == "text" and child.get_attribute("content", "").strip():
                has_content = True
                break
        
        if not has_content:
            # 为空任务添加默认内容
            node.set_attribute("_has_default_content", True)
    
    def _check_tool_type(self, node: ASTNode, context: ParseContext) -> None:
        """检查工具类型"""
        tool_name = node.get_attribute("name")
        if not tool_name:
            raise SemanticError("工具缺少名称", line=node.line)
        
        # 检查工具名称格式
        if not self._is_valid_identifier(tool_name):
            raise SemanticError(f"无效的工具名称格式: {tool_name}", 
                              node_id=tool_name, line=node.line)
    
    def _check_variable_type(self, node: ASTNode, context: ParseContext) -> None:
        """检查变量类型"""
        var_name = node.get_attribute("name")
        if not var_name:
            raise SemanticError("变量缺少名称", line=node.line)
        
        # 检查变量名称格式
        if not self._is_valid_identifier(var_name):
            raise SemanticError(f"无效的变量名称格式: {var_name}", 
                              node_id=var_name, line=node.line)
        
        # 检查变量值
        var_value = node.get_attribute("value")
        if var_value is not None:
            # 简单的类型推断
            inferred_type = self._infer_type(var_value)
            node.set_attribute("inferred_type", inferred_type)
    
    def _check_condition_type(self, node: ASTNode, context: ParseContext) -> None:
        """检查条件类型"""
        condition = node.get_attribute("condition")
        if not condition:
            raise SemanticError("条件表达式为空", line=node.line)
        
        # 简单的条件表达式验证
        if not self._is_valid_condition(condition):
            raise SemanticError(f"无效的条件表达式: {condition}", line=node.line)
    
    def _resolve_references(self, node: ASTNode, context: ParseContext) -> None:
        """解析引用"""
        # 收集引用
        if node.node_type == "text":
            content = node.get_attribute("content", "")
            refs = self._extract_references(content)
            for ref in refs:
                if ref not in self.references:
                    self.references[ref] = []
                self.references[ref].append(node)
        
        # 递归处理子节点
        for child in node.children:
            self._resolve_references(child, context)
        
        # 验证引用
        self._validate_references(context)
    
    def _validate_references(self, context: ParseContext) -> None:
        """验证引用的有效性"""
        for ref_name, ref_nodes in self.references.items():
            if ref_name not in self.symbol_table:
                # 检查是否是内置引用
                if not self._is_builtin_reference(ref_name):
                    for ref_node in ref_nodes:
                        raise SemanticError(f"未定义的引用: {ref_name}", 
                                          node_id=ref_name, line=ref_node.line)
    
    def _complete_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """补全默认值"""
        if node.node_type == "task":
            self._complete_task_defaults(node, context)
        elif node.node_type == "tool":
            self._complete_tool_defaults(node, context)
        elif node.node_type == "var":
            self._complete_variable_defaults(node, context)
        
        # 递归处理子节点
        for child in node.children:
            self._complete_defaults(child, context)
    
    def _complete_task_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """补全任务默认值"""
        # 如果任务没有标题，使用 ID 作为标题
        if not node.get_attribute("title"):
            task_id = node.get_attribute("id")
            if task_id:
                node.set_attribute("title", task_id.replace("_", " ").title())
        
        # 如果任务没有内容，添加默认内容
        if node.get_attribute("_has_default_content"):
            from .parser import ASTNode as ParserASTNode
            default_content = ParserASTNode("text", node.line, node.column)
            default_content.set_attribute("content", f"执行任务: {node.get_attribute('title')}")
            node.add_child(default_content)
    
    def _complete_tool_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """补全工具默认值"""
        # 如果工具没有描述，使用名称作为描述
        if not node.get_attribute("description"):
            tool_name = node.get_attribute("name")
            if tool_name:
                node.set_attribute("description", f"工具: {tool_name}")
    
    def _complete_variable_defaults(self, node: ASTNode, context: ParseContext) -> None:
        """补全变量默认值"""
        # 如果变量没有值，设置为 None
        if node.get_attribute("value") is None:
            node.set_attribute("value", None)
            node.set_attribute("inferred_type", "none")
    
    def _check_scopes(self, node: ASTNode, context: ParseContext) -> None:
        """检查作用域"""
        # 进入新作用域
        if node.node_type in ["task", "tool", "if", "else"]:
            self.scopes.append({})
        
        # 处理当前节点
        if node.node_type == "var":
            var_name = node.get_attribute("name")
            if var_name and self.scopes:
                # 检查当前作用域是否已定义
                if var_name in self.scopes[-1]:
                    raise SemanticError(f"变量在当前作用域重复定义: {var_name}", 
                                      node_id=var_name, line=node.line)
                self.scopes[-1][var_name] = node
        
        # 递归处理子节点
        for child in node.children:
            self._check_scopes(child, context)
        
        # 退出作用域
        if node.node_type in ["task", "tool", "if", "else"]:
            self.scopes.pop()
    
    def _validate_semantics(self, node: ASTNode, context: ParseContext) -> None:
        """语义验证"""
        # 检查条件块匹配
        if node.node_type == "if":
            self._validate_conditional_block(node, context)
        
        # 检查任务流
        if node.node_type == "task":
            self._validate_task_flow(node, context)
        
        # 递归处理子节点
        for child in node.children:
            self._validate_semantics(child, context)
    
    def _validate_conditional_block(self, node: ASTNode, context: ParseContext) -> None:
        """验证条件块"""
        # 检查是否有匹配的 endif
        # 这里需要在父节点层面检查，简化实现
        pass
    
    def _validate_task_flow(self, node: ASTNode, context: ParseContext) -> None:
        """验证任务流"""
        # 检查任务是否有循环引用
        task_id = node.get_attribute("id")
        if task_id:
            self._check_circular_references(task_id, set(), context)
    
    def _check_circular_references(self, task_id: str, visited: Set[str], context: ParseContext) -> None:
        """检查循环引用"""
        if task_id in visited:
            raise SemanticError(f"检测到循环引用: {task_id}", node_id=task_id)
        
        visited.add(task_id)
        
        # 检查任务的依赖
        if task_id in self.task_definitions:
            task_node = self.task_definitions[task_id]
            # 这里需要根据实际的依赖关系检查
            # 简化实现，暂时跳过
        
        visited.remove(task_id)
    
    def _is_valid_identifier(self, name: str) -> bool:
        """检查是否是有效的标识符"""
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
    
    def _infer_type(self, value: Any) -> str:
        """推断类型"""
        if value is None:
            return "none"
        
        # 如果已经是具体类型，直接返回
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
        
        # 处理字符串类型的值
        if isinstance(value, str):
            value = value.strip()
            
            # 布尔值
            if value.lower() in ["true", "false"]:
                return "boolean"
            
            # 数字
            try:
                if '.' in value:
                    float(value)
                    return "float"
                else:
                    int(value)
                    return "integer"
            except ValueError:
                pass
        
        # 默认字符串
        return "string"
    
    def _is_valid_condition(self, condition: str) -> bool:
        """检查条件表达式是否有效"""
        # 简单的条件表达式验证
        if not condition.strip():
            return False
        
        # 检查是否包含危险字符
        dangerous_chars = [';', '&', '|', '`', '$']
        for char in dangerous_chars:
            if char in condition:
                return False
        
        return True
    
    def _extract_references(self, content: str) -> List[str]:
        """提取文本中的引用"""
        import re
        # 查找形如 ${variable} 或 @{task_id} 的引用
        pattern = r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        matches = re.findall(pattern, content)
        return matches
    
    def _is_builtin_reference(self, ref_name: str) -> bool:
        """检查是否是内置引用"""
        builtin_refs = ["env", "config", "context", "result", "input", "output"]
        return ref_name in builtin_refs
    
    def get_symbol_table(self) -> Dict[str, Any]:
        """获取符号表"""
        return self.symbol_table.copy()
    
    def get_task_definitions(self) -> Dict[str, ASTNode]:
        """获取任务定义"""
        return self.task_definitions.copy()
    
    def get_tool_definitions(self) -> Dict[str, ASTNode]:
        """获取工具定义"""
        return self.tool_definitions.copy()
    
    def get_variable_definitions(self) -> Dict[str, ASTNode]:
        """获取变量定义"""
        return self.variable_definitions.copy()
    
    def get_references(self) -> Dict[str, List[ASTNode]]:
        """获取引用信息"""
        return self.references.copy() 