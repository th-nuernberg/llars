"""
Permission System Seeder

Seeds permissions, roles, and assigns default roles to users.
"""
from datetime import datetime


def initialize_permissions(db):
    """
    Initialize the permission system with base permissions and roles.
    This runs on every app startup but uses idempotent checks.

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import Permission, Role, RolePermission

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
        # Feature: Markdown Collab
        {
            'permission_key': 'feature:markdown_collab:view',
            'display_name': 'Markdown Collab ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen von Markdown Collab Workspaces und Dokumenten'
        },
        {
            'permission_key': 'feature:markdown_collab:edit',
            'display_name': 'Markdown Collab bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Erstellen und Bearbeiten von Markdown Collab Dokumenten'
        },
        {
            'permission_key': 'feature:markdown_collab:share',
            'display_name': 'Markdown Collab teilen',
            'category': 'feature',
            'description': 'Erlaubt das Teilen von Markdown Collab Dateien und Ordnern'
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
        # Feature: RAG Document Management
        {
            'permission_key': 'feature:rag:view',
            'display_name': 'RAG-Dokumente ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen von RAG-Dokumenten und Statistiken'
        },
        {
            'permission_key': 'feature:rag:edit',
            'display_name': 'RAG-Dokumente bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Hochladen und Bearbeiten von RAG-Dokumenten'
        },
        {
            'permission_key': 'feature:rag:delete',
            'display_name': 'RAG-Dokumente löschen',
            'category': 'feature',
            'description': 'Erlaubt das Löschen von RAG-Dokumenten und Collections'
        },
        # Feature: Chatbots
        {
            'permission_key': 'feature:chatbots:view',
            'display_name': 'Chatbots ansehen',
            'category': 'feature',
            'description': 'Erlaubt das Ansehen und Verwenden von Chatbots'
        },
        {
            'permission_key': 'feature:chatbots:edit',
            'display_name': 'Chatbots bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt das Erstellen und Bearbeiten von Chatbots'
        },
        {
            'permission_key': 'feature:chatbots:delete',
            'display_name': 'Chatbots löschen',
            'category': 'feature',
            'description': 'Erlaubt das Löschen von Chatbots'
        },
        # Feature: KAIMO
        {
            'permission_key': 'feature:kaimo:view',
            'display_name': 'KAIMO ansehen',
            'category': 'feature',
            'description': 'Erlaubt den Zugriff auf das KAIMO Panel'
        },
        {
            'permission_key': 'feature:kaimo:edit',
            'display_name': 'KAIMO bearbeiten',
            'category': 'feature',
            'description': 'Erlaubt Bewertungen und Zuordnungen im KAIMO Panel'
        },
        {
            'permission_key': 'admin:kaimo:manage',
            'display_name': 'KAIMO Fälle verwalten',
            'category': 'admin',
            'description': 'Erlaubt das Anlegen, Bearbeiten und Veröffentlichen von KAIMO Fällen'
        },
        {
            'permission_key': 'admin:kaimo:results',
            'display_name': 'KAIMO Ergebnisse einsehen',
            'category': 'admin',
            'description': 'Erlaubt aggregierte Ergebnisse und Statistiken zu sehen'
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
                'feature:markdown_collab:view',
                'feature:markdown_collab:edit',
                'feature:markdown_collab:share',
                'feature:rag:view',
                'feature:rag:edit',
                'feature:chatbots:view',
                'feature:chatbots:edit',
                'feature:kaimo:view',
                'feature:kaimo:edit',
                'admin:kaimo:manage',
                'admin:kaimo:results',
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
                'feature:rag:view',
                'feature:chatbots:view',
                'feature:markdown_collab:view',
                'feature:kaimo:view',
                'feature:kaimo:edit',
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
            # Update existing role with any new permissions
            role = existing_role
            existing_perm_ids = {rp.permission_id for rp in
                               RolePermission.query.filter_by(role_id=role.id).all()}

            added_perms = []
            for perm_key in permission_keys:
                if perm_key in permission_map:
                    perm = permission_map[perm_key]
                    if perm.id not in existing_perm_ids:
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=perm.id
                        )
                        db.session.add(role_perm)
                        added_perms.append(perm_key)

            if added_perms:
                db.session.commit()
                print(f"Role '{role_name}' updated with new permissions: {added_perms}")
            else:
                print(f"Role already exists: {role_name}")

    # Assign admin role to default admin user
    assign_default_admin_role(db)
    assign_default_demo_roles(db)

    print("Permission system initialized successfully.")


def assign_default_admin_role(db):
    """
    Automatically assign admin role to the default 'admin' user.
    This ensures the admin user always has admin permissions after database reset.

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import UserRole, Role

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


def assign_default_demo_roles(db):
    """
    Assign default demo roles to 'researcher' and 'viewer' users if they exist.
    Uses username-based mapping (no foreign key to users table required).

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import UserRole, Role

    role_map = {
        'researcher': 'researcher',
        'viewer': 'viewer',
    }

    for username, role_name in role_map.items():
        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            print(f"Warning: Role '{role_name}' not found; skipping assignment for {username}")
            continue

        existing = UserRole.query.filter_by(username=username, role_id=role.id).first()
        if existing:
            continue

        assignment = UserRole(
            username=username,
            role_id=role.id,
            assigned_by='system',
            assigned_at=datetime.utcnow()
        )
        db.session.add(assignment)

    db.session.commit()
