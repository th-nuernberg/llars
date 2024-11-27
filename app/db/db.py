from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from sqlalchemy import text

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
        initialize_consulting_category_types()
        seed_user_groups()  # Hier wird die neue Funktion für das Seeden der User-Gruppen aufgerufen
        # db.session.execute(text("UPDATE users SET group_id = 1 WHERE group_id IS NULL"))
        # db.session.commit()


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

def initialize_consulting_category_types():
    from .tables import ConsultingCategoryType
    if not ConsultingCategoryType.query.filter_by(id=1).first():
        category = ConsultingCategoryType(
            id=1,
            name='Unversorgtheit des jungen Menschen',
            description='Ausfall der Bezugspersonen wegen Krankheit, stationärer Unterbringung, Inhaftierung, Tod; unbegleitet eingereiste Minderjährige',)
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=2).first():
        category = ConsultingCategoryType(
            id=2,
            name='Unzureichende Förderung / Betreuung / Versorgung des jungen Menschen in der Familie',
            description='soziale, gesundheitliche, wirtschaftliche Probleme', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=3).first():
        category = ConsultingCategoryType(
            id=3,
            name='Gefährdung des Kindeswohls',
            description='Vernachlässigung, körperliche, psychische, sexuelle Gewalt in der Familie', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=4).first():
        category = ConsultingCategoryType(
            id=4,
            name='Eingeschränkte Erziehungskompetenz der Eltern/Personensorgeberechtigten',
            description='Erziehungsunsicherheit, pädagogische Überforderung, unangemessene Verwöhnung',)
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=5).first():
        category = ConsultingCategoryType(
            id=5,
            name='Belastungen des jungen Menschen durch Problemlagen der Eltern ',
            description='Suchtverhalten, geistige oder seelische Behinderung', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=6).first():
        category = ConsultingCategoryType(
            id=6,
            name='Belastungen des jungen Menschen durch familiäre Konflikte',
            description='Partnerkonflikte, Trennung und Scheidung, Umgangs- / Sorgerechtsstreitigkeiten, Eltern- / Stiefeltern-Kind-Konflikte, migrationsbedingte Konfliktlagen', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=7).first():
        category = ConsultingCategoryType(
            id=7,
            name='Auffälligkeiten im sozialen Verhalten (dissoziales Verhalten) des jungen Menschen',
            description='Gehemmtheit, Isolation, Geschwisterrivalität, Weglaufen, Aggressivität, Drogen- / Alkoholkonsum, Delinquenz / Straftat',)
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=8).first():
        category = ConsultingCategoryType(
            id=8,
            name='Entwicklungsauffälligkeiten/seelische Probleme des jungen Menschen ',
            description='Entwicklungsrückstand, Ängste, Zwänge, selbst verletzendes Verhalten, suizidale Tendenzen', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=9).first():
        category = ConsultingCategoryType(
            id=9,
            name='Schulische / berufliche Probleme des jungen Menschen',
            description='Schwierigkeiten mit Leistungsanforderungen, Konzentrationsprobleme (ADS, Hyperaktivität), schulvermeidendes Verhalten (Schwänzen), Hochbegabung', )
        db.session.add(category)

    if not ConsultingCategoryType.query.filter_by(id=10).first():
        category = ConsultingCategoryType(
            id=10,
            name='Sonstiges',
            description=None, )
        db.session.add(category)

    db.session.commit()


def seed_user_groups():
    from .tables import UserGroup  # Importiere das UserGroup Model

    # Prüfen, ob die Gruppen bereits existieren
    if not UserGroup.query.filter_by(name='Standard').first():
        standard_group = UserGroup(name='Standard')
        db.session.add(standard_group)
    if not UserGroup.query.filter_by(name='Admin').first():
        admin_group = UserGroup(name='Admin')
        db.session.add(admin_group)

    db.session.commit()
    print("User groups seeded successfully.")
