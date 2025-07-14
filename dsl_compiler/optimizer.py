"""
DSL Compiler Optimizer
Long text summarization, constant folding, dead node elimination
"""

from typing import List, Dict, Set, Any, Optional
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import CompilerError


class Optimizer:
    """Optimizer"""
    
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
        Optimize AST
        
        Args:
            ast_root: Root AST node
            context: Parse context
            
        Returns:
            ASTNode: Optimized AST
        """
        self.optimizations_applied = []
        self.removed_nodes = []
        self.statistics["nodes_before"] = self._count_nodes(ast_root)
        
        try:
            # 1. Dead code elimination
            ast_root = self._eliminate_dead_code(ast_root, context)
            
            # 2. Constant folding
            ast_root = self._fold_constants(ast_root, context)
            
            # 3. Text compression
            ast_root = self._compress_text(ast_root, context)
            
            # 4. Node merging
            ast_root = self._merge_nodes(ast_root, context)
            
            # 5. Duplicate elimination
            ast_root = self._eliminate_duplicates(ast_root, context)
            
            # 6. Structure optimization
            ast_root = self._optimize_structure(ast_root, context)
            
            self.statistics["nodes_after"] = self._count_nodes(ast_root)
            
            return ast_root
            
        except Exception as e:
            raise CompilerError(f"Error occurred during optimization: {str(e)}")
    
    def _eliminate_dead_code(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Eliminate dead code"""
        # Mark reachable nodes
        reachable = set()
        self._mark_reachable(ast_root, reachable)
        
        # Remove unreachable nodes
        optimized_root = self._remove_unreachable(ast_root, reachable)
        
        if len(self.removed_nodes) > 0:
            self.optimizations_applied.append(f"Dead code elimination: removed {len(self.removed_nodes)} nodes")
            self.statistics["dead_code_removed"] = len(self.removed_nodes)
        
        return optimized_root or ast_root
    
    def _fold_constants(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Constant folding"""
        folded_count = 0
        
        # Recursively process all nodes
        folded_count += self._fold_node_constants(ast_root, context)
        
        if folded_count > 0:
            self.optimizations_applied.append(f"Constant folding: folded {folded_count} constants")
            self.statistics["constants_folded"] = folded_count
        
        return ast_root
    
    def _compress_text(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Compress text"""
        compressed_count = 0
        
        # Process all text nodes
        text_nodes = self._find_nodes_by_type(ast_root, "text")
        
        for text_node in text_nodes:
            if self._compress_text_node(text_node):
                compressed_count += 1
        
        if compressed_count > 0:
            self.optimizations_applied.append(f"Text compression: compressed {compressed_count} text nodes")
            self.statistics["text_compressed"] = compressed_count
        
        return ast_root
    
    def _merge_nodes(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Merge nodes"""
        merged_count = 0
        
        # Merge adjacent text nodes
        merged_count += self._merge_text_nodes(ast_root)
        
        # Merge similar task nodes
        merged_count += self._merge_similar_tasks(ast_root)
        
        if merged_count > 0:
            self.optimizations_applied.append(f"Node merging: merged {merged_count} nodes")
        
        return ast_root
    
    def _eliminate_duplicates(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Eliminate duplicates"""
        # Find duplicate variable definitions
        self._remove_duplicate_variables(ast_root)
        
        # Find duplicate tool definitions
        self._remove_duplicate_tools(ast_root)
        
        return ast_root
    
    def _optimize_structure(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Optimize structure"""
        # Flatten nested structures
        self._flatten_nested_structures(ast_root)
        
        # Reorder nodes
        self._reorder_nodes(ast_root)
        
        return ast_root
    
    def _mark_reachable(self, node: ASTNode, reachable: Set[ASTNode]) -> None:
        """Mark reachable nodes"""
        if node in reachable:
            return
        
        reachable.add(node)
        
        # Special handling: references from task nodes
        if node.node_type == "task":
            # Find nodes referenced by the task
            referenced_nodes = self._find_referenced_nodes(node)
            for ref_node in referenced_nodes:
                self._mark_reachable(ref_node, reachable)
        
        # Recursively process child nodes
        for child in node.children:
            self._mark_reachable(child, reachable)
    
    def _remove_unreachable(self, node: ASTNode, reachable: Set[ASTNode]) -> Optional[ASTNode]:
        """Remove unreachable nodes"""
        if node not in reachable:
            self.removed_nodes.append(node)
            return None
        
        # Recursively process child nodes
        new_children = []
        for child in node.children:
            optimized_child = self._remove_unreachable(child, reachable)
            if optimized_child is not None:
                new_children.append(optimized_child)
        
        node.children = new_children
        return node
    
    def _fold_node_constants(self, node: ASTNode, context: ParseContext) -> int:
        """Fold constants in node"""
        folded_count = 0
        
        # Process variable nodes
        if node.node_type == "var":
            var_value = node.get_attribute("value")
            if var_value and isinstance(var_value, str):
                # Try to evaluate constant expressions
                folded_value = self._evaluate_constant_expression(var_value)
                if folded_value != var_value:
                    node.set_attribute("value", folded_value)
                    folded_count += 1
        
        # Process constant references in text nodes
        elif node.node_type == "text":
            content = node.get_attribute("content", "")
            if content:
                folded_content = self._fold_text_constants(content, context)
                if folded_content != content:
                    node.set_attribute("content", folded_content)
                    folded_count += 1
        
        # Recursively process child nodes
        for child in node.children:
            folded_count += self._fold_node_constants(child, context)
        
        return folded_count
    
    def _compress_text_node(self, text_node: ASTNode) -> bool:
        """Compress text node"""
        content = text_node.get_attribute("content", "")
        
        if not content or len(content) < 100:  # Only compress longer text
            return False
        
        # Remove excess whitespace
        import re
        compressed = re.sub(r'\s+', ' ', content.strip())
        
        # Remove repeated punctuation
        compressed = re.sub(r'[。！？]{2,}', '。', compressed)
        compressed = re.sub(r'[.,!?]{2,}', '.', compressed)
        
        # Simplify repeated words
        compressed = re.sub(r'\b(\w+)\s+\1\b', r'\1', compressed)
        
        if len(compressed) < len(content):
            text_node.set_attribute("content", compressed)
            text_node.set_attribute("_original_length", len(content))
            text_node.set_attribute("_compressed_length", len(compressed))
            return True
        
        return False
    
    def _merge_text_nodes(self, node: ASTNode) -> int:
        """Merge adjacent text nodes"""
        merged_count = 0
        
        if not node.children:
            return merged_count
        
        new_children = []
        i = 0
        
        while i < len(node.children):
            current = node.children[i]
            
            # If current node is text node, look for adjacent text nodes
            if current.node_type == "text":
                text_content = [current.get_attribute("content", "")]
                j = i + 1
                
                # Find consecutive text nodes
                while j < len(node.children) and node.children[j].node_type == "text":
                    text_content.append(node.children[j].get_attribute("content", ""))
                    j += 1
                
                # If multiple consecutive text nodes found, merge them
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
        
        # Recursively process child nodes
        for child in node.children:
            merged_count += self._merge_text_nodes(child)
        
        return merged_count
    
    def _merge_similar_tasks(self, ast_root: ASTNode) -> int:
        """Merge similar tasks"""
        merged_count = 0
        
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        
        # Group by similarity
        groups = self._group_similar_tasks(task_nodes)
        
        for group in groups:
            if len(group) > 1:
                # Merge tasks in group
                merged_task = self._merge_task_group(group)
                if merged_task:
                    merged_count += len(group) - 1
        
        return merged_count
    
    def _remove_duplicate_variables(self, ast_root: ASTNode) -> None:
        """Remove duplicate variable definitions"""
        var_nodes = self._find_nodes_by_type(ast_root, "var")
        seen_vars = {}
        
        for var_node in var_nodes:
            var_name = var_node.get_attribute("name")
            var_value = var_node.get_attribute("value")
            
            if var_name:
                key = (var_name, str(var_value))
                if key in seen_vars:
                    # Remove duplicate variable
                    self._remove_node(var_node)
                else:
                    seen_vars[key] = var_node
    
    def _remove_duplicate_tools(self, ast_root: ASTNode) -> None:
        """Remove duplicate tool definitions"""
        tool_nodes = self._find_nodes_by_type(ast_root, "tool")
        seen_tools = {}
        
        for tool_node in tool_nodes:
            tool_name = tool_node.get_attribute("name")
            tool_desc = tool_node.get_attribute("description")
            
            if tool_name:
                key = (tool_name, tool_desc)
                if key in seen_tools:
                    # Remove duplicate tool
                    self._remove_node(tool_node)
                else:
                    seen_tools[key] = tool_node
    
    def _flatten_nested_structures(self, node: ASTNode) -> None:
        """Flatten nested structures"""
        # Flatten single-child nesting
        if len(node.children) == 1 and node.children[0].node_type == node.node_type:
            child = node.children[0]
            node.children = child.children
            node.attributes.update(child.attributes)
        
        # Recursively process child nodes
        for child in node.children:
            self._flatten_nested_structures(child)
    
    def _reorder_nodes(self, node: ASTNode) -> None:
        """Reorder nodes"""
        # Sort by type: variables -> tools -> tasks
        type_order = {"var": 0, "tool": 1, "task": 2, "text": 3}
        
        node.children.sort(key=lambda child: type_order.get(child.node_type, 99))
        
        # Recursively process child nodes
        for child in node.children:
            self._reorder_nodes(child)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """Find nodes of specified type"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _find_referenced_nodes(self, task_node: ASTNode) -> List[ASTNode]:
        """Find nodes referenced by task"""
        referenced = []
        
        # Extract references from task content
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # Find reference patterns
                import re
                refs = re.findall(r'[@$]\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
                # This needs to be resolved based on actual symbol table
                # Temporarily simplified
        
        return referenced
    
    def _evaluate_constant_expression(self, expression: str) -> str:
        """Evaluate constant expression"""
        # Simple constant expression evaluation
        try:
            # Only allow simple math operations
            import re
            if re.match(r'^[\d\+\-\*\/\.\(\)\s]+$', expression):
                result = eval(expression)
                return str(result)
        except:
            pass
        
        return expression
    
    def _fold_text_constants(self, content: str, context: ParseContext) -> str:
        """Fold constants in text"""
        # Find and replace constant references
        import re
        
        def replace_constant(match):
            var_name = match.group(1)
            # Look up variable value from context
            if hasattr(context, 'variables') and var_name in context.variables:
                return str(context.variables[var_name])
            return match.group(0)
        
        # Replace ${variable} form constant references
        folded = re.sub(r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}', replace_constant, content)
        
        return folded
    
    def _group_similar_tasks(self, task_nodes: List[ASTNode]) -> List[List[ASTNode]]:
        """Group similar tasks"""
        groups = []
        
        for task_node in task_nodes:
            task_content = self._get_task_content(task_node)
            
            # Find similar group
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
        """Determine if two tasks are similar"""
        content1 = self._get_task_content(task1)
        content2 = self._get_task_content(task2)
        
        # Simple similarity judgment
        if not content1 or not content2:
            return False
        
        # Calculate text similarity
        similarity = self._calculate_text_similarity(content1, content2)
        return similarity > 0.8
    
    def _get_task_content(self, task_node: ASTNode) -> str:
        """Get task content"""
        content_parts = []
        
        for child in task_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                if content:
                    content_parts.append(content)
        
        return " ".join(content_parts)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity"""
        # Simple vocabulary-based similarity calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _merge_task_group(self, task_group: List[ASTNode]) -> Optional[ASTNode]:
        """Merge task group"""
        if not task_group:
            return None
        
        # Use first task as base
        base_task = task_group[0]
        
        # Merge content from other tasks
        for task in task_group[1:]:
            for child in task.children:
                if child.node_type == "text":
                    base_task.add_child(child)
            
            # Remove merged task
            self._remove_node(task)
        
        return base_task
    
    def _remove_node(self, node: ASTNode) -> None:
        """Remove node"""
        if node.parent:
            node.parent.children.remove(node)
        self.removed_nodes.append(node)
    
    def _count_nodes(self, node: ASTNode) -> int:
        """Count number of nodes"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization report"""
        return {
            "optimizations_applied": self.optimizations_applied,
            "statistics": self.statistics,
            "removed_nodes_count": len(self.removed_nodes),
            "compression_ratio": self.statistics["nodes_before"] / max(self.statistics["nodes_after"], 1)
        } 