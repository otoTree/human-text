# Mirror Source Configuration Guide

## Overview

为了提高中国大陆用户的下载速度，本项目已预配置了多个国内镜像源。通过 `pyproject.toml` 文件中的 `[tool.uv]` 配置，用户可以享受更快的依赖下载体验。

## 当前配置

### 主要镜像源

- **清华大学镜像**（主要）：https://pypi.tuna.tsinghua.edu.cn/simple
  - 由清华大学开源软件镜像站提供
  - 更新频率高，稳定性好
  - 支持 HTTPS，安全可靠

### 备用镜像源

当主要镜像源不可用时，系统会自动尝试以下备用源：

1. **阿里云镜像**：https://mirrors.aliyun.com/pypi/simple/
   - 阿里云提供，覆盖全国
   - 响应速度快

2. **腾讯云镜像**：https://mirrors.cloud.tencent.com/pypi/simple/
   - 腾讯云提供，稳定可靠
   - 适合腾讯云用户

3. **百度镜像**：https://mirror.baidu.com/pypi/simple/
   - 百度提供，历史悠久
   - 包覆盖度高

4. **豆瓣镜像**：https://pypi.douban.com/simple/
   - 豆瓣提供，社区广泛使用
   - 更新及时

## 配置详解

### pyproject.toml 中的 [tool.uv] 配置

```toml
[pip]
# 主要镜像源
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 备用镜像源
extra-index-url = [
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
    "https://mirror.baidu.com/pypi/simple/",
    "https://pypi.douban.com/simple/",
]

# 信任的主机
trusted-host = [
    "pypi.tuna.tsinghua.edu.cn",
    "mirrors.aliyun.com",
    "mirrors.cloud.tencent.com",
    "mirror.baidu.com", 
    "pypi.douban.com",
]

# 网络设置
timeout = 60
retries = 3

[tool.uv]
# 并发下载数
concurrent-downloads = 8
# 不使用系统站点包
system-site-packages = false
```

### 配置参数说明

- **index-url**：主要的包索引 URL
- **extra-index-url**：额外的包索引 URL（备用）
- **trusted-host**：信任的主机列表，允许 HTTP 连接
- **timeout**：网络请求超时时间（秒）
- **retries**：失败时的重试次数
- **concurrent-downloads**：并发下载的最大数量

## 使用方法

### 自动使用（推荐）

项目已配置好镜像源，直接使用 uv 命令即可：

```bash
# 安装依赖（自动使用配置的镜像源）
uv sync

# 添加新包（自动使用配置的镜像源）
uv add package-name
```

### 临时指定镜像源

如需临时使用特定镜像源：

```bash
# 使用清华镜像安装包
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple package-name

# 使用阿里云镜像安装包
uv pip install --index-url https://mirrors.aliyun.com/pypi/simple/ package-name
```

### 查看当前配置

```bash
# 查看 pip 配置
uv pip config list

# 查看 uv 配置
uv config show
```

## 自定义配置

### 修改项目配置

编辑项目根目录的 `pyproject.toml` 文件中的 `[tool.uv]` 部分：

```toml
[pip]
# 更改主要镜像源
index-url = "https://mirrors.aliyun.com/pypi/simple/"

# 添加或删除备用源
extra-index-url = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    # 添加其他镜像源...
]
```

### 用户级配置

创建用户级配置文件 `~/.config/uv/uv.toml`：

```toml
[pip]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
extra-index-url = [
    "https://mirrors.aliyun.com/pypi/simple/",
]
trusted-host = [
    "pypi.tuna.tsinghua.edu.cn",
    "mirrors.aliyun.com",
]
```

### 环境变量配置

通过环境变量临时设置：

```bash
# 设置主要镜像源
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# 设置额外镜像源
export UV_EXTRA_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"

# 使用配置
uv sync
```

## 性能优化

### 网络优化设置

```toml
[pip]
timeout = 60          # 适当的超时时间
retries = 3           # 重试次数

[tool.uv]
concurrent-downloads = 8    # 并发下载数（根据网络情况调整）
```

### 缓存优化

uv 会自动缓存下载的包，提高后续安装速度：

```bash
# 查看缓存位置
uv cache dir

# 清理缓存（如需要）
uv cache clean
```

## 故障排除

### 常见问题

1. **连接超时**
   ```bash
   # 增加超时时间
   uv pip install --timeout 120 package-name
   ```

2. **SSL 证书错误**
   ```bash
   # 使用 trusted-host（已在配置中设置）
   uv pip install --trusted-host pypi.tuna.tsinghua.edu.cn package-name
   ```

3. **包不存在**
   ```bash
   # 尝试官方源
   uv pip install --index-url https://pypi.org/simple/ package-name
   ```

### 测试镜像源

```bash
# 测试镜像源连通性
curl -I https://pypi.tuna.tsinghua.edu.cn/simple/

# 测试包下载
uv pip install --dry-run --index-url https://pypi.tuna.tsinghua.edu.cn/simple pydantic
```

### 切换回官方源

如需使用官方 PyPI 源：

```bash
# 临时使用官方源
uv pip install --index-url https://pypi.org/simple/ package-name

# 或者修改 pyproject.toml 中的 [tool.uv] 部分
[pip]
index-url = "https://pypi.org/simple/"
```

## 镜像源对比

| 镜像源 | 提供商 | 更新频率 | 速度 | 稳定性 | 推荐度 |
|--------|--------|----------|------|--------|--------|
| 清华大学 | 清华大学 | 5分钟 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 阿里云 | 阿里巴巴 | 5分钟 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 腾讯云 | 腾讯 | 10分钟 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 百度 | 百度 | 30分钟 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 豆瓣 | 豆瓣 | 30分钟 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 更多信息

- [uv 官方文档](https://docs.astral.sh/uv/)
- [清华大学镜像站](https://mirrors.tuna.tsinghua.edu.cn/)
- [阿里云镜像站](https://developer.aliyun.com/mirror/)
- [腾讯云镜像站](https://mirrors.cloud.tencent.com/) 