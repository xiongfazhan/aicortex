# AICortex 使用说明

## 快速开始

### 1. 安装

```bash
cd E:\kaifa\aicortex
pip install -e .
```

### 2. 设置 API Key

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-xxx"

# Windows (CMD)
set OPENAI_API_KEY=sk-xxx

# Linux/Mac
export OPENAI_API_KEY=sk-xxx
```

### 3. 运行

```bash
aicortex "你好"
```

## 使用方式

### CLI 使用示例

```bash
# 基本使用
aicortex "你好，介绍一下 Python"

# 指定模型
aicortex -m openai:gpt-4 "写一个快速排序"

# 使用角色
aicortex --role programmer "解释这段代码"

# 关闭流式输出
aicortex --no-stream "分析这段文本"

# 包含文件
aicortex --file code.py "解释这个文件"

# 使用 RAG
aicortex --rag my-docs "总结文档里的关键点"

# 启动 HTTP 服务
aicortex --serve 127.0.0.1:8000
```

### CLI 参数说明

```text
-f, --file TEXT
  输入文件（可多次）

-m, --model TEXT
  使用的模型（如 openai:gpt-4）

--role TEXT
  使用的角色（如 programmer）

-s, --session TEXT
  会话名称

--prompt TEXT
  设置提示

--rag TEXT
  RAG 名称

--agent TEXT
  智能体名称

-e, --execute
  Shell 执行模式

-c, --code
  代码模式

--serve TEXT
  启动 HTTP 服务

--no-stream
  禁用流式输出

--dry-run
  干运行模式

--list-models
  列出可用模型

--list-roles
  列出可用角色

--list-sessions
  列出可用会话

--list-rags
  列出可用 RAG

--list-agents
  列出可用智能体

--info
  显示配置信息

--help
  显示帮助
```

### CLI 功能速查

```text
单次对话
  aicortex "你的问题"

指定模型
  aicortex -m openai:gpt-4 "你的问题"

指定角色
  aicortex --role programmer "解释这段代码"

会话管理
  aicortex -s my-session "继续会话"

RAG 检索
  aicortex --rag my-docs "查询文档"

Agent 模式
  aicortex --agent helper "开始对话"

Shell 执行
  aicortex -e "ls -la"

代码模式
  aicortex -c "写一个排序"

启动 HTTP 服务
  aicortex --serve 127.0.0.1:8000

列出资源
  aicortex --list-models
  aicortex --list-roles
  aicortex --list-sessions
  aicortex --list-rags
  aicortex --list-agents

显示配置信息
  aicortex --info
```

### REPL 使用示例

```text
# 启动 REPL
aicortex

# 帮助与信息
/help
/info

# 切换模型与角色
/model openai:gpt-4
/role programmer

# 会话管理
/session daily
/compress session
/save session

# RAG 使用
/rag my-docs
/edit rag-docs --add README.md
/rebuild rag
/sources rag

# 语言与运行时设置
/language zh
/set temperature=0.7

# 退出
/exit
```

### REPL 参数说明

```text
基础:
  /help
  /info
  /model <模型>
  /prompt <提示>
  /set <键>=<值>
  /language <zh|en|auto>
  /exit

角色:
  /role <名称>
  /info role
  /edit role
  /save role
  /exit role

会话:
  /session <名称>
  /empty session
  /compress session
  /info session
  /edit session
  /save session
  /exit session

RAG:
  /rag <名称>
  /edit rag-docs --list
  /edit rag-docs --add <路径...>
  /edit rag-docs --remove <文件ID...>
  /rebuild rag
  /sources rag
  /info rag
  /exit rag

输入:
  /file <路径|目录|URL>
  /continue
  /regenerate
  /copy

Agent:
  /agent <名称>
  /starter [<数字>|<文本>]
  /edit agent-config

宏:
  /macro [<宏名> [args...]]
```

## 加载配置文件

配置文件位置: `~/.config/aicortex/config.yaml`

```bash
# 复制示例配置
mkdir -p ~/.config/aicortex
cp config.example.yaml ~/.config/aicortex/config.yaml

# 编辑配置文件
# 设置你的 API Key 和模型
```

## 与 OpenAI 兼容模型对话

```bash
# DeepSeek
$env:DEEPSEEK_API_KEY="xxx"
aicortex -m deepseek:deepseek-chat "你好"

# Groq
$env:GROQ_API_KEY="xxx"
aicortex -m groq:llama3-70b-8192 "你好"

# 使用通用接口
$env:API_KEY="xxx"
$env:API_BASE="https://api.deepseek.com/v1"
aicortex "你好"
```

## 文本切分示例

```python
from aicortex.rag.splitter import RecursiveCharacterTextSplitter, RagDocument, SplitterChunkHeaderOptions

text = "Python 是一种编程语言..."

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
)

documents = [RagDocument(page_content=text, metadata={"source": "test.txt"})]
header_options = SplitterChunkHeaderOptions(chunk_header="", chunk_overlap_header=None)
chunks = splitter.split_documents(documents, header_options)

for i, chunk in enumerate(chunks):
    print(f"块 {i+1}: {chunk.page_content}")
```

## 故障排除

### Windows 编码问题

```bash
# Windows PowerShell
chcp 65001
```

### API Key 错误

```
Error: API key not found
```

解决: 设置环境变量或配置文件中的 API Key。

### 模块未找到

```
ModuleNotFoundError: No module named 'xxx'
```

解决: 解释器环境未安装依赖，运行 `pip install -e .`。

## 下一步

- 查看 `README.md` 了解项目概览
- 查看 `CONFIG_GUIDE.md` 了解配置项
- 查看 `config.example.yaml` 作为配置模板
