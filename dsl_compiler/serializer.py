"""
DSL 编译器序列化器
输出 YAML/JSON/Proto，可插拔 Formatter
"""

import json
from typing import Dict, List, Any, Optional, cast, Literal, Union
from datetime import datetime

from .config import CompilerConfig
from .models import ParseContext, DSLOutput, TaskNode, ToolNode, VariableNode, Block, ConditionalNext
from .parser import ASTNode
from .exceptions import CompilerError


class Serializer:
    """序列化器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.formatters = {
            "yaml": self._format_yaml,
            "json": self._format_json,
            "proto": self._format_proto
        }
    
    def serialize(self, ast_root: ASTNode, context: ParseContext) -> DSLOutput:
        """
        序列化 AST 为 DSL 输出
        
        Args:
            ast_root: 根 AST 节点
            context: 解析上下文
            
        Returns:
            DSLOutput: DSL 输出对象
            
        Raises:
            CompilerError: 序列化错误
        """
        try:
            # 1. 转换 AST 为 DSL 节点
            dsl_nodes = self._convert_ast_to_dsl(ast_root, context)
            
            # 2. 分离不同类型的节点
            tasks = []
            tools = []
            variables = []
            
            for node in dsl_nodes:
                if isinstance(node, TaskNode):
                    tasks.append(node)
                elif isinstance(node, ToolNode):
                    tools.append(node)
                elif isinstance(node, VariableNode):
                    variables.append(node)
            
            # 3. 提取元数据
            metadata = self._extract_metadata(ast_root, context)
            
            # 4. 确定入口点
            entry_point = self._determine_entry_point(tasks)
            
            # 5. 创建 DSL 输出
            dsl_output = DSLOutput(
                version="1.0",
                metadata=metadata,
                variables=variables,
                tools=tools,
                tasks=tasks,
                entry_point=entry_point,
                compiled_at=datetime.now(),
                compiler_version="1.0.0",
                source_files=[context.source_file] if context.source_file else []
            )
            
            return dsl_output
            
        except Exception as e:
            raise CompilerError(f"序列化失败: {str(e)}")
    
    def _convert_ast_to_dsl(self, ast_root: ASTNode, context: ParseContext) -> List[Any]:
        """将 AST 转换为 DSL 节点"""
        dsl_nodes = []
        
        # 递归转换所有节点
        for child in ast_root.children:
            converted_nodes = self._convert_ast_node(child, context)
            dsl_nodes.extend(converted_nodes)
        
        return dsl_nodes
    
    def _convert_ast_node(self, node: ASTNode, context: ParseContext) -> List[Any]:
        """转换单个 AST 节点"""
        if node.node_type == "task":
            return [self._convert_task_node(node, context)]
        elif node.node_type == "tool":
            return [self._convert_tool_node(node, context)]
        elif node.node_type == "var":
            return [self._convert_variable_node(node, context)]
        else:
            # 对于其他类型的节点，递归处理子节点
            converted = []
            for child in node.children:
                converted.extend(self._convert_ast_node(child, context))
            return converted
    
    def _convert_task_node(self, node: ASTNode, context: ParseContext) -> TaskNode:
        """将 AST 任务节点转换为 TaskNode"""
        task_id = node.get_attribute("id", "")
        title = node.get_attribute("title", "")
        
        body = []
        next_tasks = []
        i = 0
        while i < len(node.children):
            child = node.children[i]
            
            # 检查是否是条件语句的开始
            if child.node_type == "if":
                conditional_block, processed_count = self._convert_conditional_statement(node.children, i)
                if conditional_block:
                    body.append(conditional_block)
                    # 跳过已处理的节点
                    i += processed_count
                    continue
            
            # 处理其他类型的节点
            if child.node_type == "text":
                content = child.get_attribute("content", "").strip()
                if content:
                    block = Block(
                        type="text",
                        content=content,
                        line_number=child.line
                    )
                    body.append(block)
            
            elif child.node_type == "tool":
                # 创建结构化的工具调用块
                from src.dsl_compiler.models import ToolCall
                tool_name = child.get_attribute("name", "")
                tool_desc = child.get_attribute("description", "")
                
                tool_call = ToolCall(
                    name=tool_name,
                    description=tool_desc
                )
                
                block = Block(
                    type="tool_call",
                    tool_call=tool_call,
                    line_number=child.line
                )
                body.append(block)
            
            elif child.node_type == "agent":
                # 创建结构化的Agent调用块
                from src.dsl_compiler.models import AgentCall
                agent_name = child.get_attribute("name", "")
                agent_params = child.get_attribute("parameters", "")
                
                agent_call = AgentCall(
                    name=agent_name,
                    parameters=agent_params
                )
                
                block = Block(
                    type="agent_call",
                    agent_call=agent_call,
                    line_number=child.line
                )
                body.append(block)
            
            elif child.node_type == "next":
                # 创建结构化的跳转块
                from src.dsl_compiler.models import JumpAction
                target = child.get_attribute("target", "")
                
                jump_action = JumpAction(target=target)
                
                block = Block(
                    type="next_action",
                    next_action=jump_action,
                    line_number=child.line
                )
                body.append(block)
                
                # 同时记录到任务级别的next字段
                next_tasks.append(target)
            
            elif child.node_type in ["lang", "var"]:
                # 其他指令类型保持directive格式
                directive_content = self._convert_directive_to_content(child)
                if directive_content:
                    block = Block(
                        type="directive",
                        content=directive_content,
                        line_number=child.line
                    )
                    body.append(block)
            
            i += 1
        
        return TaskNode(
            id=task_id,
            title=title,
            body=body,
            next=next_tasks
        )
    
    def _convert_conditional_statement(self, children: List[ASTNode], start_index: int) -> tuple[Optional[Block], int]:
        """将if/else/endif序列转换为结构化的条件语句，返回(Block, 处理的节点数量)"""
        if start_index >= len(children) or children[start_index].node_type != "if":
            return None, 0
        
        from src.dsl_compiler.models import ConditionalStatement, ConditionalBranch
        
        branches = []
        current_index = start_index
        if_node = children[current_index]
        
        # 处理if分支
        if_condition = if_node.get_attribute("condition", "")
        if_actions = self._extract_conditional_actions(if_node)
        if_branch = ConditionalBranch(condition=if_condition, actions=if_actions)
        branches.append(if_branch)
        
        current_index += 1
        processed_count = 1  # 已处理if节点
        
        # 查找else分支
        while current_index < len(children):
            if children[current_index].node_type == "else":
                else_node = children[current_index]
                else_actions = self._extract_conditional_actions(else_node)
                else_branch = ConditionalBranch(condition=None, actions=else_actions)  # else分支条件为None
                branches.append(else_branch)
                processed_count += 1
                current_index += 1
            elif children[current_index].node_type == "endif":
                processed_count += 1  # 包含endif节点
                break
            else:
                # 遇到非else/endif节点，条件语句结束
                break
        
        conditional_statement = ConditionalStatement(branches=branches, line_number=if_node.line)
        
        conditional_block = Block(
            type="conditional",
            conditional=conditional_statement,
            line_number=if_node.line
        )
        
        return conditional_block, processed_count
    
    def _extract_conditional_actions(self, conditional_node: ASTNode) -> List:
        """从条件节点中提取动作列表"""
        from src.dsl_compiler.models import ConditionalAction, ToolCall, AgentCall, JumpAction
        
        actions = []
        
        for child in conditional_node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "").strip()
                if content:
                    action = ConditionalAction(
                        type="text",
                        content=content
                    )
                    actions.append(action)
            
            elif child.node_type == "tool":
                tool_name = child.get_attribute("name", "")
                tool_desc = child.get_attribute("description", "")
                tool_call = ToolCall(name=tool_name, description=tool_desc)
                action = ConditionalAction(
                    type="tool_call",
                    tool_call=tool_call
                )
                actions.append(action)
            
            elif child.node_type == "agent":
                agent_name = child.get_attribute("name", "")
                agent_params = child.get_attribute("parameters", "")
                agent_call = AgentCall(name=agent_name, parameters=agent_params)
                action = ConditionalAction(
                    type="agent_call",
                    agent_call=agent_call
                )
                actions.append(action)
            
            elif child.node_type == "next":
                target = child.get_attribute("target", "")
                jump = JumpAction(target=target)
                action = ConditionalAction(
                    type="jump",
                    jump=jump
                )
                actions.append(action)
        
        return actions
    
    def _find_endif_index(self, children: List[ASTNode], start_index: int) -> int:
        """查找对应的endif节点索引"""
        if_count = 1  # 当前if的计数
        index = start_index + 1
        
        while index < len(children) and if_count > 0:
            if children[index].node_type == "if":
                if_count += 1
            elif children[index].node_type == "endif":
                if_count -= 1
            index += 1
        
        return index - 1  # 返回endif的索引
    
    def _convert_directive_to_content(self, directive_node: ASTNode) -> Optional[str]:
        """将指令节点转换为内容字符串"""
        directive_type = directive_node.node_type
        
        # 根据指令类型生成内容
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
            
            # 处理if块内的嵌套内容
            nested_content = []
            for child in directive_node.children:
                if child.node_type == "text":
                    nested_content.append(f"    {child.get_attribute('content', '').strip()}")
                elif child.node_type in ["tool", "agent", "lang", "next"]:
                    nested_directive = self._convert_directive_to_content(child)
                    if nested_directive:
                        nested_content.append(f"    {nested_directive}")
            
            if nested_content:
                content += "\n" + "\n".join(nested_content)
            
        elif directive_type == "else":
            content = "@else"
            
            # 处理else块内的嵌套内容
            nested_content = []
            for child in directive_node.children:
                if child.node_type == "text":
                    nested_content.append(f"    {child.get_attribute('content', '').strip()}")
                elif child.node_type in ["tool", "agent", "lang", "next"]:
                    nested_directive = self._convert_directive_to_content(child)
                    if nested_directive:
                        nested_content.append(f"    {nested_directive}")
            
            if nested_content:
                content += "\n" + "\n".join(nested_content)
            
        elif directive_type == "endif":
            content = "@endif"
            
        else:
            return None
        
        return content
    
    def _convert_tool_node(self, node: ASTNode, context: ParseContext) -> ToolNode:
        """转换工具节点"""
        tool_id = node.get_attribute("id", f"tool_{node.line}")
        tool_name = node.get_attribute("name", tool_id)
        description = node.get_attribute("description")
        parameters = node.get_attribute("parameters", {})
        
        return ToolNode(
            id=tool_id,
            name=tool_name,
            description=description,
            parameters=parameters
        )
    
    def _convert_variable_node(self, node: ASTNode, context: ParseContext) -> VariableNode:
        """转换变量节点"""
        var_name = node.get_attribute("name")
        var_value = node.get_attribute("value")
        var_type = node.get_attribute("inferred_type", "string")
        
        # 处理变量值
        if var_value is not None:
            var_value = self._process_variable_value(var_value, var_type)
        
        return VariableNode(
            name=var_name,
            value=var_value,
            type=var_type,
            scope="global"
        )
    
    def _detect_block_type(self, content: str) -> str:
        """检测块类型"""
        content_stripped = content.strip()
        
        # 检查是否是代码块
        if content_stripped.startswith("```") and content_stripped.endswith("```"):
            return "code"
        
        # 检查是否是指令
        if content_stripped.startswith("@"):
            return "directive"
        
        # 默认为文本
        return "text"
    
    def _detect_language(self, content: str) -> Optional[str]:
        """检测代码语言"""
        import re
        
        # 从代码块标记中提取语言
        match = re.match(r'```(\w+)', content.strip())
        if match:
            return match.group(1)
        
        # 简单的语言检测
        if "def " in content or "import " in content:
            return "python"
        elif "function " in content or "const " in content:
            return "javascript"
        elif "#!/bin/bash" in content or "sudo " in content:
            return "bash"
        
        return None
    
    def _extract_next_tasks(self, node: ASTNode) -> List[str]:
        """提取下一步任务"""
        next_tasks = []
        
        # 从任务内容中提取引用
        for child in node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # 查找任务引用
                import re
                refs = re.findall(r'@\{([a-zA-Z_][a-zA-Z0-9_]*)\}', content)
                next_tasks.extend(refs)
        
        return list(set(next_tasks))  # 去重
    
    def _extract_dependencies(self, node: ASTNode) -> List[str]:
        """提取依赖"""
        dependencies = []
        
        # 从任务内容中提取依赖引用
        for child in node.children:
            if child.node_type == "text":
                content = child.get_attribute("content", "")
                # 查找依赖引用
                import re
                deps = re.findall(r'depends_on:\s*([a-zA-Z_][a-zA-Z0-9_]*)', content)
                dependencies.extend(deps)
        
        return dependencies
    
    def _extract_task_metadata(self, node: ASTNode) -> Dict[str, Any]:
        """提取任务元数据"""
        metadata = {}
        
        # 从属性中提取元数据
        for key, value in node.attributes.items():
            if key.startswith("_"):
                continue
            if key not in ["id", "title", "timeout", "retry_count"]:
                metadata[key] = value
        
        return metadata
    
    def _process_variable_value(self, value: Any, var_type: str) -> Any:
        """处理变量值"""
        if var_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ["true", "yes", "1"]
            return bool(value)
        elif var_type == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        elif var_type == "float":
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        elif var_type == "string":
            return str(value) if value is not None else ""
        else:
            return value
    
    def _extract_metadata(self, ast_root: ASTNode, context: ParseContext) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        # 从根节点属性中提取
        for key, value in ast_root.attributes.items():
            if not key.startswith("_"):
                metadata[key] = value
        
        # 从上下文中提取
        if hasattr(context, 'directive_index'):
            metadata["directive_count"] = sum(len(directives) for directives in context.directive_index.values())
            metadata["directive_types"] = list(context.directive_index.keys())
        
        # 添加源文件信息
        if context.source_file:
            metadata["source_file"] = context.source_file
        
        # 添加编译时间
        metadata["compiled_at"] = datetime.now().isoformat()
        
        return metadata
    
    def _determine_entry_point(self, tasks: List[TaskNode]) -> Optional[str]:
        """确定入口点"""
        if not tasks:
            return None
        
        # 查找没有被其他任务引用的任务
        referenced_tasks = set()
        for task in tasks:
            for next_task in task.next:
                if isinstance(next_task, str):
                    referenced_tasks.add(next_task)
        
        # 找到没有被引用的任务
        entry_candidates = [task for task in tasks if task.id not in referenced_tasks]
        
        if entry_candidates:
            return entry_candidates[0].id
        
        # 如果所有任务都被引用，返回第一个任务
        return tasks[0].id
    
    def _format_yaml(self, dsl_output: DSLOutput) -> str:
        """格式化为 YAML"""
        return dsl_output.to_yaml()
    
    def _format_json(self, dsl_output: DSLOutput) -> str:
        """格式化为 JSON"""
        return dsl_output.to_json(compact=self.config.compact_mode)
    
    def _format_proto(self, dsl_output: DSLOutput) -> str:
        """格式化为 Protobuf"""
        # 简化的 Proto 格式输出
        proto_lines = []
        proto_lines.append('syntax = "proto3";')
        proto_lines.append('package dsl;')
        proto_lines.append('')
        
        # 定义消息类型
        proto_lines.append('message DSLWorkflow {')
        proto_lines.append('  string version = 1;')
        proto_lines.append('  map<string, string> metadata = 2;')
        proto_lines.append('  repeated Variable variables = 3;')
        proto_lines.append('  repeated Tool tools = 4;')
        proto_lines.append('  repeated Task tasks = 5;')
        proto_lines.append('  string entry_point = 6;')
        proto_lines.append('}')
        proto_lines.append('')
        
        # 定义任务消息
        proto_lines.append('message Task {')
        proto_lines.append('  string id = 1;')
        proto_lines.append('  string title = 2;')
        proto_lines.append('  repeated Block body = 3;')
        proto_lines.append('  repeated string next = 4;')
        proto_lines.append('  repeated string dependencies = 5;')
        proto_lines.append('  map<string, string> metadata = 6;')
        proto_lines.append('}')
        proto_lines.append('')
        
        # 定义块消息
        proto_lines.append('message Block {')
        proto_lines.append('  string type = 1;')
        proto_lines.append('  string content = 2;')
        proto_lines.append('  string language = 3;')
        proto_lines.append('  int32 line_number = 4;')
        proto_lines.append('}')
        proto_lines.append('')
        
        # 定义工具消息
        proto_lines.append('message Tool {')
        proto_lines.append('  string id = 1;')
        proto_lines.append('  string name = 2;')
        proto_lines.append('  string description = 3;')
        proto_lines.append('  map<string, string> parameters = 4;')
        proto_lines.append('}')
        proto_lines.append('')
        
        # 定义变量消息
        proto_lines.append('message Variable {')
        proto_lines.append('  string name = 1;')
        proto_lines.append('  string value = 2;')
        proto_lines.append('  string type = 3;')
        proto_lines.append('  string scope = 4;')
        proto_lines.append('}')
        
        return '\n'.join(proto_lines)
    
    def format_output(self, dsl_output: DSLOutput, format_type: Optional[str] = None) -> str:
        """格式化输出"""
        format_type = format_type or self.config.output_format
        
        if format_type in self.formatters:
            return self.formatters[format_type](dsl_output)
        else:
            raise CompilerError(f"不支持的输出格式: {format_type}")
    
    def register_formatter(self, format_name: str, formatter_func) -> None:
        """注册自定义格式化器"""
        self.formatters[format_name] = formatter_func
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表"""
        return list(self.formatters.keys())
    
    def validate_output(self, dsl_output: DSLOutput) -> List[str]:
        """验证输出"""
        errors = []
        
        # 验证 DAG 结构
        dag_errors = dsl_output.validate_dag()
        errors.extend(dag_errors)
        
        # 验证任务完整性
        for task in dsl_output.tasks:
            if not task.id:
                errors.append("任务缺少 ID")
            
            if not task.body:
                errors.append(f"任务 '{task.id}' 没有内容")
        
        # 验证工具完整性
        for tool in dsl_output.tools:
            if not tool.name:
                errors.append("工具缺少名称")
        
        # 验证变量完整性
        for variable in dsl_output.variables:
            if not variable.name:
                errors.append("变量缺少名称")
        
        return errors 