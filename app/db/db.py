from flask_sqlalchemy import SQLAlchemy
import os
from . import db  # Importieren Sie db aus dem database-Paket

def configure_database(app):
    # Datenbankkonfiguration und Initialisierung
    db_root_password = os.getenv('MYSQL_ROOT_PASSWORD')
    db_database_name = os.getenv('MYSQL_DATABASE')
    db_user = os.getenv('MYSQL_USER')
    db_user_password = os.getenv('MYSQL_PASSWORD')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_root_password}@db-maria-service:3306/{db_database_name}'

    db.init_app(app)
    with app.app_context():
        db.create_all()