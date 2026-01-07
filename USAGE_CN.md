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

### 3. 运行测试

```bash
# 运行测试脚本
python test_usage.py
```

## 使用方式

### CLI 模式 - 单次查询

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
```

### REPL 模式 - 交互式对话

```bash
# 启动 REPL
aicortex

# 在 REPL 中可用命令:
> .help                  # 显示帮助
> .info                  # 显示系统信息
> .model                 # 查看当前模型
> .model openai:gpt-4    # 切换模型
> .role                  # 列出所有角色
> .role programmer       # 切换到程序员角色
> .set temperature=0.7   # 设置参数
> .language zh           # 切换到中文
> .language en           # 切换到英文
> .language auto         # 自动检测语言
> .exit                  # 退出 REPL
```

### 加载配置文件

配置文件位置: `~/.config/aicortex/config.yaml`

```bash
# 复制示例配置
mkdir -p ~/.config/aicortex
cp config.example.yaml ~/.config/aicortex/config.yaml

# 编辑配置文件
# 设置你的 API Key 和模型
```

### 与 OpenAI 兼容模型对话

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

### 文本切分测试

```python
from aicortex.rag.splitter import RecursiveCharacterTextSplitter, RagDocument, SplitterChunkHeaderOptions

# 准备文本
text = "Python 是一种编程语言..."

# 创建切分器
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,      # 每块最大字符数
    chunk_overlap=50,    # 块之间重叠
)

# 切分
documents = [RagDocument(page_content=text, metadata={"source": "test.txt"})]
header_options = SplitterChunkHeaderOptions(chunk_header="", chunk_overlap_header=None)
chunks = splitter.split_documents(documents, header_options)

for i, chunk in enumerate(chunks):
    print(f"块 {i+1}: {chunk.page_content}")
```

## 运行测试

完整测试脚本位于 `test_usage.py`，包含:

1. **文本切分测试** - 验证 RAG 文档分割功能
2. **配置加载测试** - 验证配置系统
3. **客户端创建测试** - 验证各种 LLM 客户端
4. **RAG 功能测试** - 验证向量检索数据结构
5. **OpenAI 对话测试** - 验证实际的 LLM 调用（需要 API Key）

```bash
# 运行所有测试
python test_usage.py

# 只测试文本切分
python -c "
import asyncio
from test_usage import test_text_splitting
asyncio.run(test_text_splitting())
"
```

## 项目结构

```
aicortex/
├── aicortex/                 # 主包
│   ├── __init__.py
│   ├── __main__.py         # 入口点
│   ├── cli.py              # CLI 定义
│   ├── llm.py              # LLM 核心模块
│   ├── agent.py            # Agent 系统
│   ├── function.py         # 函数调用
│   ├── serve.py            # HTTP 服务器
│   ├── client/             # 客户端模块
│   │   ├── openai.py
│   │   ├── claude.py
│   │   ├── gemini.py
│   │   ├── cohere.py
│   │   └── openai_compatible.py
│   ├── config/             # 配置模块
│   ├── rag/                # RAG 模块
│   │   └── splitter/        # 文档分割器
│   ├── render/             # 渲染模块
│   ├── repl/               # REPL 模块
│   └── utils/              # 工具模块
├── roles/                  # 内置角色
│   ├── default.md
│   ├── programmer.md
│   ├── shell.md
│   └── translate.md
├── test_usage.py          # 测试脚本
├── QUICKSTART.md          # 快速开始指南
├── config.example.yaml    # 配置示例
├── models.yaml           # 模型定义
├── .env.example          # 环境变量示例
├── pyproject.toml        # 项目配置
└── README.md             # 项目说明
```

## 故障排除

### Windows 编码问题

如果看到乱码，可以在命令行设置编码:

```bash
# Windows PowerShell
chcp 65001
python test_usage.py

# 或设置环境变量
$env:PYTHONIOENCODING="utf-8"
python test_usage.py
```

### API Key 错误

```
Error: API key not found
```
解决: 设置环境变量或配置文件中的 API Key

### 模块未找到

```
ModuleNotFoundError: No module named 'xxx'
```
解决: 运行 `pip install -e .` 安装依赖

## 下一步

- 查看 `QUICKSTART.md` 了解更多使用示例
- 查看 `README.md` 了解项目架构
- 查看 `config.example.yaml` 了解配置选项
- 运行 `python test_usage.py` 测试所有功能
