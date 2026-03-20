---
name: vectorvein-cli
description: VectorVein CLI 完整使用指南。当用户需要通过命令行操作 VectorVein 平台时使用此 skill，包括：运行工作流（workflow run）、管理工作流（list/create/update/delete）、上传文件、管理 AI Agent 及任务（task-agent）、操作 Agent 工作区（agent-workspace）、查看用户信息等。即使用户没有明确提到 CLI，只要任务涉及通过终端/命令行与 VectorVein 交互、自动化调用 VectorVein API、或者需要用 shell 脚本编排 VectorVein 操作，都应使用此 skill。
---

# VectorVein CLI

`vectorvein` 是 VectorVein 平台的命令行工具，安装 `vectorvein-sdk` 后即可使用。

```bash
pip install vectorvein-sdk
# 或
uv tool install vectorvein-sdk
```

---

## 认证与全局选项

每条命令都支持以下全局选项：

| 选项 | 说明 |
|---|---|
| `--api-key <key>` | API 密钥，优先级高于环境变量 `VECTORVEIN_API_KEY` |
| `--base-url <url>` | 自定义 API 地址，优先级高于环境变量 `VECTORVEIN_BASE_URL` |
| `--format text\|json` | 输出格式，默认 `text`（人类可读），`json` 适合脚本/Agent 消费 |
| `--compact` | 搭配 `--format json` 输出单行紧凑 JSON |
| `--debug` | 错误时输出完整 traceback |

**认证方式（二选一）：**

```bash
# 方式一：环境变量（推荐）
export VECTORVEIN_API_KEY="your_key"
vectorvein auth whoami

# 方式二：命令行参数
vectorvein --api-key your_key auth whoami
```

**退出码：** 0=成功, 2=参数错误, 3=认证错误, 4=API 业务错误, 5=网络错误

---

## JSON 输入规则

接受 JSON 的选项（如 `--input-field`、`--body`、`--attachments`）支持两种传递方式：

```bash
# 内联 JSON
--body '{"page":1}'

# 从文件读取（@前缀）
--input-fields @inputs.json
--body @payload.json
```

---

## 命令参考

### auth — 认证

```bash
# 查看当前账户信息（uid, username, email, credits, date_joined）
vectorvein auth whoami

# JSON 格式输出
vectorvein --format json auth whoami
```

### user — 用户

```bash
# 完整用户资料
vectorvein user info

# 验证 API key 有效性
vectorvein user validate-api-key
```

### workflow — 工作流

#### 运行工作流

```bash
# 基本运行（传入输入字段）
vectorvein workflow run \
  --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hello"}'

# 从文件读取输入字段
vectorvein workflow run --wid wf_xxx --input-fields @inputs.json

# 同步等待完成（轮询，默认超时 300 秒）
vectorvein workflow run --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hello"}' \
  --wait --timeout 180

# 上传文件并绑定到工作流输入（格式：node_id:field_name:本地路径）
vectorvein workflow run --wid wf_xxx \
  --upload-to n1:upload_files:./report.pdf

# 上传多个文件到同一字段（用 --upload-as list）
vectorvein workflow run --wid wf_xxx \
  --upload-to n1:upload_files:./a.pdf \
  --upload-to n1:upload_files:./b.pdf \
  --upload-as list

# 控制输出范围
vectorvein workflow run --wid wf_xxx --output-scope all
# output-scope: all | output_fields_only（默认）

# 使用 VAPP 类型密钥
vectorvein workflow run --wid wf_xxx --api-key-type VAPP \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hi"}'
```

**`--input-field` 格式：** `{"node_id":"<节点ID>","field_name":"<字段名>","value":"<值>"}`
**`--upload-to` 格式：** `node_id:field_name:local_file_path`

#### 查询工作流状态

```bash
vectorvein workflow status --rid rid_xxx

# VAPP 密钥需要同时传 --wid
vectorvein workflow status --rid rid_xxx --wid wf_xxx --api-key-type VAPP
```

#### 描述工作流输入字段（Agent 友好）

```bash
# 返回标题、简介和所有用户输入字段（含类型和默认值）
vectorvein workflow describe --wid wf_xxx
```

#### 工作流 CRUD

```bash
# 列表
vectorvein workflow list --page 1 --page-size 10
vectorvein workflow list --tag tag_id --search-text "关键词" --sort-field update_time --sort-order descend

# 搜索
vectorvein workflow search --query "translation"

# 获取详情
vectorvein workflow get --wid wf_xxx

# 创建（可从已有工作流复制）
vectorvein workflow create --title "My Workflow" --brief "描述" --language zh-CN
vectorvein workflow create --title "Copy" --source-wid wf_xxx

# 更新
vectorvein workflow update --wid wf_xxx --data @workflow_data.json --title "Updated"

# 删除
vectorvein workflow delete --wid wf_xxx
```

#### 运行记录

```bash
# 列表（可按状态过滤：FINISHED, FAILED, RUNNING 等）
vectorvein workflow run-record list --wid wf_xxx --status FINISHED

# 获取单条记录
vectorvein workflow run-record get --rid rid_xxx

# 删除记录
vectorvein workflow run-record delete --rid rid_xxx

# 停止正在运行的任务
vectorvein workflow run-record stop --rid rid_xxx
```

### file — 文件上传

```bash
# 上传单个文件（返回 OSS 路径、文件名、大小、类型）
vectorvein file upload --path ./report.pdf

# 上传多个文件
vectorvein file upload --path ./a.pdf --path ./b.pdf
```

### task-agent — AI Agent

#### Agent 管理

```bash
# 列表
vectorvein task-agent agent list --page 1 --page-size 10

# 搜索
vectorvein task-agent agent search --query "translator"

# 获取详情
vectorvein task-agent agent get --agent-id agent_xxx

# 创建
vectorvein task-agent agent create \
  --name "My Bot" \
  --system-prompt "You are a helpful assistant." \
  --model-name gpt-4 \
  --max-cycles 20

# 更新
vectorvein task-agent agent update --agent-id agent_xxx --name "New Name"

# 删除
vectorvein task-agent agent delete --agent-id agent_xxx
```

#### 任务管理

```bash
# 创建任务
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text "Summarize this article"

# 创建并等待完成（默认超时 600 秒）
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text "Do it" \
  --wait --timeout 120

# 带附件创建
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text "Analyze this file" \
  --attachment '{"name":"report.pdf","url":"https://..."}'

# 自定义模型偏好
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text "Quick task" \
  --model-preference low_cost

# 继续对话
vectorvein task-agent task continue \
  --task-id task_xxx \
  --message "Also provide a TL;DR" \
  --wait

# 回复 Agent 的提问（human-in-the-loop）
vectorvein task-agent task respond \
  --task-id task_xxx \
  --tool-call-id tc_xxx \
  --response "Yes, proceed"

# 暂停 / 恢复
vectorvein task-agent task pause --task-id task_xxx
vectorvein task-agent task resume --task-id task_xxx --wait

# 查询 / 搜索 / 删除
vectorvein task-agent task get --task-id task_xxx
vectorvein task-agent task list --status running --agent-id agent_xxx
vectorvein task-agent task search --query "summary"
vectorvein task-agent task delete --task-id task_xxx
```

#### 推理步骤（Cycles）

```bash
vectorvein task-agent cycle list --task-id task_xxx
vectorvein task-agent cycle get --cycle-id cycle_xxx
```

### agent-workspace — Agent 工作区

```bash
# 列表工作区
vectorvein agent-workspace list --page 1 --page-size 10

# 获取工作区详情
vectorvein agent-workspace get --workspace-id ws_xxx

# 列出文件（支持前缀过滤和树形视图）
vectorvein agent-workspace files --workspace-id ws_xxx
vectorvein agent-workspace files --workspace-id ws_xxx --prefix docs/ --tree-view

# 读取文件（支持行范围）
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt
vectorvein agent-workspace read --workspace-id ws_xxx --file-path notes.txt --start-line 1 --end-line 20

# 写入文件
vectorvein agent-workspace write --workspace-id ws_xxx --file-path output.txt --content "done"
vectorvein agent-workspace write --workspace-id ws_xxx --file-path output.txt --content-file ./local.txt

# 删除文件
vectorvein agent-workspace delete --workspace-id ws_xxx --file-path old.txt

# 获取临时下载链接
vectorvein agent-workspace download --workspace-id ws_xxx --file-path result.csv

# 打包下载整个工作区
vectorvein agent-workspace zip --workspace-id ws_xxx

# 触发容器到 OSS 的同步（Computer Agent 工作区）
vectorvein agent-workspace sync --workspace-id ws_xxx
```

### api — 原始 API 请求

用于尚未封装的接口或高级用法：

```bash
vectorvein api request --method POST --endpoint workflow/list --body '{"page":1,"page_size":5}'
vectorvein api request --method GET --endpoint user-info/get
vectorvein api request --method POST --endpoint workflow/check-status --body @payload.json
```

支持的 HTTP 方法：GET, POST, PUT, PATCH, DELETE

---

## 常用脚本模式

### 运行工作流并获取 JSON 结果

```bash
vectorvein --format json workflow run \
  --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"Hello"}' \
  --wait --timeout 300
```

### 批量上传文件后运行工作流

```bash
vectorvein workflow run --wid wf_xxx \
  --upload-to n1:upload_files:./file1.pdf \
  --upload-to n1:upload_files:./file2.pdf \
  --upload-as list \
  --wait

```

### 查看工作流的输入字段后运行

```bash
# 先看看需要哪些输入
vectorvein workflow describe --wid wf_xxx

# 然后根据输出构造输入
vectorvein workflow run --wid wf_xxx \
  --input-field '{"node_id":"n1","field_name":"text","value":"..."}'
```

### 创建 Agent 任务并轮询结果

```bash
vectorvein task-agent task create \
  --agent-id agent_xxx \
  --text "Research the latest AI trends" \
  --wait --timeout 600
```
