"""Deutsche Bahn Price Agent database models."""

from datetime import datetime
from db import db


class DbPriceScan(db.Model):
    """Metadata for a single price scan run."""
    __tablename__ = 'db_price_scans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    direction = db.Column(db.String(20), nullable=False)  # 'outbound' or 'return'
    scan_date = db.Column(db.Date, nullable=False)  # which travel date was scanned
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    journey_count = db.Column(db.Integer, default=0)
    cheapest_price = db.Column(db.Float, nullable=True)
    error = db.Column(db.Text, nullable=True)

    entries = db.relationship('DbPriceEntry', backref='scan', lazy='dynamic',
                              cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('ix_db_price_scans_date_dir', 'scan_date', 'direction'),
        db.Index('ix_db_price_scans_scanned_at', 'scanned_at'),
    )


class DbPriceEntry(db.Model):
    """A single journey with price found during a scan."""
    __tablename__ = 'db_price_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('db_price_scans.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    departure = db.Column(db.DateTime, nullable=False)
    arrival = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    transfers = db.Column(db.Integer, nullable=False, default=0)
    is_direct = db.Column(db.Boolean, nullable=False, default=False)

    train_types = db.Column(db.String(200), nullable=True)  # e.g. "ICE 523, RE 11"
    price_eur = db.Column(db.Float, nullable=False)

    direction = db.Column(db.String(20), nullable=False)  # 'outbound' or 'return'
    travel_date = db.Column(db.Date, nullable=False)
    is_night = db.Column(db.Boolean, nullable=False, default=False)  # departure 22:00-06:00

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('ix_db_price_entries_travel_dir', 'travel_date', 'direction'),
        db.Index('ix_db_price_entries_price', 'price_eur'),
        db.Index('ix_db_price_entries_dedup', 'departure', 'direction', 'travel_date'),
    )


class DbTripSearch(db.Model):
    """A user's trip search request."""
    __tablename__ = 'db_trip_searches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), nullable=False)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    flexibility_days = db.Column(db.Integer, default=3)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    llm_analysis = db.Column(db.Text, nullable=True)  # LLM recommendation text
    analyzed_at = db.Column(db.DateTime, nullable=True)
