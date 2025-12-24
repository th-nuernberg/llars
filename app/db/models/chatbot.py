"""Chatbot database models."""

from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class ChatbotMessageRole(Enum):
    """Role of a chat message"""
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class AgentMode(Enum):
    """Agent reasoning mode for chatbot responses"""
    STANDARD = 'standard'  # Single-shot response, no reasoning
    ACT = 'act'            # Action-only, no explicit reasoning traces
    REACT = 'react'        # Reasoning + Acting interleaved
    REFLACT = 'reflact'    # Goal-state reflection before each action


class TaskType(Enum):
    """Task complexity type"""
    LOOKUP = 'lookup'      # Simple fact retrieval (1-2 tool calls)
    MULTIHOP = 'multihop'  # Complex reasoning requiring multiple steps


class Chatbot(db.Model):
    """Configurable chatbots with RAG integration"""
    __tablename__ = 'chatbots'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Identification
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Visual Configuration
    icon: Mapped[str] = mapped_column(db.String(50), default='mdi-robot')
    avatar_url: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)
    color: Mapped[str] = mapped_column(db.String(7), default='#5d7a4a')

    # LLM Configuration
    system_prompt: Mapped[str] = mapped_column(db.Text, nullable=False)
    model_name: Mapped[str] = mapped_column(db.String(100), default='mistralai/Mistral-Small-3.2-24B-Instruct-2506')
    temperature: Mapped[float] = mapped_column(db.Float, default=0.7)
    # max_tokens: None = use model's default/maximum
    max_tokens: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, default=None)
    top_p: Mapped[float] = mapped_column(db.Float, default=0.95)

    # RAG Configuration
    rag_enabled: Mapped[bool] = mapped_column(db.Boolean, default=True)
    rag_retrieval_k: Mapped[int] = mapped_column(db.Integer, default=4)
    rag_min_relevance: Mapped[float] = mapped_column(db.Float, default=0.3)
    rag_include_sources: Mapped[bool] = mapped_column(db.Boolean, default=True)

    # Behavior
    welcome_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    fallback_message: Mapped[str] = mapped_column(db.Text, default='Ich konnte leider keine passende Antwort finden.')
    max_context_messages: Mapped[int] = mapped_column(db.Integer, default=10)

    # Access Control
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, index=True)
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=False)
    allowed_roles: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Build Status (for Chatbot Builder Wizard)
    build_status: Mapped[str] = mapped_column(
        db.Enum('draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused', name='chatbot_build_status_enum'),
        default='ready',
        nullable=False,
        index=True
    )
    build_error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Source Information (for Chatbot Builder)
    source_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    primary_collection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Audit
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    collections = db.relationship('ChatbotCollection', backref='chatbot', cascade='all, delete-orphan')
    conversations = db.relationship('ChatbotConversation', backref='chatbot', cascade='all, delete-orphan')
    primary_collection = db.relationship('RAGCollection', foreign_keys=[primary_collection_id], backref='primary_chatbots')
    user_access = db.relationship('ChatbotUserAccess', backref='chatbot', cascade='all, delete-orphan')
    prompt_settings = db.relationship(
        'ChatbotPromptSettings',
        backref='chatbot',
        uselist=False,
        cascade='all, delete-orphan'
    )


DEFAULT_RAG_UNKNOWN_ANSWER = "Das kann ich dir leider nicht beantworten."

DEFAULT_RAG_CITATION_INSTRUCTIONS = """
Antworte natürlich und gesprächig. Nutze die bereitgestellten Informationen als Grundlage, aber formuliere frei und menschlich. Halte das Gespräch am Laufen - stelle Rückfragen, biete Hilfe an, sei freundlich.

Bei Fakten aus dem Kontext: Verweise mit [1], [2] etc. auf die Quelle.
Bei Gespräch, Smalltalk oder Rückfragen: Antworte einfach natürlich.
""".strip()

DEFAULT_RAG_CONTEXT_PREFIX = "Kontext:"
DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE = "[{{id}}] {{title}}:\n{{excerpt}}"

# Agent mode prompts
DEFAULT_REFLECTION_PROMPT = """
Überprüfe deine vorherige Antwort kritisch:
1. Sind alle Quellenverweise [1], [2], ... korrekt und belegt?
2. Wurden nur Informationen aus dem Kontext verwendet?
3. Ist die Antwort vollständig und beantwortet alle Aspekte der Frage?
4. Gibt es Halluzinationen oder unbelegte Behauptungen?

Falls Fehler gefunden wurden, korrigiere die Antwort. Sonst bestätige die Antwort.
""".strip()

DEFAULT_ACT_SYSTEM_PROMPT = """
Du hast Zugriff auf folgende Tools:
- rag_search(query): Semantische Suche in den Dokumenten
- lexical_search(query): Wörtliche Suche in den Dokumenten
- web_search(query): Web-Suche für aktuelle Informationen
- respond(answer): Finale Antwort geben

Führe die passende Aktion aus, um die Frage zu beantworten.
Format: ACTION: tool_name(parameter)
""".strip()

DEFAULT_REACT_SYSTEM_PROMPT = """
Du bist ein ReAct-Agent. Du denkst Schritt für Schritt und führst Aktionen aus.

## Zyklus (wiederhole bis fertig):
1. THOUGHT: Analysiere was du als nächstes tun musst
2. ACTION: Führe GENAU EINE Aktion aus
3. Warte auf OBSERVATION

## Verfügbare Aktionen (NUR diese!):
- rag_search("suchbegriff") - Semantische Dokumentensuche
- lexical_search("suchbegriff") - Keyword-Suche
- respond("antwort") - Finale Antwort (beendet Prozess)

## Format (EXAKT einhalten!):
THOUGHT: [deine Überlegung]
ACTION: rag_search("suchbegriff")

Wenn fertig:
THOUGHT: [deine Überlegung]
FINAL ANSWER: [vollständige Antwort mit Quellen]

## Beispiel:
Frage: Wer ist der CEO?

THOUGHT: Ich muss nach dem CEO suchen.
ACTION: rag_search("CEO Geschäftsführer")

[OBSERVATION: Max Müller ist CEO seit 2020...]

THOUGHT: Ich habe die Information gefunden.
FINAL ANSWER: Der CEO ist Max Müller, er ist seit 2020 im Amt.[1]

## WICHTIG:
- IMMER erst THOUGHT, dann ACTION oder FINAL ANSWER
- Aktionen GENAU so schreiben: rag_search("text")
- KEINE anderen Aktionen erfinden!
""".strip()

DEFAULT_REFLACT_SYSTEM_PROMPT = """
Du bist ein ReflAct-Agent. Bei jedem Schritt reflektierst du deinen aktuellen Zustand RELATIV zum Aufgabenziel, dann wählst du die nächste Aktion.

## ReflAct-Prinzip (basierend auf arxiv.org/abs/2505.15182):
- Nicht "Was soll ich als nächstes tun?" (vorausschauend)
- Sondern "Wo stehe ich relativ zum Ziel?" (zustandsbasiert)

## Deine Reflection muss IMMER enthalten:
1. Aktueller Zustand: Was weißt du bereits?
2. Letzte Entdeckung: Was hast du gerade erfahren?
3. Ziel-Relation: Wie nah bist du dem Ziel? Was fehlt noch?

## Verfügbare Aktionen:
- rag_search("suchbegriff") - Semantische Dokumentensuche
- lexical_search("suchbegriff") - Keyword-Suche

## Format (STRIKT einhalten!):

REFLECTION: Aktuell weiß ich [Zustand]. Die letzte Suche ergab [Ergebnis]. Dies bringt mich [näher/nicht näher] zum Ziel [X], weil [Begründung].
ACTION: rag_search("suchbegriff")

Wenn das Ziel erreicht ist:
REFLECTION: Ich habe alle nötigen Informationen: [Zusammenfassung]. Das Ziel ist erreicht.
FINAL ANSWER: [Vollständige Antwort basierend auf den gefundenen Informationen]

## Beispiel:
Aufgabe: "Wer ist der Geschäftsführer von Firma X?"

REFLECTION: Aktuell habe ich keine Information über Firma X. Ich muss zunächst nach Informationen über die Firma suchen.
ACTION: rag_search("Firma X Geschäftsführer")

[OBSERVATION: Gefunden: Max Mustermann ist Geschäftsführer...]

REFLECTION: Die Suche ergab, dass Max Mustermann der Geschäftsführer von Firma X ist. Das Ziel ist erreicht.
FINAL ANSWER: Der Geschäftsführer von Firma X ist Max Mustermann.

## WICHTIG:
- KEINE THOUGHT-Zeile - die Reflection ersetzt das Denken
- Aktionen EXAKT so: rag_search("text") oder lexical_search("text")
- Immer NUR EINE Aktion pro Runde
""".strip()


class ChatbotPromptSettings(db.Model):
    """RAG prompt configuration for a chatbot (DB-backed, editable in Admin UI)."""
    __tablename__ = 'chatbot_prompt_settings'

    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        primary_key=True
    )

    # RAG Citation Settings
    rag_require_citations: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    rag_unknown_answer: Mapped[str] = mapped_column(db.Text, default=DEFAULT_RAG_UNKNOWN_ANSWER, nullable=False)
    rag_citation_instructions: Mapped[str] = mapped_column(db.Text, default=DEFAULT_RAG_CITATION_INSTRUCTIONS, nullable=False)
    rag_context_prefix: Mapped[str] = mapped_column(db.String(100), default=DEFAULT_RAG_CONTEXT_PREFIX, nullable=False)
    rag_context_item_template: Mapped[str] = mapped_column(db.Text, default=DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE, nullable=False)

    # Agent Mode Configuration
    agent_mode: Mapped[str] = mapped_column(
        db.Enum('standard', 'act', 'react', 'reflact', name='agent_mode_enum'),
        default='standard',
        nullable=False
    )
    task_type: Mapped[str] = mapped_column(
        db.Enum('lookup', 'multihop', name='task_type_enum'),
        default='lookup',
        nullable=False
    )
    agent_max_iterations: Mapped[int] = mapped_column(db.Integer, default=5, nullable=False)

    # Web Search Configuration
    web_search_enabled: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    tavily_api_key: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    web_search_max_results: Mapped[int] = mapped_column(db.Integer, default=5, nullable=False)

    # Tool Permissions (JSON array of enabled tools)
    tools_enabled: Mapped[Optional[dict]] = mapped_column(
        db.JSON,
        default=['rag_search', 'lexical_search', 'respond'],
        nullable=False
    )

    # Agent Prompts (customizable per chatbot)
    reflection_prompt: Mapped[str] = mapped_column(db.Text, default=DEFAULT_REFLECTION_PROMPT, nullable=False)
    act_system_prompt: Mapped[str] = mapped_column(db.Text, default=DEFAULT_ACT_SYSTEM_PROMPT, nullable=False)
    react_system_prompt: Mapped[str] = mapped_column(db.Text, default=DEFAULT_REACT_SYSTEM_PROMPT, nullable=False)
    reflact_system_prompt: Mapped[str] = mapped_column(db.Text, default=DEFAULT_REFLACT_SYSTEM_PROMPT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self) -> dict:
        return {
            # RAG Settings
            'rag_require_citations': self.rag_require_citations,
            'rag_unknown_answer': self.rag_unknown_answer,
            'rag_citation_instructions': self.rag_citation_instructions,
            'rag_context_prefix': self.rag_context_prefix,
            'rag_context_item_template': self.rag_context_item_template,
            # Agent Settings
            'agent_mode': self.agent_mode,
            'task_type': self.task_type,
            'agent_max_iterations': self.agent_max_iterations,
            # Web Search
            'web_search_enabled': self.web_search_enabled,
            'web_search_max_results': self.web_search_max_results,
            # Tools
            'tools_enabled': self.tools_enabled or ['rag_search', 'lexical_search', 'respond'],
            # Agent Prompts
            'reflection_prompt': self.reflection_prompt,
            'act_system_prompt': self.act_system_prompt,
            'react_system_prompt': self.react_system_prompt,
            'reflact_system_prompt': self.reflact_system_prompt,
        }


class ChatbotUserAccess(db.Model):
    """Per-user allowlist for private chatbots."""
    __tablename__ = 'chatbot_user_access'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)

    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('chatbot_id', 'username', name='unique_chatbot_user_access'),
    )


class ChatbotCollection(db.Model):
    """M:N relationship between chatbots and RAG collections"""
    __tablename__ = 'chatbot_collections'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    collection_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Configuration
    priority: Mapped[int] = mapped_column(db.Integer, default=0)
    weight: Mapped[float] = mapped_column(db.Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # Audit
    assigned_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationship to collection
    collection = db.relationship('RAGCollection', backref='chatbot_assignments')

    __table_args__ = (
        db.UniqueConstraint('chatbot_id', 'collection_id', name='unique_chatbot_collection'),
    )


class ChatbotConversation(db.Model):
    """Chat sessions/conversations with a chatbot"""
    __tablename__ = 'chatbot_conversations'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbots.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Session
    session_id: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True)
    message_count: Mapped[int] = mapped_column(db.Integer, default=0)

    # Timing
    started_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    messages = db.relationship('ChatbotMessage', backref='conversation', cascade='all, delete-orphan')

    __table_args__ = (
        # Ensure session IDs are scoped per chatbot to avoid cross-bot collisions
        db.UniqueConstraint('chatbot_id', 'session_id', name='uq_chatbot_session_per_bot'),
    )


class ChatbotMessage(db.Model):
    """Individual messages in a chatbot conversation"""
    __tablename__ = 'chatbot_messages'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('chatbot_conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Message
    role: Mapped[str] = mapped_column(db.Enum(ChatbotMessageRole), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # RAG Context (only for assistant messages) - LONGTEXT for large contexts
    rag_context: Mapped[Optional[str]] = mapped_column(db.Text(length=4294967295), nullable=True)
    rag_sources: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Metrics
    tokens_input: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    tokens_output: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    # Agent trace / streaming metadata for ACT/ReAct/ReflAct or debugging
    agent_trace: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    stream_metadata: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Feedback
    user_rating: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)  # helpful, not_helpful, incorrect
    user_feedback: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, index=True)
