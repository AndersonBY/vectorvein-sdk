"""VectorVein API data model definitions"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VApp:
    """VApp information"""

    app_id: str
    title: str
    description: str
    info: dict[str, Any]
    images: list[str]
    workflow: str | None = None
    status: str | None = None
    public: bool | None = None
    public_process_status: str | None = None
    create_time: str | None = None
    update_time: str | None = None
    user: dict[str, Any] | None = None
    used_credits: int | None = None
    run_count: int | None = None
    sync_workflow_update_time: str | None = None
    wx_mini_program_settings: dict[str, Any] | None = None
    payment_settings: dict[str, Any] | None = None


@dataclass
class APIUserIdentity:
    """Validated user identity."""

    user_id: str
    username: str


@dataclass
class AccessKey:
    """Access key information"""

    access_key: str
    access_key_type: str  # O: one-time, M: multiple, L: long-term
    use_count: int
    max_use_count: int | None
    max_credits: int | None
    used_credits: int
    v_app: VApp | None
    v_apps: list[VApp]
    records: list[Any]
    status: str  # AC: valid, IN: invalid, EX: expired, US: used
    access_scope: str  # S: single application, M: multiple applications
    description: str
    create_time: str
    expire_time: str
    last_use_time: str | None


@dataclass
class WorkflowInputField:
    """Workflow input field"""

    node_id: str
    field_name: str
    value: Any


@dataclass
class WorkflowOutput:
    """Workflow output result"""

    type: str
    title: str
    value: Any


@dataclass
class WorkflowRunResult:
    """Workflow run result"""

    rid: str
    status: int
    msg: str
    data: list[WorkflowOutput] | dict[str, Any]


@dataclass
class AccessKeyListResponse:
    """Access key list response"""

    access_keys: list[AccessKey]
    total: int
    page_size: int
    page: int


@dataclass
class WorkflowTag:
    """Workflow tag"""

    tid: str
    title: str
    is_public: bool = False
    language: str | None = None
    color: str | None = None


@dataclass
class Workflow:
    """Workflow information"""

    wid: str
    title: str
    brief: str
    data: dict[str, Any]
    language: str
    images: list[str]
    tags: list[WorkflowTag]
    source_workflow: str | None = None
    tool_call_data: dict[str, Any] | None = None
    create_time: str | None = None
    update_time: str | None = None


@dataclass
class WorkflowCreateRequest:
    """Workflow creation request data"""

    title: str = "New workflow"
    brief: str = ""
    images: list[str] | None = None
    tags: list[dict[str, str]] | None = None
    data: dict[str, Any] | None = None
    language: str = "zh-CN"
    tool_call_data: dict[str, Any] | None = None
    source_workflow_wid: str | None = None


# File Upload Models
@dataclass
class FileUploadResult:
    """File upload result"""

    oss_path: str
    original_filename: str
    file_size: int
    content_type: str


# Task Agent Models
@dataclass
class AttachmentDetail:
    """Attachment detail"""

    name: str
    url: str


@dataclass
class OssAttachmentDetail:
    """Attachment detail"""

    name: str
    oss_key: str


@dataclass
class TaskInfo:
    """Task information"""

    text: str
    attachments_detail: list[AttachmentDetail | OssAttachmentDetail] | None = None
    model_preference: str = "default"  # default, high_performance, low_cost, custom
    custom_backend_type: str | None = None
    custom_model_name: str | None = None
    reasoning_effort: str | None = None
    enable_workflow_design_tools: bool | None = None


@dataclass
class AgentDefinition:
    """Agent definition"""

    model_name: str
    backend_type: str
    system_prompt: str = "You are a helpful assistant."
    allow_interruption: bool = True
    use_workspace: bool = True
    compress_memory_after_tokens: int | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    agent_type: str | None = None
    workspace_files: list[dict[str, Any]] = field(default_factory=list)
    sub_agent_ids: list[str] = field(default_factory=list)
    computer_pod_setting_id: str | None = None
    output_verifier: str | None = None
    active_skills: list[str] | None = None
    bound_skills: list[dict[str, str]] | None = None
    required_skills_status: dict[str, Any] | None = None
    enable_workflow_design_tools: bool | None = None
    reasoning_effort: str | None = None
    progress_mode: str | None = None
    sandbox_resource_tier: str | None = None


@dataclass
class AgentSettings:
    """Agent settings override"""

    model_name: str | None = None
    backend_type: str | None = None
    use_workspace: bool | None = None
    allow_interruption: bool | None = None
    compress_memory_after_tokens: int | None = None
    agent_type: str | None = None
    computer_pod_setting_id: str | None = None
    sandbox_resource_tier: str | None = None


@dataclass
class User:
    """User information"""

    nickname: str
    avatar: str


@dataclass
class Agent:
    """Agent configuration"""

    agent_id: str
    user: User
    name: str
    avatar: str | None
    description: str | None
    system_prompt: str
    default_model_name: str | None
    default_backend_type: str | None
    default_max_cycles: int
    default_allow_interruption: bool
    default_load_user_memory: bool | None
    default_compress_memory_after_tokens: int
    shared: bool
    is_public: bool
    used_count: int
    is_official: bool
    official_order: int
    is_owner: bool
    create_time: str
    update_time: str
    # Additional fields that may be present in API responses
    name_display: str | None = None
    avatar_display: str | None = None
    usage_hint: dict[str, Any] | None = None
    default_agent_type: str | None = None
    default_reasoning_effort: str | None = None
    default_progress_mode: str | None = None
    default_workspace_files: list[dict[str, Any]] | None = None
    default_sub_agent_ids: list[str] | None = None
    required_skills: list[dict[str, Any]] | None = None
    required_skills_count: int | None = None
    default_output_verifier: str | None = None
    default_computer_pod_setting_id: str | None = None
    default_cloud_storage_paths: list[str] | None = None
    default_cloud_storage_write_enabled: bool | None = None
    tags: list[dict[str, Any]] | None = None
    available_workflows: list[dict[str, Any]] | None = None
    available_workflow_templates: list[dict[str, Any]] | None = None
    available_mcp_tools: list[dict[str, Any]] | None = None
    is_favorited: bool | None = None
    tools_count: int | None = None
    default_sandbox_resource_tier: str | None = None
    available_workflow_ids: list[str] | None = None
    available_template_ids: list[str] | None = None
    available_mcp_tool_ids: list[str] | None = None
    tag_ids: list[str] | None = None


@dataclass
class AgentListResponse:
    """Agent list response"""

    agents: list[Agent]
    total: int
    page: int
    page_size: int
    page_count: int


@dataclass
class WaitingQuestion:
    """Waiting question information"""

    cycle_id: str
    tool_call_id: str
    question: str | None
    options: list[Any] | None = None
    questions: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None
    selection_type: str | None = None
    allow_custom_options: bool | None = None


@dataclass
class AgentTask:
    """Agent task"""

    task_id: str
    user: User | None = None
    source_agent_id: str | None = None
    source_agent_name: str | None = None
    source_agent_avatar: str | None = None
    title: str | None = None
    task_info: dict[str, Any] | None = None
    agent_definition: dict[str, Any] | None = None
    status: str | None = None
    max_cycles: int | None = None
    workspace_id: str | None = None
    current_cycle_index: int | None = None
    result: Any = None
    total_prompt_tokens: int | None = None
    total_completion_tokens: int | None = None
    used_credits: int | None = None
    error_reason_title: str | None = None
    shared: bool | None = None
    is_public: bool | None = None
    shared_meta: dict[str, Any] | None = None
    create_time: str | None = None
    update_time: str | None = None
    complete_time: str | None = None
    waiting_question: WaitingQuestion | None = None
    cycles: list[Any] | None = None
    task_type: str | None = None
    parent_task_id: str | None = None
    sub_agent_ids: list[str] | None = None
    source_organization_id: str | None = None
    sandbox_resource_tier: str | None = None
    environment_expired: bool | None = None
    sandbox_execution_mode: str | None = None
    environment_expired_at: str | None = None
    computer_sandbox_expires_at: str | None = None
    workspace_snapshot_id: str | None = None
    project_id: str | None = None
    worktree_id: str | None = None
    worktree: dict[str, Any] | None = None
    workspace_state: str | None = None
    worktree_state: str | None = None
    finish_state: str | None = None
    merge_state: str | None = None
    base_revision_id: str | None = None
    branch_revision_id: str | None = None
    head_revision_id: str | None = None
    operation_epoch: int | None = None
    write_fence_token: str | None = None
    finish_attempt: dict[str, Any] | None = None
    conflicts: list[dict[str, Any]] | None = None
    runtime: dict[str, Any] | None = None
    runtime_identity: dict[str, Any] | None = None
    effective_profile: dict[str, Any] | None = None
    runtime_capabilities: dict[str, Any] | None = None
    effective_capabilities: list[str] | None = None
    capabilities_authoritative: bool | None = None
    permissions: dict[str, Any] | None = None
    execution_archived_at: str | None = None
    fork_source_update_time: str | None = None
    todo_list: list[dict[str, Any]] | None = None
    context_usage: dict[str, Any] | None = None
    total_cached_tokens: int | None = None
    total_used_credits: int | None = None
    optimization_context: dict[str, Any] | None = None
    is_hidden: bool | None = None
    is_favorited: bool | None = None
    is_unread: bool | None = None
    load_user_memory: bool | None = None
    send_email: bool | None = None
    mounted_cloud_storage_paths: list[str] | None = None
    cloud_storage_write_enabled: bool | None = None
    agent_id_to_start: str | None = None
    agent_definition_to_start: dict[str, Any] | None = None
    category: dict[str, Any] | None = None
    view_count: int | None = None
    shared_order: int | None = None
    sub_task_runs: list[dict[str, Any]] | None = None
    sub_agent_infos: dict[str, Any] | None = None
    pending_messages: list[dict[str, Any]] | None = None


@dataclass
class AgentTaskListResponse:
    """Agent task list response"""

    tasks: list[AgentTask]
    total: int
    page: int
    page_size: int
    page_count: int


@dataclass
class AgentCycle:
    """Agent task cycle"""

    cycle_id: str
    agent_task_id: str
    cycle_index: int
    status: str
    title: str | None = None
    messages: list[dict[str, Any]] | None = None
    ai_response: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_responses: list[dict[str, Any]] | None = None
    memory_compressed: bool | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    used_credits: int | None = None
    start_time: str | None = None
    complete_time: str | None = None
    details_revision: str | None = None
    user_continuation_data: dict[str, Any] | None = None
    has_user_continuation: bool = False
    cached_tokens: int | None = None


@dataclass
class AgentCycleListResponse:
    """Agent cycle list response"""

    cycles: list[AgentCycle]
    total: int
    returned_count: int | None = None
    has_more: bool = False
    next_start_index: int | None = None
    next_end_index: int | None = None
    direction: str = "forward"
    page_size: int | None = None


# Agent Workspace Models
@dataclass
class WorkspaceFile:
    """Workspace file information"""

    key: str
    size: int
    etag: str | None
    last_modified: str | None = None
    oss_path: str | None = None
    relative_path: str | None = None
    is_dir: bool = False
    storage_path: str | None = None
    version_id: str | None = None
    content_sha256: str | None = None
    path: str | None = None
    node_id: str | None = None
    revision_id: str | None = None
    updated_revision: str | None = None


@dataclass
class WorkspaceFileListResponse:
    """Workspace file list response"""

    files: list[WorkspaceFile] | dict[str, Any]  # Can be list or tree structure
    tree_view: bool
    source: str | None = None
    is_computer_agent: bool = False
    recursive: bool = False
    workspace_revision: int | None = None
    page_size: int | None = None
    next_cursor: str | None = None
    has_more: bool = False
    can_write: bool | None = None
    write_blocked_reason: str | None = None


@dataclass
class WorkspaceFileContent:
    """Workspace file content"""

    content: str
    file_info: WorkspaceFile
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    meta_data: dict[str, Any] | None = None
    download_url: str | None = None


@dataclass
class AgentWorkspace:
    """Agent workspace"""

    workspace_id: str
    agent_task_id: str | None
    user: User
    oss_bucket: str
    base_storage_path: str
    created_at: str
    last_accessed: str
    latest_files: list[WorkspaceFile]
    file_count: int
    scope: str | None = None
    revision: int | None = None
    project_id: str | None = None
    task_count: int | None = None
    current_size_bytes: int | None = None
    max_size_bytes: int | None = None
    can_write: bool | None = None
    write_blocked_reason: str | None = None


@dataclass
class AgentWorkspaceListResponse:
    """Agent workspace list response"""

    workspaces: list[AgentWorkspace]
    total: int
    page: int
    page_size: int
    page_count: int
