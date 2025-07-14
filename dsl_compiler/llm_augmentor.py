"""
DSL 编译器 LLM 增强器
自然语言→结构化，调用 RAG & PromptCompiler
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import LLMError, CompilerError


class LLMAugmentor:
    """LLM 增强器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    def augment(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """
        增强 AST
        
        Args:
            ast_root: 根 AST 节点
            context: 解析上下文
            
        Returns:
            ASTNode: 增强后的 AST
            
        Raises:
            LLMError: LLM 调用错误
        """
        try:
            # 检查是否需要 LLM 增强
            if not self._needs_augmentation(ast_root):
                return ast_root
            
            # 异步处理 LLM 增强
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._augment_async(ast_root, context))
            
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            else:
                raise LLMError(f"LLM 增强失败: {str(e)}")
    
    async def _augment_async(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """异步增强 AST"""
        # 创建 HTTP 会话
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # 1. 分析文本结构
            await self._analyze_structure(ast_root, context)
            
            # 2. 提取任务结构
            await self._extract_tasks(ast_root, context)
            
            # 3. 增强内容
            await self._enhance_content(ast_root, context)
            
            # 4. 验证结果
            self._validate_augmented_ast(ast_root, context)
            
            return ast_root
    
    async def _analyze_structure(self, ast_root: ASTNode, context: ParseContext) -> None:
        """分析文本结构"""
        # 收集所有文本内容
        text_content = self._collect_text_content(ast_root)
        
        if not text_content.strip():
            return
        
        # 调用 LLM 分析结构
        prompt = f"""
请分析以下文本的结构，并提供结构化建议：

输入文本：
{text_content}

请分析：
1. 文本是否包含明确的任务流程？
2. 是否有条件判断逻辑？
3. 是否需要工具或变量定义？
4. 文本的主要意图是什么？

请以JSON格式回答：
{{
    "has_workflow": true/false,
    "has_conditions": true/false,
    "needs_tools": true/false,
    "needs_variables": true/false,
    "main_intent": "主要意图描述",
    "suggested_structure": "建议的结构化方式",
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = await self._call_llm(prompt)
            analysis = json.loads(response)
            
            # 将分析结果存储到根节点
            ast_root.set_attribute("structure_analysis", analysis)
            
        except Exception as e:
            raise LLMError(f"结构分析失败: {str(e)}")
    
    async def _extract_tasks(self, ast_root: ASTNode, context: ParseContext) -> None:
        """提取任务结构"""
        # 获取结构分析结果
        analysis = ast_root.get_attribute("structure_analysis", {})
        
        if not analysis.get("has_workflow", False):
            return
        
        # 收集需要处理的文本
        text_content = self._collect_text_content(ast_root)
        
        # 调用 LLM 提取任务
        prompt = f"""
请从以下自然语言描述中提取任务结构：

输入文本：
{text_content}

请按照以下格式输出 JSON：
{{
    "tasks": [
        {{
            "id": "任务ID",
            "title": "任务标题",
            "description": "任务描述",
            "steps": ["步骤1", "步骤2", "..."]
        }}
    ],
    "tools": [
        {{
            "name": "工具名称",
            "description": "工具描述",
            "parameters": {{"param1": "参数说明"}}
        }}
    ],
    "variables": [
        {{
            "name": "变量名",
            "value": "变量值",
            "type": "变量类型"
        }}
    ]
}}

要求：
1. 任务ID使用snake_case格式
2. 识别出明确的操作步骤
3. 提取出可能需要的工具和变量
4. 保持语义的准确性
"""
        
        try:
            response = await self._call_llm(prompt)
            extraction = json.loads(response)
            
            # 创建新的 AST 节点
            await self._create_extracted_nodes(ast_root, extraction, context)
            
        except Exception as e:
            raise LLMError(f"任务提取失败: {str(e)}")
    
    async def _enhance_content(self, ast_root: ASTNode, context: ParseContext) -> None:
        """增强内容"""
        # 遍历所有任务节点
        for task_node in self._find_nodes_by_type(ast_root, "task"):
            await self._enhance_task_content(task_node, context)
    
    async def _enhance_task_content(self, task_node: ASTNode, context: ParseContext) -> None:
        """增强任务内容"""
        task_id = task_node.get_attribute("id", "")
        title = task_node.get_attribute("title", "")
        
        # 收集任务的文本内容
        content = self._collect_text_content(task_node)
        
        if not content.strip():
            return
        
        # 收集相关工具和变量
        tools = self._collect_related_tools(task_node)
        variables = self._collect_related_variables(task_node)
        
        # 调用 LLM 增强内容
        prompt = f"""
请增强以下任务内容，使其更加清晰和可执行：

原始内容：
{content}

上下文信息：
- 任务ID: {task_id}
- 任务标题: {title}
- 相关工具: {json.dumps(tools)}
- 相关变量: {json.dumps(variables)}

请提供：
1. 增强的任务描述
2. 具体的执行步骤
3. 可能的输入输出
4. 注意事项

以JSON格式回答：
{{
    "enhanced_description": "增强后的描述",
    "execution_steps": ["步骤1", "步骤2", "..."],
    "inputs": ["输入1", "输入2", "..."],
    "outputs": ["输出1", "输出2", "..."],
    "notes": ["注意事项1", "注意事项2", "..."]
}}
"""
        
        try:
            response = await self._call_llm(prompt)
            enhancement = json.loads(response)
            
            # 更新任务节点
            self._apply_content_enhancement(task_node, enhancement)
            
        except Exception as e:
            raise LLMError(f"内容增强失败: {str(e)}")
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 服务"""
        if self.session is None:
            raise LLMError("HTTP 会话未初始化")
        
        if self.config.llm_provider == "dashscope":
            return await self._call_dashscope(prompt)
        elif self.config.llm_provider == "openai":
            return await self._call_openai(prompt)
        elif self.config.llm_provider == "context_service":
            return await self._call_context_service(prompt)
        else:
            raise LLMError(f"不支持的 LLM 提供商: {self.config.llm_provider}")
    
    async def _call_dashscope(self, prompt: str) -> str:
        """调用 DashScope API"""
        if self.session is None:
            raise LLMError("HTTP 会话未初始化")
        
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.llm_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        }
        
        try:
            async with self.session.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.llm_timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["output"]["text"]
                else:
                    error_text = await response.text()
                    raise LLMError(f"DashScope API 错误: {error_text}")
                    
        except asyncio.TimeoutError:
            raise LLMError("LLM 调用超时")
        except Exception as e:
            raise LLMError(f"DashScope 调用失败: {str(e)}")
    
    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        if self.session is None:
            raise LLMError("HTTP 会话未初始化")
        
        headers = {
            "Authorization": f"Bearer {self.config.llm_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.llm_model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 4000
        }
        
        api_base = self.config.llm_api_base or "https://api.openai.com/v1"
        
        try:
            async with self.session.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.llm_timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise LLMError(f"OpenAI API 错误: {error_text}")
                    
        except asyncio.TimeoutError:
            raise LLMError("LLM 调用超时")
        except Exception as e:
            raise LLMError(f"OpenAI 调用失败: {str(e)}")
    
    async def _call_context_service(self, prompt: str) -> str:
        """调用 Context Service"""
        if self.session is None:
            raise LLMError("HTTP 会话未初始化")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "max_tokens": 4000
        }
        
        try:
            async with self.session.post(
                f"{self.config.context_service_url}/llm/generate",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.context_service_timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["response"]
                else:
                    error_text = await response.text()
                    raise LLMError(f"Context Service 错误: {error_text}")
                    
        except asyncio.TimeoutError:
            raise LLMError("Context Service 调用超时")
        except Exception as e:
            raise LLMError(f"Context Service 调用失败: {str(e)}")
    
    def _needs_augmentation(self, ast_root: ASTNode) -> bool:
        """检查是否需要增强"""
        # 检查是否有纯文本内容没有结构化
        text_nodes = self._find_nodes_by_type(ast_root, "text")
        
        for text_node in text_nodes:
            content = text_node.get_attribute("content", "")
            if content.strip() and not self._is_structured_content(content):
                return True
        
        # 检查是否有空的任务需要增强
        task_nodes = self._find_nodes_by_type(ast_root, "task")
        for task_node in task_nodes:
            if not task_node.children:
                return True
        
        return False
    
    def _is_structured_content(self, content: str) -> bool:
        """检查内容是否已经结构化"""
        # 简单的启发式检查
        structured_patterns = [
            r'^\s*\d+\.',  # 数字列表
            r'^\s*[-*+]',  # 项目符号
            r'^\s*@\w+',   # 指令
            r'```',        # 代码块
        ]
        
        import re
        for pattern in structured_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False
    
    def _collect_text_content(self, node: ASTNode) -> str:
        """收集节点的文本内容"""
        content = []
        
        if node.node_type == "text":
            text = node.get_attribute("content", "")
            if text.strip():
                content.append(text)
        
        for child in node.children:
            child_content = self._collect_text_content(child)
            if child_content.strip():
                content.append(child_content)
        
        return "\n".join(content)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """查找指定类型的节点"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    def _collect_related_tools(self, task_node: ASTNode) -> List[Dict[str, Any]]:
        """收集相关工具"""
        tools = []
        
        # 从父节点或兄弟节点中查找工具定义
        if task_node.parent:
            for sibling in task_node.parent.children:
                if sibling.node_type == "tool":
                    tools.append({
                        "name": sibling.get_attribute("name", ""),
                        "description": sibling.get_attribute("description", "")
                    })
        
        return tools
    
    def _collect_related_variables(self, task_node: ASTNode) -> List[Dict[str, Any]]:
        """收集相关变量"""
        variables = []
        
        # 从父节点或兄弟节点中查找变量定义
        if task_node.parent:
            for sibling in task_node.parent.children:
                if sibling.node_type == "var":
                    variables.append({
                        "name": sibling.get_attribute("name", ""),
                        "value": sibling.get_attribute("value", ""),
                        "type": sibling.get_attribute("inferred_type", "")
                    })
        
        return variables
    
    async def _create_extracted_nodes(self, ast_root: ASTNode, extraction: Dict[str, Any], context: ParseContext) -> None:
        """创建提取的节点"""
        # 创建任务节点
        for task_data in extraction.get("tasks", []):
            task_node = ASTNode("task", 0, 0)
            task_node.set_attribute("id", task_data["id"])
            task_node.set_attribute("title", task_data["title"])
            
            # 创建描述文本节点
            if task_data.get("description"):
                desc_node = ASTNode("text", 0, 0)
                desc_node.set_attribute("content", task_data["description"])
                task_node.add_child(desc_node)
            
            # 创建步骤文本节点
            for step in task_data.get("steps", []):
                step_node = ASTNode("text", 0, 0)
                step_node.set_attribute("content", f"- {step}")
                task_node.add_child(step_node)
            
            ast_root.add_child(task_node)
        
        # 创建工具节点
        for tool_data in extraction.get("tools", []):
            tool_node = ASTNode("tool", 0, 0)
            tool_node.set_attribute("name", tool_data["name"])
            tool_node.set_attribute("description", tool_data["description"])
            tool_node.set_attribute("parameters", tool_data.get("parameters", {}))
            ast_root.add_child(tool_node)
        
        # 创建变量节点
        for var_data in extraction.get("variables", []):
            var_node = ASTNode("var", 0, 0)
            var_node.set_attribute("name", var_data["name"])
            var_node.set_attribute("value", var_data["value"])
            var_node.set_attribute("inferred_type", var_data.get("type", "string"))
            ast_root.add_child(var_node)
    
    def _apply_content_enhancement(self, task_node: ASTNode, enhancement: Dict[str, Any]) -> None:
        """应用内容增强"""
        # 更新任务描述
        if enhancement.get("enhanced_description"):
            # 查找或创建描述节点
            desc_node = None
            for child in task_node.children:
                if child.node_type == "text":
                    desc_node = child
                    break
            
            if not desc_node:
                desc_node = ASTNode("text", task_node.line, task_node.column)
                task_node.add_child(desc_node)
            
            desc_node.set_attribute("content", enhancement["enhanced_description"])
        
        # 添加执行步骤
        for step in enhancement.get("execution_steps", []):
            step_node = ASTNode("text", task_node.line, task_node.column)
            step_node.set_attribute("content", f"步骤: {step}")
            task_node.add_child(step_node)
        
        # 添加注意事项
        for note in enhancement.get("notes", []):
            note_node = ASTNode("text", task_node.line, task_node.column)
            note_node.set_attribute("content", f"注意: {note}")
            task_node.add_child(note_node)
    
    def _validate_augmented_ast(self, ast_root: ASTNode, context: ParseContext) -> None:
        """验证增强后的 AST"""
        # 检查是否有重复的任务ID
        task_ids = set()
        for task_node in self._find_nodes_by_type(ast_root, "task"):
            task_id = task_node.get_attribute("id")
            if task_id:
                if task_id in task_ids:
                    raise LLMError(f"LLM 生成了重复的任务ID: {task_id}")
                task_ids.add(task_id)
        
        # 检查是否有重复的工具名
        tool_names = set()
        for tool_node in self._find_nodes_by_type(ast_root, "tool"):
            tool_name = tool_node.get_attribute("name")
            if tool_name:
                if tool_name in tool_names:
                    raise LLMError(f"LLM 生成了重复的工具名: {tool_name}")
                tool_names.add(tool_name) 