"""
DSL Compiler Main Module
"""

import os
import time
from typing import Union, Optional, Dict, Any
from pathlib import Path
import logging

from .config import CompilerConfig
from .models import DSLOutput, ParseContext
from .exceptions import CompilerError, TimeoutError, ConfigurationError
from .preprocessor import Preprocessor
from .lexer import Lexer
from .parser import Parser
from .semantic_analyzer import SemanticAnalyzer
from .llm_augmentor import LLMAugmentor
from .validator import Validator
from .optimizer import Optimizer
from .serializer import Serializer

logger = logging.getLogger(__name__)


def compile(
    source: Union[str, Path],
    config: Optional[CompilerConfig] = None,
    **kwargs
) -> DSLOutput:
    """
    Compile Human-Text script to DSL
    
    Args:
        source: Source file path or source code string
        config: Compiler configuration
        **kwargs: Additional configuration parameters
    
    Returns:
        DSLOutput: Compilation result
    
    Raises:
        CompilerError: Compilation error
        TimeoutError: Compilation timeout
        ConfigurationError: Configuration error
    """
    # Initialize configuration
    if config is None:
        config = CompilerConfig.from_env()
    
    # Apply additional parameters
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Validate configuration
    try:
        if config.llm_enabled:
            config.validate_llm_config()
    except ValueError as e:
        raise ConfigurationError(str(e))
    
    # Set log level
    logging.basicConfig(level=getattr(logging, config.log_level.upper()))
    
    # Create compiler instance
    compiler = DSLCompiler(config)
    
    # Execute compilation
    return compiler.compile(source)


class DSLCompiler:
    """DSL Compiler"""
    
    def __init__(self, config: CompilerConfig):
        self.config = config
        self.preprocessor = Preprocessor(config)
        self.lexer = Lexer(config)
        self.parser = Parser(config)
        self.semantic_analyzer = SemanticAnalyzer(config)
        self.llm_augmentor = LLMAugmentor(config) if config.llm_enabled else None
        self.validator = Validator(config)
        self.optimizer = Optimizer(config)
        self.serializer = Serializer(config)
    
    def compile(self, source: Union[str, Path]) -> DSLOutput:
        """Compile source code"""
        start_time = time.time()
        
        try:
            # Parse source code
            if isinstance(source, Path) or os.path.isfile(str(source)):
                source_path = Path(source)
                if source_path.stat().st_size > self.config.max_file_size:
                    raise CompilerError(f"File size exceeds limit: {self.config.max_file_size} bytes")
                
                with open(source_path, 'r', encoding='utf-8') as f:
                    source_content = f.read()
                
                context = ParseContext(source_file=str(source_path))
            else:
                source_content = str(source)
                context = ParseContext()
            
            # Check timeout
            if time.time() - start_time > self.config.parse_timeout:
                raise TimeoutError("Compilation timeout", self.config.parse_timeout, "compile")
            
            # 1. Preprocessing
            logger.info("Starting preprocessing...")
            preprocessed_content = self.preprocessor.process(source_content, context)
            
            # 2. Lexical analysis
            logger.info("Starting lexical analysis...")
            tokens = self.lexer.tokenize(preprocessed_content, context)
            
            # 3. Syntax analysis
            logger.info("Starting syntax analysis...")
            ast = self.parser.parse(tokens, context)
            
            # 4. Semantic analysis
            logger.info("Starting semantic analysis...")
            analyzed_ast = self.semantic_analyzer.analyze(ast, context)
            
            # 5. LLM enhancement (if enabled)
            if self.llm_augmentor and self._needs_llm_augmentation(analyzed_ast):
                logger.info("Starting LLM enhancement...")
                analyzed_ast = self.llm_augmentor.augment(analyzed_ast, context)
            
            # 6. Validation
            logger.info("Starting validation...")
            validation_errors = self.validator.validate(analyzed_ast, context)
            if validation_errors and self.config.strict_mode:
                error_messages = [str(error) for error in validation_errors]
                raise CompilerError(f"Validation failed: {'; '.join(error_messages)}")
            
            # 7. Optimization
            logger.info("Starting optimization...")
            optimized_ast = self.optimizer.optimize(analyzed_ast, context)
            
            # 8. Serialization
            logger.info("Starting serialization...")
            dsl_output = self.serializer.serialize(optimized_ast, context)
            
            # Set compilation information
            dsl_output.compiler_version = "1.0.0"
            if context.source_file:
                dsl_output.source_files = [context.source_file]
            
            compilation_time = time.time() - start_time
            logger.info(f"Compilation completed in {compilation_time:.2f}s")
            
            return dsl_output
            
        except Exception as e:
            if isinstance(e, CompilerError):
                raise
            else:
                raise CompilerError(f"Error occurred during compilation: {str(e)}")
    
    def _needs_llm_augmentation(self, ast: Any) -> bool:
        """Determine if LLM enhancement is needed"""
        if not self.config.llm_enabled:
            return False
        
        # Check if there's natural language content that needs LLM processing
        # This logic needs to be adjusted based on AST structure
        return True  # Temporarily return True, specific implementation needs AST structure adjustment
    
    def compile_to_file(self, source: Union[str, Path], output_path: Path) -> None:
        """Compile and output to file"""
        dsl_output = self.compile(source)
        
        # Determine output format based on file extension
        suffix = output_path.suffix.lower()
        if suffix == '.yaml' or suffix == '.yml':
            content = dsl_output.to_yaml()
        elif suffix == '.json':
            content = dsl_output.to_json(compact=self.config.compact_mode)
        else:
            # Use configured format by default
            if self.config.output_format == 'json':
                content = dsl_output.to_json(compact=self.config.compact_mode)
            else:
                content = dsl_output.to_yaml()
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Compilation result saved to: {output_path}")
    
    def validate_syntax(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Validate syntax only, without full compilation"""
        try:
            # Execute only up to syntax analysis phase
            if isinstance(source, Path) or os.path.isfile(str(source)):
                with open(source, 'r', encoding='utf-8') as f:
                    source_content = f.read()
                context = ParseContext(source_file=str(source))
            else:
                source_content = str(source)
                context = ParseContext()
            
            preprocessed_content = self.preprocessor.process(source_content, context)
            tokens = self.lexer.tokenize(preprocessed_content, context)
            ast = self.parser.parse(tokens, context)
            
            return {
                "valid": True,
                "message": "Syntax validation passed",
                "ast": ast
            }
            
        except CompilerError as e:
            return {
                "valid": False,
                "message": str(e),
                "error": e
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Syntax validation failed: {str(e)}",
                "error": e
            } 