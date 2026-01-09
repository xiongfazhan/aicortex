<div align="center">

# AICortex

### 统一 AI 智能中枢 - 全能型 LLM 命令行工具

[![Python 版本](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.com/downloads/)
[![许可证](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-green.svg)](LICENSE)
[![代码风格](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**一个强大的、统一的命令行界面，用于与多个提供商的大语言模型交互**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [贡献](#-贡献)

[**English**](README.md) | [**中文文档**](README_CN.md)

</div>

---

## ✨ 项目概述

**AICortex** 是一个强大的 LLM 命令行工具，作为统一的 AI 智能中枢，支持与多个 AI 提供商交互。它结合了命令行界面的简洁性和强大的 AI 功能，如 RAG、Agent 和函数调用。

### 为什么选择 AICortex？

AICortex 为所有 AI 交互提供统一的中心枢纽：
- **统一接口** - 一个工具支持 OpenAI、Claude、Gemini 等
- **深度集成** - 与 Python 数据科学/ML 技术栈无缝集成
- **RAG & Agent** - 内置检索增强生成和智能体工作流
- **高度可扩展** - 使用 Python 轻松定制和扩展
- **熟悉的生态** - 使用你喜爱的 Python 工具

---

## 🚀 功能特性

### 核心能力

| 功能 | 描述 |
|---------|-------------|
| **多提供商支持** | OpenAI、Claude、Gemini、Cohere、Azure OpenAI、DeepSeek、Groq、Mistral、Perplexity、Together AI、Fireworks AI 和 [NVIDIA NIM](https://build.nvidia.com/) |
| **OpenAI 兼容 API** | 支持 15+ 个提供商的 OpenAI 兼容接口 |
| **RAG 系统** | 混合向量搜索 (FAISS) + BM25 关键词检索，智能文档分割 |
| **函数调用** | 工具使用和外部命令执行 |
| **AI 智能体** | 支持变量插值的多步骤工作流 |
| **交互式 REPL** | 36 个内置命令，支持自动补全和语法高亮 |
| **会话管理** | 持久化对话，智能压缩 |
| **角色系统** | 可定制的 AI 人格，支持温度/提示控制 |
| **HTTP 服务器** | 基于 FastAPI 的 OpenAI 兼容 API 服务器 |
| **视觉支持** | 多模态图像理解（支持视觉的模型） |

### 高级功能

- **流式响应** - 实时令牌流式传输
- **Markdown 渲染** - 美观的格式化输出和语法高亮
- **代码执行** - 安全的 Shell 命令执行
- **文件操作** - 在聊天中直接读取文件和目录
- **剪贴板集成** - 将响应复制到剪贴板
- **跨平台** - Windows、macOS、Linux

---

## 📦 安装

### 系统要求

- Python 3.12 或更高版本
- pip 或 uv 包管理器

### 从 PyPI 安装

```bash
pip install aicortex
```

### 从源码安装

```bash
git clone https://github.com/xiongfazhan/aicortex.git
cd aicortex
pip install -e .
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

---

## 🎯 快速开始

### 1. 配置

在 `~/.config/aicortex/config.yaml` 创建配置文件：

```yaml
# 默认模型
model_id: nim:mistralai/mistral-large-3-675b-instruct-2512

# 客户端配置
clients:
  - type: openai
    api_key: ${OPENAI_API_KEY}
    models:
      - name: gpt-4
        type: chat
        max_input_tokens: 8192

  - type: nim
    api_key: ${NVIDIA_API_KEY}
    api_base: https://integrate.api.nvidia.com/v1
    models:
      - name: meta/llama-3.1-405b-instruct
        type: chat
        max_input_tokens: 131072
```

### 2. 基本使用

```bash
# 启动交互式 REPL
aicortex

# 单次查询
aicortex "什么是 Python？"

# 使用指定模型
aicortex -m openai:gpt-4 "解释量子计算"

# 使用角色
aicortex --role programmer "写一个斐波那契函数"

# 包含文件到上下文
aicortex --file main.py "重构这段代码"

# 启动 HTTP 服务器
aicortex --serve 127.0.0.1:8000
```

### 3. REPL 命令

```bash
aicortex

> .help                  # 显示所有命令
> .model                 # 显示当前模型
> .model openai:gpt-4    # 切换模型
> .role programmer       # 切换角色
> .session my-chat       # 保存/加载会话
> .language zh           # 切换到中文
> .language en           # 切换到英文
> .language auto         # 自动检测语言
> .exit                  # 退出 REPL
```

---

## 📖 文档

### 核心文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目介绍和快速开始（英文） |
| [README_CN.md](README_CN.md) | 项目介绍和快速开始（中文） |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 项目结构和代码组织 |
| [FEATURES.md](FEATURES.md) | 与 Rust 版本的功能对照（91% 完成度） |
| [QUICKSTART.md](QUICKSTART.md) | 快速入门教程 |
| [CONFIG_GUIDE.md](CONFIG_GUIDE.md) | 详细配置指南 |
| [NIM_GUIDE.md](NIM_GUIDE.md) | NVIDIA NIM 集成指南 |

### 支持的提供商

| 提供商 | 模型 | 视觉 | 流式 |
|----------|--------|--------|-----------|
| **OpenAI** | GPT-4、GPT-4o、GPT-3.5 | ✅ | ✅ |
| **Claude** | Claude 3.5 Sonnet、Opus、Haiku | ✅ | ✅ |
| **Gemini** | Gemini 1.5 Pro | ✅ | ✅ |
| **NVIDIA NIM** | Llama 3.1 405B、Mistral Large | ❌ | ✅ |
| **DeepSeek** | DeepSeek Chat、Coder | ❌ | ✅ |
| **Groq** | Llama 3、Mixtral | ❌ | ✅ |
| **Cohere** | Command R/R+ | ❌ | ✅ |

### CLI 选项

```bash
选项:
  -f, --file TEXT          输入文件
  -m, --model TEXT          使用的模型 (如: openai:gpt-4)
  --role TEXT               使用的角色 (如: programmer)
  -s, --session TEXT        会话名称
  --prompt TEXT             设置提示
  --rag TEXT                RAG 名称
  --agent TEXT              智能体名称
  -e, --execute             Shell 执行模式
  -c, --code                代码模式
  --serve TEXT              启动 HTTP 服务器
  --no-stream               禁用流式输出
  --dry-run                 干运行模式
  --list-models             列出可用模型
  --list-roles              列出可用角色
  --list-sessions           列出可用会话
  --list-rags               列出可用 RAG
  --list-agents             列出可用智能体
  --info                    显示配置信息
  --help                    显示帮助
```

### 环境变量

```bash
# 全局 API Key
export API_KEY="your-api-key"

# 提供商特定的 API Key
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export NVIDIA_API_KEY="nvapi-..."
```

---

## 🔧 配置

### 配置文件位置

- **Linux/macOS**: `~/.config/aicortex/config.yaml`
- **Windows**: `C:\Users\<用户名>\.config\aicortex\config.yaml`

### 配置示例

```yaml
# 基本设置
model_id: nim:mistralai/mistral-large-3-675b-instruct-2512
temperature: 0.7
top_p: 1.0
stream: true

# 客户端配置
clients:
  - type: openai
    api_key: ${OPENAI_API_KEY}
    api_base: https://api.openai.com/v1
    models:
      - name: gpt-4
        type: chat
        max_input_tokens: 8192
        max_output_tokens: 4096
        supports_vision: true

  - type: azure_openai
    api_base: https://my-resource.openai.azure.com
    api_key: ${AZURE_OPENAI_API_KEY}
    models:
      - name: gpt-4
        id: gpt-4-deployment
        type: chat
        max_input_tokens: 8192

# RAG 配置
rag_embedding_model: nim:nvidia/nv-embedqa-e5-v5
rag_reranker_model: nim:nvidia/nv-rerankqa-mistral-4b-v3
rag_top_k: 5

# 外观设置
highlight: true
theme: default
```

---

## 🎨 角色系统

在 `~/.config/aicortex/roles/` 创建自定义 AI 人格：

```markdown
---
name: 程序员
model_id: openai:gpt-4
temperature: 0.3
---

你是一个专业的程序员。你提供简洁、高效、有良好文档的代码。
总是解释你的解决方案并遵循最佳实践。
```

使用角色：

```bash
aicortex --role programmer "写一个二叉搜索树"
```

---

## 🔌 RAG (检索增强生成)

### 索引文档

```bash
# 创建 RAG 索引
aicortex --rag my-docs --add ./docs/*.md

# 使用 RAG 查询
aicortex --rag my-docs "文档中关于 X 说了什么？"
```

### RAG 配置

```yaml
# 使用 NVIDIA NIM 模型（推荐，免费）
rag_embedding_model: nim:nvidia/nv-embedqa-e5-v5
rag_reranker_model: nim:nvidia/nv-rerankqa-mistral-4b-v3

# 或使用其他提供商
# rag_embedding_model: openai:text-embedding-ada-002
# rag_reranker_model: cohere:rerank-english-v2.0

rag_top_k: 5
rag_chunk_size: 1000
rag_chunk_overlap: 200
```

---

## 🌐 HTTP 服务器

启动 OpenAI 兼容的 API 服务器：

```bash
aicortex --serve 127.0.0.1:8000
```

### 使用 OpenAI 客户端

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="nim:mistralai/mistral-large-3-675b-instruct-2512",
    messages=[{"role": "user", "content": "你好！"}]
)
```

---

## 🧪 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/xiongfazhan/aicortex.git
cd aicortex

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 格式化代码
black aicortex/
ruff check aicortex/

# 类型检查
mypy aicortex/
```

### 项目结构

```
aicortex/
├── aicortex/
│   ├── __init__.py
│   ├── __main__.py          # 入口点
│   ├── cli.py               # CLI 接口
│   ├── llm.py               # LLM 核心
│   ├── config/              # 配置管理
│   ├── client/              # LLM 客户端
│   ├── repl/                # REPL 实现
│   ├── rag/                 # RAG 系统
│   ├── render/              # 输出渲染
│   └── utils/               # 工具函数
├── tests/                   # 测试套件
├── pyproject.toml           # 项目配置
└── README.md
```

---

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加某个很棒的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📜 许可证

本项目采用以下任一许可证：

- MIT 许可证 ([LICENSE-MIT](LICENSE-MIT) 或 https://opensource.org/licenses/MIT)
- Apache 许可证 2.0 版 ([LICENSE-APACHE](LICENSE-APACHE) 或 https://www.apache.org/licenses/LICENSE-2.0)

由你选择。

---

## 🙏 致谢

本项目是 [sigoden](https://github.com/sigoden) 的原始 [**AIChat**](https://github.com/sigoden/aichat) 项目的 Python 重写版本，项目名称改为 AICortex。

原始 Rust 实现提供：
- 卓越的性能和效率
- 跨平台单一二进制分发
- 最小的资源占用

本 Python 版本旨在提供功能对等，同时利用 Python 生态系统实现更简单的定制和集成。

### 原始 AIChat (Rust)

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/sigoden/aichat?style=social)](https://github.com/sigoden/aichat)
[![GitHub issues](https://img.shields.io/github/issues/sigoden/aichat)](https://github.com/sigoden/aichat/issues)

**查看原版**: [https://github.com/sigoden/aichat](https://github.com/sigoden/aichat)

</div>

---

## 📮 支持

- **文档**: [docs/](docs/)
- **问题反馈**: [GitHub Issues](https://github.com/xiongfazhan/aicortex/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/xiongfazhan/aicortex/discussions)

---

## 🗺️ 路线图

### 已完成 ✅
- [x] 多提供商支持
- [x] RAG 系统
- [x] 函数调用
- [x] AI 智能体
- [x] REPL 交互模式
- [x] HTTP 服务器

### 计划中 🚧
- [ ] 更多 LLM 提供商
- [ ] 图像生成支持
- [ ] 语音输入/输出
- [ ] 插件系统
- [ ] Web UI

---

<div align="center">

**由 AICortex 社区用 ❤️ 构建**

</div>
