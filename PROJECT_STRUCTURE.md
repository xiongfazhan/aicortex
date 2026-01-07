# AICortex Python 项目结构

本文档描述 AICortex Python 项目的文件和目录组织。

## 目录结构

```
aicortex/
├── aicortex/                  # 主包目录
│   ├── __init__.py
│   ├── __main__.py           # 程序入口点
│   ├── cli.py                # CLI 定义
│   ├── llm.py                # LLM 接口
│   ├── agent.py              # Agent 系统
│   ├── function.py           # 函数调用
│   ├── serve.py              # HTTP 服务器
│   │
│   ├── client/               # 客户端模块
│   │   ├── mod.py            # 客户端接口
│   │   ├── message.py        # 消息定义
│   │   ├── model.py          # 模型管理
│   │   ├── stream.py         # 流式响应
│   │   ├── openai.py         # OpenAI 客户端
│   │   ├── claude.py         # Claude 客户端
│   │   ├── gemini.py         # Gemini 客户端
│   │   ├── cohere.py         # Cohere 客户端
│   │   ├── azure_openai.py   # Azure OpenAI 客户端
│   │   └── openai_compatible.py  # 兼容客户端
│   │
│   ├── config/               # 配置模块
│   │   ├── mod.py            # 配置核心
│   │   ├── role.py           # 角色系统
│   │   ├── session.py        # 会话管理
│   │   ├── agent.py          # Agent 配置
│   │   ├── input.py          # 输入处理
│   │   └── macro.py          # 宏系统
│   │
│   ├── repl/                 # REPL 模块
│   │   ├── mod.py            # REPL 核心（37 个命令）
│   │   ├── completer.py      # 自动补全
│   │   ├── highlighter.py    # 语法高亮
│   │   └── prompt.py         # 提示符渲染
│   │
│   ├── rag/                  # RAG 模块
│   │   ├── mod.py            # RAG 核心
│   │   ├── serde_vectors.py  # 向量序列化
│   │   ├── language.py       # 语言检测
│   │   └── splitter/         # 文档分割器
│   │       ├── mod.py
│   │       └── language.py
│   │
│   ├── render/               # 渲染模块
│   │   ├── mod.py            # 渲染核心
│   │   ├── markdown.py       # Markdown 渲染
│   │   └── stream.py         # 流式渲染
│   │
│   └── utils/                # 工具模块
│       ├── mod.py            # 工具汇总
│       ├── crypto.py         # 加密工具
│       ├── path.py           # 路径工具
│       ├── variables.py      # 变量处理
│       ├── clipboard.py      # 剪贴板
│       ├── abort_signal.py   # 中断信号
│       ├── command.py        # 命令执行
│       ├── html_to_md.py     # HTML 转换
│       ├── input.py          # 输入工具
│       ├── loader.py         # 文档加载
│       ├── render_prompt.py  # 提示符渲染
│       ├── request.py        # HTTP 请求
│       └── spinner.py        # 加载动画
│
├── assets/                   # 静态资源
├── roles/                    # 角色定义目录
│   ├── default.md
│   ├── programmer.md
│   ├── shell.md
│   └── translate.md
│
├── 文档
├── README.md                 # 英文文档
├── README_CN.md              # 中文文档
├── FEATURES.md               # 功能完成度对照
├── QUICKSTART.md             # 快速开始
├── CONFIG_GUIDE.md           # 配置指南
├── NIM_GUIDE.md              # NVIDIA NIM 使用指南
├── QUICK_FIX.md              # 快速修复指南
├── USAGE_CN.md               # 使用说明
├── PROJECT_STRUCTURE.md      # 本文档
│
├── 配置
├── config.example.yaml       # 配置示例
├── config.simple.yaml        # 简化配置示例
├── models.yaml               # 模型定义
├── .env.example              # 环境变量示例
│
├── pyproject.toml            # 项目配置
├── LICENSE-MIT               # MIT 许可证
├── LICENSE-APACHE            # Apache 许可证
└── .gitignore                # Git 忽略规则
```

## 模块说明

### 核心模块

| 模块 | 描述 | 代码行数 |
|------|------|----------|
| `aicortex/client/` | LLM 提供商客户端 | ~1,350 |
| `aicortex/config/` | 配置系统 | ~1,800 |
| `aicortex/repl/` | 交互式 REPL | ~1,300 |
| `aicortex/rag/` | 检索增强生成 | ~700 |
| `aicortex/render/` | 输出渲染 | ~300 |
| `aicortex/utils/` | 工具函数 | ~1,000 |

### 文档说明

| 文档 | 用途 |
|------|------|
| `README.md` | 项目介绍和快速开始（英文） |
| `README_CN.md` | 项目介绍和快速开始（中文） |
| `FEATURES.md` | 与 Rust 版本的功能对照表 |
| `QUICKSTART.md` | 快速入门教程 |
| `CONFIG_GUIDE.md` | 详细配置说明 |
| `NIM_GUIDE.md` | NVIDIA NIM 集成指南 |
| `QUICK_FIX.md` | 常见问题修复 |
| `USAGE_CN.md` | 使用说明（中文） |
| `PROJECT_STRUCTURE.md` | 项目结构说明（本文档） |

### 配置文件

| 文件 | 说明 |
|------|------|
| `config.example.yaml` | 完整配置示例 |
| `config.simple.yaml` | 简化配置示例 |
| `models.yaml` | 模型定义 |
| `.env.example` | 环境变量示例 |

**注意**：
- 用户应复制 `config.example.yaml` 为 `config.yaml` 并修改
- `config.yaml` 和 `.env` 在 `.gitignore` 中，不会提交到版本控制

## 测试文件

| 文件 | 说明 |
|------|------|
| `test_usage.py` | 功能测试和使用示例 |
| `verify_fix.py` | 快速验证脚本 |

## 开发指南

### 添加新客户端

1. 在 `aicortex/client/` 创建新文件（如 `bedrock.py`）
2. 继承 `Client` 基类并实现必需方法
3. 在 `aicortex/client/__init__.py` 中导出
4. 在 `CONFIG_GUIDE.md` 中添加配置说明

### 添加新命令

1. 在 `aicortex/repl/mod.py` 中添加 `_cmd_xxx()` 方法
2. 在 `_run_command()` 的 match 语句中添加 case
3. 在 `.dump_help()` 中添加帮助文本

### 添加新工具函数

1. 在 `aicortex/utils/` 创建新文件
2. 在 `aicortex/utils/__init__.py` 中导出
3. 添加必要的文档字符串

## 依赖关系

```
cli.py
  ├─> config/mod.py (Config)
  ├─> repl/mod.py (Repl)
  │   ├─> config/* (配置系统)
  │   ├─> client/* (LLM 客户端)
  │   ├─> render/* (渲染)
  │   └─> utils/* (工具)
  ├─> serve.py (HTTP 服务器)
  └─> llm.py (直接 LLM 调用)
```

## 总体完成度

**91%** - 核心功能完整，企业级扩展可选

详见 [FEATURES.md](FEATURES.md)
