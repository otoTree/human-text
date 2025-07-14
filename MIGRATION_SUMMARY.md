# 项目迁移总结

## 概述

本项目已成功迁移到使用 `uv` 进行环境管理，并将 `dsl_compiler` 作为单独的包在根目录进行管理。

## 主要变化

### 1. 项目结构调整

**之前的结构**：
```
human-text/
├── dsl_compiler/
│   ├── requirements.txt
│   ├── setup.py
│   └── ... (其他文件)
├── example/
└── README.md
```

**现在的结构**：
```
human-text/
├── pyproject.toml              # 项目配置和依赖管理
├── .pre-commit-config.yaml     # 代码质量检查配置
├── .gitignore                  # Git 忽略文件
├── DEVELOPMENT.md              # 开发指南
├── test_setup.py               # 项目设置验证脚本
├── dsl_compiler/               # DSL 编译器包
│   └── ... (所有原有文件)
├── example/                    # 示例文件
└── README.md                   # 项目文档
```

### 2. 依赖管理

- **删除的文件**：
  - `dsl_compiler/requirements.txt`
  - `dsl_compiler/setup.py` 
  - `dsl_compiler/pyproject.toml` (临时创建的)

- **新增的文件**：
  - `pyproject.toml` (根目录)
  - `.pre-commit-config.yaml`
  - `.gitignore`
  - 镜像源配置（在 `pyproject.toml` 的 `[tool.uv]` 部分）

### 3. Python 版本要求

- **之前**：Python 3.8+
- **现在**：Python 3.12+

### 4. 包管理工具

- **之前**：pip + requirements.txt
- **现在**：uv + pyproject.toml

### 5. 镜像源配置

- **新增**：镜像源配置（在 `pyproject.toml` 的 `[tool.uv]` 部分）
- **支持的镜像源**：
  - 清华大学镜像（主要）
  - 阿里云镜像
  - 腾讯云镜像
  - 百度镜像
  - 豆瓣镜像
- **优化特性**：
  - 自动重试机制
  - 并发下载支持
  - 网络超时设置

## 新的开发流程

### 环境设置

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/otoTree/human-text.git
cd human-text

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 安装开发模式
uv pip install -e .

# 安装 pre-commit hooks
uv run pre-commit install
```

### 常用命令

```bash
# 添加依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 运行 CLI
uv run dslc input.txt -o output.yaml

# 运行测试
uv run pytest

# 代码格式化
uv run black .
uv run isort .
uv run ruff check --fix .

# 类型检查
uv run mypy dsl_compiler/
```

## 配置文件详解

### pyproject.toml

包含了以下配置：

- **项目元信息**：名称、版本、描述、作者等
- **依赖管理**：运行时依赖、开发依赖、可选依赖
- **构建系统**：使用 setuptools
- **工具配置**：black、ruff、mypy、pytest、coverage 等

### .pre-commit-config.yaml

配置了以下代码质量检查：

- **基础检查**：尾部空白、文件结尾、YAML/JSON 格式等
- **代码格式化**：black、isort
- **代码检查**：ruff、mypy、bandit
- **升级检查**：pyupgrade（Python 3.12+）
- **文档格式化**：docformatter
- **测试运行**：pytest

## 依赖项对比

### 核心依赖

- `pydantic>=2.0.0`
- `ruamel.yaml>=0.17.0`
- `python-dotenv>=1.0.0`
- `typer>=0.9.0`
- `rich>=13.0.0`
- `aiohttp>=3.8.0`

### 开发依赖

- **测试**：pytest、pytest-asyncio、pytest-cov、pytest-mock
- **代码质量**：black、ruff、mypy、isort
- **安全检查**：bandit
- **Git hooks**：pre-commit
- **文档**：sphinx、sphinx-rtd-theme

## 迁移验证

运行以下命令验证迁移是否成功：

```bash
# 验证项目设置
python test_setup.py

# 验证基本功能
uv run dslc example/test_input.txt -o test_output.yaml

# 验证代码质量检查
uv run pre-commit run --all-files
```

## 兼容性说明

### 向后兼容

- 所有原有的 Python 代码保持不变
- API 接口保持不变
- 配置文件格式保持不变

### 不兼容的变化

- **Python 版本**：现在需要 Python 3.12+
- **安装方式**：不再使用 pip install -r requirements.txt
- **开发工具**：需要使用 uv 进行依赖管理

## 优势

### 使用 uv 的好处

1. **更快的依赖解析**：uv 比 pip 快 10-100 倍
2. **更好的依赖锁定**：自动生成 uv.lock 文件
3. **统一的工具链**：构建、测试、运行都使用同一工具
4. **更好的虚拟环境管理**：自动创建和管理虚拟环境

### 项目结构的好处

1. **集中管理**：所有配置都在根目录
2. **清晰的包结构**：dsl_compiler 作为独立包
3. **现代化的配置**：使用 pyproject.toml 标准
4. **完整的开发工具链**：pre-commit、代码格式化、测试覆盖率等

## 注意事项

1. **Python 版本**：确保使用 Python 3.12 或更高版本
2. **uv 安装**：确保已安装 uv 包管理器
3. **环境变量**：原有的环境变量配置保持不变
4. **文档更新**：README.md 和 DEVELOPMENT.md 已更新

## 下一步

1. 更新 CI/CD 配置以使用 uv
2. 添加更多的测试用例
3. 完善文档
4. 考虑添加 Docker 支持 