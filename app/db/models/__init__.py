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
    CollectionDocumentLink,
    RAGDocument,
    RAGDocumentChunk,
    RAGDocumentVersion,
    RAGRetrievalLog,
    RAGDocumentPermission,
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
    ComparisonSession,
    ComparisonMessage,
    ComparisonEvaluation,
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
    'CollectionDocumentLink',
    'RAGDocument',
    'RAGDocumentChunk',
    'RAGDocumentVersion',
    'RAGRetrievalLog',
    'RAGDocumentPermission',
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
    'UserPrompt',
    'UserPromptShare',
    'ComparisonSession',
    'ComparisonMessage',
    'ComparisonEvaluation',
]
