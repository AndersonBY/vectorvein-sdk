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
- **Strict hierarchy**: task-agent commands stay explicit, for example `vectorvein task-agent agent create`.
- **Human-readable by default**: standard text output for normal terminal usage.
- **Machine mode on demand**: use `--format json` when an Agent needs structured output.
- **Repairable usage errors**: invalid command paths explain what is wrong and suggest corrected commands.
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
vectorvein workflow run \
  --wid wf_xxx \
  --upload-to n1:upload_files:./report.pdf
vectorvein workflow run \
  --wid wf_xxx \
  --upload-to n1:upload_files:./a.pdf \
  --upload-to n1:upload_files:./b.pdf \
  --upload-as list
vectorvein workflow status --rid rid_xxx
vectorvein workflow list --page 1 --page-size 10
vectorvein workflow get --wid wf_xxx
vectorvein workflow describe --wid wf_xxx
vectorvein workflow create --title 'My Workflow' --source-wid wf_xxx
vectorvein workflow update --wid wf_xxx --data @workflow_data.json --title 'Updated'
vectorvein workflow delete --wid wf_xxx
vectorvein workflow search --query 'translation'

# Workflow run records
vectorvein workflow run-record list --wid wf_xxx --status FINISHED
vectorvein workflow run-record get --rid rid_xxx
vectorvein workflow run-record stop --rid rid_xxx

# File upload
vectorvein file upload --path ./report.pdf
vectorvein file upload --path ./a.pdf --path ./b.pdf

# Task Agent — agents
vectorvein task-agent agent list --page 1 --page-size 10
vectorvein task-agent agent get --agent-id agent_xxx
vectorvein task-agent agent create --name 'My Bot' --system-prompt 'Be helpful'
vectorvein task-agent agent create \
  --name 'Research Assistant' \
  --model-name gpt-4o \
  --backend-type openai \
  --default-compress-memory-after-tokens 64000 \
  --default-load-user-memory true \
  --available-mcp-tool-ids '["tool_1"]'
vectorvein task-agent agent update --agent-id agent_xxx --name 'New Name'
vectorvein task-agent agent delete --agent-id agent_xxx
vectorvein task-agent agent search --query 'translator'
vectorvein task-agent agent public-list --official true
vectorvein task-agent agent favorite-list --tag-ids '["tag_1"]'
vectorvein task-agent agent duplicate --agent-id agent_xxx --add-templates true
vectorvein task-agent agent toggle-favorite --agent-id agent_xxx --is-favorited true

# Task Agent — tasks
vectorvein task-agent task create --agent-id agent_xxx --text "Summarize this article"
vectorvein task-agent task create --agent-id agent_xxx --text "Do it" --wait --timeout 120
vectorvein task-agent task create \
  --text "Analyze the report" \
  --agent-definition @agent_definition.json \
  --agent-settings @agent_settings.json
vectorvein task-agent task continue --task-id task_xxx --message "Also provide a TL;DR" --wait
vectorvein task-agent task respond --task-id task_xxx --tool-call-id tc_xxx --response "Yes, proceed"
vectorvein task-agent task get --task-id task_xxx
vectorvein task-agent task list --status running --agent-id agent_xxx
vectorvein task-agent task search --query 'summary'
vectorvein task-agent task delete --task-id task_xxx
vectorvein task-agent task update-share --task-id task_xxx --shared true --shared-meta @share_meta.json
vectorvein task-agent task public-shared-list --search research
vectorvein task-agent task batch-delete --task-ids '["task_1","task_2"]'
vectorvein task-agent task prompt-optimizer-config

# Task Agent — cycles
vectorvein task-agent cycle list --task-id task_xxx
vectorvein task-agent cycle get --cycle-id cycle_xxx
vectorvein task-agent cycle run-workflow --cycle-id cycle_xxx --tool-name search --workflow-inputs @workflow_inputs.json
vectorvein task-agent cycle replay --task-id task_xxx --start-index 0 --end-index 3

# Task Agent — tags / collections
vectorvein task-agent tag create --title Office --color '#3366ff'
vectorvein task-agent tag list --public-only true
vectorvein task-agent collection create --title 'Docs Agents' --description 'Knowledge assistants' --data @collection.json
vectorvein task-agent collection add-agent --collection-id collection_xxx --agent-id agent_xxx

# Task Agent — MCP / memory / skills
vectorvein task-agent mcp-server test-connection --data @mcp_server.json
vectorvein task-agent mcp-tool list --server-id server_xxx
vectorvein task-agent user-memory create --content 'Remember I prefer markdown.'
vectorvein task-agent user-memory batch-toggle --memory-ids '["memory_1"]' --is-active true
vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto
vectorvein task-agent skill upload-and-parse --path ./demo.skill --filename demo.skill
vectorvein task-agent skill-review create --skill-id skill_xxx --rating 5 --comment 'Great skill'

# Task Agent — workflow tools / schedules / categories
vectorvein task-agent task-category list
vectorvein task-agent tool-category list
vectorvein task-agent workflow-tool batch-create --workflow-wids '["wf_1"]' --template-tids '["tpl_1"]' --category-id cat_xxx
vectorvein task-agent task-schedule update --cron-expression '0 0 * * *' --agent-id agent_xxx --task-info @task_info.json

# Agent Workspace
vectorvein agent-workspace list
vectorvein agent-workspace files --workspace-id ws_xxx
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20
vectorvein agent-workspace write --workspace-id ws_xxx --file-path output.txt --content 'done'
vectorvein agent-workspace delete --workspace-id ws_xxx --file-path old.txt
vectorvein agent-workspace download --workspace-id ws_xxx --file-path result.csv
vectorvein agent-workspace zip --workspace-id ws_xxx
vectorvein agent-workspace sync --workspace-id ws_xxx

# Raw request for advanced / not-yet-wrapped operations
vectorvein api request --method POST --endpoint workflow/list --body '{"page":1,"page_size":5}'
```

`auth whoami` returns `uid`, `username`, `email`, `credits`, and `date_joined` (it does not expose internal numeric user IDs).
`workflow list` hides verbose fields by default: `language`, `images`, `is_fast_access`, `browser_settings`, `chrome_settings`, `use_in_wechat`.

### JSON Input Rules

- Options like `--input-field`, `--attachments`, `--body` accept inline JSON.
- You can also pass `@file.json`, for example: `--input-fields @inputs.json`.
- For `workflow run`, input field objects must include: `node_id`, `field_name`, `value`.
- `workflow run --upload-to` format: `node_id:field_name:local_file_path` (repeat this option for multiple files).
- Task-agent `--agent-definition` / `--agent-settings` must use `compress_memory_after_tokens`; legacy character-threshold fields are rejected with fix suggestions.

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
from vectorvein.api import AgentDefinition, AgentSettings, TaskInfo, VectorVeinClient

with VectorVeinClient(api_key="YOUR_API_KEY") as client:
    # Create an agent
    agent = client.create_agent(
        name="Research Assistant",
        system_prompt="You are a helpful research assistant.",
        default_model_name="gpt-5.4",
        default_load_user_memory=True,
        default_compress_memory_after_tokens=64000,
        default_cloud_storage_paths=["/documents/reports"],
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

### Agent Schema Notes

```python
# Custom agent definitions / settings follow backend ai_agents field names.
# Use *_after_tokens; legacy *_after_characters is removed from the SDK.
definition = AgentDefinition(
    model_name="glm-5.1",
    backend_type="zhipuai",
    compress_memory_after_tokens=64000,
    agent_type="computer",
    workspace_files=[],
    sub_agent_ids=[],
)

settings = AgentSettings(
    model_name="glm-5.1",
    backend_type="zhipuai",
    compress_memory_after_tokens=96000,
    agent_type="tool",
)
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
