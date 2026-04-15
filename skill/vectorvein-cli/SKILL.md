---
name: vectorvein-cli
description: Use when tasks require using the official `vectorvein` CLI from a shell, scripting workflow or task-agent operations, or navigating current VectorVein command paths instead of the Python SDK.
---

# VectorVein CLI

优先在 shell、CI、Agent 自动化里使用 `vectorvein`。需要精确 flag 时，先看内置帮助：`vectorvein --help`、`vectorvein <group> -h`、`vectorvein <group> <command> -h`。当前 CLI 的 help 已经提供分组说明、示例，以及错误时的推荐命令。

```bash
pip install vectorvein-sdk
# 或
uv tool install vectorvein-sdk
```

## 全局规则

| 规则 | 说明 |
|---|---|
| 鉴权优先级 | `--api-key` > `VECTORVEIN_API_KEY` |
| 地址优先级 | `--base-url` > `VECTORVEIN_BASE_URL` |
| 输出格式 | 默认 `text`；脚本或 Agent 消费用 `--format json` |
| 紧凑 JSON | `--compact` 仅在 `--format json` 时有意义 |
| 调试 | `--debug` 会在错误输出里带 traceback |
| 退出码 | `0` 成功，`2` 用法错误，`3` 鉴权错误，`4` API 业务错误，`5` 网络错误 |

## 输入约定

- JSON 参数通常支持内联 JSON 或 `@file`。常见参数：`--body`、`--input-field`、`--input-fields`、`--attachments`、`--shared-meta`、`--task-info`、`--data`
- 长文本参数通常支持 `@file`。常见参数：`--description`、`--system-prompt`、`--brief`、`--text`、`--message`、`--content`、`--comment`
- `workflow run --input-field` 的对象格式必须是 `{"node_id":"...","field_name":"...","value":...}`
- `workflow run --upload-to` 的格式是 `node_id:field_name:local_file_path`
- `task-agent` 的 JSON schema 使用 `compress_memory_after_tokens`，不要再传旧的字符阈值字段
- 如果 `task-agent task create --model-preference custom`，还要同时给 `--custom-backend-type` 和 `--custom-model-name`

## 顶层命令

### auth / user

```bash
vectorvein auth whoami
vectorvein --format json auth whoami
vectorvein user info
vectorvein user validate-api-key
```

### workflow

先用 `describe` 看输入，再 `run`。常用路径：

```bash
vectorvein workflow describe --wid wf_xxx

vectorvein workflow run \
  --wid wf_xxx \
  --input-fields @inputs.json \
  --wait --timeout 300

vectorvein workflow run --wid wf_xxx \
  --upload-to n1:upload_files:./report.pdf
vectorvein workflow run --wid wf_xxx \
  --upload-to n1:upload_files:./a.pdf \
  --upload-to n1:upload_files:./b.pdf \
  --upload-as list

vectorvein workflow status --rid rid_xxx
vectorvein workflow status --rid rid_xxx --wid wf_xxx --api-key-type VAPP
vectorvein workflow list --page 1 --page-size 20
vectorvein workflow search --query "translation"
vectorvein workflow get --wid wf_xxx
vectorvein workflow create --title "My Workflow" --source-wid wf_xxx
vectorvein workflow update --wid wf_xxx --data @workflow.json --title "Renamed"
vectorvein workflow delete --wid wf_xxx

vectorvein workflow run-record list --wid wf_xxx --status FINISHED
vectorvein workflow run-record get --rid rid_xxx
vectorvein workflow run-record stop --rid rid_xxx
vectorvein workflow run-record delete --rid rid_xxx
```

`workflow run` 还支持 `--output-scope all|output_fields_only`，以及：

```bash
vectorvein workflow run --wid wf_xxx --api-key-type VAPP \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hi"}'
```

### file

```bash
vectorvein file upload --path ./report.pdf
vectorvein file upload --path ./a.pdf --path ./b.pdf
```

### task-agent

先用导航 help，再进入具体分组：

```bash
vectorvein task-agent -h
vectorvein task-agent agent -h
vectorvein task-agent task -h
vectorvein task-agent skill -h
```

当前主要分组是 `agent`、`task`、`cycle`、`tag`、`collection`、`mcp-server`、`mcp-tool`、`user-memory`、`skill`、`skill-review`、`task-category`、`tool-category`、`workflow-tool`、`task-schedule`。

#### agent

```bash
vectorvein task-agent agent list --page 1 --page-size 10
vectorvein task-agent agent list --is-public true --official true
vectorvein task-agent agent search --query "research" --is-public true
vectorvein task-agent agent get --agent-id agent_xxx

vectorvein task-agent agent create \
  --name "Research Assistant" \
  --system-prompt @prompt.md \
  --model-name gpt-4o \
  --backend-type openai \
  --default-load-user-memory true \
  --default-compress-memory-after-tokens 64000 \
  --available-mcp-tool-ids '["tool_1"]' \
  --tag-ids '["tag_1"]'

vectorvein task-agent agent update \
  --agent-id agent_xxx \
  --default-load-user-memory false \
  --tag-ids '["tag_2"]'

vectorvein task-agent agent favorite-list --tag-ids '["tag_1"]'
vectorvein task-agent agent duplicate --agent-id agent_xxx --add-templates true
vectorvein task-agent agent toggle-favorite --agent-id agent_xxx --is-favorited true
vectorvein task-agent agent update-system-prompt --agent-id agent_xxx --system-prompt @prompt.md
vectorvein task-agent agent create-optimized --agent-id agent_xxx --system-prompt @optimized-prompt.md
vectorvein task-agent agent delete --agent-id agent_xxx
```

`agent create` / `update` 已对齐最新 schema，常见扩展字段包括 `--usage-hint`、`--default-workspace-files`、`--default-sub-agent-ids`、`--required-skills`、`--default-output-verifier`、`--default-cloud-storage-paths`、`--available-workflow-ids`、`--available-template-ids`、`--shared`、`--is-public`。

#### task

```bash
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text @task.md \
  --wait

vectorvein task-agent task create \
  --text "Analyze this report" \
  --agent-definition @agent-definition.json \
  --agent-settings @agent-settings.json

vectorvein task-agent task continue --task-id task_xxx --message @reply.md --wait
vectorvein task-agent task respond --task-id task_xxx --tool-call-id tc_xxx --response "Yes, proceed" --wait
vectorvein task-agent task pause --task-id task_xxx
vectorvein task-agent task resume --task-id task_xxx --message "Continue" --wait

vectorvein task-agent task get --task-id task_xxx
vectorvein task-agent task list --status running --agent-id agent_xxx
vectorvein task-agent task search --query "summary"
vectorvein task-agent task delete --task-id task_xxx
vectorvein task-agent task update-share --task-id task_xxx --shared true --shared-meta @share-meta.json
vectorvein task-agent task get-shared --task-id task_xxx
vectorvein task-agent task public-shared-list --search design
vectorvein task-agent task batch-delete --task-ids '["task_1","task_2"]'
vectorvein task-agent task add-pending-message --task-id task_xxx --message @note.md
vectorvein task-agent task toggle-hidden --task-id task_xxx --is-hidden true
vectorvein task-agent task toggle-favorite --task-id task_xxx --is-favorited true
vectorvein task-agent task start-prompt-optimization --task-id task_xxx --optimization-direction @goal.md
vectorvein task-agent task prompt-optimizer-config
vectorvein task-agent task computer-pod-settings
vectorvein task-agent task close-computer-environment --task-id task_xxx
```

#### cycle

```bash
vectorvein task-agent cycle list --task-id task_xxx
vectorvein task-agent cycle get --cycle-id cycle_xxx
vectorvein task-agent cycle run-workflow --cycle-id cycle_xxx --tool-name search --workflow-inputs @inputs.json
vectorvein task-agent cycle check-workflow-status --rid rid_xxx
vectorvein task-agent cycle finish-task --cycle-id cycle_xxx --message @done.md
vectorvein task-agent cycle replay --task-id task_xxx --start-index 0 --end-index 3
vectorvein task-agent cycle replay-summary --task-id task_xxx
```

#### 生态分组速查

| 分组 | 用途 | 典型命令 |
|---|---|---|
| `tag` | 管理 agent 标签 | `vectorvein task-agent tag list --public-only true` |
| `collection` | 管理 agent 合集 | `vectorvein task-agent collection create --title "Docs Agents" --data @collection.json` |
| `mcp-server` | 注册或测试 MCP Server | `vectorvein task-agent mcp-server test-connection --data @server.json` |
| `mcp-tool` | 管理 MCP 工具与日志 | `vectorvein task-agent mcp-tool logs --tool-id tool_xxx --page 1 --page-size 20` |
| `user-memory` | 管理持久记忆 | `vectorvein task-agent user-memory batch-toggle --memory-ids '["memory_1"]' --is-active true` |
| `skill` | 浏览、创建、安装技能 | `vectorvein task-agent skill install --skill-id skill_xxx --permission-level auto` |
| `skill-review` | 技能评分与评论 | `vectorvein task-agent skill-review create --skill-id skill_xxx --rating 5 --comment @review.md` |
| `task-category` | 列出任务分类 | `vectorvein task-agent task-category list` |
| `tool-category` | 列出工具分类 | `vectorvein task-agent tool-category list` |
| `workflow-tool` | 把工作流发布成可复用工具 | `vectorvein task-agent workflow-tool batch-create --workflow-wids '["wf_1"]' --template-tids '["tpl_1"]' --category-id cat_xxx` |
| `task-schedule` | 管理定时任务 | `vectorvein task-agent task-schedule update --cron-expression '0 0 * * *' --agent-id agent_xxx --task-info @task-info.json` |

技能相关的高频命令还包括：

```bash
vectorvein task-agent skill list --search markdown
vectorvein task-agent skill my-skills
vectorvein task-agent skill upload-and-parse --path ./demo.skill --filename demo.skill
vectorvein task-agent skill installed --agent-id agent_xxx
vectorvein task-agent skill update-installation --installation-id install_xxx --is-enabled true
vectorvein task-agent skill set-agent-override --skill-id skill_xxx --agent-id agent_xxx --is-enabled true
vectorvein task-agent skill remove-agent-override --skill-id skill_xxx --agent-id agent_xxx
vectorvein task-agent skill categories
```

### agent-workspace

```bash
vectorvein agent-workspace list
vectorvein agent-workspace get --workspace-id ws_xxx
vectorvein agent-workspace files --workspace-id ws_xxx --prefix docs/ --tree-view
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20
vectorvein agent-workspace write --workspace-id ws_xxx --file-path output.txt --content @local.txt
vectorvein agent-workspace delete --workspace-id ws_xxx --file-path old.txt
vectorvein agent-workspace download --workspace-id ws_xxx --file-path result.csv
vectorvein agent-workspace zip --workspace-id ws_xxx
vectorvein agent-workspace sync --workspace-id ws_xxx
```

### api

仅在 CLI 还没封装高层命令时退回原始请求。支持 `GET`、`POST`、`PUT`、`PATCH`、`DELETE`。

```bash
vectorvein api request --method GET --endpoint user-info/get
vectorvein api request --method POST --endpoint workflow/list --body '{"page":1,"page_size":5}'
vectorvein api request --method POST --endpoint workflow/check-status --body @payload.json
```

## 常用工作流

### 查看输入后再运行工作流

```bash
vectorvein workflow describe --wid wf_xxx
vectorvein --format json workflow run --wid wf_xxx --input-fields @inputs.json --wait
```

### 创建 agent 后直接发任务

```bash
vectorvein task-agent agent create --name "Ops Assistant" --system-prompt @prompt.md
vectorvein task-agent task create --agent-id agent_xxx --text @task.md --wait
```

### 发布 workflow tool 并挂到定时任务

```bash
vectorvein task-agent workflow-tool batch-create \
  --workflow-wids '["wf_1"]' \
  --template-tids '["tpl_1"]' \
  --category-id cat_xxx

vectorvein task-agent task-schedule update \
  --cron-expression '0 0 * * *' \
  --agent-id agent_xxx \
  --task-info @task-info.json
```

## 使用建议

- 不确定命令路径时，先跑 `-h`。当前 CLI 会给分组说明、示例，缺少子组时还会提示推荐命令
- 自动化脚本默认用 `--format json`，交互式排查默认用文本输出
- 先用高层命令；只有遇到 CLI 还没封装的接口，再退回 `vectorvein api request`
- 需要和本地文件交互时，优先用 `@file` 和 `agent-workspace`，不要把大段 JSON 或 prompt 直接硬编码在 shell 里
```
