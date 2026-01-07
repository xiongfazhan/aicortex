# AICortex 快速修复指南

## 问题已修复 ✅

之前的错误已经全部修复，应用现在可以正常使用 NVIDIA NIM API。

### 修复内容

#### 1. API Key 读取问题
- 添加了 `Config.get_client_config()` 方法来获取客户端配置
- 修改了 `cli.py` 和 `repl/mod.py` 来从配置文件中读取 API key
- 支持环境变量和配置文件中的 API key（包括 `${VAR}` 格式）

#### 2. NIM 客户端支持
- 更新了 `llm.py` 中的 `create_client()` 函数
- 添加了对 OpenAI 兼容提供商（nim, nvidia, deepseek, groq 等）的支持
- 自动使用正确的 API base URL

#### 3. Windows 编码问题
- 在 `cli.py`、`llm.py` 和 `repl/mod.py` 中添加了 UTF-8 编码修复
- 使用 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` 确保正确显示中文和 emoji

#### 4. 属性访问问题
修复了三个文件中 `model.client_name()` 被错误地作为方法调用的问题：
- `aicortex/cli.py` - 修复了 4 处
- `aicortex/repl/mod.py` - 修复了 4 处
- `aicortex/serve.py` - 修复了 2 处

将 `model.client_name()` 改为 `model.client_name`（去除括号），因为 `client_name` 是属性而不是方法。

## 重新安装

```bash
cd E:\kaifa\aicortex
pip install -e .
```

## 基本使用

### 1. 查看帮助
```bash
aicortex --help
```

### 2. 查看配置信息
```bash
aicortex --info
```

### 3. 列出可用模型
```bash
aicortex --list-models
```

### 4. 列出可用角色
```bash
aicortex --list-roles
```

## 使用示例

### 基本对话
```bash
# 简单对话
aicortex "你好"

# 指定模型
aicortex -m openai:gpt-4 "介绍一下 Python"

# 使用角色
aicortex --role programmer "写一个快速排序"
```

### 使用 NVIDIA NIM
```bash
# 设置 API Key
$env:NVIDIA_API_KEY="nvapi-xxx"

# 使用 Llama 3.1 70B
aicortex -m nim:meta/llama-3.1-70b-instruct "你好"

# 使用 Llama 3.1 405B
aicortex -m nim:meta/llama-3.1-405b-instruct "写一首诗"
```

### REPL 模式
```bash
# 启动交互式对话
aicortex

# REPL 命令
> .help                  # 显示帮助
> .info                  # 显示配置信息
> .model                 # 查看当前模型
> .model nim:meta/llama-3.1-70b-instruct  # 切换模型
> .role programmer       # 切换角色
> .exit                  # 退出
```

### 查看更多命令
```bash
aicortex --help
```

## 配置文件

配置文件位置: `C:\Users\<用户名>\.config\aicortex\config.yaml`

如果需要重新生成配置:
```bash
# 复制配置文件
mkdir C:\Users\<用户名>\.config\aicortex
copy config.yaml C:\Users\<用户名>\.config\aicortex\config.yaml

# 编辑配置文件，添加你的 API Key
notepad C:\Users\<用户名>\.config\aicortex\config.yaml
```

## 环境变量设置

### Windows PowerShell
```powershell
# 当前会话
$env:OPENAI_API_KEY="sk-xxx"
$env:NVIDIA_API_KEY="nvapi-xxx"

# 永久设置（系统环境变量）
# 1. 右键"此电脑" → "属性"
# 2. 点击"高级系统设置"
# 3. 点击"环境变量"
# 4. 在"用户变量"中添加:
#    变量名: NVIDIA_API_KEY
#    变量值: nvapi-xxx
```

## 常用命令

```bash
# CLI 模式 - 单次查询
aicortex "什么是 Python?"

# 指定模型
aicortex -m openai:gpt-4 "你好"

# 使用角色
aicortex --role programmer "解释这段代码"

# 禁用流式输出
aicortex --no-stream "分析这段文本"

# 包含文件
aicortex --file code.py "解释这个文件"

# 列出模型
aicortex --list-models

# 列出角色
aicortex --list-roles

# 显示配置信息
aicortex --info

# 启动 REPL
aicortex
```

## 支持的模型

### OpenAI
```bash
aicortex -m openai:gpt-3.5-turbo "你好"
aicortex -m openai:gpt-4 "你好"
aicortex -m openai:gpt-4o "你好"
```

### NVIDIA NIM
```bash
aicortex -m nim:meta/llama-3.1-405b-instruct "你好"
aicortex -m nim:meta/llama-3.1-70b-instruct "你好"
aicortex -m nim:meta/codellama-70b-instruct "写个函数"
```

### DeepSeek
```bash
aicortex -m deepseek:deepseek-chat "你好"
aicortex -m deepseek:deepseek-coder "写代码"
```

### Groq
```bash
aicortex -m groq:llama3-70b-8192 "你好"
aicortex -m groq:mixtral-8x7b-32768 "你好"
```

### Claude
```bash
aicortex -m claude:claude-3-sonnet "你好"
aicortex -m claude:claude-3-opus "你好"
```

## 验证安装

运行验证脚本:
```bash
python verify_fix.py
```

## 故障排除

### 问题: 命令未找到
```bash
# 确保 aicortex 已安装
pip install -e .

# 或使用完整命令
python -m aicortex "你好"
```

### 问题: API Key 未找到
```bash
# 设置环境变量
$env:OPENAI_API_KEY="sk-xxx"

# 或在配置文件中设置
# 编辑 C:\Users\<用户名>\.config\aicortex\config.yaml
```

### 问题: 模型未找到
```bash
# 检查可用模型
aicortex --list-models

# 确认模型名称格式正确
aicortex -m openai:gpt-3.5-turbo "你好"
```

## 下一步

- 查看 `NIM_GUIDE.md` - NVIDIA NIM 使用指南
- 查看 `CONFIG_GUIDE.md` - 配置文件指南
- 查看 `QUICKSTART.md` - 快速开始指南
- 运行 `python test_usage.py` - 完整功能测试
