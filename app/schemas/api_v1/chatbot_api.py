"""
Request / response schemas for ``/api/v1/chatbots`` and ``/api/v1/chatbot-wizard``.

These are the external contract for the public chatbot v1 API. Changes here
are breaking changes for API clients. Mirrors the pattern set by
``schemas/api_v1/scenario_api.py`` — strict ``extra='forbid'``, enum-as-value,
and dedicated request/response shapes per route.

Reuse note
----------
``_ApiModel`` is imported from ``scenario_api`` so the chatbot surface shares
the exact same Pydantic configuration (extra='forbid', use_enum_values).
This keeps the two surfaces from drifting apart on validation semantics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, HttpUrl, field_validator

from schemas.api_v1.scenario_api import _ApiModel


# ---------------------------------------------------------------------------
# Sub-payloads
# ---------------------------------------------------------------------------


class RagCollectionRef(_ApiModel):
    """One entry in a chatbot's RAG-collection assignment list."""

    collection_id: int = Field(ge=1)
    priority: int = Field(default=0, ge=0, le=1000)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    is_primary: bool = False


class ChatbotPromptSettingsBlock(_ApiModel):
    """Optional advanced prompt-engineering knobs (1:1 with ChatbotPromptSettings).

    All fields are Optional so a PATCH can update any subset. The orchestrator
    drops keys that are None before forwarding to ChatbotService — partial
    update semantics."""

    rag_require_citations: Optional[bool] = None
    rag_use_cross_encoder: Optional[bool] = None
    rag_unknown_answer: Optional[str] = Field(default=None, max_length=2000)
    rag_citation_instructions: Optional[str] = Field(default=None, max_length=4000)
    rag_context_prefix: Optional[str] = Field(default=None, max_length=255)
    rag_context_item_template: Optional[str] = Field(default=None, max_length=4000)
    agent_mode: Optional[Literal["standard", "act", "react", "reflact"]] = None
    task_type: Optional[Literal["lookup", "multihop"]] = None
    agent_max_iterations: Optional[int] = Field(default=None, ge=1, le=20)
    web_search_enabled: Optional[bool] = None
    web_search_max_results: Optional[int] = Field(default=None, ge=1, le=20)
    tools_enabled: Optional[List[str]] = Field(default=None, max_length=20)


class ChatbotAccessSpec(_ApiModel):
    """Allowlist + visibility for a chatbot.

    SECURITY: ``allowed_roles`` is regex-restricted to scenario-side roles
    only — same hardening as ReferralLinkSpec.role_name on the scenario
    surface (C1-pattern). Without this, a researcher with chatbot:write
    could mint a public chatbot whose access list grants every visitor
    admin-class roles via the existing role-share mechanism.
    """

    is_public: bool = False
    allowed_usernames: List[str] = Field(default_factory=list, max_length=200)
    allowed_roles: List[str] = Field(default_factory=list, max_length=20)

    @field_validator("allowed_roles")
    @classmethod
    def _restrict_role_names(cls, v: List[str]) -> List[str]:
        # Allow only the same coarse roles a scenario allows in its referral
        # link — narrow on purpose. Adding new roles here is a deliberate
        # decision that should be paired with a security review.
        allowed = {"evaluator", "assessor", "viewer", "researcher",
                   "chatbot_manager"}
        bad = [r for r in v if r not in allowed]
        if bad:
            raise ValueError(
                f"role(s) {bad} not allowed on chatbot access list "
                f"(allowed: {sorted(allowed)})"
            )
        return v


class WizardCrawlSpec(_ApiModel):
    """Crawl configuration block — gates how much the crawler may pull.

    Caps mirror ChatbotBuilderService.start_crawl defaults but tighter to
    keep API-driven creates from accidentally launching multi-thousand-page
    crawls.

    SECURITY (F1, SSRF): ``crawl_url`` is validated against
    :func:`services.security.url_safety.assert_external_url_safe`.
    The helper rejects literal RFC1918 / loopback / link-local IPs,
    well-known cloud-metadata hostnames, wildcard-DNS-to-IP suffix
    providers (.nip.io / .sslip.io / .xip.io — H1 finding), and any
    host whose A/AAAA records resolve to internal space (defeats
    attacker-owned CNAMEs).

    The same helper is invoked from the service layer
    (``ChatbotCreator``) as defence-in-depth so non-v1 callers — e.g.
    the legacy ``/api/chatbots/<id>/wizard/crawl`` route — get the
    same protection without depending on schema validation.
    """

    crawl_url: HttpUrl
    max_pages: int = Field(default=50, ge=1, le=2000)
    max_depth: int = Field(default=3, ge=1, le=10)
    use_playwright: bool = True
    use_vision_llm: bool = False
    take_screenshots: bool = False

    @field_validator("crawl_url")
    @classmethod
    def _block_internal_hosts(cls, v):
        from services.security.url_safety import assert_external_url_safe

        # ``UnsafeUrlError`` subclasses ValueError, so Pydantic surfaces
        # it as a normal validation failure (HTTP 400 via _validate_request).
        assert_external_url_safe(str(v))
        return v


# ---------------------------------------------------------------------------
# CRUD requests
# ---------------------------------------------------------------------------


class ChatbotCreateRequest(_ApiModel):
    """One-shot scenario create.

    If ``wizard`` is set, the response returns a chatbot in
    ``build_status='crawling'`` plus a ``job_id`` to poll. If ``wizard`` is
    None, the chatbot is created in ``build_status='ready'`` with the
    explicit prompt + collections from the payload — useful for manual
    config or migrating from another system.
    """

    name: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    icon: str = Field(default="mdi-robot", max_length=64)
    color: str = Field(default="#5d7a4a", pattern=r"^#[0-9a-fA-F]{6}$")
    avatar_url: Optional[str] = Field(default=None, max_length=512)

    system_prompt: str = Field(min_length=1, max_length=10000)
    welcome_message: Optional[str] = Field(default=None, max_length=2000)
    fallback_message: Optional[str] = Field(default=None, max_length=2000)

    model_name: Optional[str] = Field(default=None, max_length=255)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=128000)
    top_p: float = Field(default=0.95, ge=0, le=1)

    rag_enabled: bool = True
    rag_retrieval_k: int = Field(default=8, ge=0, le=64)
    rag_min_relevance: float = Field(default=0.05, ge=0, le=1)
    rag_include_sources: bool = True
    rag_reranker_model: Optional[str] = Field(default=None, max_length=255)
    rag_use_cross_encoder: bool = False

    max_context_messages: int = Field(default=10, ge=0, le=100)
    is_active: bool = True

    collections: List[RagCollectionRef] = Field(default_factory=list, max_length=20)
    access: ChatbotAccessSpec = Field(default_factory=ChatbotAccessSpec)
    prompt_settings: Optional[ChatbotPromptSettingsBlock] = None
    wizard: Optional[WizardCrawlSpec] = None


class ChatbotPatchRequest(_ApiModel):
    """Partial update — every field optional. ``name`` is intentionally
    not patchable here (it's the unique business key; renames go through
    DELETE + re-create or via the UI's full editor)."""

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    icon: Optional[str] = Field(default=None, max_length=64)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    avatar_url: Optional[str] = Field(default=None, max_length=512)

    system_prompt: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    welcome_message: Optional[str] = Field(default=None, max_length=2000)
    fallback_message: Optional[str] = Field(default=None, max_length=2000)

    model_name: Optional[str] = Field(default=None, max_length=255)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)

    rag_enabled: Optional[bool] = None
    rag_retrieval_k: Optional[int] = Field(default=None, ge=0, le=64)
    rag_min_relevance: Optional[float] = Field(default=None, ge=0, le=1)
    rag_include_sources: Optional[bool] = None
    rag_reranker_model: Optional[str] = Field(default=None, max_length=255)
    rag_use_cross_encoder: Optional[bool] = None

    max_context_messages: Optional[int] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None

    prompt_settings: Optional[ChatbotPromptSettingsBlock] = None


class ChatbotTweakRequest(_ApiModel):
    """Tighter PATCH for hot-tuning a live chatbot (A/B-style).

    Only fields safe to flip without re-deploy. CI tools doing prompt
    A/B-tests should use this rather than the full PATCH so the contract
    is narrower and obvious."""

    system_prompt: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    model_name: Optional[str] = Field(default=None, max_length=255)
    rag_retrieval_k: Optional[int] = Field(default=None, ge=0, le=64)
    rag_min_relevance: Optional[float] = Field(default=None, ge=0, le=1)
    rag_use_cross_encoder: Optional[bool] = None


class ChatbotCollectionAssign(_ApiModel):
    """POST body for assigning a RAG collection to a chatbot."""

    collection_id: int = Field(ge=1)
    priority: int = Field(default=0, ge=0, le=1000)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    is_primary: bool = False


class ChatbotCollectionPatch(_ApiModel):
    """PATCH body for tweaking an existing collection assignment."""

    priority: Optional[int] = Field(default=None, ge=0, le=1000)
    weight: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    is_primary: Optional[bool] = None


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatMessageRequest(_ApiModel):
    """Single chat turn. ``conversation_id`` may be omitted; the service
    auto-creates a fresh conversation in that case."""

    message: str = Field(min_length=1, max_length=20000)
    conversation_id: Optional[int] = Field(default=None, ge=1)
    session_id: Optional[str] = Field(default=None, max_length=128)
    include_sources: bool = True
    stream: bool = False


# ---------------------------------------------------------------------------
# Wizard requests
# ---------------------------------------------------------------------------


class WizardSessionCreateRequest(_ApiModel):
    """POST /api/v1/chatbot-wizard/sessions — start a new wizard session."""

    crawl_url: HttpUrl
    crawler_config: Optional[WizardCrawlSpec] = None


class WizardCrawlRequest(_ApiModel):
    """POST /api/v1/chatbot-wizard/sessions/{id}/crawl — kick off the crawl."""

    crawler_config: WizardCrawlSpec


class WizardGenerateFieldRequest(_ApiModel):
    field: Literal["name", "display_name", "system_prompt", "icon",
                   "welcome_message", "all"]
    context: Optional[str] = Field(default=None, max_length=4000)
    force_llm: bool = False
    stream: bool = False


class WizardFinalizeRequest(_ApiModel):
    """POST /api/v1/chatbot-wizard/sessions/{id}/finalize.

    The fields below override the values that came out of generate-field;
    if both are unset, the LLM-generated values stay."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    system_prompt: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    icon: Optional[str] = Field(default=None, max_length=64)
    welcome_message: Optional[str] = Field(default=None, max_length=2000)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    model_name: Optional[str] = Field(default=None, max_length=255)
    access: Optional[ChatbotAccessSpec] = None


class WizardQuickbuildRequest(_ApiModel):
    """POST /api/v1/chatbot-wizard/quickbuild — single-call entry point.

    Chains the full wizard flow (``create_wizard_chatbot`` →
    ``start_crawl`` → ``generate_field('all')`` → ``finalize``) and
    returns the eventual ``chatbot_id`` + ``job_id``. The orchestrator
    spawns a daemon thread that drives the field-generation +
    finalize steps once the crawl reaches ``configuring``; the caller
    only polls ``/sessions/{id}/status`` to know when ``build_status``
    flips to ``ready``. The response field ``auto_finalize`` reports
    whether that thread was spawned successfully (almost always
    ``True``).
    """

    crawl: WizardCrawlSpec
    model_name: str = Field(min_length=1, max_length=255)
    name_override: Optional[str] = Field(default=None, min_length=1, max_length=120)
    display_name_override: Optional[str] = Field(default=None, min_length=1,
                                                  max_length=255)
    access: ChatbotAccessSpec = Field(default_factory=ChatbotAccessSpec)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ChatbotCollectionResponse(_ApiModel):
    collection_id: int
    name: Optional[str] = None
    priority: int
    weight: float
    is_primary: bool


class ChatbotResponse(_ApiModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    icon: str
    color: str
    avatar_url: Optional[str]

    system_prompt: str
    welcome_message: Optional[str]
    fallback_message: Optional[str]

    model_name: Optional[str]
    temperature: float
    max_tokens: Optional[int]
    top_p: float

    rag_enabled: bool
    rag_retrieval_k: int
    rag_min_relevance: float
    rag_include_sources: bool
    rag_reranker_model: Optional[str]
    rag_use_cross_encoder: bool

    max_context_messages: int
    is_active: bool
    is_public: bool

    build_status: Optional[str]
    build_error: Optional[str]
    source_url: Optional[str]
    primary_collection_id: Optional[int]

    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    collections: List[ChatbotCollectionResponse] = Field(default_factory=list)
    allowed_usernames: List[str] = Field(default_factory=list)
    allowed_roles: List[str] = Field(default_factory=list)
    prompt_settings: Optional[Dict[str, Any]] = None

    # Async-job pointer when create was triggered with a wizard block
    job_id: Optional[str] = None


class ChatbotListResponse(_ApiModel):
    success: bool = True
    chatbots: List[ChatbotResponse]
    total: int
    limit: int
    offset: int


class ChatMessageResponse(_ApiModel):
    """Non-streaming /chat response."""

    success: bool = True
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: int
    message_id: Optional[int] = None


class WizardSessionResponse(_ApiModel):
    success: bool = True
    chatbot_id: int
    session_id: int
    build_status: str
    progress: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


class WizardQuickbuildResponse(_ApiModel):
    """Response shape returned by ``POST /chatbot-wizard/quickbuild``.

    ``auto_finalize`` reports whether the daemon thread that drives
    ``generate-field`` + ``finalize`` after the crawl/embedding has
    completed was spawned successfully. ``True`` is the normal
    happy-path; ``False`` means the caller has to drive the rest of
    the wizard themselves (rare, only when thread spawn fails).
    """

    success: bool = True
    chatbot_id: int
    session_id: int
    build_status: str
    job_id: Optional[str] = None
    polling_url: str
    auto_finalize: Optional[bool] = None
