"""
LLARS Database Models

Alle Models sind hier re-exportiert für einfachen Import.
Import: from db.models import User, Permission, JudgeSession
"""

# User models
from db.models.user import User, UserGroup, UserApiKey

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

# LLM Model configuration
from db.models.llm_model import (
    LLMModel,
    DEFAULT_LLM_MODELS,
    seed_default_models,
)
from db.models.llm_model_permission import LLMModelPermission
from db.models.llm_provider import LLMProvider
from db.models.llm_task_result import LLMTaskResult
from db.models.llm_eval_run import LLMEvalRun
from db.models.labeling_copilot_log import LabelingCopilotLog
from db.models.evaluation_item_timing import EvaluationItemTiming

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
    KaimoCaseShare,
)

# Scenario and Rating models
from db.models.scenario import (
    ManagerRole,
    EvaluationRole,
    ScenarioRoles,
    AccessLevel,
    InvitationStatus,
    ProgressionStatus,
    FeatureFunctionType,
    MembershipStatus,
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
    FeatureType,
    ConsultingCategoryType,
    UserConsultingCategorySelection,
    Feature,
    UserFeatureRanking,
    UserFeatureRating,
    RatingScenarios,
    ScenarioUsers,
    UserMailHistoryRating,
    ItemDimensionRating,  # New multi-dimensional rating model
    ItemLabelingEvaluation,  # Labeling/classification evaluation model
    ItemComparisonEvaluation,  # A/B comparison evaluation model
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

# Referral/Invitation models
from db.models.referral import (
    ReferralCampaignStatus,
    ReferralCampaign,
    ReferralLink,
    ReferralRegistration,
)

# Password-reset tokens (self-service "forgot password" flow)
from db.models.password_reset import PasswordResetToken

# Mail-Center: central email log + referral invitation tracking
from db.models.email_log import (
    EmailLog,
    ReferralInvitation,
    MailType,
    MailStatus,
)

# User LLM Provider models
from db.models.user_llm_provider import (
    UserLLMProvider,
    UserLLMProviderShare,
)

# User Demographics (one-time survey)
from db.models.user_demographics import UserDemographics

# Batch Generation models
from db.models.generation import (
    GenerationJobStatus,
    GeneratedOutputStatus,
    GenerationJob,
    GeneratedOutput,
    GenerationJobShare,
    get_pending_outputs_for_job,
    get_failed_outputs_for_job,
)

# Pipeline models
from db.models.pipeline import (
    PipelineStatus,
    PipelineIterationPhase,
    PipelineIterationStatus,
    PipelineRun,
    PipelineIteration,
)

# Anonymization Pipeline models
from db.models.anonymization import (
    AnonymizationConversation,
    AnonymizationMessage,
    AnonymizationEntity,
    AnonymizationMessageVersion,
)

# Conference Manager models
from db.models.conference import (
    CoreRanking,
    PaperStatus,
    SubmissionStatus,
    ResearchGroupRole,
    ResearchGroupRequestStatus,
    ResearchGroup,
    ResearchGroupMember,
    ResearchGroupAccessRequest,
    ConferenceSeries,
    Conference,
    Paper,
    PaperAuthor,
    PaperSubmission,
)

# Messaging models
from db.models.messaging import (
    MessagingConversation,
    MessagingParticipant,
    MessagingMessage,
    MessagingAttachment,
    MessagingReaction,
    MessagingReadReceipt,
    MessagingEncryptionKey,
    MessagingLinkPreview,
)

# Scenario Stats Cache
from db.models.scenario_stats_cache import ScenarioStatsCache
from db.models.scenario_stats_job import ScenarioStatsJob

__all__ = [
    # User
    'User',
    'UserGroup',
    'UserApiKey',
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
    # LLM Model
    'LLMModel',
    'DEFAULT_LLM_MODELS',
    'seed_default_models',
    'LLMModelPermission',
    'LLMProvider',
    'LLMTaskResult',
    'LabelingCopilotLog',
    'EvaluationItemTiming',
    'LLMEvalRun',
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
    'KaimoCaseShare',
    # Scenario
    'ManagerRole',
    'EvaluationRole',
    'ScenarioRoles',
    'AccessLevel',
    'InvitationStatus',
    'ProgressionStatus',
    'FeatureFunctionType',
    'MembershipStatus',
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
    'FeatureType',
    'ConsultingCategoryType',
    'UserConsultingCategorySelection',
    'Feature',
    'UserFeatureRanking',
    'UserFeatureRating',
    'RatingScenarios',
    'ScenarioUsers',
    'UserMailHistoryRating',
    'ItemDimensionRating',
    'ItemLabelingEvaluation',
    'ItemComparisonEvaluation',
    'UserMessageRating',
    # Authenticity
    'AuthenticityConversation',
    'UserAuthenticityVote',
    # Anonymization Pipeline
    'AnonymizationConversation',
    'AnonymizationMessage',
    'AnonymizationEntity',
    'AnonymizationMessageVersion',
    'UserPrompt',
    'UserPromptShare',
    'PromptCommit',
    'ComparisonSession',
    'ComparisonMessage',
    'ComparisonEvaluation',
    # Referral
    'ReferralCampaignStatus',
    'ReferralCampaign',
    'ReferralLink',
    'ReferralRegistration',
    # Password reset
    'PasswordResetToken',
    # Mail-Center
    'EmailLog',
    'ReferralInvitation',
    'MailType',
    'MailStatus',
    # User LLM Provider
    'UserLLMProvider',
    'UserLLMProviderShare',
    # User Demographics
    'UserDemographics',
    # Batch Generation
    'GenerationJobStatus',
    'GeneratedOutputStatus',
    'GenerationJob',
    'GeneratedOutput',
    'GenerationJobShare',
    'get_pending_outputs_for_job',
    'get_failed_outputs_for_job',
    # Pipeline
    'PipelineStatus',
    'PipelineIterationPhase',
    'PipelineIterationStatus',
    'PipelineRun',
    'PipelineIteration',
    # Conference Manager
    'CoreRanking',
    'PaperStatus',
    'SubmissionStatus',
    'ResearchGroupRole',
    'ResearchGroupRequestStatus',
    'ResearchGroup',
    'ResearchGroupMember',
    'ResearchGroupAccessRequest',
    'ConferenceSeries',
    'Conference',
    'Paper',
    'PaperAuthor',
    'PaperSubmission',
    # Messaging
    'MessagingConversation',
    'MessagingParticipant',
    'MessagingMessage',
    'MessagingAttachment',
    'MessagingReaction',
    'MessagingReadReceipt',
    'MessagingEncryptionKey',
    'MessagingLinkPreview',
    # Scenario Stats Cache
    'ScenarioStatsCache',
    'ScenarioStatsJob',
]
