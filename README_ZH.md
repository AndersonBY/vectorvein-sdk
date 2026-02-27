# vectorvein-sdk

[English](README.md)

[VectorVein](https://vectorvein.com) 平台的 Python SDK — 运行工作流、代码构建工作流、管理 AI 智能体。

## 安装

```bash
pip install vectorvein-sdk
```

需要 Python 3.10+。

## 快速开始

```python
from vectorvein.api import VectorVeinClient, WorkflowInputField

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    result = client.run_workflow(
        wid="YOUR_WORKFLOW_ID",
        input_fields=[
            WorkflowInputField(node_id="node_id", field_name="input", value="你好"),
        ],
        wait_for_completion=True,
        timeout=60,
    )
    for output in result.data:
        print(f"{output.title}: {output.value}")
```

## CLI 命令行工具

安装后可直接运行：

```bash
vectorvein --help
```

以下安装方式都会提供 `vectorvein` 命令：

```bash
pip install vectorvein-sdk
uv tool install vectorvein-sdk
```

### CLI 设计目标（对 Agent 友好）

- **帮助信息可自解释**：各模块与子命令都提供详细 `--help` 与示例。
- **默认人类可读**：终端默认输出可读文本，更符合常规 CLI 使用习惯。
- **按需结构化输出**：需要给 Agent 稳定解析时使用 `--format json`。
- **鉴权优先级明确**：API Key 解析顺序为 `--api-key` > `VECTORVEIN_API_KEY`。
- **退出码固定**：
  - `0`：成功
  - `2`：参数/调用方式错误
  - `3`：鉴权（API Key）错误
  - `4`：业务 API 错误
  - `5`：请求/网络错误

### 常用 CLI 示例

```bash
# 鉴权 / 用户
vectorvein --api-key YOUR_API_KEY auth whoami
vectorvein user info
vectorvein --format json auth whoami

# 工作流
vectorvein workflow run \
  --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"你好"}'
vectorvein workflow status --rid rid_xxx
vectorvein workflow list --page 1 --page-size 10

# Task Agent
vectorvein task-agent agent list --page 1 --page-size 10
vectorvein task-agent task create --agent-id agent_xxx --text "请总结这篇文章"
vectorvein task-agent task continue --task-id task_xxx --message "再给一个 TL;DR"

# 智能体工作空间
vectorvein agent-workspace list
vectorvein agent-workspace files --workspace-id ws_xxx
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20

# 高级用法：调用暂未封装成高级命令的 API
vectorvein api request --method POST --endpoint workflow/list --body '{"page":1,"page_size":5}'
```

`auth whoami` 返回字段为 `uid`、`username`、`email`、`credits`、`date_joined`（不会暴露内部自增 `user_id`）。

### JSON 参数规则

- `--input-field`、`--attachments`、`--body` 等参数支持直接传入 JSON 字符串。
- 也支持 `@file.json` 形式，例如：`--input-fields @inputs.json`。
- `workflow run` 的输入字段对象必须包含：`node_id`、`field_name`、`value`。

## 功能概览

- **同步 & 异步客户端** — `VectorVeinClient` 和 `AsyncVectorVeinClient`
- **工作流执行** — 运行工作流、轮询状态、通过 API 创建工作流
- **工作流管理接口** — 列表/更新工作流、运行记录、调度、模板、标签、回收站、快速入口
- **工作流构建器** — 用 Python 代码构建工作流，支持 50+ 节点类型
- **AI 智能体管理** — 创建智能体、运行任务、管理执行周期
- **文件上传** — 上传文件到平台
- **访问密钥管理** — 创建、列出、更新、删除访问密钥
- **智能体工作空间** — 读写/列出/打包文件，并触发容器同步
- **用户接口** — 获取当前用户信息、校验 API Key

## 工作流执行

### 同步调用

```python
from vectorvein.api import VectorVeinClient, WorkflowInputField

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    # 异步提交，不等待结果
    rid = client.run_workflow(
        wid="workflow_id",
        input_fields=[WorkflowInputField(node_id="n1", field_name="text", value="你好")],
        wait_for_completion=False,
    )

    # 轮询结果
    result = client.check_workflow_status(rid=rid)
    print(result.status, result.data)
```

### 异步调用

```python
import asyncio
from vectorvein.api import AsyncVectorVeinClient, WorkflowInputField

async def main():
    async with AsyncVectorVeinClient(api_key="YOUR_API_KEY") as client:
        result = await client.run_workflow(
            wid="workflow_id",
            input_fields=[WorkflowInputField(node_id="n1", field_name="text", value="你好")],
            wait_for_completion=True,
            timeout=120,
        )
        print(result.data)

asyncio.run(main())
```

### 通过 API 创建工作流

```python
workflow = client.create_workflow(
    title="我的工作流",
    brief="通过 SDK 创建",
    data={"nodes": [...], "edges": [...]},
    language="zh-CN",
)
print(workflow.wid)
```

### 工作流管理接口

```python
# 工作流
wf = client.get_workflow("workflow_id")
items = client.list_workflows(page=1, page_size=20)
client.update_workflow("workflow_id", data=wf.data, title="更新后的标题")

# 模板 / 标签
templates = client.list_workflow_templates(page=1, page_size=20)
tags = client.list_workflow_tags()

# 运行记录 / 调度
records = client.list_workflow_run_records(page=1, page_size=20)
schedules = client.list_workflow_run_schedules(page=1, page_size=20)

# 向量库 / 关系库数据资产
vector_dbs = client.list_vector_databases(page=1, page_size=20)
objects = client.list_vector_database_objects("vid_1", page=1, page_size=20)
tables = client.list_relational_database_tables("rid_1", page=1, page_size=20)
records = client.list_relational_database_table_records("tid_1", page=1, page_size=20)
```

## 工作流构建器

用纯 Python 代码构建工作流，无需手动编辑 JSON。

```python
from vectorvein.workflow.graph.workflow import Workflow
from vectorvein.workflow.nodes import OpenAI, TemplateCompose, TextInOut, Text

workflow = Workflow()

# 创建节点
text_input = TextInOut("input")
text_input.ports["text"].value = "给我讲个笑话"

template = TemplateCompose("tpl")
template.ports["template"].value = "用户说: {{user_input}}\n请用幽默的方式回应。"
template.add_port("user_input", "text", value="", is_output=False)

llm = OpenAI("llm")
llm.ports["llm_model"].value = "gpt-4"
llm.ports["temperature"].value = 0.9

output = Text("out")

# 组装工作流
workflow.add_nodes([text_input, template, llm, output])
workflow.connect(text_input, "output", template, "user_input")
workflow.connect(template, "output", llm, "prompt")
workflow.connect(llm, "output", output, "text")

# 校验 & 布局
print(workflow.check())   # {"no_cycle": True, "no_isolated_nodes": True, ...}
workflow.layout({"direction": "LR"})

# 导出
json_str = workflow.to_json()
mermaid_str = workflow.to_mermaid()

# 推送到平台
client.create_workflow(title="笑话机器人", data=workflow.to_dict())
```

### 可用节点类型 (50+)

| 分类 | 节点 |
|---|---|
| 大语言模型 | `OpenAI`, `Claude`, `Gemini`, `Deepseek`, `AliyunQwen`, `BaiduWenxin`, `ChatGLM`, `MiniMax`, `Moonshot`, `LingYiWanWu`, `XAi`, `CustomModel` |
| 文本处理 | `TextInOut`, `TemplateCompose`, `TextSplitters`, `TextReplace`, `TextTruncation`, `RegexExtract`, `ListRender`, `MarkdownToHtml` |
| 输出展示 | `Text`, `Table`, `Audio`, `Document`, `Html`, `Echarts`, `Email`, `Mermaid`, `Mindmap`, `PictureRender` |
| 图像生成 | `DallE`, `StableDiffusion`, `Flux1`, `Kolors`, `Recraft`, `Pulid`, `Inpainting`, `BackgroundGeneration` |
| 媒体处理 | `GptVision`, `ClaudeVision`, `GeminiVision`, `QwenVision`, `DeepseekVl`, `GlmVision`, `InternVision`, `Ocr`, `SpeechRecognition` |
| 媒体编辑 | `ImageEditing`, `ImageBackgroundRemoval`, `ImageSegmentation`, `ImageWatermark`, `AudioEditing`, `VideoEditing`, `VideoScreenshot` |
| 视频生成 | `KlingVideo`, `CogVideoX` |
| 音频 | `Tts`, `SoundEffects`, `MinimaxMusicGeneration` |
| 网页爬虫 | `TextCrawler`, `BilibiliCrawler`, `DouyinCrawler`, `YoutubeCrawler` |
| 工具 | `ProgrammingFunction`, `TextSearch`, `ImageSearch`, `TextTranslation`, `CodebaseAnalysis`, `WorkflowInvoke` |
| 控制流 | `Conditional`, `JsonProcess`, `RandomChoice`, `HumanFeedback`, `Empty` |
| 文件处理 | `FileUpload`, `FileLoader` |
| 关系数据库 | `RunSql`, `GetTableInfo`, `SmartQuery` |
| 向量数据库 | `AddData`, `DeleteData`, `Search` |
| 触发器 | `ButtonTrigger` |

### 工作流工具函数

```python
from vectorvein.workflow.utils.json_to_code import generate_python_code
from vectorvein.workflow.utils.analyse import analyse_workflow_record, format_workflow_analysis_for_llm

# 将工作流 JSON 转换为 Python 代码
code = generate_python_code(json_file="workflow.json")

# 分析工作流结构
result = analyse_workflow_record(json_str, connected_only=True)
summary = format_workflow_analysis_for_llm(result, max_length=200)
```

## AI 智能体

### 创建并运行智能体任务

```python
from vectorvein.api import VectorVeinClient, TaskInfo

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    # 创建智能体
    agent = client.create_agent(
        name="研究助手",
        system_prompt="你是一个专业的研究助手。",
        default_model_name="gpt-4",
    )

    # 运行任务
    task = client.create_agent_task(
        task_info=TaskInfo(text="总结最新的 AI 新闻"),
        agent_id_to_start=agent.agent_id,
    )

    # 查看状态
    task = client.get_agent_task(task.task_id)
    print(task.status, task.result)

    # 列出执行周期（推理步骤）
    cycles = client.list_agent_cycles(task_id=task.task_id)
    for cycle in cycles.cycles:
        print(f"周期 {cycle.cycle_index}: {cycle.title}")
```

### 任务控制

```python
client.pause_agent_task(task_id=task.task_id)     # 暂停
client.resume_agent_task(task_id=task.task_id)     # 恢复
client.continue_agent_task(task_id=task.task_id, message="也查一下 arxiv")  # 追加指令

# 添加待处理消息与任务偏好
client.add_pending_message(task_id=task.task_id, message="优先检查安全风险")
client.toggle_agent_task_favorite(task_id=task.task_id, is_favorited=True)

# 提示词优化相关能力
client.start_prompt_optimization(task_id=task.task_id, optimization_direction="提升指令清晰度")
optimizer = client.get_prompt_optimizer_config()

# 收藏智能体与系统提示词更新
favorites = client.list_favorite_agents(page=1, page_size=20)
client.update_agent_system_prompt(agent_id=agent.agent_id, system_prompt="你需要简洁且准确地回答。")
```

### 智能体生态接口

```python
# 合集 / 标签
collections = client.list_agent_collections(page=1, page_size=20)
tags = client.list_agent_tags()

# 技能 / 用户记忆
skills = client.list_skills(page=1, page_size=20)
memories = client.list_user_memories(page=1, page_size=20)

# MCP / 工作流工具 / 定时任务
servers = client.list_mcp_servers(page=1, page_size=20)
tools = client.list_my_workflow_tools()
schedules = client.list_task_schedules(page=1, page_size=20)
```

## 文件上传

```python
result = client.upload_file("report.pdf")
print(result.oss_path, result.file_size)
```

## 访问密钥管理

```python
# 创建长期访问密钥
keys = client.create_access_keys(access_key_type="L", app_id="app_id", description="生产密钥")
print(keys[0].access_key)

# 列出密钥
response = client.list_access_keys(page=1, page_size=20)
for key in response.access_keys:
    print(key.access_key, key.status, key.use_count)

# 删除
client.delete_access_keys(app_id="app_id", access_keys=["key_to_delete"])
```

## 智能体工作空间

```python
# 列出工作空间文件
files = client.list_workspace_files(workspace_id="ws_id")
for f in files.files:
    print(f.key, f.size)

# 读写文件
content = client.read_workspace_file(workspace_id="ws_id", file_path="notes.txt")
client.write_workspace_file(workspace_id="ws_id", file_path="output.txt", content="完成")

# 下载文件
url = client.download_workspace_file(workspace_id="ws_id", file_path="result.csv")

# 打包整个工作空间并获取下载链接
zip_info = client.zip_workspace_files(workspace_id="ws_id")
print(zip_info["download_url"])

# 触发容器到 OSS 的异步同步（Computer Agent 工作空间）
client.sync_workspace_container_to_oss(workspace_id="ws_id")
```

## 用户接口

```python
identity = client.validate_api_key()
print(identity.user_id, identity.username)

profile = client.get_user_info()
print(profile["username"], profile["credits"])
```

## 异常处理

所有异常继承自 `VectorVeinAPIError`：

| 异常类 | 说明 |
|---|---|
| `APIKeyError` | API 密钥无效或已过期 |
| `WorkflowError` | 工作流执行失败 |
| `AccessKeyError` | 访问密钥操作失败 |
| `RequestError` | HTTP 请求失败 |
| `TimeoutError` | 操作超时 |

```python
from vectorvein.api import VectorVeinClient, APIKeyError, WorkflowError, TimeoutError

try:
    result = client.run_workflow(wid="wf_id", input_fields=[], wait_for_completion=True, timeout=30)
except TimeoutError:
    print("工作流执行超时")
except WorkflowError as e:
    print(f"工作流失败: {e}")
except APIKeyError:
    print("请检查 API 密钥")
```

## 开发

```bash
git clone <repo-url>
cd vectorvein-sdk
pip install -e ".[dev]"

# 运行单元测试（不需要 API 密钥）
python -m pytest tests/ -v

# 运行全部测试（包括 live API 测试）
VECTORVEIN_RUN_LIVE_TESTS=1 python -m pytest tests/ -v
```

运行 live 测试前，将 `tests/dev_settings.example.py` 复制为 `tests/dev_settings.py` 并填入你的凭证。

## 许可证

MIT
