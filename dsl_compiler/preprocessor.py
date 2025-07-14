"""
DSL 编译器预处理器
负责 BOM 清理、换行统一、Tab → 4 空格、指令快速索引
"""

import re
from typing import List, Dict, Any, Tuple
from .config import CompilerConfig
from .models import ParseContext
from .exceptions import CompilerError

class Preprocessor:
    """预处理器"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        # 指令识别正则
        self.directive_pattern = re.compile(r'^\s*@(task|tool|var|if|else|endif|include|agent|lang|next)\b', re.MULTILINE)
        # 注释识别正则
        self.comment_pattern = re.compile(r'^\s*#.*$', re.MULTILINE)
    
    def process(self, content: str, context: ParseContext) -> str:
        """
        预处理文本内容
        
        Args:
            content: 原始文本内容
            context: 解析上下文
            
        Returns:
            str: 预处理后的文本
            
        Raises:
            CompilerError: 预处理错误
        """
        try:
            # 1. 清理 BOM
            content = self._remove_bom(content)
            
            # 2. 统一换行符
            content = self._normalize_newlines(content)
            
            # 3. Tab → 4 空格
            content = self._expand_tabs(content)
            
            # 4. 清理尾部空白
            content = self._clean_trailing_whitespace(content)
            
            # 5. 确保文件以换行符结尾
            content = self._ensure_final_newline(content)
            
            # 6. 构建指令索引
            self._build_directive_index(content, context)
            
            return content
            
        except Exception as e:
            raise CompilerError(f"预处理失败: {str(e)}")
    
    def _remove_bom(self, content: str) -> str:
        """移除 BOM 标记"""
        # UTF-8 BOM
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # UTF-16 BOM
        if content.startswith('\xff\xfe') or content.startswith('\xfe\xff'):
            content = content[2:]
        
        return content
    
    def _normalize_newlines(self, content: str) -> str:
        """统一换行符为 \\n"""
        # Windows CRLF → LF
        content = content.replace('\r\n', '\n')
        # Old Mac CR → LF
        content = content.replace('\r', '\n')
        
        return content
    
    def _expand_tabs(self, content: str) -> str:
        """将 Tab 替换为 4 个空格"""
        return content.expandtabs(4)
    
    def _clean_trailing_whitespace(self, content: str) -> str:
        """清理行尾空白"""
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        return '\n'.join(cleaned_lines)
    
    def _ensure_final_newline(self, content: str) -> str:
        """确保文件以换行符结尾"""
        if content and not content.endswith('\n'):
            content += '\n'
        return content
    
    def _build_directive_index(self, content: str, context: ParseContext) -> None:
        """构建指令索引"""
        lines = content.split('\n')
        directive_index = {}
        
        for line_num, line in enumerate(lines, 1):
            # 检查是否是指令行
            match = self.directive_pattern.match(line)
            if match:
                directive_type = match.group(1)
                if directive_type not in directive_index:
                    directive_index[directive_type] = []
                
                directive_index[directive_type].append({
                    'line': line_num,
                    'content': line.strip(),
                    'indent': len(line) - len(line.lstrip())
                })
        
        # 存储到上下文中
        if not hasattr(context, 'directive_index'):
            context.directive_index = directive_index
        else:
            context.directive_index.update(directive_index)
    
    def get_directive_locations(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取指令位置信息"""
        lines = content.split('\n')
        locations = {}
        
        for line_num, line in enumerate(lines, 1):
            match = self.directive_pattern.match(line)
            if match:
                directive_type = match.group(1)
                if directive_type not in locations:
                    locations[directive_type] = []
                
                locations[directive_type].append({
                    'line': line_num,
                    'column': match.start(1),
                    'content': line.strip(),
                    'indent_level': (len(line) - len(line.lstrip())) // 4
                })
        
        return locations
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        lines = content.split('\n')
        
        # 查找文件头部的元数据注释
        for line_num, line in enumerate(lines[:10], 1):  # 只检查前10行
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
                
            # 检查是否是注释
            if line.startswith('#'):
                # 提取键值对格式的注释
                comment_content = line[1:].strip()
                if ':' in comment_content:
                    key, value = comment_content.split(':', 1)
                    metadata[key.strip()] = value.strip()
                elif comment_content.startswith('title:'):
                    metadata['title'] = comment_content[6:].strip()
                elif comment_content.startswith('author:'):
                    metadata['author'] = comment_content[7:].strip()
                elif comment_content.startswith('version:'):
                    metadata['version'] = comment_content[8:].strip()
                elif comment_content.startswith('description:'):
                    metadata['description'] = comment_content[12:].strip()
            else:
                # 遇到非注释行，停止扫描
                break
        
        return metadata
    
    def validate_encoding(self, content: str) -> bool:
        """验证文本编码"""
        try:
            # 尝试编码为 UTF-8
            content.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False
    
    def calculate_complexity(self, content: str) -> Dict[str, int]:
        """计算文本复杂度"""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        directive_count = len(self.directive_pattern.findall(content))
        comment_count = len(self.comment_pattern.findall(content))
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'directive_count': directive_count,
            'comment_count': comment_count,
            'average_line_length': int(sum(len(line) for line in non_empty_lines) / len(non_empty_lines)) if non_empty_lines else 0
        }
    
    def split_into_sections(self, content: str) -> List[Tuple[str, str, int]]:
        """
        将内容分割为逻辑段落
        
        Returns:
            List[Tuple[str, str, int]]: (section_type, content, start_line)
        """
        sections = []
        lines = content.split('\n')
        current_section = []
        current_type = 'text'
        section_start = 1
        
        for line_num, line in enumerate(lines, 1):
            # 检查是否是指令行
            if self.directive_pattern.match(line):
                # 保存当前段落
                if current_section:
                    sections.append((current_type, '\n'.join(current_section), section_start))
                
                # 开始新段落
                current_section = [line]
                current_type = 'directive'
                section_start = line_num
            else:
                # 如果当前是指令段落，检查是否需要切换
                if current_type == 'directive' and line.strip() and not line.startswith(' '):
                    # 保存指令段落
                    sections.append((current_type, '\n'.join(current_section), section_start))
                    
                    # 开始文本段落
                    current_section = [line]
                    current_type = 'text'
                    section_start = line_num
                else:
                    current_section.append(line)
        
        # 保存最后一个段落
        if current_section:
            sections.append((current_type, '\n'.join(current_section), section_start))
        
        return sections 