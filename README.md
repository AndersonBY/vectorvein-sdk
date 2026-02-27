# vectorvein-sdk

[中文文档](README_ZH.md)

Python SDK for the [VectorVein](https://vectorvein.com) platform — run workflows, build workflows programmatically, and manage AI agents.

## Installation

```bash
pip install vectorvein-sdk
```

Requires Python 3.10+.

## Quick Start

```python
from vectorvein.api import VectorVeinClient, WorkflowInputField

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    result = client.run_workflow(
        wid="YOUR_WORKFLOW_ID",
        input_fields=[
            WorkflowInputField(node_id="node_id", field_name="input", value="Hello"),
        ],
        wait_for_completion=True,
        timeout=60,
    )
    for output in result.data:
        print(f"{output.title}: {output.value}")
```

## CLI

After installation you can run:

```bash
vectorvein --help
```

Install methods that expose the `vectorvein` command:

```bash
pip install vectorvein-sdk
uv tool install vectorvein-sdk
```

### CLI Design (Agent-Friendly)

- **Self-descriptive help**: every module and subcommand has detailed `--help` text and examples.
- **Human-readable by default**: standard text output for normal terminal usage.
- **Machine mode on demand**: use `--format json` when an Agent needs structured output.
- **Predictable auth**: API key resolution order is `--api-key` > `VECTORVEIN_API_KEY`.
- **Stable exit codes**:
  - `0`: success
  - `2`: invalid CLI usage / arguments
  - `3`: authentication (API key) error
  - `4`: API business error
  - `5`: request/network error

### Common CLI Examples

```bash
# Auth / user
vectorvein --api-key YOUR_API_KEY auth whoami
vectorvein user info
vectorvein --format json auth whoami

# Workflow
vectorvein workflow run \
  --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hello"}'
vectorvein workflow status --rid rid_xxx
vectorvein workflow list --page 1 --page-size 10

# Task Agent
vectorvein task-agent agent list --page 1 --page-size 10
vectorvein task-agent task create --agent-id agent_xxx --text "Summarize this article"
vectorvein task-agent task continue --task-id task_xxx --message "Also provide a TL;DR"

# Agent Workspace
vectorvein agent-workspace list
vectorvein agent-workspace files --workspace-id ws_xxx
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20

# Raw request for advanced / not-yet-wrapped operations
vectorvein api request --method POST --endpoint workflow/list --body '{"page":1,"page_size":5}'
```

`auth whoami` returns `uid`, `username`, `email`, `credits`, and `date_joined` (it does not expose internal numeric user IDs).

### JSON Input Rules

- Options like `--input-field`, `--attachments`, `--body` accept inline JSON.
- You can also pass `@file.json`, for example: `--input-fields @inputs.json`.
- For `workflow run`, input field objects must include: `node_id`, `field_name`, `value`.

## Features

- **Sync & Async clients** — `VectorVeinClient` and `AsyncVectorVeinClient`
- **Workflow execution** — run workflows, poll status, create workflows via API
- **Workflow management APIs** — list/update workflows, records, schedules, templates, tags, trash, fast access
- **Workflow builder** — programmatically construct workflows with 50+ node types
- **AI Agent management** — create agents, run tasks, manage cycles
- **File upload** — upload files to the platform
- **Access key management** — create, list, update, delete access keys
- **Agent workspace** — read/write/list/zip files and trigger container sync
- **User APIs** — get current user info and validate API key

## Workflow Execution

### Synchronous

```python
from vectorvein.api import VectorVeinClient, WorkflowInputField

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    # Fire-and-forget
    rid = client.run_workflow(
        wid="workflow_id",
        input_fields=[WorkflowInputField(node_id="n1", field_name="text", value="hello")],
        wait_for_completion=False,
    )

    # Poll for result
    result = client.check_workflow_status(rid=rid)
    print(result.status, result.data)
```

### Asynchronous

```python
import asyncio
from vectorvein.api import AsyncVectorVeinClient, WorkflowInputField

async def main():
    async with AsyncVectorVeinClient(api_key="YOUR_API_KEY") as client:
        result = await client.run_workflow(
            wid="workflow_id",
            input_fields=[WorkflowInputField(node_id="n1", field_name="text", value="hello")],
            wait_for_completion=True,
            timeout=120,
        )
        print(result.data)

asyncio.run(main())
```

### Create a Workflow via API

```python
workflow = client.create_workflow(
    title="My Workflow",
    brief="Created via SDK",
    data={"nodes": [...], "edges": [...]},
    language="en-US",
)
print(workflow.wid)
```

### Workflow Management APIs

```python
# Workflows
wf = client.get_workflow("workflow_id")
items = client.list_workflows(page=1, page_size=20)
client.update_workflow("workflow_id", data=wf.data, title="Updated title")

# Templates / Tags
templates = client.list_workflow_templates(page=1, page_size=20)
tags = client.list_workflow_tags()

# Run records / schedules
records = client.list_workflow_run_records(page=1, page_size=20)
schedules = client.list_workflow_run_schedules(page=1, page_size=20)

# Vector / relational data assets
vector_dbs = client.list_vector_databases(page=1, page_size=20)
objects = client.list_vector_database_objects("vid_1", page=1, page_size=20)
tables = client.list_relational_database_tables("rid_1", page=1, page_size=20)
records = client.list_relational_database_table_records("tid_1", page=1, page_size=20)
```

## Workflow Builder

Build workflows in pure Python — no JSON editing required.

```python
from vectorvein.workflow.graph.workflow import Workflow
from vectorvein.workflow.nodes import OpenAI, TemplateCompose, TextInOut, Text

workflow = Workflow()

# Create nodes
text_input = TextInOut("input")
text_input.ports["text"].value = "Tell me a joke"

template = TemplateCompose("tpl")
template.ports["template"].value = "User says: {{user_input}}\nRespond with humor."
template.add_port("user_input", "text", value="", is_output=False)

llm = OpenAI("llm")
llm.ports["llm_model"].value = "gpt-4"
llm.ports["temperature"].value = 0.9

output = Text("out")

# Assemble
workflow.add_nodes([text_input, template, llm, output])
workflow.connect(text_input, "output", template, "user_input")
workflow.connect(template, "output", llm, "prompt")
workflow.connect(llm, "output", output, "text")

# Validate & layout
print(workflow.check())   # {"no_cycle": True, "no_isolated_nodes": True, ...}
workflow.layout({"direction": "LR"})

# Export
json_str = workflow.to_json()
mermaid_str = workflow.to_mermaid()

# Push to platform
client.create_workflow(title="Joke Bot", data=workflow.to_dict())
```

### Available Node Types (50+)

| Category | Nodes |
|---|---|
| LLMs | `OpenAI`, `Claude`, `Gemini`, `Deepseek`, `AliyunQwen`, `BaiduWenxin`, `ChatGLM`, `MiniMax`, `Moonshot`, `LingYiWanWu`, `XAi`, `CustomModel` |
| Text Processing | `TextInOut`, `TemplateCompose`, `TextSplitters`, `TextReplace`, `TextTruncation`, `RegexExtract`, `ListRender`, `MarkdownToHtml` |
| Output | `Text`, `Table`, `Audio`, `Document`, `Html`, `Echarts`, `Email`, `Mermaid`, `Mindmap`, `PictureRender` |
| Image Generation | `DallE`, `StableDiffusion`, `Flux1`, `Kolors`, `Recraft`, `Pulid`, `Inpainting`, `BackgroundGeneration` |
| Media Processing | `GptVision`, `ClaudeVision`, `GeminiVision`, `QwenVision`, `DeepseekVl`, `GlmVision`, `InternVision`, `Ocr`, `SpeechRecognition` |
| Media Editing | `ImageEditing`, `ImageBackgroundRemoval`, `ImageSegmentation`, `ImageWatermark`, `AudioEditing`, `VideoEditing`, `VideoScreenshot` |
| Video Generation | `KlingVideo`, `CogVideoX` |
| Audio | `Tts`, `SoundEffects`, `MinimaxMusicGeneration` |
| Web Crawlers | `TextCrawler`, `BilibiliCrawler`, `DouyinCrawler`, `YoutubeCrawler` |
| Tools | `ProgrammingFunction`, `TextSearch`, `ImageSearch`, `TextTranslation`, `CodebaseAnalysis`, `WorkflowInvoke` |
| Control Flow | `Conditional`, `JsonProcess`, `RandomChoice`, `HumanFeedback`, `Empty` |
| File Processing | `FileUpload`, `FileLoader` |
| Database | `RunSql`, `GetTableInfo`, `SmartQuery` |
| Vector DB | `AddData`, `DeleteData`, `Search` |
| Triggers | `ButtonTrigger` |

### Workflow Utilities

```python
from vectorvein.workflow.utils.json_to_code import generate_python_code
from vectorvein.workflow.utils.analyse import analyse_workflow_record, format_workflow_analysis_for_llm

# Convert workflow JSON to Python code
code = generate_python_code(json_file="workflow.json")

# Analyse workflow structure
result = analyse_workflow_record(json_str, connected_only=True)
summary = format_workflow_analysis_for_llm(result, max_length=200)
```

## AI Agent

### Create and Run an Agent Task

```python
from vectorvein.api import VectorVeinClient, TaskInfo

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    # Create an agent
    agent = client.create_agent(
        name="Research Assistant",
        system_prompt="You are a helpful research assistant.",
        default_model_name="gpt-4",
    )

    # Run a task
    task = client.create_agent_task(
        task_info=TaskInfo(text="Summarize the latest AI news"),
        agent_id_to_start=agent.agent_id,
    )

    # Check status
    task = client.get_agent_task(task.task_id)
    print(task.status, task.result)

    # List cycles (reasoning steps)
    cycles = client.list_agent_cycles(task_id=task.task_id)
    for cycle in cycles.cycles:
        print(f"Cycle {cycle.cycle_index}: {cycle.title}")
```

### Agent Task Control

```python
client.pause_agent_task(task_id=task.task_id)
client.resume_agent_task(task_id=task.task_id)
client.continue_agent_task(task_id=task.task_id, message="Also check arxiv")

# Pending input and task preferences
client.add_pending_message(task_id=task.task_id, message="Prioritize security checks")
client.toggle_agent_task_favorite(task_id=task.task_id, is_favorited=True)

# Prompt optimization helpers
client.start_prompt_optimization(task_id=task.task_id, optimization_direction="Improve instruction clarity")
optimizer = client.get_prompt_optimizer_config()

# Agent favorites and system-prompt updates
favorites = client.list_favorite_agents(page=1, page_size=20)
client.update_agent_system_prompt(agent_id=agent.agent_id, system_prompt="You are concise and accurate.")
```

### Agent Ecosystem APIs

```python
# Collections / tags
collections = client.list_agent_collections(page=1, page_size=20)
tags = client.list_agent_tags()

# Skills / user memory
skills = client.list_skills(page=1, page_size=20)
memories = client.list_user_memories(page=1, page_size=20)

# MCP / workflow tools / schedules
servers = client.list_mcp_servers(page=1, page_size=20)
tools = client.list_my_workflow_tools()
schedules = client.list_task_schedules(page=1, page_size=20)
```

## File Upload

```python
result = client.upload_file("report.pdf")
print(result.oss_path, result.file_size)
```

## Access Key Management

```python
# Create a long-term access key
keys = client.create_access_keys(access_key_type="L", app_id="app_id", description="prod key")
print(keys[0].access_key)

# List keys
response = client.list_access_keys(page=1, page_size=20)
for key in response.access_keys:
    print(key.access_key, key.status, key.use_count)

# Delete
client.delete_access_keys(app_id="app_id", access_keys=["key_to_delete"])
```

## Agent Workspace

```python
# List files in workspace
files = client.list_workspace_files(workspace_id="ws_id")
for f in files.files:
    print(f.key, f.size)

# Read / Write
content = client.read_workspace_file(workspace_id="ws_id", file_path="notes.txt")
client.write_workspace_file(workspace_id="ws_id", file_path="output.txt", content="done")

# Download
url = client.download_workspace_file(workspace_id="ws_id", file_path="result.csv")

# Zip all files in workspace
zip_info = client.zip_workspace_files(workspace_id="ws_id")
print(zip_info["download_url"])

# Trigger async container-to-OSS sync (Computer Agent workspace)
client.sync_workspace_container_to_oss(workspace_id="ws_id")
```

## User APIs

```python
identity = client.validate_api_key()
print(identity.user_id, identity.username)

profile = client.get_user_info()
print(profile["username"], profile["credits"])
```

## Exceptions

All exceptions inherit from `VectorVeinAPIError`:

| Exception | Description |
|---|---|
| `APIKeyError` | Invalid or expired API key |
| `WorkflowError` | Workflow execution failure |
| `AccessKeyError` | Access key operation failure |
| `RequestError` | HTTP request failure |
| `TimeoutError` | Operation timed out |

```python
from vectorvein.api import VectorVeinClient, APIKeyError, WorkflowError, TimeoutError

try:
    result = client.run_workflow(wid="wf_id", input_fields=[], wait_for_completion=True, timeout=30)
except TimeoutError:
    print("Workflow took too long")
except WorkflowError as e:
    print(f"Workflow failed: {e}")
except APIKeyError:
    print("Check your API key")
```

## Development

```bash
git clone <repo-url>
cd vectorvein-sdk
pip install -e ".[dev]"

# Run unit tests (no API key needed)
python -m pytest tests/ -v

# Run all tests including live API tests
VECTORVEIN_RUN_LIVE_TESTS=1 python -m pytest tests/ -v
```

For live tests, copy `tests/dev_settings.example.py` to `tests/dev_settings.py` and fill in your credentials.

## License

MIT
