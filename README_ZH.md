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

## 功能概览

- **同步 & 异步客户端** — `VectorVeinClient` 和 `AsyncVectorVeinClient`
- **工作流执行** — 运行工作流、轮询状态、通过 API 创建工作流
- **工作流构建器** — 用 Python 代码构建工作流，支持 50+ 节点类型
- **AI 智能体管理** — 创建智能体、运行任务、管理执行周期
- **文件上传** — 上传文件到平台
- **访问密钥管理** — 创建、列出、更新、删除访问密钥
- **智能体工作空间** — 读写、列出智能体工作空间中的文件

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
client.continue_agent_task(task_id=task.task_id, task_info=TaskInfo(text="也查一下 arxiv"))  # 追加指令
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
