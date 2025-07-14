"""
DSL Compiler Configuration Management
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CompilerConfig(BaseModel):
    """Compiler configuration"""
    
    # Output format configuration
    output_format: str = Field(default="yaml", description="Output format: yaml, json, proto")
    compact_mode: bool = Field(default=False, description="Compact mode, output only required fields")
    strict_mode: bool = Field(default=True, description="Strict mode, return errors on parse failures")
    
    # LLM configuration
    llm_enabled: bool = Field(default=True, description="Enable LLM-assisted parsing")
    llm_provider: str = Field(default="dashscope", description="LLM provider")
    llm_model: str = Field(default="qwen-turbo", description="LLM model")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API Key")
    llm_api_base: Optional[str] = Field(default=None, description="LLM API base URL")
    llm_timeout: int = Field(default=30, description="LLM request timeout (seconds)")
    llm_max_retries: int = Field(default=3, description="LLM request max retries")
    
    # Performance configuration
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size (bytes)")
    max_tokens: int = Field(default=100000, description="Max token count")
    parse_timeout: int = Field(default=60, description="Parse timeout (seconds)")
    
    # Debug configuration
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    
    # Context Service configuration
    context_service_url: str = Field(default="http://localhost:8001", description="Context Service URL")
    context_service_timeout: int = Field(default=30, description="Context Service timeout")
    
    @classmethod
    def from_env(cls) -> 'CompilerConfig':
        """Create configuration from environment variables"""
        return cls(
            output_format=os.getenv("DSL_OUTPUT_FORMAT", "yaml"),
            compact_mode=os.getenv("DSL_COMPACT_MODE", "false").lower() == "true",
            strict_mode=os.getenv("DSL_STRICT_MODE", "true").lower() == "true",
            
            llm_enabled=os.getenv("DSL_LLM_ENABLED", "true").lower() == "true",
            llm_provider=os.getenv("DSL_LLM_PROVIDER", "dashscope"),
            llm_model=os.getenv("DSL_LLM_MODEL", "qwen-turbo"),
            llm_api_key=os.getenv("DSL_LLM_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
            llm_api_base=os.getenv("DSL_LLM_API_BASE"),
            llm_timeout=int(os.getenv("DSL_LLM_TIMEOUT", "30")),
            llm_max_retries=int(os.getenv("DSL_LLM_MAX_RETRIES", "3")),
            
            max_file_size=int(os.getenv("DSL_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            max_tokens=int(os.getenv("DSL_MAX_TOKENS", "100000")),
            parse_timeout=int(os.getenv("DSL_PARSE_TIMEOUT", "60")),
            
            debug=os.getenv("DSL_DEBUG", "false").lower() == "true",
            log_level=os.getenv("DSL_LOG_LEVEL", "INFO"),
            
            context_service_url=os.getenv("DSL_CONTEXT_SERVICE_URL", "http://localhost:8001"),
            context_service_timeout=int(os.getenv("DSL_CONTEXT_SERVICE_TIMEOUT", "30")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()
    
    def validate_llm_config(self) -> None:
        """Validate LLM configuration"""
        if self.llm_enabled:
            if not self.llm_api_key:
                raise ValueError("LLM is enabled but API key is not set")
            if self.llm_provider not in ["dashscope", "openai", "context_service"]:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}") 