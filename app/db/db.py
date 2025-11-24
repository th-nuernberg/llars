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

    # Datenbank-URI konfigurieren (use MYSQL_USER instead of root for better security)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_user_password}@db-maria-service:3306/{db_database_name}'

    # Initialisiere SQLAlchemy mit der App
    db.init_app(app)

    # Flask-Migrate initialisieren
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
        initialize_feature_function_types()
        initialize_consulting_category_types()
        initialize_permissions()  # Initialize permission system
        # Seeder nur ausführen, wenn START_SEEDER in der Umgebung auf 'true' gesetzt ist
        start_seeder = os.getenv('START_SEEDER', 'false').lower()
        if start_seeder == 'true':
            seed_user_groups()
        else:
            print(f"Seeder übersprungen (START_SEEDER={start_seeder})")
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
    if not FeatureFunctionType.query.filter_by(function_type_id=4).first():
        comparison = FeatureFunctionType(function_type_id=4, name='comparison')
        db.session.add(comparison)

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


def initialize_permissions():
    """
    Initialize the permission system with base permissions and roles.
    This runs on every app startup but uses idempotent checks.
    """
    from .tables import Permission, Role, RolePermission

    # Define all base permissions
    permissions_data = [
        # Feature: Mail Rating
        {
            'permission_key': 'feature:mail_rating:view',
            'display_name': 'Mail Rating ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen der Mail-Rating-Funktion'
        },
        {
            'permission_key': 'feature:mail_rating:edit',
            'display_name': 'Mail Rating bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Bearbeiten und Bewerten von Mails'
        },
        # Feature: Ranking
        {
            'permission_key': 'feature:ranking:view',
            'display_name': 'Ranking ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen der Ranking-Funktion'
        },
        {
            'permission_key': 'feature:ranking:edit',
            'display_name': 'Ranking bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Erstellen und Bearbeiten von Rankings'
        },
        # Feature: Rating
        {
            'permission_key': 'feature:rating:view',
            'display_name': 'Rating ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen der Rating-Funktion'
        },
        {
            'permission_key': 'feature:rating:edit',
            'display_name': 'Rating bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Erstellen und Bearbeiten von Ratings'
        },
        # Feature: Comparison
        {
            'permission_key': 'feature:comparison:view',
            'display_name': 'LLM-Vergleich ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen der LLM-Vergleichs-Funktion'
        },
        {
            'permission_key': 'feature:comparison:edit',
            'display_name': 'LLM-Vergleich bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Durchführen von LLM-Vergleichen'
        },
        # Feature: Prompt Engineering
        {
            'permission_key': 'feature:prompt_engineering:view',
            'display_name': 'Prompt Engineering ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen der Prompt-Engineering-Funktion'
        },
        {
            'permission_key': 'feature:prompt_engineering:edit',
            'display_name': 'Prompt Engineering bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Erstellen und Bearbeiten von Prompts'
        },
        # Admin: Permissions Management
        {
            'permission_key': 'admin:permissions:manage',
            'display_name': 'Berechtigungen verwalten',
            'category': 'admin',
            'description': 'Erlaubt das Verwalten von Benutzerberechtigungen'
        },
        {
            'permission_key': 'admin:users:manage',
            'display_name': 'Benutzer verwalten',
            'category': 'admin',
            'description': 'Erlaubt das Verwalten von Benutzern'
        },
        {
            'permission_key': 'admin:roles:manage',
            'display_name': 'Rollen verwalten',
            'category': 'admin',
            'description': 'Erlaubt das Verwalten von Rollen'
        },
        {
            'permission_key': 'admin:system:configure',
            'display_name': 'System konfigurieren',
            'category': 'admin',
            'description': 'Erlaubt Systemkonfigurationen'
        },
        # Data Operations
        {
            'permission_key': 'data:export',
            'display_name': 'Daten exportieren',
            'category': 'data',
            'description': 'Erlaubt das Exportieren von Daten'
        },
        {
            'permission_key': 'data:import',
            'display_name': 'Daten importieren',
            'category': 'data',
            'description': 'Erlaubt das Importieren von Daten'
        },
        {
            'permission_key': 'data:delete',
            'display_name': 'Daten löschen',
            'category': 'data',
            'description': 'Erlaubt das Löschen von Daten'
        },
    ]

    # Create permissions (idempotent)
    permission_map = {}  # Maps permission_key to Permission object
    for perm_data in permissions_data:
        existing = Permission.query.filter_by(
            permission_key=perm_data['permission_key']
        ).first()

        if not existing:
            perm = Permission(**perm_data)
            db.session.add(perm)
            db.session.flush()  # Get ID
            permission_map[perm_data['permission_key']] = perm
        else:
            permission_map[perm_data['permission_key']] = existing

    db.session.commit()

    # Define roles
    roles_data = [
        {
            'role_name': 'admin',
            'display_name': 'Administrator',
            'description': 'Voller Zugriff auf alle Funktionen und Einstellungen',
            'permissions': [p['permission_key'] for p in permissions_data]  # All permissions
        },
        {
            'role_name': 'researcher',
            'display_name': 'Forscher',
            'description': 'Zugriff auf alle Features zum Forschen und Daten exportieren',
            'permissions': [
                'feature:mail_rating:view',
                'feature:mail_rating:edit',
                'feature:ranking:view',
                'feature:ranking:edit',
                'feature:rating:view',
                'feature:rating:edit',
                'feature:comparison:view',
                'feature:comparison:edit',
                'feature:prompt_engineering:view',
                'feature:prompt_engineering:edit',
                'data:export',
            ]
        },
        {
            'role_name': 'viewer',
            'display_name': 'Betrachter',
            'description': 'Nur Lesezugriff auf Features',
            'permissions': [
                'feature:mail_rating:view',
                'feature:ranking:view',
                'feature:rating:view',
                'feature:comparison:view',
                'feature:prompt_engineering:view',
            ]
        },
    ]

    # Create roles and assign permissions (idempotent)
    for role_data in roles_data:
        role_name = role_data['role_name']
        permission_keys = role_data.pop('permissions')

        existing_role = Role.query.filter_by(role_name=role_name).first()

        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            db.session.flush()  # Get ID

            # Assign permissions to role
            for perm_key in permission_keys:
                if perm_key in permission_map:
                    perm = permission_map[perm_key]
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    )
                    db.session.add(role_perm)

            db.session.commit()
            print(f"Created role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")

    # Assign admin role to default admin user
    assign_default_admin_role()

    print("Permission system initialized successfully.")


def assign_default_admin_role():
    """
    Automatically assign admin role to the default 'admin' user.
    This ensures the admin user always has admin permissions after database reset.
    """
    from .tables import UserRole, Role
    from datetime import datetime

    # Find admin role
    admin_role = Role.query.filter_by(role_name='admin').first()
    if not admin_role:
        print("Warning: Admin role not found. Skipping default admin assignment.")
        return

    # Check if admin user already has admin role
    existing = UserRole.query.filter_by(
        username='admin',
        role_id=admin_role.id
    ).first()

    if not existing:
        # Assign admin role to admin user
        user_role = UserRole(
            username='admin',
            role_id=admin_role.id,
            assigned_by='system',
            assigned_at=datetime.utcnow()
        )
        db.session.add(user_role)
        db.session.commit()
        print("✅ Assigned admin role to user 'admin' automatically.")
    else:
        print("✅ User 'admin' already has admin role.")
