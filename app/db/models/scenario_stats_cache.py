"""
Scenario Stats Cache Model.

Stores pre-computed scenario statistics in the database for fast retrieval.
Background threads recompute stats and push updates via Socket.IO.
"""

from db.database import db
from sqlalchemy.orm import mapped_column
from sqlalchemy import Integer, Text, String, DateTime, Boolean


class ScenarioStatsCache(db.Model):
    __tablename__ = 'scenario_stats_cache'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(Integer, unique=True, nullable=False, index=True)
    stats_json = mapped_column(Text, nullable=False)
    function_type = mapped_column(String(50), nullable=False)
    computed_at = mapped_column(DateTime, nullable=False)
    item_count = mapped_column(Integer, default=0)
    is_computing = mapped_column(Boolean, default=False)
