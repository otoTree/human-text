# Human-Text DSL Compiler

A powerful compiler that converts human-readable text into structured DSL (Domain Specific Language), supporting both controlled scripts and natural language input with LLM enhancement.

## Features

- **Dual Input Modes**: 
  - Controlled scripts with explicit directives (`@task`, `@tool`, etc.)
  - Free-form natural language with LLM-powered structuring
  
- **Multi-format Output**: YAML, JSON, and Protocol Buffers
- **Advanced Processing**: Lexical analysis, semantic validation, optimization
- **LLM Integration**: Support for multiple LLM providers (DashScope, OpenAI, Context Service)
- **CLI & Library**: Both command-line tool and Python library interface
- **Structured Representation**: Complex conditionals, tool calls, agent invocations, and flow control

## Quick Start

### Installation

```bash
# Install from requirements
pip install -r requirements.txt

# Or install individual dependencies
pip install pydantic ruamel.yaml typer rich aiohttp python-dotenv
```

### Basic Usage

#### Python Library

```python
from dsl_compiler import compile, CompilerConfig

# Create configuration
config = CompilerConfig(
    llm_enabled=True,
    output_format="yaml"
)

# Compile a file
result = compile("input.txt", config)
print(result.to_yaml())

# Compile from string
source_code = """
@task data_processing
    Process user data from database
    Validate and clean the data
    Generate comprehensive report

@var user_id = 12345
@tool data_validator
    Tool for validating data integrity
"""

result = compile(source_code, config)
```

#### Command Line Interface

```bash
# Basic compilation
python -m dsl_compiler.cli input.txt -o output.yaml

# Different output formats
python -m dsl_compiler.cli input.txt -f json -o output.json

# Disable LLM for faster processing
python -m dsl_compiler.cli input.txt --no-llm

# Syntax validation only
python -m dsl_compiler.cli validate input.txt

# Show configuration
python -m dsl_compiler.cli config --show
```

## Syntax Guide

### Basic Directives

#### Task Definition
```
@task task_name
    Task description
    
    Detailed steps and instructions...
```

#### Variable Declaration
```
@var variable_name = value
@var user_id = 12345
@var debug_mode = true
@var config_file = "settings.json"
```

#### Tool Definition
```
@tool tool_name
    Tool description and usage instructions
```

#### Agent Invocation
```
@agent AgentName(param1=value1, param2=value2)
```

#### Flow Control
```
@next target_task

@if condition_expression
    Actions when condition is true
@else
    Actions when condition is false
@endif
```

### Advanced Features

#### Conditional Statements
```
@task order_validation
    Validate customer order
    
    @tool check_order
        Order validation tool
    
    @if result.valid == false
        Order is invalid, terminate process
        @next END
    @else
        Proceed with order processing
        @next process_payment
    @endif
```

#### Structured Output Example
The above compiles to:
```yaml
version: "1.0"
tasks:
  - id: order_validation
    title: Order validation
    body:
      - type: text
        content: "Validate customer order"
        line_number: 2
      - type: tool_call
        tool_call:
          name: check_order
          description: "Order validation tool"
        line_number: 4
      - type: conditional
        conditional:
          branches:
            - condition: "result.valid == false"
              actions:
                - type: text
                  content: "Order is invalid, terminate process"
                - type: jump
                  jump:
                    target: END
            - condition: null  # else branch
              actions:
                - type: text
                  content: "Proceed with order processing"
                - type: jump
                  jump:
                    target: process_payment
        line_number: 6
```

## Configuration

### Environment Variables

Copy `dsl_compiler.env.example` to `.env` and configure:

```bash
# Output format
DSL_OUTPUT_FORMAT=yaml

# LLM configuration
DSL_LLM_ENABLED=true
DSL_LLM_PROVIDER=dashscope
DSL_LLM_API_KEY=your_api_key_here
DSL_LLM_MODEL=qwen-turbo

# Performance settings
DSL_MAX_FILE_SIZE=10485760
DSL_PARSE_TIMEOUT=60

# Debug settings
DSL_DEBUG=false
DSL_LOG_LEVEL=INFO
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `output_format` | `yaml` | Output format (yaml/json/proto) |
| `llm_enabled` | `true` | Enable LLM enhancement |
| `llm_provider` | `dashscope` | LLM provider |
| `strict_mode` | `true` | Strict validation mode |
| `compact_mode` | `false` | Compact output format |
| `max_file_size` | `10MB` | Maximum file size |
| `parse_timeout` | `60s` | Parse timeout |

## LLM Integration

The compiler supports multiple LLM providers for natural language processing:

### DashScope (Alibaba Cloud)
```bash
export DSL_LLM_PROVIDER=dashscope
export DSL_LLM_API_KEY=your_dashscope_key
export DSL_LLM_MODEL=qwen-turbo
```

### OpenAI
```bash
export DSL_LLM_PROVIDER=openai
export DSL_LLM_API_KEY=your_openai_key
export DSL_LLM_MODEL=gpt-3.5-turbo
```

### Context Service (Internal)
```bash
export DSL_LLM_PROVIDER=context_service
export DSL_CONTEXT_SERVICE_URL=http://localhost:8001
```

## Architecture

The compiler follows a multi-stage pipeline:

```
Input Text → Preprocessor → Lexer → Parser → Semantic Analyzer
                                              ↓
Output ← Serializer ← Optimizer ← Validator ← LLM Augmentor
```

### Components

- **Preprocessor**: BOM removal, line normalization, tab expansion
- **Lexer**: Tokenization with indentation tracking
- **Parser**: AST construction with directive parsing
- **Semantic Analyzer**: Symbol table building, type checking, scope validation
- **LLM Augmentor**: Natural language enhancement (optional)
- **Validator**: DAG validation, reference checking, conflict detection
- **Optimizer**: Dead code elimination, constant folding, text compression
- **Serializer**: Multi-format output generation

## Output Formats

### YAML (Default)
```yaml
version: "1.0"
tasks:
  - id: "data_processing"
    title: "Data Processing Task"
    body:
      - type: "text"
        content: "Process user data"
        line_number: 2
```

### JSON
```json
{
  "version": "1.0",
  "tasks": [
    {
      "id": "data_processing",
      "title": "Data Processing Task",
      "body": [
        {
          "type": "text",
          "content": "Process user data",
          "line_number": 2
        }
      ]
    }
  ]
}
```

### Protocol Buffers
```proto
syntax = "proto3";
package dsl;

message DSLWorkflow {
  string version = 1;
  map<string, string> metadata = 2;
  repeated Task tasks = 3;
}
```

## Development

### Project Structure
```
src/dsl_compiler/
├── __init__.py          # Main interface
├── config.py            # Configuration management
├── compiler.py          # Main compiler logic
├── preprocessor.py      # Text preprocessing
├── lexer.py             # Lexical analyzer
├── parser.py            # Syntax parser
├── semantic_analyzer.py # Semantic analysis
├── llm_augmentor.py     # LLM enhancement
├── validator.py         # Validation engine
├── optimizer.py         # Code optimization
├── serializer.py        # Output serialization
├── cli.py               # Command-line interface
├── models.py            # Data models
├── exceptions.py        # Exception classes
└── requirements.txt     # Dependencies
```

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src/dsl_compiler tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Error Handling

The compiler provides detailed error information:

```python
from dsl_compiler import compile
from dsl_compiler.exceptions import CompilerError, ValidationError

try:
    result = compile("input.txt")
except ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Rule: {e.rule}")
    print(f"Suggestions: {e.suggestions}")
except CompilerError as e:
    print(f"Compilation error: {e}")
    print(f"File: {e.source_file}")
    print(f"Line: {e.line}")
```

## Performance Features

- **Dead Code Elimination**: Remove unreachable code blocks
- **Constant Folding**: Evaluate constant expressions at compile time
- **Text Compression**: Optimize text content while preserving meaning
- **Structure Optimization**: Flatten unnecessary nesting
- **Duplicate Removal**: Eliminate redundant definitions

## Troubleshooting

### Common Issues

1. **LLM Call Failures**
   - Check API key configuration
   - Verify network connectivity
   - Check LLM service status

2. **Parse Errors**
   - Validate directive format
   - Check file encoding (should be UTF-8)
   - Review detailed error messages

3. **Performance Issues**
   - Disable LLM with `--no-llm` flag
   - Reduce file size
   - Adjust timeout settings

### Debug Mode

```bash
# Enable debug output
python -m dsl_compiler.cli input.txt --debug

# Set environment variable
export DSL_DEBUG=true
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License

## Changelog

### v1.0.0
- Initial release
- Multi-format output support
- LLM integration
- Comprehensive validation
- CLI and library interfaces 