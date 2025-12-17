"""Analytics settings stored in the LLARS database."""

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from db import db


class AnalyticsSettings(db.Model):
    """
    Global analytics configuration.

    This is a single-row table (id=1) used to configure Matomo tracking behavior
    without relying on build-time environment variables.
    """

    __tablename__ = "analytics_settings"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=False, default=1)

    # Matomo core
    matomo_enabled: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    matomo_base_url: Mapped[str] = mapped_column(db.String(255), default="/analytics/", nullable=False)
    matomo_site_id: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)

    # Privacy/consent
    include_query: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    disable_cookies: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    require_consent: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    require_cookie_consent: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    set_user_id: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Interaction tracking
    track_clicks: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    track_hovers: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    hover_min_ms: Mapped[int] = mapped_column(db.Integer, default=400, nullable=False)
    hover_sample_rate: Mapped[float] = mapped_column(db.Float, default=1.0, nullable=False)

    # Time on page
    heartbeat_enabled: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    heartbeat_seconds: Mapped[int] = mapped_column(db.Integer, default=15, nullable=False)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

