"""
DSL Compiler Preprocessor
Handles BOM cleanup, line normalization, Tab → 4 spaces, directive quick indexing
"""

import re
from typing import List, Dict, Any, Tuple
from .config import CompilerConfig
from .models import ParseContext
from .exceptions import CompilerError

class Preprocessor:
    """Preprocessor"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        # Directive recognition regex
        self.directive_pattern = re.compile(r'^\s*@(task|tool|var|if|else|endif|include|agent|lang|next)\b', re.MULTILINE)
        # Comment recognition regex
        self.comment_pattern = re.compile(r'^\s*#.*$', re.MULTILINE)
    
    def process(self, content: str, context: ParseContext) -> str:
        """
        Preprocess text content
        
        Args:
            content: Original text content
            context: Parse context
            
        Returns:
            str: Preprocessed text
            
        Raises:
            CompilerError: Preprocessing error
        """
        try:
            # 1. Remove BOM
            content = self._remove_bom(content)
            
            # 2. Normalize line endings
            content = self._normalize_newlines(content)
            
            # 3. Tab → 4 spaces
            content = self._expand_tabs(content)
            
            # 4. Clean trailing whitespace
            content = self._clean_trailing_whitespace(content)
            
            # 5. Ensure file ends with newline
            content = self._ensure_final_newline(content)
            
            # 6. Build directive index
            self._build_directive_index(content, context)
            
            return content
            
        except Exception as e:
            raise CompilerError(f"Preprocessing failed: {str(e)}")
    
    def _remove_bom(self, content: str) -> str:
        """Remove BOM markers"""
        # UTF-8 BOM
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # UTF-16 BOM
        if content.startswith('\xff\xfe') or content.startswith('\xfe\xff'):
            content = content[2:]
        
        return content
    
    def _normalize_newlines(self, content: str) -> str:
        """Normalize line endings to \\n"""
        # Windows CRLF → LF
        content = content.replace('\r\n', '\n')
        # Old Mac CR → LF
        content = content.replace('\r', '\n')
        
        return content
    
    def _expand_tabs(self, content: str) -> str:
        """Replace Tab with 4 spaces"""
        return content.expandtabs(4)
    
    def _clean_trailing_whitespace(self, content: str) -> str:
        """Clean line-ending whitespace"""
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        return '\n'.join(cleaned_lines)
    
    def _ensure_final_newline(self, content: str) -> str:
        """Ensure file ends with newline"""
        if content and not content.endswith('\n'):
            content += '\n'
        return content
    
    def _build_directive_index(self, content: str, context: ParseContext) -> None:
        """Build directive index"""
        lines = content.split('\n')
        directive_index = {}
        
        for line_num, line in enumerate(lines, 1):
            # Check if it's a directive line
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
        
        # Store in context
        if not hasattr(context, 'directive_index'):
            context.directive_index = directive_index
        else:
            context.directive_index.update(directive_index)
    
    def get_directive_locations(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get directive location information"""
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
        """Extract metadata"""
        metadata = {}
        lines = content.split('\n')
        
        # Look for metadata comments in file header
        for line_num, line in enumerate(lines[:10], 1):  # Only check first 10 lines
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check if it's a comment
            if line.startswith('#'):
                # Extract key-value pair format comments
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
                # Stop scanning when encountering non-comment line
                break
        
        return metadata
    
    def validate_encoding(self, content: str) -> bool:
        """Validate text encoding"""
        try:
            # Try encoding as UTF-8
            content.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False
    
    def calculate_complexity(self, content: str) -> Dict[str, int]:
        """Calculate text complexity"""
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
        Split content into logical sections
        
        Returns:
            List[Tuple[str, str, int]]: (section_type, content, start_line)
        """
        sections = []
        lines = content.split('\n')
        current_section = []
        current_type = 'text'
        section_start = 1
        
        for line_num, line in enumerate(lines, 1):
            # Check if it's a directive line
            if self.directive_pattern.match(line):
                # Save current section
                if current_section:
                    sections.append((current_type, '\n'.join(current_section), section_start))
                
                # Start new section
                current_section = [line]
                current_type = 'directive'
                section_start = line_num
            else:
                # If current is directive section, check if we need to switch
                if current_type == 'directive' and line.strip() and not line.startswith(' '):
                    # Save directive section
                    sections.append((current_type, '\n'.join(current_section), section_start))
                    
                    # Start text section
                    current_section = [line]
                    current_type = 'text'
                    section_start = line_num
                else:
                    current_section.append(line)
        
        # Save last section
        if current_section:
            sections.append((current_type, '\n'.join(current_section), section_start))
        
        return sections 