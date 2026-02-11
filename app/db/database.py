from __future__ import annotations

import os

from flask_migrate import Migrate

from . import db as db_instance

# Re-export the db instance for backwards compatibility (modules import `from db.database import db`)
db = db_instance

migrate = Migrate()  # Initialisiere Flask-Migrate


def configure_database(app):
    """
    Configure and initialize the database with Flask app.

    This function sets up the database connection, runs migrations,
    and seeds all required data.

    Args:
        app: Flask application instance
    """
    # Datenbankkonfiguration und Initialisierung
    db_root_password = os.getenv('MYSQL_ROOT_PASSWORD')
    db_database_name = os.getenv('MYSQL_DATABASE')
    db_user = os.getenv('MYSQL_USER')
    db_user_password = os.getenv('MYSQL_PASSWORD')

    # Datenbank-URI konfigurieren (use MYSQL_USER instead of root for better security)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_user_password}@db-maria-service:3306/{db_database_name}'

    # Connection pool: sized for concurrent LLM evaluator threads + HTTP requests.
    # Default (5+10=15) is too small when multiple scenarios run LLM evals simultaneously.
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,       # total max: 30 connections
        'pool_timeout': 60,       # wait up to 60s for a connection (default 30)
        'pool_recycle': 1800,     # recycle connections every 30min (MariaDB wait_timeout)
        'pool_pre_ping': True,    # verify connection is alive before using
    }

    # Initialisiere SQLAlchemy mit der App
    db_instance.init_app(app)

    # Flask-Migrate initialisieren
    migrate.init_app(app, db_instance)

    with app.app_context():
        db_instance.create_all()

        # Run all database seeders
        from .seeders import run_all_seeders
        run_all_seeders(db_instance)

        try:
            from services.system_event_service import SystemEventService

            SystemEventService.log_event(
                event_type="system.startup",
                severity="info",
                message="LLARS backend started",
                details={"project_state": os.getenv("PROJECT_STATE", "development")},
                throttle_key="backend_startup",
                throttle_seconds=30,
            )
        except Exception:
            pass
