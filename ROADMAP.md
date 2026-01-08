# AICortex 功能清单与使用指南

**项目**: AICortex - 统一 AI 智能中枢
**版本**: v0.9.1
**最后更新**: 2025-01-07
**仓库**: https://github.com/xiongfazhan/aicortex

---

## 📖 目录

1. [功能清单](#功能清单)
2. [快速开始](#快速开始)
3. [详细使用示例](#详细使用示例)
4. [配置指南](#配置指南)
5. [待优化项](#待优化项)
6. [开发计划](#开发计划)

---

## 功能清单

### ✅ 已实现功能（91% 完成度）

#### 1. LLM 客户端支持（6/8）

| 客户端 | 状态 | 说明 | 配置示例 |
|--------|------|------|----------|
| OpenAI | ✅ | GPT-4o, GPT-4o-mini | `openai:gpt-4o` |
| Claude | ✅ | Claude 3.5 Sonnet, Opus | `claude:claude-3-5-sonnet-20241022` |
| Gemini | ✅ | Gemini Pro, Flash | `gemini:gemini-2.0-flash-exp` |
| Cohere | ✅ | Command R, R+ | `cohere:command-r-plus-08-2024` |
| OpenAI Compatible | ✅ | 15+ 提供商 | `deepseek:deepseek-chat` |
| Azure OpenAI | ✅ | 企业级 Azure | `azure:gpt-4o` |

**支持的兼容提供商**:
- DeepSeek, Groq, Mistral, Perplexity, Together AI, Fireworks AI
- NVIDIA NIM, OpenRouter, Anthropic Claude, Google Gemini

#### 2. REPL 交互系统（38/38 命令）

**基本命令（6个）**:
```bash
.help                  # 显示帮助
.info                  # 显示系统信息
.model [name]           # 查看/切换模型
.role [name]            # 切换角色
.set key=value         # 设置参数
.language [zh|en|auto]  # 切换语言 ✨
.exit                  # 退出
```

**角色命令（6个）**:
```bash
.prompt [text]          # 临时角色提示
.role [name]            # 切换角色
.info role             # 显示角色信息
.edit role             # 修改角色
.save role             # 保存角色
.exit role             # 退出角色模式
```

**会话命令（6个）**:
```bash
.session [name]         # 启动/切换会话
.empty session         # 清空会话
.compress session      # 压缩会话
.info session          # 会话信息
.edit session          # 编辑会话
.save session          # 保存会话
```

**RAG 命令（6个）**:
```bash
.rag [name]             # 启动 RAG
.edit rag-docs          # 编辑文档
.rebuild rag            # 重建索引
.sources rag            # 显示来源
.info rag               # RAG 信息
.exit rag               # 退出 RAG
```

**输入命令（4个）**:
```bash
.file <path>            # 包含文件
.continue               # 继续生成
.regenerate             # 重新生成
.copy                   # 复制响应
```

**Agent 命令（4个）**:
```bash
.agent [name]            # 启动 Agent
.starter [num|text]      # 设置启动提示
.edit agent-config      # 编辑 Agent 配置
.info agent             # Agent 信息
```

#### 3. RAG 知识检索（100%）

- ✅ FAISS 向量索引
- ✅ BM25 全文检索
- ✅ 智能文档分割
- ✅ 多语言支持（中文、英文等）
- ✅ 文档管理（添加、删除、重建）

#### 4. Agent 智能体系统（100%）

- ✅ Agent 定义（YAML）
- ✅ 变量插值
- ✅ 多步骤执行
- ✅ 函数调用支持
- ✅ 对话启动器

#### 5. 函数调用/工具使用（100%）

- ✅ Shell 命令执行
- ✅ 文件操作
- ✅ MCP 工具集成
- ✅ 自动去重逻辑
- ✅ 错误处理

#### 6. 配置系统（100%）

- ✅ YAML 配置文件
- ✅ 环境变量支持
- ✅ 多配置合并
- ✅ 角色管理
- ✅ 会话管理
- ✅ 宏系统

#### 7. 工具函数（12/12）

- ✅ 加密工具
- ✅ 剪贴板操作
- ✅ HTML 转 Markdown
- ✅ Shell 命令执行
- ✅ 文档加载器
- ✅ 提示符渲染
- ✅ HTTP 请求
- ✅ 加载动画

#### 8. 双语界面（100%）✨

- ✅ 中英文界面
- ✅ 自动语言检测
- ✅ 手动切换语言
- ✅ 所有命令、消息双语支持

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/xiongfazhan/aicortex.git
cd aicortex

# 安装依赖
pip install -e .

# 或使用开发模式
pip install -e ".[dev]"
```

### 配置 API Key

```bash
# 方式 1: 环境变量
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 方式 2: 配置文件
mkdir -p ~/.config/aicortex
cat > ~/.config/aicortex/config.yaml << EOF
clients:
  - type: openai
    api_key: your-key

  - type: claude
    api_key: your-key
EOF
```

### 基本使用

```bash
# 启动 REPL
aicortex

# 切换到中文界面
> .language zh

# 查看帮助
> .help

# 切换模型
> .model claude:claude-3-5-sonnet-20241022

# 开始对话
> 你好，请介绍一下 Python 的异步编程
```

---

## 详细使用示例

### 1. 角色系统使用

```bash
# 查看所有角色
> .role

# 切换到程序员角色
> .role programmer

# 查看当前角色信息
> .info role

# 编辑当前角色
> .edit role
# 进入编辑模式，输入新的角色定义
# 按 Ctrl+D 结束

# 保存角色
> .save role

# 退出角色模式
> .exit role
```

### 2. 会话管理使用

```bash
# 创建新会话
> .session my-project

# 在会话中对话
> 请帮我设计一个 RESTful API

# 清空会话历史
> .empty session

# 压缩会话（总结历史对话）
> .compress session

# 查看会话信息
> .info session

# 保存会话
> .save session

# 退出会话
> .exit session
```

### 3. RAG 知识检索使用

```bash
# 初始化 RAG
> .rag my-docs

# 添加文档
> .edit rag-docs --add README.md docs/*.md

# 列出所有文档
> .edit rag-docs --list

# 重建索引
> .rebuild rag

# 提问（会自动检索相关文档）
> 这个项目的主要功能是什么？

# 查看引用来源
> .sources rag

# 删除文档
> .edit rag-docs --remove 1
```

### 4. Agent 智能体使用

```bash
# 启动 Agent
> .agent code-reviewer

# 查看对话启动器
> .starter

# 使用启动器
> .starter 1

# 编辑 Agent 配置
> .edit agent-config

# 查看 Agent 信息
> .info agent
```

### 5. 宏系统使用

```bash
# 创建宏文件
mkdir -p ~/.config/aicortex/macros
cat > ~/.config/aicortex/macros/review.yaml << EOF
name: review
description: 代码审查流程
commands:
  - command: .role programmer
  - command: 请审查以下代码
  - command: .file
EOF

# 执行宏
> .macro review

# 查看所有宏
> .macro
```

### 6. 文件操作使用

```bash
# 读取文件到对话
> .file src/main.py

# 复制上一次响应
> .copy

# 继续生成
> .continue

# 重新生成
> .regenerate
```

### 7. 函数调用使用

```bash
# 启动会话
> .session test

# 让 AI 执行命令（会自动调用函数）
> 列出当前目录的文件

# 让 AI 读取文件
> 读取 README.md 的前 10 行

# 让 AI 执行多个操作
> 创建一个测试文件 test.txt，内容是 "hello world"
```

---

## 配置指南

### 配置文件结构

```
~/.config/aicortex/
├── config.yaml         # 主配置
├── roles/              # 角色定义
│   ├── programmer.md
│   ├── translator.md
│   └── shell.md
├── sessions/           # 会话数据
│   └── chat.yaml
├── rags/               # RAG 索引
│   └── docs/
├── macros/             # 宏定义
│   └── review.yaml
└── agents/             # Agent 定义
    └── coder/
        └── index.yaml
```

### 完整配置示例

```yaml
# ~/.config/aicortex/config.yaml

# 客户端配置
clients:
  - type: openai
    api_key: ${OPENAI_API_KEY}
    models:
      - id: gpt-4o
        name: gpt-4o

  - type: claude
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - id: claude-3-5-sonnet-20241022
        name: claude-3.5-sonnet

# 默认模型
model: openai:gpt-4o

# 默认角色
role: default

# 温度参数
temperature: 0.7

# 顶部采样
top_p: 0.9

# 流式输出
stream: true

# 压缩阈值
compress_threshold: 4000

# 函数调用
function_calling: true

# 保存会话
save_session: true

# 会话文件
session_file: chat

# 编辑器
editor: code

# 剪贴板
clipboard: true
```

---

## 待优化项

### 1. 性能优化

- [ ] **流式响应优化**
  - 当前状态：基础流式已实现
  - 优化方向：减少首字延迟，优化分块大小
  - 优先级：中

- [ ] **RAG 检索性能**
  - 当前状态：使用 FAISS，性能良好
  - 优化方向：添加缓存机制，支持增量索引
  - 优先级：中

- [ ] **并发请求支持**
  - 当前状态：串行处理
  - 优化方向：支持多模型并行调用
  - 优先级：低

### 2. 功能增强

- [ ] **自动保存会话**
  - 当前状态：需手动保存
  - 优化方向：定时自动保存
  - 优先级：高

- [ ] **会话历史搜索**
  - 当前状态：无搜索功能
  - 优化方向：支持关键词搜索历史会话
  - 优先级：中

- [ ] **角色模板库**
  - 当前状态：需手动创建角色
  - 优化方向：内置常用角色模板
  - 优先级：中

- [ ] **多模态支持**
  - 当前状态：仅支持文本
  - 优化方向：支持图片、音频输入
  - 优先级：低

### 3. 用户体验

- [ ] **更好的错误提示**
  - 当前状态：基础错误信息
  - 优化方向：提供错误解决建议
  - 优先级：高

- [ ] **命令自动补全**
  - 当前状态：Tab 补全已实现
  - 优化方向：智能提示，基于历史推荐
  - 优先级：中

- [ ] **进度条显示**
  - 当前状态：部分命令有进度提示
  - 优化方向：所有长操作显示进度
  - 优先级：中

### 4. 稳定性提升

- [ ] **异常处理完善**
  - 当前状态：基础异常捕获
  - 优化方向：细化异常类型，提供恢复机制
  - 优先级：高

- [ ] **输入验证增强**
  - 当前状态：基础验证
  - 优化方向：更严格的参数检查
  - 优先级：中

- [ ] **资源清理**
  - 当前状态：基础清理
  - 优化方向：确保所有资源正确释放
  - 优先级：中

---

## 开发计划

### ❌ 待实现功能

#### 优先级 1: 企业级客户端（2个）

| 客户端 | 复杂度 | 预计工作量 |
|--------|--------|-----------|
| AWS Bedrock | 高 | 2-3 天 |
| Vertex AI | 高 | 2-3 天 |

**挑战**：
- AWS Signature V4 认证
- Google OAuth 流程
- 企业级安全要求

#### 优先级 2: HTTP 服务器功能（3个）

| 功能 | 状态 | 说明 |
|------|------|------|
| Rerank API | ❌ | 文档重排序 API 端点 |
| Playground UI | ❌ | Web 交互界面 |
| Arena UI | ❌ | 模型对比界面 |

**当前进度**：
- ✅ 基础 HTTP 服务器（57.1%）
- ✅ Chat Completions API
- ✅ Embeddings API
- ❌ Rerank API
- ❌ Web UI

#### 优先级 3: 高级功能（5个）

| 功能 | 复杂度 | 预计工作量 |
|------|--------|-----------|
| 多模态支持 | 高 | 5-7 天 |
| 插件系统 | 中 | 3-5 天 |
| 工作流编排 | 高 | 7-10 天 |
| 分布式 RAG | 高 | 5-7 天 |
| 自定义工具 | 中 | 3-5 天 |

### 📅 近期开发计划

#### Q1 2025（1-3月）

**目标**: 完成核心企业功能

- [ ] **1月：稳定性提升**
  - [ ] 异常处理完善
  - [ ] 资源清理优化
  - [ ] 错误提示改进
  - [ ] 单元测试覆盖（目标：80%）

- [ ] **2月：企业级客户端**
  - [ ] AWS Bedrock 客户端
  - [ ] Vertex AI 客户端
  - [ ] 企业级文档编写

- [ ] **3月：HTTP 服务器完善**
  - [ ] Rerank API 实现
  - [ ] Playground UI 开发
  - [ ] API 文档完善

#### Q2 2025（4-6月）

**目标**: 高级功能开发

- [ ] **4月：多模态支持**
  - [ ] 图片输入支持
  - [ ] 图片处理工具
  - [ ] 多模态 RAG

- [ ] **5月：插件系统**
  - [ ] 插件架构设计
  - [ ] 插件加载机制
  - [ ] 内置插件开发

- [ ] **6月：工作流编排**
  - [ ] 工作流引擎
  - [ ] 可视化编辑器
  - [ ] 模板库建设

### 🎯 长期愿景（2025下半年-2026）

**核心目标**: 打造企业级 AI 平台

1. **分布式架构**
   - 支持分布式 RAG
   - 多节点部署
   - 负载均衡

2. **企业级功能**
   - 用户权限管理
   - 审计日志
   - 数据加密

3. **生态建设**
   - 插件市场
   - 模板库
   - 社区贡献

---

## 测试与调试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_client.py

# 查看测试覆盖率
pytest --cov=aicortex --cov-report=html

# 代码格式检查
ruff check aicortex/

# 代码格式化
ruff format aicortex/
```

### 调试模式

```bash
# 启用调试日志
aicortex --log-level debug

# 查看配置
aicortex --print-config

# 测试客户端
aicortex --test-client openai
```

---

## 常见问题

### Q1: 如何切换模型？

```bash
> .model                 # 查看当前模型
> .model claude:gpt-4o   # 切换到 GPT-4o
> .model deepseek:chat    # 切换到 DeepSeek
```

### Q2: 如何创建自定义角色？

```bash
# 方式 1: 交互式创建
> .role my-role
> .edit role
# 输入角色定义
> .save role

# 方式 2: 直接创建文件
cat > ~/.config/aicortex/roles/my-role.md << EOF
# My Custom Role
You are a helpful assistant specializing in...
EOF
```

### Q3: RAG 返回结果不准确？

```bash
# 1. 重建索引
> .rebuild rag

# 2. 添加更多相关文档
> .edit rag-docs --add more-docs/

# 3. 调整检索参数
> .set rag_top_k=10
> .set rag_threshold=0.7
```

### Q4: 如何启用函数调用？

```yaml
# config.yaml
function_calling: true

# 或通过命令
> .set function_calling=true
```

---

## 贡献指南

欢迎贡献代码！请查看：

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [开发指南](docs/DEVELOPMENT.md)
- [代码规范](docs/CODING_STYLE.md)

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 MIT 和 Apache-2.0 双许可证。详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

- **GitHub Issues**: https://github.com/xiongfazhan/aicortex/issues
- **GitHub Discussions**: https://github.com/xiongfazhan/aicortex/discussions
- **Email**: xiongfazhan@example.com

---

**最后更新**: 2025-01-07
**文档版本**: v1.0.0
