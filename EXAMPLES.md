# AICortex 使用示例集合

**版本**: v0.9.1
**最后更新**: 2025-01-07

本文档提供了 AICortex 的详细使用示例和最佳实践。

---

## 目录

1. [基础使用](#基础使用)
2. [角色系统示例](#角色系统示例)
3. [会话管理示例](#会话管理示例)
4. [RAG 知识检索示例](#rag-知识检索示例)
5. [Agent 智能体示例](#agent-智能体示例)
6. [函数调用示例](#函数调用示例)
7. [高级用法](#高级用法)
8. [实战场景](#实战场景)

---

## 基础使用

### 快速对话

```bash
# 启动 AICortex
$ aicortex

# 切换到中文
> .language zh
语言已设置为: zh

# 开始对话
> 解释一下什么是闭包
```

### 切换模型

```bash
# 查看当前模型
> .model
当前模型: openai:gpt-4o

# 切换到 Claude
> .model claude:claude-3-5-sonnet-20241022
模型已设置为: claude:claude-3-5-sonnet-20241022

# 切换到 DeepSeek
> .model deepseek:deepseek-chat
模型已设置为: deepseek:deepseek-chat
```

### 设置参数

```bash
# 设置温度
> .set temperature=0.7
已设置 temperature = 0.7

# 设置最大 token 数
> .set max_tokens=2000
已设置 max_tokens = 2000

# 设置顶部采样
> .set top_p=0.9
已设置 top_p = 0.9

# 查看所有设置
> .info
```

---

## 角色系统示例

### 内置角色使用

```bash
# 查看所有可用角色
> .role
可用角色:
  - default       (默认助手)
  - programmer    (程序员)
  - translator    (翻译员)
  - shell         (Shell 助手)

# 切换到程序员角色
> .role programmer
角色已设置为: programmer

# 使用程序员角色提问
> 解释一下 Python 的装饰器
```

### 创建自定义角色

```bash
# 方式 1: 通过交互式编辑
> .role my-custom-role
# 进入编辑模式
> .edit role
Enter new role content (press Ctrl+D when done):
你是一位资深的数据科学家，擅长：
- 数据分析与可视化
- 机器学习模型开发
- 统计学建模
- 数据驱动的业务洞察

请用专业但易懂的语言回答问题。
^D
角色已更新

# 保存角色
> .save role
角色已保存到: /home/user/.config/aicortex/roles/my-custom-role.md
```

### 角色文件定义

创建 `~/.config/aicortex/roles/code-reviewer.md`：

```markdown
# Code Reviewer

你是一位经验丰富的代码审查专家，职责是：

1. 检查代码质量和规范性
2. 识别潜在的 bug 和安全问题
3. 提供优化建议
4. 确保代码可维护性

审查时请关注：
- 代码风格一致性
- 错误处理
- 性能优化
- 安全漏洞
- 测试覆盖

请以建设性的方式提供反馈。
```

使用这个角色：

```bash
> .role code-reviewer
> 请审查这段 Python 代码：
```

---

## 会话管理示例

### 创建和管理会话

```bash
# 创建新会话
> .session python-learning
会话已设置为: python-learning

# 在会话中进行多轮对话
> 什么是列表推导式？
> [AI 回答...]
> 能给几个例子吗？
> [AI 回答...]

# 查看会话信息
> .info session
Session: python-learning
Messages: 5
Tokens: 1234

# 清空会话
> .empty session
清空会话 'python-learning' 中的所有消息?
确认 (y/N): y
会话 'python-learning' 已清空

# 压缩会话（总结历史）
> .compress session
正在压缩会话 'python-learning'...
会话压缩成功
  已压缩 15 条消息
  Current tokens: 456 (12.3%)

# 保存会话
> .save session
会话已保存到: /home/user/.config/aicortex/sessions/python-learning.yaml

# 退出会话
> .exit session
已退出会话模式
```

### 会话恢复

```bash
# 重新进入之前的会话
> .session python-learning
会话已设置为: python-learning
# 之前的对话历史会自动加载
```

---

## RAG 知识检索示例

### 初始化 RAG

```bash
# 创建新的 RAG 索引
> .rag project-docs
RAG 已设置为: project-docs

# 添加文档
> .edit rag-docs --add README.md CONTRIBUTING.md docs/*.md
正在索引: README.md
  已添加: README.md
正在索引: CONTRIBUTING.md
  已添加: CONTRIBUTING.md
...

# 列出所有文档
> .edit rag-docs --list
RAG 'project-docs' 中的文档:
  [0] README.md (3 chunks)
  [1] CONTRIBUTING.md (5 chunks)
  [2] docs/api.md (8 chunks)
```

### 重建索引

```bash
# 添加或删除文档后重建索引
> .rebuild rag
正在重建 RAG 'project-docs'...
RAG 重建成功
  Files: 3
  Documents: 16
  Vectors: 128
```

### 使用 RAG 查询

```bash
# 提问会自动检索相关文档
> 这个项目的主要功能是什么？
# AI 会基于检索到的文档回答

# 查看引用来源
> .sources rag
来源:
[0] README.md - 第 1-2 段
[1] docs/api.md - 第 3-4 段
```

### 删除文档

```bash
# 删除不需要的文档
> .edit rag-docs --remove 1
已移除: [1] CONTRIBUTING.md

# 删除后需要重建索引
> .rebuild rag
```

---

## Agent 智能体示例

### 使用内置 Agent

```bash
# 启动代码审查 Agent
> .agent code-reviewer
[显示 Agent 横幅]
[Agent 启动提示]

# 使用对话启动器
> .starter
'code-reviewer' 的对话启动语:
  1. 请审查这段代码的逻辑
  2. 检查代码安全性
  3. 提供优化建议

用法: .starter <数字> 或 .starter <文本>

> .starter 1
请审查这段代码的逻辑：
```python
def calculate(a, b):
    return a / b
```
```

### 创建自定义 Agent

创建 `~/.config/aicortex/agents/translator/index.yaml`：

```yaml
name: translator
description: 专业翻译助手
version: 1.0.0

# 提示词模板
prompt: |
  你是一位专业翻译，擅长：
  - 中英文互译
  - 保持原文语境
  - 技术术语准确翻译

  翻译时请遵循：
  1. 准确传达原文含义
  2. 保持语言流畅自然
  3. 保留专业术语

  目标语言：{{target_language}}

# 变量定义
variables:
  - name: target_language
    description: 目标语言
    default: 中文

# 对话启动器
conversation_starters:
  - 翻译以下技术文档
  - 将这段代码注释翻译成英文
  - 翻译并保持技术准确性
```

使用这个 Agent：

```bash
# 启动 Agent
> .agent translator

# 编辑 Agent 配置
> .edit agent-config
正在编辑 Agent 'translator' 配置

当前配置:
  Model: gpt-4o
  Temperature: 0.3
  Use Tools: false

输入变量值 (完成后按 Ctrl+D):
... target_language=日语
^D

已更新 1 个变量

# 使用 Agent
> 翻译以下技术文档：
Python is a high-level programming language.
```

---

## 函数调用示例

### Shell 命令执行

```bash
# 启用函数调用
> .set function_calling=true

# 让 AI 执行命令
> 列出当前目录的所有 Python 文件
[AI 自动调用 list_files 函数]
[执行结果] main.py, config.py, utils.py...

> 查看文件 main.py 的前 10 行
[AI 自动调用 read_file 函数]
[显示文件内容]
```

### 文件操作

```bash
# 让 AI 创建文件
> 创建一个名为 test.txt 的文件，内容是 "Hello World"
[AI 自动调用 write_file 函数]
文件已创建: test.txt

# 让 AI 读取文件
> 读取 test.txt 的内容
[AI 自动调用 read_file 函数]
Hello World
```

### 多步骤操作

```bash
> 分析当前目录的结构，统计每种语言的代码行数
[AI 自动调用多个函数]
1. list_files
2. read_files
3. analyze_code
4. count_lines

[最终结果]
- Python: 1234 行
- Markdown: 567 行
- YAML: 89 行
```

---

## 高级用法

### 宏系统

创建宏 `~/.config/aicortex/macros/code-analysis.yaml`：

```yaml
name: analyze
description: 代码分析工作流
usage: .macro analyze <file-path>
variables:
  - name: file_path
    description: 要分析的文件路径
    required: true

commands:
  # 切换到程序员角色
  - command: .role programmer

  # 读取文件
  - command: .file ${file_path}

  # 分析代码质量
  - command: |
      请分析这段代码的：
      1. 代码质量
      2. 潜在问题
      3. 优化建议

  # 切换到代码审查角色
  - command: .role code-reviewer

  # 提供审查意见
  - command: |
      基于以上分析，请提供详细的代码审查意见。
```

使用宏：

```bash
# 执行宏
> .macro analyze src/main.py
[自动执行一系列命令]
```

### 管道操作

```bash
# 结合 .file 和其他命令
> .file data.json | 提取所有用户名
[AI 处理文件内容并提取信息]

# 结合 RAG 和分析
> .rag docs
> .file report.md
> 结合文档分析报告中的数据
```

### 流程自动化

```bash
# 创建完整的测试流程
> .session test-app
> .role tester
> .rag test-docs
> .file app.py
> 设计测试用例
> .save session
```

---

## 实战场景

### 场景 1: 代码审查流程

```bash
# 1. 启动代码审查会话
> .session review-main

# 2. 切换到代码审查角色
> .role code-reviewer

# 3. 添加代码文档到 RAG
> .rag coding-standards
> .edit rag-docs --add docs/standards.md

# 4. 读取待审查代码
> .file src/auth.py

# 5. 执行审查
> 请按照项目编码标准审查这段代码，重点关注：
1. 安全性
2. 错误处理
3. 代码风格

# 6. 保存审查结果
> .copy
> .save session
```

### 场景 2: 学习新技术

```bash
# 1. 创建学习会话
> .session learn-rust

# 2. 切换到教师角色
> .role teacher

# 3. 添加学习资料到 RAG
> .rag rust-guide
> .edit rag-docs --add rust-book/*.md

# 4. 系统化学习
> 我想学习 Rust 语言，请帮我制定学习计划
[AI 基于 RAG 文档制定计划]

# 5. 深入某个主题
> 详细解释 Rust 的所有权系统
[AI 结合文档深入讲解]

# 6. 实践练习
> 给我几个练习题巩固所有权概念
[AI 提供练习题]

# 7. 保存学习记录
> .compress session
> .save session
```

### 场景 3: 文档翻译

```bash
# 1. 使用翻译 Agent
> .agent translator

# 2. 设置目标语言
> .edit agent-config
target_language=英文
^D

# 3. 翻译文档
> 翻译以下文档：
```markdown
# AICortex 使用指南

AICortex 是一个全能型 LLM 命令行工具...
```

# 4. 复制翻译结果
> .copy

# 5. 保存到文件
[手动粘贴到文件]
```

### 场景 4: 数据分析

```bash
# 1. 创建数据分析会话
> .session data-analysis

# 2. 添加数据文档
> .rag data-docs
> .edit rag-docs --add data/schema.md

# 3. 读取数据文件
> .file data/sales.csv

# 4. 分析数据
> 请分析销售数据，找出：
1. 最佳销售月份
2. 增长趋势
3. 异常值

# 5. 生成可视化建议
> 基于分析结果，建议用哪些图表展示数据？

# 6. 生成分析报告
> 生成完整的分析报告
> .copy
```

### 场景 5: API 开发辅助

```bash
# 1. 启动开发会话
> .session api-dev

# 2. 切换到程序员角色
> .role programmer

# 3. 添加 API 文档
> .rag api-specs
> .edit rag-docs --add docs/openapi.yaml

# 4. 设计 API 端点
> 基于以下需求设计 RESTful API：
- 用户管理
- 认证授权
- 数据查询

# 5. 生成代码
> 为用户管理端点生成代码

# 6. 代码审查
> .role code-reviewer
> 审查刚才生成的代码

# 7. 保存工作成果
> .save session
```

---

## 最佳实践

### 1. 会话组织

```bash
# 建议为不同任务创建独立会话
> .session work-project-a    # 工作 A 项目
> .session learning-rust      # Rust 学习
> .session blog-writing       # 博客写作
> .session code-review        # 代码审查
```

### 2. RAG 管理

```bash
# 按主题组织 RAG 索引
> .rag project-docs           # 项目文档
> .rag tech-standards         # 技术标准
> .rag team-knowledge         # 团队知识库
> .rag customer-docs          # 客户文档
```

### 3. 角色切换

```bash
# 灵活使用不同角色
> .role researcher            # 研究阶段
> .role writer                # 写作阶段
> .role reviewer              # 审查阶段
> .role translator            # 翻译阶段
```

### 4. 定期保存

```bash
# 重要节点保存会话
> .save session              # 手动保存
> .compress session          # 压缩后再保存
```

### 5. 使用宏自动化

```bash
# 创建常用工作流宏
> .macro setup-project        # 项目初始化
> .macro daily-standup       # 每日站会
> .macro code-review          # 代码审查
```

---

## 故障排除

### 问题 1: 模型切换失败

```bash
> .model unknown:model
错误: 未知的模型提供商

# 解决方案：检查可用模型
> .info
# 查看配置文件中定义的模型
```

### 问题 2: RAG 检索不准确

```bash
# 解决方案：
1. 重建索引
> .rebuild rag

2. 添加更多相关文档
> .edit rag-docs --add more-docs/

3. 调整检索参数
> .set rag_top_k=15
> .set rag_threshold=0.6
```

### 问题 3: 会话丢失

```bash
# 解决方案：定期保存
> .save session

# 查看已保存的会话
> ls ~/.config/aicortex/sessions/

# 恢复会话
> .session session-name
```

---

## 更多资源

- [完整功能清单](ROADMAP.md)
- [配置指南](CONFIG_GUIDE.md)
- [快速开始](QUICKSTART.md)
- [项目结构](PROJECT_STRUCTURE.md)

---

**最后更新**: 2025-01-07
**版本**: v1.0.0
