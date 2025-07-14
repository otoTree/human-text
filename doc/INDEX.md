# 文档索引

本目录包含 Human-Text DSL Compiler 项目的所有详细文档。

## 📚 文档列表

### 🚀 开发相关文档

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - 项目开发指南
  - 环境设置、开发工具链、代码规范
  - 测试策略、构建流程、镜像源配置

- **[dsl_compiler_DEVELOPMENT.md](dsl_compiler_DEVELOPMENT.md)** - DSL 编译器开发文档
  - 编译器内部架构和开发细节

### 📦 包文档

- **[dsl_compiler_README.md](dsl_compiler_README.md)** - DSL 编译器包的详细说明
  - 编译器功能、API 文档、使用示例

### 🔄 项目迁移和配置

- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)** - 项目迁移总结
  - 从传统工具链到 uv + pyproject.toml 的完整迁移记录
  - 项目结构调整、依赖管理变化

- **[CONFIG_FIX_SUMMARY.md](CONFIG_FIX_SUMMARY.md)** - 配置修复总结
  - 配置文件冲突解决过程
  - 最佳实践建议

- **[MIRROR_CONFIG.md](MIRROR_CONFIG.md)** - 镜像源配置说明
  - 国内镜像源配置详解
  - 网络优化和性能调优

### 🔧 重构记录

- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - 代码重构总结
  - 重构历史和架构改进记录

## 📖 如何使用这些文档

1. **新手入门**: 请先阅读项目根目录的 `README.md`，然后参考 `DEVELOPMENT.md`
2. **深入开发**: 查看 `dsl_compiler_README.md` 和 `dsl_compiler_DEVELOPMENT.md`
3. **了解变更**: 查看各种 SUMMARY 文档了解项目演进历史
4. **配置问题**: 参考 `CONFIG_FIX_SUMMARY.md` 和 `MIRROR_CONFIG.md`

## 📁 文档组织原则

- **根目录**: 只保留主要的 `README.md` 作为项目入口
- **doc 目录**: 包含所有详细文档和技术说明
- **命名规范**: 来自子目录的文档使用前缀区分（如 `dsl_compiler_`）

## 🔗 快速导航

- [返回项目根目录](../README.md)
- [开发环境设置](DEVELOPMENT.md)
- [项目迁移历史](MIGRATION_SUMMARY.md)
- [编译器文档](dsl_compiler_README.md) 