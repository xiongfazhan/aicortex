# AICortex 快速开始

## 安装

```bash
cd /path/to/aicortex
pip install -e .
```

## 设置 API Key

### 方式 1: 环境变量
```bash
# Linux/Mac
export OPENAI_API_KEY=sk-xxx

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-xxx"

# Windows (CMD)
set OPENAI_API_KEY=sk-xxx
```

### 方式 2: .env 文件
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 方式 3: 配置文件
```bash
mkdir -p ~/.config/aicortex
cp config.example.yaml ~/.config/aicortex/config.yaml
# 编辑配置文件
```

## 使用方式

### 1. CLI 模式 - 单次查询

```bash
# 基本使用
aicortex "你好，请介绍一下 Python"

# 指定模型
aicortex -m openai:gpt-4 "写一个快速排序"

# 使用角色
aicortex --role programmer "解释这段代码"

# 禁用流式输出
aicortex --no-stream "分析这段文本"

# 包含文件
aicortex --file code.py "解释这个文件"

# 使用环境变量中的 API Key
API_KEY=sk-xxx aicortex "Hello"
```

### 2. REPL 模式 - 交互式对话

```bash
# 启动 REPL
aicortex

# 在 REPL 中可用命令:
.help                  # 显示帮助
.info                  # 显示系统信息
.model                 # 查看当前模型
.model openai:gpt-4    # 切换模型
.role                  # 列出所有角色
.role programmer       # 切换到程序员角色
.prompt                # 设置临时提示
.session chat          # 切换会话
.set temperature=0.7   # 设置参数
.exit                  # 退出 REPL
```

### 3. 加载配置文件

配置文件位置: `~/.config/aicortex/config.yaml`

```yaml
# 设置默认模型
model_id: openai:gpt-3.5-turbo

# 设置参数
temperature: 0.7
stream: true

# 配置多个客户端
clients:
  - type: openai
    api_key: ${OPENAI_API_KEY}
    models:
      - name: gpt-3.5-turbo
      - name: gpt-4

  - type: claude
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - name: claude-3-sonnet
```

### 4. 与 OpenAI 兼容模型对话

支持所有 OpenAI 兼容的 API:

```bash
# DeepSeek
export DEEPSEEK_API_KEY=xxx
aicortex -m deepseek:deepseek-chat "你好"

# Groq
export GROQ_API_KEY=xxx
aicortex -m groq:llama3-70b-8192 "你好"

# 使用通用 OpenAI 兼容接口
export API_KEY=xxx
export API_BASE=https://api.deepseek.com/v1
aicortex -m openai:gpt-3.5-turbo "你好"
```

### 5. 文本切分测试

运行测试脚本:

```bash
python test_usage.py
```

或手动测试:

```python
from aicortex.rag.splitter import RecursiveCharacterTextSplitter, RagDocument

# 准备文本
text = """
Python 是一种编程语言。它有简单的语法。
Java 也是一种编程语言。它是面向对象的。
"""

# 创建切分器
splitter = RecursiveCharacterTextSplitter(
    chunk_size=50,      # 每块最大字符数
    chunk_overlap=10,   # 块之间重叠
)

# 切分
documents = [RagDocument(path="test.txt", content=text)]
chunks = splitter.split_documents(documents)

for i, chunk in enumerate(chunks):
    print(f"块 {i+1}: {chunk.content}")
```

## 命令行选项

```
选项:
  -m, --model <模型>      指定模型 (例如: openai:gpt-4)
  --role <角色>           使用指定角色
  --session <会话>        指定会话名称
  --rag <RAG>            使用 RAG 检索
  --agent <Agent>        使用 Agent
  -e, --execute          执行 shell 模式
  -c, --code             代码模式
  --serve <地址>         启动 HTTP 服务器
  --no-stream            禁用流式输出
  --dry-run              干运行模式
  --list-models          列出所有模型
  --list-roles           列出所有角色
  --list-sessions        列出所有会话
  --list-rags            列出所有 RAG
  --list-agents          列出所有 Agent
  --info                 显示配置信息
  -f, --file <文件>      包含文件内容
  -h, --help             显示帮助
```

## 角色

内置角色:
- `default` - 默认助手
- `programmer` - 编程专家
- `shell` - Shell 命令专家
- `translate` - 翻译专家

自定义角色放在 `~/.config/aicortex/roles/` 目录:
```markdown
---
description: 我的自定义角色
temperature: 0.7
model: openai:gpt-4
---

你是一个专业的 xxx...
```

## 示例

### 对话示例
```bash
$ aicortex
> .role programmer
> 写一个 Python 函数计算斐波那契数列

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### 文件分析
```bash
aicortex --file main.py --file utils.py "重构这段代码"
```

### 多轮对话
```bash
$ aicortex --session mychat
> 什么是 Python?
Python 是一种...
> 它有什么特点?
[使用会话历史继续对话]
```

## 故障排除

### 1. API Key 错误
```
Error: API key not found
```
解决: 设置环境变量或配置文件中的 API Key

### 2. 模块未找到
```
ModuleNotFoundError: No module named 'xxx'
```
解决: 运行 `pip install -e .` 安装依赖

### 3. 权限错误
```
Permission denied
```
解决: 使用虚拟环境或 sudo

## 更多信息

- 完整文档: README.md
- 配置示例: config.example.yaml
- 模型列表: models.yaml
- 测试脚本: test_usage.py
