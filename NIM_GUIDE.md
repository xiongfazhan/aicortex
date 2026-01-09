# NVIDIA NIM 使用指南

[NVIDIA NIM](https://www.nvidia.com/en-us/ai-data-center/products/nim-inference-microservices/) 是 NVIDIA 提供的推理微服务，提供 OpenAI 兼容的 API 接口，**目前免费使用**。

## 快速开始

### 1. 获取 API Key

1. 访问 [build.nvidia.com](https://build.nvidia.com/)
2. 注册/登录账号
3. 创建新的 API Key
4. 复制 API Key

### 2. 配置 AICortex

#### 方式 1: 使用环境变量（推荐）

```bash
# Linux/Mac
export NVIDIA_API_KEY="nvapi-xxx"

# Windows PowerShell
$env:NVIDIA_API_KEY="nvapi-xxx"

# Windows CMD
set NVIDIA_API_KEY=nvapi-xxx
```

#### 方式 2: 使用配置文件

编辑 `~/.config/aicortex/config.yaml`:

```yaml
clients:
  - type: nim
    api_key: ${NVIDIA_API_KEY}
    api_base: https://integrate.api.nvidia.com/v1
    models:
      - name: meta/llama-3.1-405b-instruct
      - name: meta/llama-3.1-70b-instruct
      - name: meta/llama-3.1-8b-instruct
```

## 可用模型

### Llama 3.1 系列

| 模型 | 参数量 | 上下文 | 特点 |
|------|--------|--------|------|
| `meta/llama-3.1-405b-instruct` | 405B | 131K | 最强大，适合复杂任务 |
| `meta/llama-3.1-70b-instruct` | 70B | 131K | 平衡性能和速度 |
| `meta/llama-3.1-8b-instruct` | 8B | 131K | 最快速 |

### 其他模型

| 模型 | 参数量 | 上下文 | 特点 |
|------|--------|--------|------|
| `mistralai/mistral-nemo-12b-instruct` | 12B | 131K | Mistral 最新 |
| `mistralai/mixtral-8x7b-instruct-v0.1` | 8x7B | 32K | MoE 架构 |
| `meta/codellama-70b-instruct` | 70B | 131K | 代码生成 |
| `google/gemma-2-27b-it` | 27B | 131K | Google Gemma |

### Embedding 模型（用于 RAG）

| 模型 | 上下文 | 特点 |
|------|--------|------|
| `nvidia/llama-3.2-nv-embedqa-1b-v2` | 32K | 高质量，长上下文，默认推荐 |
| `nvidia/nv-embedqa-e5-v5` | 512 | 轻量级，速度快 |

### Rerank 模型（用于 RAG）

| 模型 | 上下文 | 特点 |
|------|--------|------|
| `nvidia/nv-rerankqa-mistral-4b-v3` | 32K | 高质量重排序 |
| `nvidia/llama-3.2-nv-rerankqa-1b-v2` | 32K | 轻量级，速度快 |

## 使用示例

### 基本使用

```bash
# 使用 Llama 3.1 405B
aicortex -m nim:meta/llama-3.1-405b-instruct "介绍一下 Python"

# 使用 Llama 3.1 70B
aicortex -m nim:meta/llama-3.1-70b-instruct "写一个快速排序"

# 使用代码模型
aicortex -m nim:meta/codellama-70b-instruct "解释这段代码"
```

### 设置为默认模型

编辑 `~/.config/aicortex/config.yaml`:

```yaml
model_id: nim:meta/llama-3.1-70b-instruct
```

然后直接运行:
```bash
aicortex "你好"
```

### REPL 模式

```bash
# 启动 REPL 并使用 NIM
aicortex

# 在 REPL 中切换模型
> /model nim:meta/llama-3.1-405b-instruct
> /model nim:meta/codellama-70b-instruct
```

### 编程任务

```bash
# 使用代码模型
aicortex -m nim:meta/codellama-70b-instruct --role programmer "
写一个 Python 函数，用于计算斐波那契数列
"
```

## 模型选择建议

### 通用对话
- **推荐**: `meta/llama-3.1-70b-instruct`
- **理由**: 性能和速度的最佳平衡

### 复杂推理
- **推荐**: `meta/llama-3.1-405b-instruct`
- **理由**: 最大的模型，最强的推理能力

### 快速响应
- **推荐**: `meta/llama-3.1-8b-instruct`
- **理由**: 最小的模型，响应最快

### 代码生成
- **推荐**: `meta/codellama-70b-instruct`
- **理由**: 专门针对代码优化

### 数学/科学计算
- **推荐**: `mistralai/mistral-nemo-12b-instruct`
- **理由**: Mistral NeMo 在数学任务上表现优秀

## 性能对比

基于实际使用体验:

| 任务 | 推荐模型 | 响应速度 | 质量 |
|------|----------|----------|------|
| 日常对话 | llama-3.1-70b | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 复杂推理 | llama-3.1-405b | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 代码生成 | codellama-70b | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 快速问答 | llama-3.1-8b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 完整配置示例

```yaml
# ~/.config/aicortex/config.yaml

# 设置 NIM 为默认模型
model_id: nim:meta/llama-3.1-70b-instruct

temperature: 0.7
stream: true

clients:
  - type: nim
    api_key: ${NVIDIA_API_KEY}
    api_base: https://integrate.api.nvidia.com/v1
    models:
      # 主要使用
      - name: meta/llama-3.1-70b-instruct
        type: chat
        max_input_tokens: 131072
        max_output_tokens: 4096

      # 备选模型
      - name: meta/llama-3.1-405b-instruct
        type: chat
        max_input_tokens: 131072
        max_output_tokens: 4096

      - name: meta/codellama-70b-instruct
        type: chat
        max_input_tokens: 131072
        max_output_tokens: 4096

      - name: meta/llama-3.1-8b-instruct
        type: chat
        max_input_tokens: 131072
        max_output_tokens: 4096

      # Embedding 模型（用于 RAG）
      - name: nvidia/llama-3.2-nv-embedqa-1b-v2
        type: embedding
        max_input_tokens: 32768

      - name: nvidia/nv-embedqa-e5-v5
        type: embedding
        api_base: https://integrate.api.nvidia.com/v1
        max_input_tokens: 512

      # Rerank 模型（用于 RAG）
      - name: nvidia/nv-rerankqa-mistral-4b-v3
        type: rerank
        max_input_tokens: 32768

      - name: nvidia/llama-3.2-nv-rerankqa-1b-v2
        type: rerank
        max_input_tokens: 32768

# RAG 配置（使用 NIM 模型）
rag_embedding_model: nim:nvidia/llama-3.2-nv-embedqa-1b-v2
rag_reranker_model: nim:nvidia/llama-3.2-nv-rerankqa-1b-v2
rag_top_k: 5
```

## 环境变量

```bash
# 设置 API Key
export NVIDIA_API_KEY="nvapi-xxx"

# 可选：设置默认模型
export AICORTEX_MODEL="nim:meta/llama-3.1-70b-instruct"
```

## 常见问题

### Q: NIM 真的免费吗？
**A**: 是的，目前 NIM 提供免费 API 访问，但可能有速率限制。

### Q: 如何查看我的使用配额？
**A**: 登录 [build.nvidia.com](https://build.nvidia.com/) 查看使用情况。

### Q: 响应速度如何？
**A**:
- 405B 模型: 中等速度
- 70B 模型: 较快
- 8B 模型: 非常快

### Q: 支持函数调用吗？
**A**: 是的，NIM 支持 OpenAI 兼容的函数调用接口。

### Q: 支持流式输出吗？
**A**: 是的，完全支持。

### Q: 模型名称中的 `/` 需要转义吗？
**A**: 不需要，直接使用完整名称即可：
```bash
aicortex -m nim:meta/llama-3.1-405b-instruct "你好"
```

## 与其他模型对比

### vs OpenAI GPT-4
- **优势**: 免费，405B 参数更大
- **劣势**: 响应速度稍慢

### vs DeepSeek
- **优势**: 模型更大（405B vs 32B）
- **劣势**: DeepSeek 更便宜

### vs Groq
- **优势**: 模型质量更高
- **劣势**: Groq 速度更快

## 推荐使用场景

### 1. 日常开发
```bash
export NVIDIA_API_KEY="nvapi-xxx"
aicortex -m nim:meta/llama-3.1-70b-instruct --role programmer
```

### 2. 复杂分析
```bash
aicortex -m nim:meta/llama-3.1-405b-instruct "
分析这段代码的优缺点，并提出改进建议
"
```

### 3. 代码审查
```bash
aicortex -m nim:meta/codellama-70b-instruct --file main.py "
审查这段代码，找出潜在的问题
"
```

### 4. 快速问答
```bash
aicortex -m nim:meta/llama-3.1-8b-instruct "什么是装饰器？"
```

## 测试 NIM 连接

```bash
# 测试基本连接
export NVIDIA_API_KEY="nvapi-xxx"
aicortex -m nim:meta/llama-3.1-70b-instruct "你好，请介绍一下你自己"

# 测试流式输出
aicortex -m nim:meta/llama-3.1-405b-instruct "写一首关于编程的诗"

# 测试长上下文
aicortex -m nim:meta/llama-3.1-70b-instruct "
总结一下 Python 的主要特性，请详细说明
"
```

## 使用 NIM 进行 RAG

NIM 提供了专门的 Embedding 和 Rerank 模型，可以构建完整的 RAG 系统：

### 配置 RAG

```yaml
# RAG 配置
rag_embedding_model: nim:nvidia/llama-3.2-nv-embedqa-1b-v2
rag_reranker_model: nim:nvidia/llama-3.2-nv-rerankqa-1b-v2
rag_top_k: 5
rag_chunk_size: 1000
rag_chunk_overlap: 200
```

### Embedding 模型选择

- **llama-3.2-nv-embedqa-1b-v2**: 高质量，支持长上下文 32K tokens，默认推荐
- **nv-embedqa-e5-v5**: 轻量级，适合快速检索，上下文 512 tokens

### Rerank 模型选择

- **llama-3.2-nv-rerankqa-1b-v2**: 轻量级，速度快，默认推荐
- **nv-rerankqa-mistral-4b-v3**: 高质量重排序，适合对精度要求高的场景

### RAG 使用示例

```bash
# 创建 RAG 索引
aicortex --rag my-docs --add ./docs/*.md

# 使用 RAG 查询
aicortex --rag my-docs "文档中关于 X 说了什么？"
```

## 总结

NVIDIA NIM 是一个极佳的免费选择，特别适合：
- 需要大模型但不想付费的用户
- 需要长上下文（131K tokens）
- 开发和测试环境
- 代码生成和分析
- 构建完整的 RAG 系统（Embedding + Rerank）

立即可用，无需等待审核！
