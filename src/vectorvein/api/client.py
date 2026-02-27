"""VectorVein API Client - Unified modular implementation"""

from .base import BaseSyncClient, BaseAsyncClient
from .workflow import WorkflowSyncMixin, WorkflowAsyncMixin
from .access_key import AccessKeySyncMixin, AccessKeyAsyncMixin
from .file_upload import FileUploadSyncMixin, FileUploadAsyncMixin
from .task_agent import TaskAgentSyncMixin, TaskAgentAsyncMixin
from .agent_workspace import AgentWorkspaceSyncMixin, AgentWorkspaceAsyncMixin
from .user import UserSyncMixin, UserAsyncMixin


class VectorVeinClient(
    BaseSyncClient,
    UserSyncMixin,
    WorkflowSyncMixin,
    AccessKeySyncMixin,
    FileUploadSyncMixin,
    TaskAgentSyncMixin,
    AgentWorkspaceSyncMixin,
):
    """VectorVein API Sync Client with all functionality"""

    pass


class AsyncVectorVeinClient(
    BaseAsyncClient,
    UserAsyncMixin,
    WorkflowAsyncMixin,
    AccessKeyAsyncMixin,
    FileUploadAsyncMixin,
    TaskAgentAsyncMixin,
    AgentWorkspaceAsyncMixin,
):
    """VectorVein API Async Client with all functionality"""

    pass
