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
    ProgressionStatus,
    FeatureFunctionType,
    EmailThread,
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
    ScenarioThreads,
    ScenarioThreadDistribution,
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
    'ProgressionStatus',
    'FeatureFunctionType',
    'EmailThread',
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
    'ScenarioThreads',
    'ScenarioThreadDistribution',
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
]
