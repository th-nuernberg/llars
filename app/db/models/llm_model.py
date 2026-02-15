"""
LLM Model Configuration Database Model

Stores available LLM models with their capabilities and pricing.
Used for model selection in chatbots and other LLM-powered features.
"""

from typing import Iterable, Optional, Tuple
import colorsys
import re
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db


# Neutral color generation (avoid strong red/green semantics)
NEUTRAL_HUE_RANGES = [
    (25, 80),   # warm amber/orange
    (160, 240), # teal/blue
    (260, 320), # purple/magenta
]
NEUTRAL_SAT_RANGE = (38, 56)    # %
NEUTRAL_LIGHT_RANGE = (42, 56)  # %
COLOR_SEARCH_HUE_STEP = 3       # degrees
COLOR_SEARCH_SAT_STEP = 3       # %
COLOR_SEARCH_LIGHT_STEP = 3     # %

# Legacy palette (kept for automatic migration of existing colors)
LEGACY_MODEL_COLOR_PALETTE = [
    "#1E88E5",
    "#FB8C00",
    "#A06060",
    "#E53935",
    "#00897B",
    "#5E7C6F",
    "#43A047",
    "#FBC02D",
    "#8E24AA",
    "#D81B60",
    "#6D4C41",
    "#546E7A",
    "#3949AB",
    "#F4511E",
    "#039BE5",
    "#6F8B79",
    "#7CB342",
    "#5E35B1",
    "#00ACC1",
    "#C0CA33",
    "#757575",
    "#1565C0",
    "#EF6C00",
    "#C62828",
    "#00695C",
    "#2E7D32",
    "#F9A825",
    "#6A1B9A",
    "#AD1457",
    "#4E342E",
    "#37474F",
    "#283593",
    "#D84315",
    "#0277BD",
    "#558B2F",
    "#4527A0",
    "#00838F",
    "#9E9D24",
    "#616161",
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC949",
    "#AF7AA1",
    "#FF9DA7",
    "#9C755F",
    "#BAB0AB",
    "#1F77B4",
    "#FF7F0E",
    "#2CA02C",
    "#D62728",
    "#9467BD",
    "#8C564B",
    "#17BECF",
    "#BCBD22",
]

_LEGACY_COLOR_SET = {c.upper() for c in LEGACY_MODEL_COLOR_PALETTE}

_HEX_COLOR_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def _hash_string(value: str) -> int:
    """FNV-1a 32-bit hash (stable across Python/JS)."""
    h = 0x811C9DC5
    for ch in value:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def _pick_neutral_hue(seed: int) -> float:
    total_range = sum(end - start for start, end in NEUTRAL_HUE_RANGES)
    offset = seed % total_range
    for start, end in NEUTRAL_HUE_RANGES:
        span = end - start
        if offset < span:
            return start + offset
        offset -= span
    return NEUTRAL_HUE_RANGES[0][0]


def _hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    h = (hue % 360) / 360.0
    s = max(0.0, min(1.0, saturation / 100.0))
    l = max(0.0, min(1.0, lightness / 100.0))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def _seed_color(model_id: str) -> str:
    """Generate a stable neutral color for a model_id."""
    seed = _hash_string((model_id or "").strip())
    hue = _pick_neutral_hue(seed)
    sat_span = NEUTRAL_SAT_RANGE[1] - NEUTRAL_SAT_RANGE[0]
    light_span = NEUTRAL_LIGHT_RANGE[1] - NEUTRAL_LIGHT_RANGE[0]
    saturation = NEUTRAL_SAT_RANGE[0] + ((seed >> 8) % (sat_span + 1))
    lightness = NEUTRAL_LIGHT_RANGE[0] + ((seed >> 16) % (light_span + 1))
    return _hsl_to_hex(hue, saturation, lightness)


def _normalize_color(color: Optional[str]) -> Optional[str]:
    if not color:
        return None
    value = color.strip()
    if not _HEX_COLOR_RE.match(value):
        return None
    return value if value.startswith("#") else f"#{value}"


def _color_key(color: Optional[str]) -> Optional[str]:
    normalized = _normalize_color(color)
    return normalized.upper() if normalized else None


def _hex_to_rgb(color: str) -> Optional[Tuple[int, int, int]]:
    normalized = _color_key(color)
    if not normalized:
        return None
    value = normalized[1:]
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _rgb_distance_sq(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    dbv = a[2] - b[2]
    return dr * dr + dg * dg + dbv * dbv


def _build_neutral_color_candidates() -> list[str]:
    """
    Build a finite neutral candidate palette used for max-distance search.

    Keeps model colors in LLARS' neutral bands while giving enough combinations
    to spread many models apart visually.
    """
    candidates: list[str] = []
    seen: set[str] = set()
    for start, end in NEUTRAL_HUE_RANGES:
        for hue in range(start, end, COLOR_SEARCH_HUE_STEP):
            for sat in range(NEUTRAL_SAT_RANGE[0], NEUTRAL_SAT_RANGE[1] + 1, COLOR_SEARCH_SAT_STEP):
                for light in range(NEUTRAL_LIGHT_RANGE[0], NEUTRAL_LIGHT_RANGE[1] + 1, COLOR_SEARCH_LIGHT_STEP):
                    color = _hsl_to_hex(hue, sat, light).upper()
                    if color not in seen:
                        seen.add(color)
                        candidates.append(color)
    return candidates


NEUTRAL_COLOR_CANDIDATES = _build_neutral_color_candidates()
_NEUTRAL_COLOR_CANDIDATE_SET = set(NEUTRAL_COLOR_CANDIDATES)


def _pick_distinct_color(model_id: str, existing_colors: Iterable[str]) -> str:
    """
    Pick a neutral color that maximizes the minimum RGB distance to existing colors.

    Falls back to deterministic hash-based seed color when no existing palette
    context is available.
    """
    seed_value = (model_id or "").strip()
    seed_color = _seed_color(seed_value).upper()

    normalized_existing = sorted({
        key for key in (_color_key(c) for c in existing_colors) if key
    })
    if not normalized_existing:
        return seed_color

    existing_rgbs = [rgb for rgb in (_hex_to_rgb(c) for c in normalized_existing) if rgb]
    if not existing_rgbs:
        return seed_color

    candidate_pool = list(NEUTRAL_COLOR_CANDIDATES)
    if seed_color not in candidate_pool:
        candidate_pool.append(seed_color)

    seed_hash = _hash_string(seed_value)
    best_color = seed_color
    best_score = (-1, -1.0, -1)
    for candidate in candidate_pool:
        candidate_rgb = _hex_to_rgb(candidate)
        if not candidate_rgb:
            continue
        distances = [_rgb_distance_sq(candidate_rgb, existing_rgb) for existing_rgb in existing_rgbs]
        min_dist_sq = min(distances)
        avg_dist_sq = sum(distances) / len(distances)
        tie_breaker = _hash_string(f"{seed_hash}:{candidate}")
        score = (min_dist_sq, avg_dist_sq, tie_breaker)
        if score > best_score:
            best_color = candidate
            best_score = score

    return best_color


def _is_auto_managed_color(model_id: str, color: Optional[str]) -> bool:
    """
    Detect colors that are safe to auto-rebalance.

    We treat legacy palette colors and previously hash-seeded neutral colors as
    auto-managed. Custom/manual colors remain untouched.
    """
    key = _color_key(color)
    if not key:
        return True
    if key in _LEGACY_COLOR_SET:
        return True
    if key in _NEUTRAL_COLOR_CANDIDATE_SET:
        return True
    old_seed_key = _color_key(_seed_color(model_id))
    return key == old_seed_key


class LLMModel(db.Model):
    """
    Configuration for available LLM models.

    Stores model capabilities (vision, reasoning), pricing (input/output costs),
    and technical specifications (context window, max tokens).
    model_type distinguishes LLMs from embedders/rerankers.
    """
    __tablename__ = 'llm_models'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    MODEL_TYPE_LLM = "llm"
    MODEL_TYPE_EMBEDDING = "embedding"
    MODEL_TYPE_RERANKER = "reranker"
    MODEL_TYPE_IMAGE = "image"
    MODEL_TYPE_AUDIO = "audio"

    # Model identification
    model_id: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    provider: Mapped[str] = mapped_column(db.String(100), nullable=False)  # e.g., 'mistral', 'openai', 'anthropic'
    provider_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('llm_providers.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(
        db.String(32),
        nullable=True,
        comment="Hex color for UI tags (e.g., #1E88E5)"
    )
    model_type: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False,
        default=MODEL_TYPE_LLM,
        index=True
    )

    # Capabilities
    supports_vision: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    supports_reasoning: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    supports_function_calling: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Technical specifications
    context_window: Mapped[int] = mapped_column(db.Integer, nullable=False)  # in tokens
    max_output_tokens: Mapped[int] = mapped_column(db.Integer, nullable=False)

    # Pricing (per 1M tokens, in USD)
    input_cost_per_million: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    output_cost_per_million: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)

    # Default settings
    is_default: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    updated_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<LLMModel {self.model_id}>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'display_name': self.display_name,
            'provider': self.provider,
            'provider_id': self.provider_id,
            'description': self.description,
            'color': self.color,
            'model_type': self.model_type,
            'supports_vision': self.supports_vision,
            'supports_reasoning': self.supports_reasoning,
            'supports_function_calling': self.supports_function_calling,
            'supports_streaming': self.supports_streaming,
            'context_window': self.context_window,
            'max_output_tokens': self.max_output_tokens,
            'input_cost_per_million': self.input_cost_per_million,
            'output_cost_per_million': self.output_cost_per_million,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }

    @classmethod
    def get_assigned_colors(
        cls,
        *,
        exclude_model_id: Optional[str] = None
    ) -> list[str]:
        """
        Return normalized model colors already present in DB.

        Intended for distance-aware color assignment when inserting new models.
        """
        try:
            query = cls.query.with_entities(cls.model_id, cls.color)
            if exclude_model_id:
                query = query.filter(cls.model_id != exclude_model_id)
            colors: list[str] = []
            for model_id, color in query.all():
                if exclude_model_id and model_id == exclude_model_id:
                    continue
                normalized = _color_key(color)
                if normalized:
                    colors.append(normalized)
            return colors
        except Exception:
            # Fallback for contexts without active app/db session.
            return []

    @classmethod
    def generate_color(
        cls,
        model_id: str,
        existing_colors: Optional[Iterable[str]] = None
    ) -> str:
        """
        Generate a stable, distance-aware neutral color for a model_id.

        If existing colors are provided (or can be read from DB), the returned
        color maximizes visual distance from those colors.
        """
        if isinstance(existing_colors, str):
            palette = [existing_colors]
        elif existing_colors is None:
            palette = cls.get_assigned_colors(exclude_model_id=model_id)
        else:
            palette = list(existing_colors)
        return _pick_distinct_color(model_id, palette)

    @classmethod
    def rebalance_auto_generated_colors(
        cls,
        *,
        model_types: Optional[Iterable[str]] = None
    ) -> int:
        """
        Recompute colors for auto-managed models to maximize pairwise distance.

        Keeps explicitly customized colors stable and only reassigns colors that
        are missing, legacy, or match historical hash-seeded values.
        Returns the number of updated models.
        """
        query = cls.query
        if model_types:
            model_types_list = [m for m in model_types if isinstance(m, str) and m.strip()]
            if model_types_list:
                query = query.filter(cls.model_type.in_(model_types_list))

        models = query.order_by(cls.model_id.asc()).all()
        if not models:
            return 0

        fixed_palette: list[str] = []
        managed_models: list['LLMModel'] = []
        for model in models:
            if _is_auto_managed_color(model.model_id, model.color):
                managed_models.append(model)
            else:
                key = _color_key(model.color)
                if key:
                    fixed_palette.append(key)

        palette = list(dict.fromkeys(fixed_palette))
        changed = 0
        for model in managed_models:
            new_color = cls.generate_color(model.model_id, existing_colors=palette)
            new_key = _color_key(new_color)
            if not new_key:
                continue
            if _color_key(model.color) != new_key:
                model.color = new_key
                changed += 1
            palette.append(new_key)

        return changed

    @staticmethod
    def normalize_color(color: Optional[str]) -> Optional[str]:
        """Normalize a hex color string to #RRGGBB (or return None if invalid)."""
        return _normalize_color(color)

    @classmethod
    def get_default_model(
        cls,
        model_type: Optional[str] = None,
        *,
        supports_vision: Optional[bool] = None
    ) -> Optional['LLMModel']:
        """Get the default active model (optionally filtered by model_type/capabilities)."""
        query = cls.query.filter_by(is_default=True, is_active=True)
        if model_type:
            query = query.filter_by(model_type=model_type)
        if supports_vision is True:
            query = query.filter_by(supports_vision=True)
        model = query.first()
        if model:
            return model

        query = cls.query.filter_by(is_active=True)
        if model_type:
            query = query.filter_by(model_type=model_type)
        if supports_vision is True:
            query = query.filter_by(supports_vision=True)
        return query.order_by(cls.display_name.asc()).first()

    @classmethod
    def get_vision_models(cls) -> list['LLMModel']:
        """Get all active models that support vision."""
        return cls.query.filter_by(supports_vision=True, is_active=True).all()

    @classmethod
    def get_by_model_id(cls, model_id: str) -> Optional['LLMModel']:
        """Get model by its model_id."""
        return cls.query.filter_by(model_id=model_id).first()

    @classmethod
    def get_default_model_id(
        cls,
        model_type: Optional[str] = None,
        *,
        supports_vision: Optional[bool] = None
    ) -> Optional[str]:
        model = cls.get_default_model(model_type=model_type, supports_vision=supports_vision)
        return model.model_id if model else None


# Default models to seed into the database
DEFAULT_LLM_MODELS = [
    {
        'model_id': 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506',
        'display_name': 'Mistral Small 3.2 (24B)',
        'provider': 'mistral',
        'description': 'Schnelles und effizientes Modell für allgemeine Chat- und RAG-Anwendungen. Gute Balance zwischen Geschwindigkeit und Qualität.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 32768,
        'max_output_tokens': 8192,
        'input_cost_per_million': 0.1,
        'output_cost_per_million': 0.3,
        'is_default': True,
        'is_active': True,
    },
    {
        'model_id': 'Global/Mistral/Magistral-Small-2509',
        'display_name': 'Magistral Small (Vision + Reasoning)',
        'provider': 'mistral',
        'description': 'Multimodales Modell mit Vision- und Reasoning-Fähigkeiten. Ideal für Bildanalyse und komplexe Schlussfolgerungen.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': True,
        'supports_reasoning': True,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 131072,
        'max_output_tokens': 40960,
        'input_cost_per_million': 0.5,
        'output_cost_per_million': 1.5,
        'is_default': False,
        'is_active': True,
    },
    # === OpenAI GPT-5 Models ===
    {
        'model_id': 'Global/OpenAI/gpt-5-nano',
        'display_name': 'GPT-5 Nano',
        'provider': 'openai',
        'description': 'OpenAI fastest and cheapest GPT-5 variant. Great for summarization and classification.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 400000,
        'max_output_tokens': 16384,
        'input_cost_per_million': 0.05,
        'output_cost_per_million': 0.40,
        'is_default': False,
        'is_active': True,
    },
    {
        'model_id': 'Global/OpenAI/gpt-5-mini',
        'display_name': 'GPT-5 Mini',
        'provider': 'openai',
        'description': 'OpenAI compact GPT-5 variant with vision support. Good balance of speed and capability.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': True,
        'supports_reasoning': False,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 1000000,
        'max_output_tokens': 32768,
        'input_cost_per_million': 0.15,
        'output_cost_per_million': 0.60,
        'is_default': False,
        'is_active': True,
    },
    {
        'model_id': 'Global/OpenAI/gpt-5',
        'display_name': 'GPT-5',
        'provider': 'openai',
        'description': 'OpenAI flagship model with strong reasoning and instruction following.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': True,
        'supports_reasoning': True,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 400000,
        'max_output_tokens': 32768,
        'input_cost_per_million': 1.25,
        'output_cost_per_million': 10.00,
        'is_default': False,
        'is_active': True,
    },
    {
        'model_id': 'Global/OpenAI/gpt-5.2',
        'display_name': 'GPT-5.2',
        'provider': 'openai',
        'description': 'Latest OpenAI model with improved reasoning and coding capabilities.',
        'model_type': LLMModel.MODEL_TYPE_LLM,
        'supports_vision': True,
        'supports_reasoning': True,
        'supports_function_calling': True,
        'supports_streaming': True,
        'context_window': 400000,
        'max_output_tokens': 32768,
        'input_cost_per_million': 1.75,
        'output_cost_per_million': 14.00,
        'is_default': False,
        'is_active': True,
    },
    # === Embedding Models ===
    {
        'model_id': 'llamaindex/vdr-2b-multi-v1',
        'display_name': 'VDR-2B Multi (Embedding)',
        'provider': 'llamaindex',
        'description': 'Multimodales Embedding-Modell für Text und Bilder. Verwendet für RAG-Pipeline und Dokumentensuche.',
        'model_type': LLMModel.MODEL_TYPE_EMBEDDING,
        'supports_vision': True,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 8192,
        'max_output_tokens': 0,  # Embedding model, no text output
        'input_cost_per_million': 0.02,
        'output_cost_per_million': 0.0,
        'is_default': True,
        'is_active': True,
    },
    {
        'model_id': 'sentence-transformers/all-MiniLM-L6-v2',
        'display_name': 'MiniLM L6 v2 (Embedding, Local)',
        'provider': 'huggingface',
        'description': 'Lokales Embedding-Modell als Fallback für RAG.',
        'model_type': LLMModel.MODEL_TYPE_EMBEDDING,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 8192,
        'max_output_tokens': 0,
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0,
        'is_default': False,
        'is_active': True,
    },
    # === RERANKER MODELS ===
    # German ELECTRA - Best quality, most resources (~110M params)
    {
        'model_id': 'svalabs/cross-electra-ms-marco-german-uncased',
        'display_name': 'German ELECTRA',
        'provider': 'sentence-transformers',
        'description': 'Bestes deutsches Modell, höchste Qualität (~350ms). 110M Parameter.',
        'model_type': LLMModel.MODEL_TYPE_RERANKER,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 512,
        'max_output_tokens': 110,  # Store param count in millions (110M)
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0,
        'is_default': True,
        'is_active': True,
    },
    # German DistilBERT - Good balance (~100M params)
    {
        'model_id': 'ML6team/cross-encoder-mmarco-german-distilbert-base',
        'display_name': 'German DistilBERT',
        'provider': 'sentence-transformers',
        'description': 'Gute deutsche Qualität, schneller (~180ms). 100M Parameter.',
        'model_type': LLMModel.MODEL_TYPE_RERANKER,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 512,
        'max_output_tokens': 100,  # Store param count in millions (100M)
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0,
        'is_default': False,
        'is_active': True,
    },
    # Bilingual DE-EN MiniLM - Fast, supports German queries (~100M params)
    {
        'model_id': 'cross-encoder/msmarco-MiniLM-L6-en-de-v1',
        'display_name': 'Bilingual DE-EN MiniLM',
        'provider': 'sentence-transformers',
        'description': 'Deutsch-Englisch bilingual, schnell (~60ms). 100M Parameter.',
        'model_type': LLMModel.MODEL_TYPE_RERANKER,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 512,
        'max_output_tokens': 100,  # Store param count in millions (100M)
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0,
        'is_default': False,
        'is_active': True,
    },
    # English MiniLM-L6 - Fastest, smallest (~23M params)
    {
        'model_id': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
        'display_name': 'English MiniLM-L6',
        'provider': 'sentence-transformers',
        'description': 'Schnellstes Modell (~50ms). Englisch-optimiert. 23M Parameter.',
        'model_type': LLMModel.MODEL_TYPE_RERANKER,
        'supports_vision': False,
        'supports_reasoning': False,
        'supports_function_calling': False,
        'supports_streaming': False,
        'context_window': 512,
        'max_output_tokens': 23,  # Store param count in millions (23M)
        'input_cost_per_million': 0.0,
        'output_cost_per_million': 0.0,
        'is_default': False,
        'is_active': True,
    },
]


def _restrict_openai_models_to_admin():
    """Restrict all OpenAI models to admin role only (idempotent)."""
    from db.database import db
    from db.models.llm_model_permission import LLMModelPermission

    openai_models = LLMModel.query.filter_by(provider='openai', model_type=LLMModel.MODEL_TYPE_LLM).all()
    for model in openai_models:
        existing = LLMModelPermission.query.filter_by(llm_model_id=model.id).first()
        if existing:
            continue
        db.session.add(LLMModelPermission(
            llm_model_id=model.id,
            permission_type='role',
            target_identifier='admin',
            granted_by='system'
        ))
        print(f"  [LLM Models] Restricted to admin: {model.model_id}")
    db.session.commit()


def seed_default_models():
    """
    Seed default LLM models into the database.
    Called during application startup.
    """
    from db.database import db
    from sqlalchemy import or_

    assigned_colors = LLMModel.get_assigned_colors()

    for model_data in DEFAULT_LLM_MODELS:
        model_type = model_data.get("model_type") or LLMModel.MODEL_TYPE_LLM
        color = (
            LLMModel.normalize_color(model_data.get("color"))
            or LLMModel.generate_color(model_data.get("model_id", ""), existing_colors=assigned_colors)
        )
        if model_data.get("is_default"):
            existing_default = LLMModel.query.filter_by(
                model_type=model_type, is_default=True
            ).first()
            if existing_default and existing_default.model_id != model_data["model_id"]:
                model_data = dict(model_data)
                model_data["is_default"] = False
        model_data = dict(model_data)
        if not LLMModel.normalize_color(model_data.get("color")):
            model_data["color"] = color
        existing = LLMModel.query.filter_by(model_id=model_data['model_id']).first()
        if not existing:
            model = LLMModel(**model_data)
            db.session.add(model)
            if model.color:
                assigned_colors.append(model.color)
            print(f"  [LLM Models] Added: {model_data['display_name']}")
        else:
            # Update existing model with new data (except is_default if already set)
            for key, value in model_data.items():
                if key == 'color':
                    existing_key = _color_key(existing.color)
                    if (not existing.color and value) or (existing_key in _LEGACY_COLOR_SET):
                        existing.color = value
                    if existing.color:
                        assigned_colors.append(existing.color)
                    continue
                if key != 'is_default' or not existing.is_default:
                    setattr(existing, key, value)

    # Rebalance auto-managed colors (missing/legacy/old hash-seeded) to maximize distance.
    try:
        changed = LLMModel.rebalance_auto_generated_colors()
        if changed:
            print(f"  [LLM Models] Rebalanced colors for {changed} model(s)")
    except Exception:
        db.session.rollback()

    db.session.commit()

    # Auto-restrict OpenAI models to admin role (idempotent)
    _restrict_openai_models_to_admin()
