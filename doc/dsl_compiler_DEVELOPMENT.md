# Development Guide

This guide covers how to develop, test, and contribute to the Human-Text DSL Compiler.

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- [uv](https://docs.astral.sh/uv/) package manager

### Environment Setup

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/supercontext/dsl-compiler.git
cd dsl-compiler

# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .

# Install pre-commit hooks
uv run pre-commit install
```

### Development Dependencies

All development dependencies are automatically installed with `uv sync`. The main development tools include:

- pytest, pytest-asyncio, pytest-cov (testing)
- black, ruff (code formatting and linting)
- mypy (type checking)
- pre-commit (git hooks)
- sphinx, sphinx-rtd-theme (documentation)

### Working with uv

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Run commands in the virtual environment
uv run python script.py
uv run pytest
uv run black .
```

## Code Structure

### Architecture Overview

```
src/dsl_compiler/
├── __init__.py           # Public API
├── config.py             # Configuration management
├── compiler.py           # Main compiler orchestration
├── preprocessor.py       # Text preprocessing
├── lexer.py              # Tokenization
├── parser.py             # AST construction
├── semantic_analyzer.py  # Semantic validation
├── llm_augmentor.py      # LLM integration
├── validator.py          # Validation rules
├── optimizer.py          # Code optimization
├── serializer.py         # Output generation
├── cli.py                # Command-line interface
├── models.py             # Data models
└── exceptions.py         # Exception hierarchy
```

### Key Components

1. **Compiler Pipeline**: `Preprocessor` → `Lexer` → `Parser` → `SemanticAnalyzer` → `LLMAugmentor` → `Validator` → `Optimizer` → `Serializer`

2. **Data Models**: Pydantic models for type safety and validation

3. **Configuration**: Environment-based configuration with validation

4. **Error Handling**: Comprehensive exception hierarchy with context

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/dsl_compiler --cov-report=html

# Run specific test file
python -m pytest tests/test_compiler.py

# Run with verbose output
python -m pytest -v

# Run async tests
python -m pytest tests/test_llm_augmentor.py -v
```

### Test Structure

```
tests/
├── test_compiler.py      # End-to-end compilation tests
├── test_lexer.py         # Tokenization tests
├── test_parser.py        # Parsing tests
├── test_models.py        # Data model tests
├── test_cli.py           # CLI tests
├── fixtures/             # Test data files
│   ├── simple.txt
│   ├── complex.txt
│   └── invalid.txt
└── conftest.py           # Test configuration
```

### Writing Tests

```python
import pytest
from dsl_compiler import compile, CompilerConfig
from dsl_compiler.exceptions import CompilerError

def test_basic_compilation():
    """Test basic compilation functionality"""
    source = """
    @task example
        This is a test task
    """
    
    config = CompilerConfig(llm_enabled=False)
    result = compile(source, config)
    
    assert len(result.tasks) == 1
    assert result.tasks[0].id == "example"

@pytest.mark.asyncio
async def test_llm_integration():
    """Test LLM integration"""
    # Test LLM functionality
    pass
```

## Code Quality

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Run flake8
flake8 src/ tests/

# Configuration in setup.cfg or .flake8
```

### Type Checking

```bash
# Run mypy
mypy src/dsl_compiler

# Configuration in mypy.ini or pyproject.toml
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Adding New Features

### 1. Adding New Directives

To add a new directive (e.g., `@workflow`):

1. **Update Lexer** (`lexer.py`):
   ```python
   def _parse_workflow_directive(self, directive_text: str) -> dict:
       # Parse workflow directive
       pass
   ```

2. **Update Parser** (`parser.py`):
   ```python
   def _parse_workflow_directive(self, directive_text: str, token: Token) -> ASTNode:
       # Create workflow AST node
       pass
   ```

3. **Update Models** (`models.py`):
   ```python
   class WorkflowNode(BaseModel):
       """Workflow node model"""
       pass
   ```

4. **Update Serializer** (`serializer.py`):
   ```python
   def _convert_workflow_node(self, node: ASTNode, context: ParseContext) -> WorkflowNode:
       # Convert AST to workflow node
       pass
   ```

### 2. Adding New Output Formats

To add a new output format (e.g., XML):

1. **Update Serializer** (`serializer.py`):
   ```python
   def _format_xml(self, dsl_output: DSLOutput) -> str:
       """Format as XML"""
       pass
   
   # Register in __init__
   self.formatters["xml"] = self._format_xml
   ```

2. **Update Configuration** (`config.py`):
   ```python
   # Add to valid formats
   output_format: str = Field(default="yaml", description="Output format: yaml, json, proto, xml")
   ```

### 3. Adding New LLM Providers

To add a new LLM provider:

1. **Update LLM Augmentor** (`llm_augmentor.py`):
   ```python
   async def _call_new_provider(self, prompt: str) -> str:
       """Call new LLM provider"""
       pass
   ```

2. **Update Configuration** (`config.py`):
   ```python
   # Add to valid providers
   if self.llm_provider not in ["dashscope", "openai", "context_service", "new_provider"]:
   ```

## Debugging

### Debug Mode

```bash
# Enable debug mode
export DSL_DEBUG=true

# Run with debug output
python -m dsl_compiler.cli input.txt --debug
```

### Logging

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use in code
logger.debug("Debug message")
logger.info("Info message")
```

### Common Issues

1. **Import Errors**: Check Python path and virtual environment
2. **Test Failures**: Ensure all dependencies are installed
3. **LLM Errors**: Verify API keys and network connectivity
4. **Performance Issues**: Use profiling tools like `cProfile`

## Performance Optimization

### Profiling

```bash
# Profile code execution
python -m cProfile -o profile.stats your_script.py

# Analyze results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### Memory Usage

```bash
# Monitor memory usage
python -m memory_profiler your_script.py
```

### Optimization Guidelines

1. **Avoid Premature Optimization**: Profile first
2. **Cache Expensive Operations**: Use `@lru_cache` for pure functions
3. **Minimize Object Creation**: Reuse objects when possible
4. **Use Generators**: For large datasets
5. **Async Operations**: For I/O-bound tasks

## Documentation

### API Documentation

```bash
# Generate documentation
cd docs/
make html

# Or with sphinx directly
sphinx-build -b html source build
```

### Docstring Style

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When parameter is invalid
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Release Process

### Version Bumping

1. Update version in `__init__.py`
2. Update version in `setup.py`
3. Update `CHANGELOG.md`
4. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`

### Publishing

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run test suite: `python -m pytest`
5. Run code quality checks: `black src/ && flake8 src/ && mypy src/`
6. Commit changes: `git commit -m "Add new feature"`
7. Push branch: `git push origin feature/new-feature`
8. Create pull request

### Code Review Guidelines

- Code should be well-documented
- All tests should pass
- Code coverage should not decrease
- Follow existing code style
- Add tests for new functionality

## Support

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check README and inline documentation
- **Email**: Contact team@supercontext.ai for support 