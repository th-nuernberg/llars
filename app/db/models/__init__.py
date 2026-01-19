"""
LLARS Database Models

Alle Models sind hier re-exportiert für einfachen Import.
Import: from db.models import User, Permission, JudgeSession
"""

# User models
from db.models.user import User, UserGroup

# Permission models
from db.models.permission import (
    Permission,
    Role,
    RolePermission,
    UserPermission,
    UserRole,
    PermissionAuditLog,
)

# Analytics settings
from db.models.analytics_settings import AnalyticsSettings

# System settings
from db.models.system_settings import SystemSettings

# System monitor events
from db.models.system_event import SystemEvent

# Judge models
from db.models.judge import (
    JudgeSessionStatus,
    JudgeComparisonStatus,
    JudgeWinner,
    PillarThread,
    JudgeSession,
    JudgeComparison,
    JudgeEvaluation,
    PillarStatistics,
)

# RAG models
from db.models.rag import (
    RAGCollection,
    RAGCollectionPermission,
    CollectionDocumentLink,
    RAGDocument,
    RAGDocumentChunk,
    RAGDocumentVersion,
    RAGRetrievalLog,
    RAGDocumentPermission,
    CollectionEmbedding,
    RAGProcessingQueue,
)

# OnCoCo models
from db.models.oncoco import (
    OnCoCoAnalysisStatus,
    OnCoCoAnalysis,
    OnCoCoSentenceLabel,
    OnCoCoPillarStatistics,
    OnCoCoTransitionMatrix,
)

# Chatbot models
from db.models.chatbot import (
    ChatbotMessageRole,
    AgentMode,
    TaskType,
    Chatbot,
    ChatbotPromptSettings,
    ChatbotUserAccess,
    ChatbotCollection,
    ChatbotConversation,
    ChatbotMessage,
)

# Markdown Collab models
from db.models.markdown_collab import (
    MarkdownWorkspaceVisibility,
    MarkdownNodeType,
    MarkdownWorkspace,
    MarkdownWorkspaceMember,
    MarkdownDocument,
    MarkdownCommit,
)

# LaTeX Collab models
from db.models.latex_collab import (
    LatexWorkspaceVisibility,
    LatexNodeType,
    LatexWorkspace,
    LatexWorkspaceMember,
    LatexDocument,
    LatexAsset,
    LatexCommit,
    LatexCompileJob,
    LatexComment,
)

# LLM Model configuration
from db.models.llm_model import (
    LLMModel,
    DEFAULT_LLM_MODELS,
    seed_default_models,
)
from db.models.llm_model_permission import LLMModelPermission
from db.models.llm_provider import LLMProvider
from db.models.llm_task_result import LLMTaskResult

# Prompt Templates and LLM Usage Tracking
from db.models.prompt_template import PromptTemplate
from db.models.field_prompt_template import FieldPromptTemplate
from db.models.llm_usage_tracking import LLMUsageTracking, UserTokenBudget

# KAIMO models
from db.models.kaimo import (
    KaimoCase,
    KaimoDocument,
    KaimoCategory,
    KaimoSubcategory,
    KaimoHint,
    KaimoCaseCategory,
    KaimoAIContent,
    KaimoUserAssessment,
    KaimoHintAssignment,
    KaimoCasePermission,
)

# Scenario and Rating models
from db.models.scenario import (
    ScenarioRoles,
    InvitationStatus,
    ProgressionStatus,
    FeatureFunctionType,
    # New names (preferred)
    EvaluationItem,
    ScenarioItems,
    ScenarioItemDistribution,
    # Legacy aliases (deprecated)
    EmailThread,
    ScenarioThreads,
    ScenarioThreadDistribution,
    # Other models
    Message,
    LLM,
    FeatureType,
    ConsultingCategoryType,
    UserConsultingCategorySelection,
    Feature,
    UserFeatureRanking,
    UserFeatureRating,
    RatingScenarios,
    ScenarioUsers,
    UserMailHistoryRating,
    UserMessageRating,
    UserPrompt,
    UserPromptShare,
    PromptCommit,
    ComparisonSession,
    ComparisonMessage,
    ComparisonEvaluation,
)

# Fake-vs-Real (Authenticity) models
from db.models.authenticity import (
    AuthenticityConversation,
    UserAuthenticityVote,
)

# Zotero Integration models
from db.models.zotero import (
    ZoteroLibraryType,
    ZoteroConnection,
    WorkspaceZoteroLibrary,
    ZoteroSyncLog,
)

# Referral/Invitation models
from db.models.referral import (
    ReferralCampaignStatus,
    ReferralCampaign,
    ReferralLink,
    ReferralRegistration,
)

# User LLM Provider models
from db.models.user_llm_provider import (
    UserLLMProvider,
    UserLLMProviderShare,
)

__all__ = [
    # User
    'User',
    'UserGroup',
    # Permission
    'Permission',
    'Role',
    'RolePermission',
    'UserPermission',
    'UserRole',
    'PermissionAuditLog',
    # Analytics
    'AnalyticsSettings',
    # System Settings
    'SystemSettings',
    # System Monitor
    'SystemEvent',
    # Judge
    'JudgeSessionStatus',
    'JudgeComparisonStatus',
    'JudgeWinner',
    'PillarThread',
    'JudgeSession',
    'JudgeComparison',
    'JudgeEvaluation',
    'PillarStatistics',
    # RAG
    'RAGCollection',
    'RAGCollectionPermission',
    'CollectionDocumentLink',
    'RAGDocument',
    'RAGDocumentChunk',
    'RAGDocumentVersion',
    'RAGRetrievalLog',
    'RAGDocumentPermission',
    'CollectionEmbedding',
    'RAGProcessingQueue',
    # OnCoCo
    'OnCoCoAnalysisStatus',
    'OnCoCoAnalysis',
    'OnCoCoSentenceLabel',
    'OnCoCoPillarStatistics',
    'OnCoCoTransitionMatrix',
    # Chatbot
    'ChatbotMessageRole',
    'AgentMode',
    'TaskType',
    'Chatbot',
    'ChatbotPromptSettings',
    'ChatbotUserAccess',
    'ChatbotCollection',
    'ChatbotConversation',
    'ChatbotMessage',
    # Markdown Collab
    'MarkdownWorkspaceVisibility',
    'MarkdownNodeType',
    'MarkdownWorkspace',
    'MarkdownWorkspaceMember',
    'MarkdownDocument',
    'MarkdownCommit',
    # LaTeX Collab
    'LatexWorkspaceVisibility',
    'LatexNodeType',
    'LatexWorkspace',
    'LatexWorkspaceMember',
    'LatexDocument',
    'LatexAsset',
    'LatexCommit',
    'LatexCompileJob',
    'LatexComment',
    # LLM Model
    'LLMModel',
    'DEFAULT_LLM_MODELS',
    'seed_default_models',
    'LLMModelPermission',
    'LLMProvider',
    'LLMTaskResult',
    # Prompt Templates and Usage Tracking
    'PromptTemplate',
    'FieldPromptTemplate',
    'LLMUsageTracking',
    'UserTokenBudget',
    # KAIMO
    'KaimoCase',
    'KaimoDocument',
    'KaimoCategory',
    'KaimoSubcategory',
    'KaimoHint',
    'KaimoCaseCategory',
    'KaimoAIContent',
    'KaimoUserAssessment',
    'KaimoHintAssignment',
    'KaimoCasePermission',
    # Scenario
    'ScenarioRoles',
    'InvitationStatus',
    'ProgressionStatus',
    'FeatureFunctionType',
    # New names (preferred)
    'EvaluationItem',
    'ScenarioItems',
    'ScenarioItemDistribution',
    # Legacy aliases (deprecated)
    'EmailThread',
    'ScenarioThreads',
    'ScenarioThreadDistribution',
    # Other models
    'Message',
    'LLM',
    'FeatureType',
    'ConsultingCategoryType',
    'UserConsultingCategorySelection',
    'Feature',
    'UserFeatureRanking',
    'UserFeatureRating',
    'RatingScenarios',
    'ScenarioUsers',
    'UserMailHistoryRating',
    'UserMessageRating',
    # Authenticity
    'AuthenticityConversation',
    'UserAuthenticityVote',
    'UserPrompt',
    'UserPromptShare',
    'PromptCommit',
    'ComparisonSession',
    'ComparisonMessage',
    'ComparisonEvaluation',
    # Zotero
    'ZoteroLibraryType',
    'ZoteroConnection',
    'WorkspaceZoteroLibrary',
    'ZoteroSyncLog',
    # Referral
    'ReferralCampaignStatus',
    'ReferralCampaign',
    'ReferralLink',
    'ReferralRegistration',
    # User LLM Provider
    'UserLLMProvider',
    'UserLLMProviderShare',
]
