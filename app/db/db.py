from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

from . import db
migrate = Migrate()  # Initialisiere Flask-Migrate

def configure_database(app):
    # Datenbankkonfiguration und Initialisierung
    db_root_password = os.getenv('MYSQL_ROOT_PASSWORD')
    db_database_name = os.getenv('MYSQL_DATABASE')
    db_user = os.getenv('MYSQL_USER')
    db_user_password = os.getenv('MYSQL_PASSWORD')

    # Datenbank-URI konfigurieren
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_root_password}@db-maria-service:3306/{db_database_name}'

    # Initialisiere SQLAlchemy mit der App
    db.init_app(app)

    # Flask-Migrate initialisieren
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
        initialize_feature_function_types()

def initialize_feature_function_types():
    from .tables import FeatureFunctionType  # Importiere die Modelle hier, um zirkuläre Importe zu vermeiden

    # Check if the feature function types are already in the database
    if not FeatureFunctionType.query.filter_by(function_type_id=1).first():
        ranking = FeatureFunctionType(function_type_id=1, name='ranking')
        db.session.add(ranking)
    if not FeatureFunctionType.query.filter_by(function_type_id=2).first():
        rating = FeatureFunctionType(function_type_id=2, name='rating')
        db.session.add(rating)
    if not FeatureFunctionType.query.filter_by(function_type_id=3).first():
        mail_rating = FeatureFunctionType(function_type_id=3, name='mail_rating')
        db.session.add(mail_rating)

    db.session.commit()
