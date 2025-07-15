"""
DSL Compiler LLM Enhancement Module
Uses LLM to directly convert natural language to DSL code
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import CompilerConfig
from .models import ParseContext
from .parser import ASTNode
from .exceptions import LLMError, CompilerError


class LLMAugmentor:
    """LLM Augmentor - Direct conversion to DSL code"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    def augment(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Enhance AST"""
        try:
            if not self._needs_augmentation(ast_root):
                return ast_root
            
            # Asynchronous LLM enhancement processing
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._augment_async(ast_root, context))
            
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            else:
                raise LLMError(f"LLM enhancement failed: {str(e)}")
    
    async def _augment_async(self, ast_root: ASTNode, context: ParseContext) -> ASTNode:
        """Asynchronous enhancement processing"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Collect natural language content
            natural_content = self._collect_text_content(ast_root)
            
            if not natural_content.strip():
                return ast_root
            
            # Call LLM to directly convert to DSL code
            dsl_code = await self._convert_to_dsl(natural_content)
            
            # Save intermediate DSL code if configured
            if self.config.llm_save_intermediate:
                await self._save_intermediate_dsl(dsl_code, context)
            
            # Write generated DSL code to temporary file and re-parse
            return await self._reparse_dsl_code(dsl_code, context)
    
    async def _convert_to_dsl(self, natural_content: str) -> str:
        """Convert natural language to DSL code"""
        # 检测源文件语言
        detected_language = self._detect_language(natural_content)
        
        # 根据检测的语言构建提示词
        if detected_language == "chinese":
            language_instruction = "请使用中文描述任务内容和工具描述，但DSL语法关键字必须使用英文"
            example_task_content = "接收用户在密码重置页面输入的邮箱地址"
            example_tool_desc = "检查此用户是否存在"
            example_comment = "用户不存在，终止流程"
        else:
            language_instruction = "Please use English to describe task content and tool descriptions, with English DSL syntax keywords"
            example_task_content = "Receive user email address entered on password reset page"
            example_tool_desc = "Check if this user exists"
            example_comment = "User does not exist, terminate process"
        
        prompt = f"""
You are a professional DSL code generator. Please convert the following natural language description directly to DSL code format.

Natural language description:
{natural_content}

Language instruction: {language_instruction}

Please strictly output in the following DSL syntax format, do not add any explanatory text:

DSL syntax rules:
1. Variable definition: @var variable_name = value
2. Task definition: @task task_id task_title
3. Tool call: @tool tool_name tool_description
4. Conditional statement: @if condition / @else / @endif
5. Jump instruction: @next target_task
6. Task content is indicated by indentation

Example format:
```
@var reset_token_validity = 15
@var user_email = ""

@task verify_user Verify user identity
    {example_task_content}
    User email: {{{{user_email}}}}
    @tool user_database_query {example_tool_desc}
    @if user_exists == true
        Generate secure one-time reset token
        @next send_reset_link
    @else
        {example_comment}
        @next END

@task send_reset_link Send reset link
    Create secure link containing reset token
    @tool email_service_send Send reset link email
    @next execute_reset

@task execute_reset Execute password reset
    Verify validity of reset link
    @if token_valid == true
        Guide user to set new password
        @tool user_database_update Update user password
        @tool email_service_notify Send success notification
        @next END
    @else
        Token invalid, reset failed
        @next END

@task END Process complete
    Password reset process completed
```

Requirements:
- Identify clear steps, each major step as a task
- Assign unique IDs to each task (using snake_case format)
- Extract required tools and variables
- Tool names should avoid duplication, use descriptive suffixes
- Maintain original semantics and logical flow
- Use the detected language ({detected_language}) for task descriptions while keeping DSL syntax keywords in English
- Only output DSL code, no other text

Please start conversion:
"""
        
        try:
            response = await self._call_llm(prompt)
            # Clean response and extract code part
            dsl_code = self._extract_dsl_code(response)
            return dsl_code
            
        except Exception as e:
            raise LLMError(f"DSL conversion failed: {str(e)}")
    
    def _extract_dsl_code(self, response: str) -> str:
        """Extract DSL code from LLM response"""
        response = response.strip()
        
        # If response contains code block markers, extract content within them
        if "```" in response:
            lines = response.split('\n')
            in_code_block = False
            code_lines = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    code_lines.append(line)
            
            if code_lines:
                return '\n'.join(code_lines)
        
        # If no code block markers, look for lines starting with @
        lines = response.split('\n')
        dsl_lines = []
        found_dsl = False
        
        for line in lines:
            # Skip empty lines and explanatory text until DSL code is found
            if line.strip().startswith('@') or found_dsl:
                found_dsl = True
                dsl_lines.append(line)
            elif found_dsl and line.strip() and not line.strip().startswith('#'):
                # If already in DSL code, continue adding non-comment lines
                dsl_lines.append(line)
        
        if dsl_lines:
            return '\n'.join(dsl_lines)
        
        # If nothing found, return original response
        return response
    
    async def _reparse_dsl_code(self, dsl_code: str, context: ParseContext) -> ASTNode:
        """Re-parse generated DSL code"""
        from .preprocessor import Preprocessor
        from .lexer import Lexer
        from .parser import Parser
        
        try:
            # Create new parsing context
            new_context = ParseContext(
                source_file=context.source_file,
                current_line=1,
                current_column=1
            )
            
            # Preprocessing
            preprocessor = Preprocessor(self.config)
            processed_content = preprocessor.process(dsl_code, new_context)
            
            # Lexical analysis
            lexer = Lexer(self.config)
            tokens = lexer.tokenize(processed_content, new_context)
            
            # Syntax analysis
            parser = Parser(self.config)
            new_ast = parser.parse(tokens, new_context)
            
            return new_ast
            
        except Exception as e:
            # If re-parsing fails, return original AST with error information
            raise LLMError(f"Re-parsing DSL code failed: {str(e)}")
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM service"""
        if self.session is None:
            raise LLMError("HTTP session not initialized")
        
        if self.config.llm_provider == "dashscope":
            return await self._call_dashscope(prompt)
        elif self.config.llm_provider == "openai":
            return await self._call_openai(prompt)
        else:
            raise LLMError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    async def _call_dashscope(self, prompt: str) -> str:
        """Call DashScope API"""
        if self.session is None:
            raise LLMError("HTTP session not initialized")
        
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
                    raise LLMError(f"DashScope API error: {error_text}")
                    
        except asyncio.TimeoutError:
            raise LLMError("LLM call timeout")
        except Exception as e:
            raise LLMError(f"DashScope call failed: {str(e)}")
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        if self.session is None:
            raise LLMError("HTTP session not initialized")
        
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
            "max_tokens": 2000,
            "temperature": 0.3
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
                    raise LLMError(f"OpenAI API error: {error_text}")
                    
        except asyncio.TimeoutError:
            raise LLMError("LLM call timeout")
        except Exception as e:
            raise LLMError(f"OpenAI call failed: {str(e)}")
    
    def _needs_augmentation(self, ast_root: ASTNode) -> bool:
        """Check if augmentation is needed"""
        if not self.config.llm_enabled:
            return False
        
        # Collect all text content
        text_nodes = self._find_nodes_by_type(ast_root, "text")
        total_text_content = ""
        structured_content_count = 0
        natural_language_count = 0
        
        for text_node in text_nodes:
            content = text_node.get_attribute("content", "").strip()
            if content:
                total_text_content += content + " "
                
                if self._is_structured_content(content):
                    structured_content_count += 1
                else:
                    natural_language_count += 1
        
        # Check if tasks, tools, variables are defined
        task_count = len(self._find_nodes_by_type(ast_root, "task"))
        tool_count = len(self._find_nodes_by_type(ast_root, "tool"))
        var_count = len(self._find_nodes_by_type(ast_root, "var"))
        
        # Judgment criteria:
        # 1. If no DSL structure (tasks, tools, variables) and natural language content exists, augmentation needed
        if task_count == 0 and tool_count == 0 and var_count == 0 and total_text_content.strip():
            return True
        
        # 2. If natural language content far exceeds structured content, augmentation needed
        if natural_language_count > structured_content_count * 2:
            return True
        
        # 3. If text content is very long but structure is minimal, augmentation needed
        if len(total_text_content) > 500 and (task_count + tool_count + var_count) < 3:
            return True
        
        # 4. Check if contains process keywords
        process_keywords = ["step", "first step", "second step", "third step", "then", "next", "finally", "process", "procedure"]
        if any(keyword in total_text_content.lower() for keyword in process_keywords):
            return True
        
        return False
    
    def _detect_language(self, content: str) -> str:
        """检测文本内容的语言"""
        import re
        
        # 检测中文字符
        chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
        chinese_matches = chinese_char_pattern.findall(content)
        
        # 检测英文单词
        english_word_pattern = re.compile(r'[a-zA-Z]+')
        english_matches = english_word_pattern.findall(content)
        
        # 统计字符数量
        chinese_count = len(chinese_matches)
        english_count = len(''.join(english_matches))
        
        # 如果中文字符数量超过总字符数的30%，认为是中文
        total_chars = len(content)
        if chinese_count > 0 and (chinese_count / total_chars) > 0.1:
            return "chinese"
        
        # 检测常见的中文词汇
        chinese_keywords = ["流程", "步骤", "任务", "工具", "系统", "用户", "客户", "处理", "评估", "分析"]
        for keyword in chinese_keywords:
            if keyword in content:
                return "chinese"
        
        return "english"
    
    def _is_structured_content(self, content: str) -> bool:
        """Check if content is already structured"""
        # Check if contains DSL keywords
        dsl_keywords = ["@task", "@tool", "@var", "@if", "@else", "@endif", "@next", "@agent", "@lang"]
        
        for keyword in dsl_keywords:
            if keyword in content:
                return True
        
        # Check if contains variable reference format
        import re
        if re.search(r'\{\{.*?\}\}', content):
            return True
        
        return False
    
    def _collect_text_content(self, node: ASTNode) -> str:
        """Collect all text content from node"""
        content_parts = []
        
        if node.node_type == "text":
            content = node.get_attribute("content", "")
            if content.strip():
                content_parts.append(content.strip())
        
        # Recursively collect text from child nodes
        for child in node.children:
            child_content = self._collect_text_content(child)
            if child_content:
                content_parts.append(child_content)
        
        return "\n".join(content_parts)
    
    def _find_nodes_by_type(self, node: ASTNode, node_type: str) -> List[ASTNode]:
        """Find nodes of specified type"""
        nodes = []
        
        if node.node_type == node_type:
            nodes.append(node)
        
        for child in node.children:
            nodes.extend(self._find_nodes_by_type(child, node_type))
        
        return nodes
    
    async def _save_intermediate_dsl(self, dsl_code: str, context: ParseContext) -> None:
        """Save intermediate DSL code to file"""
        try:
            # Determine save directory
            if self.config.llm_intermediate_dir:
                save_dir = self.config.llm_intermediate_dir
            else:
                # Use the same directory as source file
                source_dir = os.path.dirname(context.source_file) if context.source_file else "."
                save_dir = os.path.join(source_dir, "llm_intermediate")
            
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = os.path.basename(context.source_file) if context.source_file else "unknown"
            base_name = os.path.splitext(source_name)[0]
            filename = f"{base_name}_llm_generated_{timestamp}.dsl"
            filepath = os.path.join(save_dir, filename)
            
            # Save DSL code to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# LLM Generated DSL Code\n")
                f.write(f"# Source: {context.source_file}\n")
                f.write(f"# Generated at: {datetime.now().isoformat()}\n")
                f.write(f"# Provider: {self.config.llm_provider}\n")
                f.write(f"# Model: {self.config.llm_model}\n\n")
                f.write(dsl_code)
            
            if self.config.debug:
                print(f"中间DSL代码已保存到: {filepath}")
                
        except Exception as e:
            # Don't fail the main process if saving fails
            if self.config.debug:
                print(f"保存中间DSL代码失败: {str(e)}") 