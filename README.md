<div align="center">

# AICortex

### Unified AI Intelligence Hub - All-in-one LLM CLI Tool

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A powerful, unified CLI interface for interacting with Large Language Models from multiple providers**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

[**English**](README.md) | [**中文文档**](README_CN.md)

</div>

---

## ✨ Overview

**AICortex** is a powerful LLM CLI tool that serves as a unified intelligence hub for interacting with multiple AI providers. It combines the simplicity of a command-line interface with the power of advanced AI capabilities like RAG, Agents, and function calling.

### Why AICortex?

AICortex offers a central hub for all your AI interactions with multiple providers:
- **Unified Interface** - One tool for OpenAI, Claude, Gemini, and more
- **Easy Integration** - Seamless integration with Python data science/ML stack
- **RAG & Agents** - Built-in retrieval-augmented generation and agent workflows
- **Highly Extensible** - Customize and extend with Python
- **Familiar Ecosystem** - Use your favorite Python tools

---

## 🚀 Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Provider Support** | OpenAI, Claude, Gemini, Cohere, Azure OpenAI, DeepSeek, Groq, Mistral, Perplexity, Together AI, Fireworks AI, and [NVIDIA NIM](https://build.nvidia.com/) |
| **OpenAI-Compatible APIs** | Support for 15+ providers with OpenAI-compatible interface |
| **RAG System** | Hybrid vector search (FAISS) + BM25 keyword retrieval with intelligent document splitting |
| **Function Calling** | Tool use and external command execution |
| **AI Agents** | Multi-step workflows with variable interpolation |
| **Interactive REPL** | 36 built-in commands with auto-completion and syntax highlighting |
| **Session Management** | Persistent conversations with smart compression |
| **Role System** | Customizable AI personas with temperature/prompt control |
| **HTTP Server** | FastAPI-based OpenAI-compatible API server |
| **Vision Support** | Multi-modal image understanding (vision-enabled models) |

### Advanced Features

- **Streaming Responses** - Real-time token streaming
- **Markdown Rendering** - Beautiful formatted output with syntax highlighting
- **Code Execution** - Safe shell command execution
- **File Operations** - Read files and directories directly in chat
- **Clipboard Integration** - Copy responses to clipboard
- **Cross-Platform** - Windows, macOS, Linux

---

## 📦 Installation

### Requirements

- Python 3.12 or higher
- pip or uv package manager

### Install from PyPI

```bash
pip install aicortex
```

### Install from Source

```bash
git clone https://github.com/xiongfazhan/aicortex.git
cd aicortex
pip install -e .
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

---

## 🎯 Quick Start

### 1. Configuration

Create your configuration file at `~/.config/aicortex/config.yaml`:

```yaml
# Default model
model_id: nim:mistralai/mistral-large-3-675b-instruct-2512

# Clients
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

### 2. Basic Usage

```bash
# Start interactive REPL
aicortex

# Single query
aicortex "What is Python?"

# Use specific model
aicortex -m openai:gpt-4 "Explain quantum computing"

# Use a role
aicortex --role programmer "Write a Fibonacci function"

# Include file in context
aicortex --file main.py "Refactor this code"

# Start HTTP server
aicortex --serve 127.0.0.1:8000
```

### 3. REPL Commands

```bash
aicortex

> .help                  # Show all commands
> .model                 # Show current model
> .model openai:gpt-4    # Switch model
> .role programmer       # Switch role
> .session my-chat       # Save/load session
> .language zh           # Switch to Chinese
> .language en           # Switch to English
> .language auto         # Auto-detect language
> .exit                  # Exit REPL
```

---

## 📖 Documentation

### Core Documents

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start (English) |
| [README_CN.md](README_CN.md) | 项目介绍和快速开始（中文） |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 项目结构和代码组织 |
| [FEATURES.md](FEATURES.md) | Feature parity with Rust version (91%) |
| [QUICKSTART.md](QUICKSTART.md) | Quick start tutorial |
| [CONFIG_GUIDE.md](CONFIG_GUIDE.md) | Detailed configuration guide |
| [NIM_GUIDE.md](NIM_GUIDE.md) | NVIDIA NIM integration guide |

### Supported Providers

| Provider | Models | Vision | Streaming |
|----------|--------|--------|-----------|
| **OpenAI** | GPT-4, GPT-4o, GPT-3.5 | ✅ | ✅ |
| **Claude** | Claude 3.5 Sonnet, Opus, Haiku | ✅ | ✅ |
| **Gemini** | Gemini 1.5 Pro | ✅ | ✅ |
| **NVIDIA NIM** | Llama 3.1 405B, Mistral Large | ❌ | ✅ |
| **DeepSeek** | DeepSeek Chat, Coder | ❌ | ✅ |
| **Groq** | Llama 3, Mixtral | ❌ | ✅ |
| **Cohere** | Command R/R+ | ❌ | ✅ |

### CLI Options

```bash
Options:
  -m, --model TEXT          Model to use (e.g., openai:gpt-4)
  --role TEXT               Role to use (e.g., programmer)
  -s, --session TEXT        Session name
  --prompt TEXT             Set prompt
  --rag TEXT                RAG name
  --agent TEXT              Agent name
  -e, --execute             Shell execute mode
  -c, --code                Code mode
  --serve TEXT              Start HTTP server
  --no-stream               Disable streaming
  --dry-run                 Dry run mode
  --list-models             List available models
  --list-roles              List available roles
  --info                    Show configuration
  --help                    Show help
```

### Environment Variables

```bash
# Global API key
export API_KEY="your-api-key"

# Provider-specific keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export NVIDIA_API_KEY="nvapi-..."
```

---

## 🔧 Configuration

### Config File Location

- **Linux/macOS**: `~/.config/aicortex/config.yaml`
- **Windows**: `C:\Users\<username>\.config\aicortex\config.yaml`

### Example Configuration

```yaml
# Basic settings
model_id: nim:mistralai/mistral-large-3-675b-instruct-2512
temperature: 0.7
top_p: 1.0
stream: true

# Client configuration
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

# RAG configuration (using NVIDIA NIM - free)
rag_embedding_model: nim:nvidia/nv-embedqa-e5-v5
rag_reranker_model: nim:nvidia/nv-rerankqa-mistral-4b-v3
rag_top_k: 5

# Appearance
highlight: true
theme: default
```

---

## 🎨 Roles

Create custom AI personas in `~/.config/aicortex/roles/`:

```markdown
---
name: Programmer
model_id: openai:gpt-4
temperature: 0.3
---

You are an expert programmer. You provide clean, efficient, well-documented code.
Always explain your solutions and follow best practices.
```

Use roles:

```bash
aicortex --role programmer "Write a binary search tree"
```

---

## 🔌 RAG (Retrieval-Augmented Generation)

### Index Documents

```bash
# Create a RAG index
aicortex --rag my-docs --add ./docs/*.md

# Query with RAG
aicortex --rag my-docs "What does the documentation say about X?"
```

### RAG Configuration

```yaml
# Using NVIDIA NIM (recommended, free)
rag_embedding_model: nim:nvidia/nv-embedqa-e5-v5
rag_reranker_model: nim:nvidia/nv-rerankqa-mistral-4b-v3
# Or use other providers:
# rag_embedding_model: openai:text-embedding-ada-002
# rag_reranker_model: cohere:rerank-english-v2.0
rag_top_k: 5
rag_chunk_size: 1000
rag_chunk_overlap: 200
```

---

## 🌐 HTTP Server

Start an OpenAI-compatible API server:

```bash
aicortex --serve 127.0.0.1:8000
```

### Usage with OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="nim:mistralai/mistral-large-3-675b-instruct-2512",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/xiongfazhan/aicortex.git
cd aicortex

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black aicortex/
ruff check aicortex/

# Type check
mypy aicortex/
```

### Project Structure

```
aicortex/
├── aicortex/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI interface
│   ├── llm.py               # LLM core
│   ├── config/              # Configuration management
│   ├── client/              # LLM clients
│   ├── repl/                # REPL implementation
│   ├── rag/                 # RAG system
│   ├── render/              # Output rendering
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under either of:

- MIT License ([LICENSE-MIT](LICENSE-MIT) or https://opensource.org/licenses/MIT)
- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or https://www.apache.org/licenses/LICENSE-2.0)

at your option.

---

## 🙏 Acknowledgments

This project is a Python rewrite of the original [**AIChat**](https://github.com/sigoden/aichat) by [sigoden](https://github.com/sigoden).

The original Rust implementation provides:
- Excellent performance and efficiency
- Cross-platform single binary distribution
- Minimal resource footprint

This Python version aims to provide feature parity while leveraging Python's ecosystem for easier customization and integration.

### Original AIChat (Rust)

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/sigoden/aichat?style=social)](https://github.com/sigoden/aichat)
[![GitHub issues](https://img.shields.io/github/issues/sigoden/aichat)](https://github.com/sigoden/aichat/issues)

**Check out the original**: [https://github.com/sigoden/aichat](https://github.com/sigoden/aichat)

</div>

---

## 📮 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/xiongfazhan/aicortex/issues)
- **Discussions**: [GitHub Discussions](https://github.com/xiongfazhan/aicortex/discussions)

---

<div align="center">

**Made with ❤️ by the AICortex community**

</div>
