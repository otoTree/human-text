"""
DSL Compiler Data Models
"""

from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ToolCall(BaseModel):
    """Tool invocation model"""
    name: str = Field(description="Tool name")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Tool parameters")
    description: Optional[str] = Field(default=None, description="Invocation description")
    
    class Config:
        exclude_defaults = True
        exclude_none = True


class AgentCall(BaseModel):
    """Agent invocation model"""
    name: str = Field(description="Agent name")
    parameters: Optional[str] = Field(default=None, description="Invocation parameters")
    description: Optional[str] = Field(default=None, description="Invocation description")
    
    class Config:
        exclude_defaults = True
        exclude_none = True


class JumpAction(BaseModel):
    """Jump action model"""
    target: str = Field(description="Target task ID")
    reason: Optional[str] = Field(default=None, description="Jump reason")
    
    class Config:
        exclude_defaults = True
        exclude_none = True


class ConditionalAction(BaseModel):
    """Conditional action model"""
    type: Literal["text", "tool_call", "agent_call", "jump"] = Field(description="Action type")
    content: Optional[str] = Field(default=None, description="Text content")
    tool_call: Optional[ToolCall] = Field(default=None, description="Tool invocation")
    agent_call: Optional[AgentCall] = Field(default=None, description="Agent invocation")
    jump: Optional[JumpAction] = Field(default=None, description="Jump action")


class ConditionalBranch(BaseModel):
    """Conditional branch model"""
    condition: Optional[str] = Field(default=None, description="Condition expression, None for else branch")
    actions: List[ConditionalAction] = Field(default_factory=list, description="Branch action list")


class ConditionalStatement(BaseModel):
    """Conditional statement model"""
    type: Literal["conditional"] = Field(default="conditional", description="Statement type")
    branches: List[ConditionalBranch] = Field(description="Conditional branch list")
    line_number: Optional[int] = Field(default=None, description="Line number")


class ConditionalNext(BaseModel):
    """Conditional jump model"""
    when: str = Field(description="Condition expression, 'default' for fallback")
    target: str = Field(description="Target task ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "when": "success",
                "target": "task_2"
            }
        }


class Block(BaseModel):
    """Text block model"""
    type: Literal["text", "code", "directive", "conditional", "tool_call", "agent_call", "next_action"] = Field(description="Block type")
    content: Optional[str] = Field(default=None, description="Block content")
    language: Optional[str] = Field(default=None, description="Code language (for code type only)")
    line_number: Optional[int] = Field(default=None, description="Line number")
    
    # Conditional statement related fields
    conditional: Optional[ConditionalStatement] = Field(default=None, description="Conditional statement (for conditional type only)")
    
    # Tool call related fields
    tool_call: Optional[ToolCall] = Field(default=None, description="Tool call (for tool_call type only)")
    
    # Agent call related fields  
    agent_call: Optional[AgentCall] = Field(default=None, description="Agent call (for agent_call type only)")
    
    # Jump action related fields
    next_action: Optional[JumpAction] = Field(default=None, description="Jump action (for next_action type only)")
    
    class Config:
        exclude_defaults = True
        exclude_none = True
        
        json_schema_extra = {
            "example": {
                "type": "text",
                "content": "This is a sample task",
                "line_number": 1
            }
        }


class TaskNode(BaseModel):
    """Task node model"""
    id: str = Field(description="Task unique identifier")
    title: Optional[str] = Field(default=None, description="Task title")
    body: List[Block] = Field(default_factory=list, description="Task content blocks")
    next: List[Union[str, ConditionalNext]] = Field(default_factory=list, description="Next tasks")
    
    # Extended fields
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    dependencies: List[str] = Field(default_factory=list, description="Dependent tasks")
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds")
    retry_count: Optional[int] = Field(default=None, description="Retry count")
    
    class Config:
        # Exclude empty values and defaults during serialization
        exclude_defaults = True
        exclude_none = True
        
        json_schema_extra = {
            "example": {
                "id": "task_1",
                "title": "Data processing task",
                "body": [
                    {
                        "type": "text",
                        "content": "Process data file"
                    }
                ],
                "next": ["task_2"]
            }
        }


class ToolNode(BaseModel):
    """Tool node model"""
    id: str = Field(description="Tool unique identifier")
    name: str = Field(description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "tool_1",
                "name": "data_processor",
                "description": "Data processing tool",
                "parameters": {
                    "input_format": "json",
                    "output_format": "csv"
                }
            }
        }


class VariableNode(BaseModel):
    """Variable node model"""
    name: str = Field(description="Variable name")
    value: Any = Field(description="Variable value")
    type: Optional[str] = Field(default=None, description="Variable type")
    scope: Literal["global", "local"] = Field(default="local", description="Scope")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_id",
                "value": "12345",
                "type": "string",
                "scope": "global"
            }
        }


class DSLOutput(BaseModel):
    """DSL output result model"""
    version: str = Field(default="1.0", description="DSL version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    variables: List[VariableNode] = Field(default_factory=list, description="Global variables")
    tools: List[ToolNode] = Field(default_factory=list, description="Tool definitions")
    tasks: List[TaskNode] = Field(default_factory=list, description="Task list")
    entry_point: Optional[str] = Field(default=None, description="Entry task ID")
    
    # Compilation information
    compiled_at: datetime = Field(default_factory=datetime.now, description="Compilation time")
    compiler_version: str = Field(default="1.0.0", description="Compiler version")
    source_files: List[str] = Field(default_factory=list, description="Source file list")
    
    class Config:
        exclude_defaults = True
        exclude_none = True
        
        json_schema_extra = {
            "example": {
                "version": "1.0",
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Example task"
                    }
                ],
                "entry_point": "task_1"
            }
        }
    
    def to_yaml(self) -> str:
        """Convert to YAML format"""
        import yaml
        from ruamel.yaml import YAML
        
        yaml_obj = YAML()
        yaml_obj.default_flow_style = False
        yaml_obj.preserve_quotes = True
        
        # Get model data and clean empty fields
        data = self.model_dump(exclude_none=True, exclude_defaults=True)
        cleaned_data = self._clean_empty_fields(data)
        
        from io import StringIO
        output = StringIO()
        yaml_obj.dump(cleaned_data, output)
        return output.getvalue()
    
    def _clean_empty_fields(self, obj):
        """Recursively clean empty fields"""
        if isinstance(obj, dict):
            cleaned = {}
            for k, v in obj.items():
                if v is not None:
                    if isinstance(v, (dict, list)):
                        cleaned_v = self._clean_empty_fields(v)
                        # Only keep non-empty dictionaries and lists
                        if cleaned_v:
                            cleaned[k] = cleaned_v
                    else:
                        cleaned[k] = v
            return cleaned
        elif isinstance(obj, list):
            cleaned = []
            for item in obj:
                if item is not None:
                    cleaned_item = self._clean_empty_fields(item)
                    # Only keep items with content (preserve number 0 and boolean False)
                    if cleaned_item or cleaned_item == 0 or cleaned_item == False:
                        cleaned.append(cleaned_item)
            return cleaned
        else:
            return obj
    
    def to_json(self, compact: bool = False) -> str:
        """Convert to JSON format"""
        import json
        from datetime import datetime
        
        def json_serializer(obj):
            """Handle special types for JSON serialization"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        data = self.model_dump(exclude_none=True)
        if compact:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'), default=json_serializer)
        else:
            return json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer)
    
    def validate_dag(self) -> List[str]:
        """Validate DAG structure, return error list"""
        errors = []
        
        # Build task ID set
        task_ids = {task.id for task in self.tasks}
        
        # Check entry point
        if self.entry_point and self.entry_point not in task_ids:
            errors.append(f"Entry point '{self.entry_point}' does not exist")
        
        # Check task references
        for task in self.tasks:
            for next_item in task.next:
                target_id = next_item if isinstance(next_item, str) else next_item.target
                if target_id not in task_ids:
                    errors.append(f"Task '{task.id}' references non-existent task '{target_id}'")
            
            # Check dependencies
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task '{task.id}' depends on non-existent task '{dep}'")
        
        # Simple cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            # Find task
            task = next((t for t in self.tasks if t.id == task_id), None)
            if task:
                for next_item in task.next:
                    target_id = next_item if isinstance(next_item, str) else next_item.target
                    if target_id in task_ids and has_cycle(target_id):
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in self.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    errors.append(f"Cycle detected involving task '{task.id}'")
        
        return errors


class Token(BaseModel):
    """Lexical token model"""
    type: Literal["directive", "text", "indent", "dedent", "newline", "eof"] = Field(description="Token type")
    value: str = Field(description="Token value")
    line: int = Field(description="Line number")
    column: int = Field(description="Column number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "directive",
                "value": "@task",
                "line": 1,
                "column": 1
            }
        }


class ParseContext(BaseModel):
    """Parse context model"""
    source_file: Optional[str] = Field(default=None, description="Source file path")
    current_line: int = Field(default=1, description="Current line number")
    current_column: int = Field(default=1, description="Current column number")
    indent_level: int = Field(default=0, description="Indentation level")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variable context")
    directive_index: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Directive index")
    
    def copy(self) -> 'ParseContext':
        """Copy context"""
        return ParseContext(
            source_file=self.source_file,
            current_line=self.current_line,
            current_column=self.current_column,
            indent_level=self.indent_level,
            variables=self.variables.copy()
        ) 