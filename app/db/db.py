from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from sqlalchemy import text

from . import db
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

    # Initialisiere SQLAlchemy mit der App
    db.init_app(app)

    # Flask-Migrate initialisieren
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

        # Run all database seeders
        from .seeders import run_all_seeders
        run_all_seeders(db)
