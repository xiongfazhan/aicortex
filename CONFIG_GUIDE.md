# AICortex 配置文件使用指南

## 配置文件位置

### Linux/Mac
```

## RAG 高级检索参数与切分策略

```yaml
# 向量与关键词召回数量
rag_vector_top_k: 60
rag_bm25_top_k: 60

# 混合召回后候选数量
rag_candidate_k: 36

# 覆盖配额
rag_file_cap: 6
rag_section_cap: 4

# Rerank 取前 N
rag_rerank_top_k: 10

# 命中块父块回填的上下文窗口
rag_parent_min_tokens: 2500
rag_parent_max_tokens: 4500

# 切分策略: auto/markdown/code/text/plain
rag_split_strategy: auto
```
## 模型级 api_base 覆盖

当同一提供商下不同模型需要使用不同的 `base_url` 时，可以在模型项里单独设置 `api_base`，
它会覆盖客户端级的 `api_base` 配置。

示例：
```yaml
clients:
  - type: nim
    api_key: ${NVIDIA_API_KEY}
    api_base: https://integrate.api.nvidia.com/v1
    models:
      - name: nvidia/llama-3.2-nv-embedqa-1b-v2
        type: embedding
        api_base: https://integrate.api.nvidia.com/v1
```

## Rerank 模型 URL 覆盖

NIM 的 rerank 接口在部分模型上使用不同的完整 URL。此时可以在模型项里设置 `rerank_url`，
它会直接作为 rerank 请求的完整 endpoint。

示例：
```yaml
clients:
  - type: nim
    api_key: ${NVIDIA_API_KEY}
    api_base: https://integrate.api.nvidia.com/v1
    models:
      - name: nvidia/nv-rerankqa-mistral-4b-v3
        type: rerank
        rerank_url: https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking
      - name: nvidia/llama-3.2-nv-rerankqa-1b-v2
        type: rerank
        rerank_url: https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking
```
~/.config/aicortex/config.yaml
```

### Windows
```
C:\Users\<用户名>\.config\aicortex\config.yaml
```

## 快速开始

### 方式 1: 使用简化配置（推荐新手）

```bash
# 1. 创建配置目录
mkdir -p ~/.config/aicortex

# 2. 复制简化配置
cp config.simple.yaml ~/.config/aicortex/config.yaml

# 3. 设置环境变量
export OPENAI_API_KEY="sk-xxx"

# 4. 运行
aicortex "你好"
```

### 方式 2: 使用完整配置（推荐高级用户）

```bash
# 1. 创建配置目录
mkdir -p ~/.config/aicortex

# 2. 复制完整配置
cp config.yaml ~/.config/aicortex/config.yaml

# 3. 编辑配置，填入你的 API Key
vim ~/.config/aicortex/config.yaml

# 4. 运行
aicortex "你好"
```

## 配置项说明

### 基础配置

```yaml
# 默认模型
model_id: openai:gpt-3.5-turbo

# 温度参数 (0.0 - 2.0)
temperature: 0.7

# Top-P 采样 (0.0 - 1.0)
top_p: 1.0

# 流式输出
stream: true
```

### 环境变量支持

```yaml
clients:
  - type: openai
    # 使用环境变量（推荐）
    api_key: ${OPENAI_API_KEY}

    # 或直接写入（不推荐，有安全风险）
    # api_key: sk-xxx...
```

### 支持的提供商

#### 1. OpenAI
```yaml
- type: openai
  api_key: ${OPENAI_API_KEY}
  models:
    - name: gpt-3.5-turbo
    - name: gpt-4
    - name: gpt-4o
```

#### 2. Claude (Anthropic)
```yaml
- type: claude
  api_key: ${ANTHROPIC_API_KEY}
  models:
    - name: claude-3-sonnet
    - name: claude-3-opus
```

#### 3. DeepSeek (性价比高)
```yaml
- type: deepseek
  api_key: ${DEEPSEEK_API_KEY}
  models:
    - name: deepseek-chat
    - name: deepseek-coder
```

#### 4. Groq (快速免费)
```yaml
- type: groq
  api_key: ${GROQ_API_KEY}
  models:
    - name: llama3-70b-8192
    - name: mixtral-8x7b-32768
```

## 环境变量设置

### Linux/Mac (.bashrc 或 .zshrc)
```bash
# OpenAI
export OPENAI_API_KEY="sk-xxx"

# Claude
export ANTHROPIC_API_KEY="sk-ant-xxx"

# DeepSeek
export DEEPSEEK_API_KEY="sk-xxx"

# Groq
export GROQ_API_KEY="gsk_xxx"

# Gemini
export GEMINI_API_KEY="xxx"

# Cohere
export COHERE_API_KEY="xxx"

# 通用（当 model_id 不包含提供商前缀时使用）
export API_KEY="sk-xxx"
```

### Windows (PowerShell)
```powershell
# OpenAI
$env:OPENAI_API_KEY="sk-xxx"

# Claude
$env:ANTHROPIC_API_KEY="sk-ant-xxx"

# DeepSeek
$env:DEEPSEEK_API_KEY="sk-xxx"

# Groq
$env:GROQ_API_KEY="gsk_xxx"
```

### Windows (CMD)
```cmd
REM OpenAI
set OPENAI_API_KEY=sk-xxx

REM Claude
set ANTHROPIC_API_KEY=sk-ant-xxx

REM DeepSeek
set DEEPSEEK_API_KEY=sk-xxx
```

### Windows (系统环境变量)
1. 右键"此电脑" → "属性"
2. 点击"高级系统设置"
3. 点击"环境变量"
4. 在"用户变量"中添加新变量
5. 变量名: `OPENAI_API_KEY`
6. 变量值: `sk-xxx`

## 使用示例

### 指定不同模型

```bash
# 使用 OpenAI GPT-4
aicortex -m openai:gpt-4 "你好"

# 使用 Claude
aicortex -m claude:claude-3-sonnet "你好"

# 使用 DeepSeek
aicortex -m deepseek:deepseek-chat "你好"

# 使用 Groq (免费)
aicortex -m groq:llama3-70b-8192 "你好"
```

### 切换默认模型

编辑 `config.yaml`:
```yaml
model_id: deepseek:deepseek-chat  # 改成 DeepSeek
```

然后直接运行:
```bash
aicortex "你好"  # 自动使用 DeepSeek
```

## 配置验证

### 检查配置文件

```bash
# 查看当前配置
aicortex --info

# 列出可用模型
aicortex --list-models

# 列出可用角色
aicortex --list-roles
```

## 常见问题

### 1. API Key 未找到

```
Error: API key not found
```

**解决方案:**
- 确认环境变量已设置: `echo $OPENAI_API_KEY`
- 或在配置文件中直接写入 API Key

### 2. 配置文件不生效

**解决方案:**
- 确认配置文件路径正确
- Linux/Mac: `~/.config/aicortex/config.yaml`
- Windows: `C:\Users\<用户名>\.config\aicortex\config.yaml`

### 3. 模型不可用

```
ValueError: Model not found: xxx
```

**解决方案:**
- 检查配置文件中是否定义了该模型
- 使用 `aicortex --list-models` 查看可用模型
- 确认模型名称格式正确: `<提供商>:<模型名>`

### 4. 网络连接问题

**解决方案:**
- 配置代理（如果在需要代理的环境）:
  ```yaml
  proxy: http://127.0.0.1:7890
  ```
- 或设置环境变量:
  ```bash
  export HTTP_PROXY=http://127.0.0.1:7890
  export HTTPS_PROXY=http://127.0.0.1:7890
  ```

## 最小配置示例

如果你只想快速开始，创建 `~/.config/aicortex/config.yaml`:

```yaml
model_id: openai:gpt-3.5-turbo
temperature: 0.7
stream: true

clients:
  - type: openai
    api_key: ${OPENAI_API_KEY}
    models:
      - name: gpt-3.5-turbo
```

然后设置环境变量:
```bash
export OPENAI_API_KEY="sk-xxx"
aicortex "你好"
```

## 安全建议

1. **使用环境变量** - 不要在配置文件中直接写入 API Key
2. **设置文件权限** - `chmod 600 ~/.config/aicortex/config.yaml`
3. **使用 .env 文件** - 配合 `python-dotenv` 加载环境变量
4. **不要提交配置** - 将 `config.yaml` 添加到 `.gitignore`

## RAG 配置

RAG（检索增强生成）需要配置 Embedding 模型和可选的 Rerank 模型。

### 使用 NVIDIA NIM（推荐，免费）

```yaml
# Embedding 模型（用于文档向量化）
rag_embedding_model: nim:nvidia/llama-3.2-nv-embedqa-1b-v2
# 可选: nim:nvidia/nv-embedqa-e5-v5（轻量级，速度快）

# Rerank 模型（用于检索结果重排序）
rag_reranker_model: nim:nvidia/llama-3.2-nv-rerankqa-1b-v2
# 可选: nim:nvidia/llama-3.2-nv-rerankqa-1b-v2（更轻量）

# 其他 RAG 参数
rag_top_k: 5              # 返回结果数量
rag_chunk_size: 1000      # 文档切分块大小
rag_chunk_overlap: 200    # 切分块重叠
```

### NIM Embedding/Rerank 模型说明

| 模型类型 | 模型名称 | 上下文 | 特点 |
|---------|---------|--------|------|
| Embedding | `nvidia/llama-3.2-nv-embedqa-1b-v2` | 32K | 高质量，长上下文，默认推荐 |
| Embedding | `nvidia/nv-embedqa-e5-v5` | 512 | 轻量级，速度快 |
| Rerank | `nvidia/nv-rerankqa-mistral-4b-v3` | 32K | 高质量重排序 |
| Rerank | `nvidia/llama-3.2-nv-rerankqa-1b-v2` | 32K | 轻量级，速度快 |

### 使用其他提供商

```yaml
# OpenAI
rag_embedding_model: openai:text-embedding-ada-002

# Cohere
rag_reranker_model: cohere:rerank-english-v2.0
```

### RAG 使用示例

```bash
# 创建 RAG 索引
aicortex --rag my-docs --add ./docs/*.md

# 使用 RAG 查询
aicortex --rag my-docs "文档中关于 X 说了什么？"

# 在 REPL 中使用
aicortex
> /rag my-docs
> 查询文档内容
```
