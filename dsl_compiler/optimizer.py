"""
DSL 编译器优化器
长文本摘要、常量折叠、无用节点剔除
"""

from typing import List, Dict, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import CompilerError


class Optimizer:
    """优化器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.optimizations_applied: List[str] = []
        self.removed_nodes: List[ASTNode] = []
        self.statistics = {
            "nodes_before": 0,
            "nodes_after": 0,
            "text_compressed": 0,
            "constants_folded": 0,
            "dead_code_removed": 0
        }
    
    def optimize(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """
        优化 AST
        
        Args:
            ast_root: 根 AST 节点
            context: 解析上下文
            
        Returns:
            ASTNode: 优化后的 AST
        """
        self.optimizations_applied = []
        self.removed_nodes = []
        self.statistics["nodes_before"] = self._count_nodes(ast_root)
        
        try:
            # 1. 死代码消除
            ast_root = self._eliminate_dead_code(ast_root, context)
            
            # 2. 常量折叠
            ast_root = self._fold_constants(ast_root, context)
            
            # 3. 文本压缩
            ast_root = self._compress_text(ast_root, context)
            
            # 4. 节点合并
            ast_root = self._merge_nodes(ast_root, context)
            
            # 5. 重复消除
            ast_root = self._eliminate_duplicates(ast_root, context)
            
            # 6. 结构优化
            ast_root = self._optimize_structure(ast_root, context)
            
            self.statistics["nodes_after"] = self._count_nodes(ast_root)
            
            return ast_root
            
        except Exception as e:
            raise CompilerError(f"优化过程发生错误: {str(e)}")
    
    def _eliminate_dead_code(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """消除死代码"""
        # 标记可达节点
        reachable = set()
        self._mark_reachable(ast_root, reachable)
        
        # 移除不可达节点
        optimized_root = self._remove_unreachable(ast_root, reachable)
        
        if len(self.removed_nodes) > 0:
            self.optimizations_applied.append(f"死代码消除: 移除 {len(self.removed_nodes)} 个节点")
            self.statistics["dead_code_removed"] = len(self.removed_nodes)
        
        return optimized_root or ast_root
    
    def _fold_constants(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """常量折叠"""
        folded_count = 0
        
        # 递归处理所有节点
        folded_count += self._fold_node_constants(ast_root, context)
        
        if folded_count > 0:
            self.optimizations_applied.append(f"常量折叠: 折叠 {folded_count} 个常量")
            self.statistics["constants_folded"] = folded_count
        
        return ast_root
    
    def _compress_text(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """压缩文本"""
        compressed_count = 0
        
        # 处理所有文本节点
        text_nodes = self._find_nodes_by_type(ast_root, "text")
        
        for text_node in text_nodes:
            if self._compress_text_node(text_node):
                compressed_count += 1
        
        if compressed_count > 0:
            self.optimizations_applied.append(f"文本压缩: 压缩 {compressed_count} 个文本节点")
            self.statistics["text_compressed"] = compressed_count
        
        return ast_root
    
    def _merge_nodes(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """合并节点"""
        merged_count = 0
        
        # 合并相邻的文本节点
        merged_count += self._merge_text_nodes(ast_root)
        
        # 合并相似的任务节点
        merged_count += self._merge_similar_tasks(ast_root)
        
        if merged_count > 0:
            self.optimizations_applied.append(f"节点合并: 合并 {merged_count} 个节点")
        
        return ast_root
    
    def _eliminate_duplicates(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """消除重复"""
        # 查找重复的变量定义
        self._remove_duplicate_variables(ast_root)
        
        # 查找重复的工具定义
        self._remove_duplicate_tools(ast_root)
        
        return ast_root
    
    def _optimize_structure(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """优化结构"""
        # 扁平化嵌套结构
        self._flatten_nested_structures(ast_root)
        
        # 重新排序节点
        self._reorder_nodes(ast_root)
        
        return ast_root
    
    def _mark_reachable(self, node: ASTNode, reachable: Set[ASTNode]) -> None:
        """标记可达节点"""
        if node in reachable:
            return
        
        reachable.add(node)
        
        # 特殊处理：任务节点的引用
        if node.node_type == "task":
            # 查找任务引用的其他节点
            referenced_nodes = self._find_referenced_nodes(node)
            for ref_node in referenced_nodes:
                self._mark_reachable(ref_node, reachable)
        
        # 递归处理子节点
        for child in node.children:
            self._mark_reachable(child, reachable)
    
    def _remove_unreachable(self, node: ASTNode, reachable: Set[ASTNode]) -> Optional[ASTNode]:
        """移除不可达节点"""
        if node not in reachable:
            self.removed_nodes.append(node)
            return None
        
        # 递归处理子节点
        new_children = []
        for child in node.children:
            optimized_child = self._remove_unreachable(child, reachable)
            if optimized_child is not None:
                new_children.append(optimized_child)
        
        node.children = new_children
        return node
    
    def _fold_node_constants(self, node: ASTNode, context: ParseContext) -> int:
        """折叠节点中的常量"""
        folded_count = 0
        
        # 处理变量节点
        if node.node_type == "var":
            var_value = node.get_attribute("value")
            if var_value and isinstance(var_value, str):
                # 尝试计算常量表达式
                folded_value = self._evaluate_constant_expression(var_value)
                if folded_value != var_value:
                    node.set_attribute("value", folded_value)
                    folded_count += 1
        
        # 处理文本节点中的常量引用
        elif node.node_type == "text":
            content = node.get_attribute("content", "")
            if content:
                folded_content = self._fold_text_constants(content, context)
                if folded_content != content:
                    node.set_attribute("content", folded_content)
                    folded_count += 1
        
        # 递归处理子节点
        for child in node.children:
            folded_count += self._fold_node_constants(child, context)
        
        return folded_count
    
    def _compress_text_node(self, text_node: ASTNode) -> bool:
        """压缩文本节点"""
        content = text_node.get_attribute("content", "")
        
        if not content or len(content) < 100:  # 只压缩较长的文本
            return False
        
        # 移除多余的空白
        import re
        compressed = re.sub(r'\s+', ' ', content.strip())
        
        # 移除重复的标点
        compressed = re.sub(r'[。！？]{2,}', '。', compressed)
        compressed = re.sub(r'[.,!?]{2,}', '.', compressed)
        
        # 简化重复的词语
        compressed = re.sub(r'\b(\w+)\s+\1\b', r'\1', compressed)
        
        if len(compressed) < len(content):
            text_node.set_attribute("content", compressed)
            text_node.set_attribute("_original_length", len(content))
            text_node.set_attribute("_compressed_length", len(compressed))
            return True
        
        return False
    
    def _merge_text_nodes(self, node: ASTNode) -> int:
        """合并相邻的文本节点"""
        merged_count = 0
        
        if not node.children:
            return merged_count
        
        new_children = []
        i = 0
        
        while i < len(node.children):
            current = node.children[i]
            
            # 如果当前节点是文本节点，查找相邻的文本节点
            if current.node_type == "text":
                text_content = [current.get_attribute("content", "")]
                j = i + 1
                
                # 查找连续的文本节点
                while j < len(node.children) and node.children[j].node_type == "text":
                    text_content.append(node.children[j].get_attribute("content", ""))
                    j += 1
                
                # 如果找到多个连续的文本节点，合并它们
                if j > i + 1:
                    merged_content = " ".join(text_content)
                    current.set_attribute("content", merged_content)
                    merged_count += j - i - 1
                    i = j
                else:
                    i += 1
                
                new_children.append(current)
            else:
                new_children.append(current)
                i += 1
        
        node.children = new_children
        
        # 递归处理子节点
        for child in node.children:
            merged_count += self._merge_text_nodes(child)
        
        return merged_count
    
    def _merge_similar_tasks(self, ast_root: ASTNode) -> int:
        """合并相似的任务"""
        merged_count = 0
        
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # 按相似性分组
        groups = self._group_similar_tasks(task_nodes)
        
        for group in groups:
            if len(group) > 1:
                # 合并组内的任务
                merged_task = self._merge_task_group(group)
                if merged_task:
                    merged_count += len(group) - 1
        
        return merged_count
    
    def _remove_duplicate_variables(self, ast_root: ASTNode) -> None:
        """移除重复的变量定义"""
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        seen_vars = {}
        
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            var_value = var_node.get_attribute("value")
            
            if var_name:
                key = (var_name, str(var_value))
                if key in seen_vars:
                    # 移除重复的变量
                    self._remove_node(var_node)
                else:
                    seen_vars[key] = var_node
    
    def _remove_duplicate_tools(self, ast_root: ASTNode) -> None:
        """移除重复的工具定义"""
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        seen_tools = {}
        
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            tool_desc = tool_node.get_attribute("description")
            
            if tool_name:
                key = (tool_name, tool_desc)
                if key in seen_tools:
                    # 移除重复的工具
                    self._remove_node(tool_node)
                else:
                    seen_tools[key] = tool_node
    
    def _flatten_nested_structures(self, node: ASTNode) -> None:
        """扁平化嵌套结构"""
        # 扁平化单子节点的嵌套
        if len(node.children) == 1 and node.children[0].node_type == node.node_type:
            child = node.children[0]
            node.children = child.children
            node.attributes.update(child.attributes)
        
        # 递归处理子节点
        for child in node.children:
            self._flatten_nested_structures(child)
    
    def _reorder_nodes(self, node: ASTNode) -> None:
        """重新排序节点"""
        # 按类型排序：变量 -> 工具 -> 任务
        type_order = {"var": 0, "tool": 1, "task": 2, "text": 3}
        
        node.children.sort(key=lambda child: type_order.get(child.node_type, 99))
        
        # 递归处理子节点
        for child in node.children:
            self._reorder_nodes(child)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """查找指定类型的节点"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _find_referenced_nodes(self, task_node: ASTNode) -> List[ASTNode]:
        """查找任务引用的其他节点"""
        referenced = []
        
        # 从任务内容中提取引用
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # 查找引用模式
                import re
                refs = re.findall(r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
                # 这里需要根据实际的符号表来解析引用
                # 暂时简化处理
        
        return referenced
    
    def _evaluate_constant_expression(self, expression: str) -> str:
        """计算常量表达式"""
        # 简单的常量表达式计算
        try:
            # 只允许简单的数学运算
            import re
            if re.match(r'^[\d\+\-\*\/\.\(\)\s]+$', expression):
                result = eval(expression)
                return str(result)
        except:
            pass
        
        return expression
    
    def _fold_text_constants(self, content: str, context: ParseContext) -> str:
        """折叠文本中的常量"""
        # 查找并替换常量引用
        import re
        
        def replace_constant(match):
            var_name = match.group(1)
            # 从上下文中查找变量值
            if hasattr(context, 'variables') and var_name in context.variables:
                return str(context.variables[var_name])
            return match.group(0)
        
        # 替换 ${variable} 形式的常量引用
        folded = re.sub(r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}', replace_constant, content)
        
        return folded
    
    def _group_similar_tasks(self, task_nodes: List[ASTNode]) -> List[List[ASTNode]]:
        """将相似的任务分组"""
        groups = []
        
        for task_node in task_nodes:
            task_content = self._get_task_content(task_node)
            
            # 查找相似的组
            found_group = None
            for group in groups:
                if self._is_similar_task(task_node, group[0]):
                    found_group = group
                    break
            
            if found_group:
                found_group.append(task_node)
            else:
                groups.append([task_node])
        
        return groups
    
    def _is_similar_task(self, task1: ASTNode, task2: ASTNode) -> bool:
        """判断两个任务是否相似"""
        content1 = self._get_task_content(task1)
        content2 = self._get_task_content(task2)
        
        # 简单的相似性判断
        if not content1 or not content2:
            return False
        
        # 计算文本相似度
        similarity = self._calculate_text_similarity(content1, content2)
        return similarity > 0.8
    
    def _get_task_content(self, task_node: ASTNode) -> str:
        """获取任务内容"""
        content_parts = []
        
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                if content:
                    content_parts.append(content)
        
        return " ".join(content_parts)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的基于词汇的相似度计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _merge_task_group(self, task_group: List[ASTNode]) -> Optional[ASTNode]:
        """合并任务组"""
        if not task_group:
            return None
        
        # 使用第一个任务作为基础
        base_task = task_group[0]
        
        # 合并其他任务的内容
        for task in task_group[1:]:
            for child in task.children:
                if child.node_type == "text":
                    base_task.add_child(child)
            
            # 移除被合并的任务
            self._remove_node(task)
        
        return base_task
    
    def _remove_node(self, node: ASTNode) -> None:
        """移除节点"""
        if node.parent:
            node.parent.children.remove(node)
        self.removed_nodes.append(node)
    
    def _count_nodes(self, node: ASTNode) -> int:
        """计算节点数量"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        return {
            "optimizations_applied": self.optimizations_applied,
            "statistics": self.statistics,
            "removed_nodes_count": len(self.removed_nodes),
            "compression_ratio": self.statistics["nodes_before"] / max(self.statistics["nodes_after"], 1)
        } 