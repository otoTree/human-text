# Development Guide

This document provides comprehensive guidance for developing the Human-Text DSL Compiler.

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
git clone https://github.com/otoTree/human-text.git
cd human-text

# Create virtual environment and install dependencies
# 项目已配置国内镜像源，提供更快的下载速度
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .

# Install pre-commit hooks
uv run pre-commit install
```

### 镜像源配置

项目已内置国内镜像源配置（`pyproject.toml` 中的 `[tool.uv]` 部分），包含以下特性：

- **多镜像源支持**：主用清华镜像，备用阿里云、腾讯云、百度、豆瓣镜像
- **自动重试**：下载失败时自动重试 3 次
- **并发下载**：支持最多 8 个并发下载
- **超时设置**：60 秒超时，适应网络环境

#### 自定义镜像源

如需使用其他镜像源，可以：

1. **项目级别**：修改 `pyproject.toml` 中的 `[tool.uv]` 配置
2. **用户级别**：创建 `~/.config/uv/uv.toml`
3. **临时使用**：使用环境变量或命令行参数

```bash
# 临时使用特定镜像源
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple package-name

# 查看当前配置
uv pip config list
```

### Development Dependencies

All development dependencies are automatically installed with `uv sync`. The main development tools include:

- **Testing**: pytest, pytest-asyncio, pytest-cov, pytest-mock
- **Code Quality**: black, ruff, isort, mypy
- **Pre-commit Hooks**: pre-commit, bandit
- **Documentation**: sphinx, sphinx-rtd-theme

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

## Project Structure

```
human-text/
├── pyproject.toml              # Project configuration and dependencies
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── README.md                   # Main project documentation
├── DEVELOPMENT.md              # This file
├── LICENSE                     # License file
├── dsl_compiler/               # Main package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── compiler.py             # Main compiler logic
│   ├── config.py               # Configuration management
│   ├── models.py               # Data models
│   ├── lexer.py                # Lexical analyzer
│   ├── parser.py               # Parser
│   ├── semantic_analyzer.py    # Semantic analysis
│   ├── llm_augmentor.py        # LLM integration
│   ├── validator.py            # Validation logic
│   ├── optimizer.py            # Optimization passes
│   ├── serializer.py           # Output serialization
│   ├── preprocessor.py         # Input preprocessing
│   └── exceptions.py           # Custom exceptions
├── example/                    # Example files
│   ├── test_input.txt
│   └── test_inpu3t.json
└── tests/                      # Test files (to be created)
```

## Development Workflow

### 1. Code Style and Formatting

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Fast linting and formatting
- **isort**: Import sorting
- **MyPy**: Type checking

```bash
# Format code
uv run black .

# Sort imports
uv run isort .

# Lint code
uv run ruff check .
uv run ruff check --fix .

# Type checking
uv run mypy dsl_compiler/

# Run all formatting tools
uv run pre-commit run --all-files
```

### 2. Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dsl_compiler --cov-report=html

# Run specific test file
uv run pytest tests/test_compiler.py

# Run tests with specific markers
uv run pytest -m "not slow"
uv run pytest -m "unit"
uv run pytest -m "integration"
```

### 3. Running the CLI

```bash
# Basic usage
uv run dslc example/test_input.txt -o output.yaml

# With different formats
uv run dslc example/test_input.txt -f json -o output.json

# Validation only
uv run dslc validate example/test_input.txt

# Debug mode
uv run dslc example/test_input.txt --debug
```

### 4. Building and Distribution

```bash
# Build the package
uv build

# Install from local build
uv pip install dist/*.whl

# Clean build artifacts
rm -rf dist/ build/ *.egg-info/
```

## Configuration

### Environment Variables

The compiler can be configured using environment variables. Create a `.env` file in the root directory:

```env
# Core settings
DSL_OUTPUT_FORMAT=yaml
DSL_LLM_ENABLED=true
DSL_LLM_PROVIDER=dashscope

# LLM configuration
DSL_LLM_MODEL=qwen-turbo
DSL_LLM_API_KEY=your_api_key_here

# Performance settings
DSL_MAX_FILE_SIZE=10485760
DSL_PARSE_TIMEOUT=60

# Debug settings
DSL_DEBUG=false
DSL_LOG_LEVEL=INFO
```

### Configuration Options

See `dsl_compiler/config.py` for all available configuration options.

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- Lexer tests
- Parser tests
- Semantic analyzer tests
- Serializer tests

### Integration Tests

Test complete workflows:
- End-to-end compilation
- LLM integration
- File I/O operations

### Performance Tests

Test performance characteristics:
- Large file handling
- Memory usage
- Processing speed

## Debugging

### Debug Mode

Enable debug mode for detailed logging:

```bash
uv run dslc input.txt --debug
```

Or set environment variable:

```bash
export DSL_DEBUG=true
uv run dslc input.txt
```

### Common Issues

1. **LLM API Errors**: Check API key configuration
2. **Parsing Errors**: Verify input syntax
3. **Memory Issues**: Check file size limits
4. **Import Errors**: Ensure all dependencies are installed

## Contributing

### Code Review Process

1. Create a feature branch
2. Make changes with tests
3. Run pre-commit hooks
4. Submit pull request
5. Address review feedback

### Commit Messages

Follow conventional commit format:

```
feat: add new parsing feature
fix: resolve memory leak in optimizer
docs: update API documentation
test: add integration tests for CLI
```

### Pull Request Guidelines

- Include tests for new features
- Update documentation
- Ensure all CI checks pass
- Add changelog entry

## Architecture

### Compilation Pipeline

```
Input → Preprocessor → Lexer → Parser → Semantic Analyzer
                                         ↓
Output ← Serializer ← Optimizer ← Validator ← LLM Augmentor
```

### Key Components

1. **Preprocessor**: Cleans and normalizes input
2. **Lexer**: Tokenizes input into structured tokens
3. **Parser**: Builds Abstract Syntax Tree (AST)
4. **Semantic Analyzer**: Validates semantics and builds symbol table
5. **LLM Augmentor**: Enhances natural language with LLM
6. **Validator**: Validates DAG structure and references
7. **Optimizer**: Optimizes AST for performance
8. **Serializer**: Converts AST to output format

## Performance Optimization

### Profiling

```bash
# Profile the compiler
uv run python -m cProfile -o profile_output.prof -m dsl_compiler.cli input.txt

# View profiling results
uv run python -m pstats profile_output.prof
```

### Memory Optimization

- Use streaming for large files
- Implement lazy loading
- Optimize data structures

### Performance Tips

- Disable LLM for faster processing
- Use compact output format
- Enable optimization passes

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv pip install -r pyproject.toml
COPY . .
RUN uv pip install -e .

ENTRYPOINT ["uv", "run", "dslc"]
```

### Production Considerations

- Set appropriate timeout values
- Configure logging levels
- Monitor memory usage
- Cache LLM responses

## Future Enhancements

### Planned Features

1. **Visual Editor**: GUI for DSL editing
2. **Language Server**: IDE integration
3. **Plugin System**: Extensible architecture
4. **Additional Output Formats**: XML, TOML support
5. **Performance Improvements**: Parallel processing

### Technical Debt

- Improve error messages
- Add more comprehensive tests
- Optimize memory usage
- Enhance documentation

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Python 3.12 Features](https://docs.python.org/3.12/whatsnew/3.12.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Typer Documentation](https://typer.tiangolo.com/) 