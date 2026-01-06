"""
Unit Tests: RAG Access Service
==============================

Tests for the RAG document/collection access control service.

Test IDs:
- ACC-001 to ACC-010: Helper Method Tests
- ACC-020 to ACC-035: Document Access Tests
- ACC-040 to ACC-055: Collection Access Tests
- ACC-060 to ACC-075: Permission Management Tests

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch


class TestHelperMethods:
    """
    Helper Method Tests

    Tests for internal helper functions.
    """

    def test_ACC_001_normalize_strings_list(self, app, app_context):
        """
        [ACC-001] Normalize String Liste

        Liste von Strings soll normalisiert werden.
        """
        from services.rag.access_service import RAGAccessService

        result = RAGAccessService._normalize_strings(['user1', 'user2', 'user3'])
        assert result == ['user1', 'user2', 'user3']

    def test_ACC_002_normalize_strings_single(self, app, app_context):
        """
        [ACC-002] Normalize Einzelner String

        Einzelner String soll in Liste konvertiert werden.
        """
        from services.rag.access_service import RAGAccessService

        result = RAGAccessService._normalize_strings('single_user')
        assert result == ['single_user']

    def test_ACC_003_normalize_strings_duplicates(self, app, app_context):
        """
        [ACC-003] Normalize Duplikate entfernen

        Duplikate sollen entfernt werden.
        """
        from services.rag.access_service import RAGAccessService

        result = RAGAccessService._normalize_strings(['user1', 'user1', 'user2'])
        assert result == ['user1', 'user2']

    def test_ACC_004_normalize_strings_empty(self, app, app_context):
        """
        [ACC-004] Normalize Leere Eingabe

        Leere Eingabe soll leere Liste zurückgeben.
        """
        from services.rag.access_service import RAGAccessService

        assert RAGAccessService._normalize_strings(None) == []
        assert RAGAccessService._normalize_strings([]) == []
        assert RAGAccessService._normalize_strings('') == []

    def test_ACC_005_normalize_strings_whitespace(self, app, app_context):
        """
        [ACC-005] Normalize Whitespace trimmen

        Whitespace soll entfernt werden.
        """
        from services.rag.access_service import RAGAccessService

        result = RAGAccessService._normalize_strings(['  user1  ', 'user2 '])
        assert result == ['user1', 'user2']

    def test_ACC_006_get_user_role_names_none(self, app, db, app_context):
        """
        [ACC-006] User Roles ohne Username

        Ohne Username soll leeres Set zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService

        result = RAGAccessService._get_user_role_names(None)
        assert result == set()

    def test_ACC_007_get_user_role_names_existing(self, app, db, app_context):
        """
        [ACC-007] User Roles für existierenden User

        Rollen des Users sollen zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import Role, UserRole

        # Create role and assignment
        role = Role(role_name='test_role', display_name='Test Role', description='Test')
        db.session.add(role)
        db.session.flush()

        user_role = UserRole(username='test_user', role_id=role.id)
        db.session.add(user_role)
        db.session.commit()

        result = RAGAccessService._get_user_role_names('test_user')
        assert 'test_role' in result

    def test_ACC_008_is_admin_user_none(self, app, db, app_context):
        """
        [ACC-008] Admin Check ohne Username

        Ohne Username soll False zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService

        assert RAGAccessService.is_admin_user(None) is False

    def test_ACC_009_is_admin_user_system_api_key(self, app, db, app_context):
        """
        [ACC-009] Admin Check mit System API Key

        System API Key soll als Admin erkannt werden.
        """
        from services.rag.access_service import RAGAccessService
        from flask import g

        g.is_system_api_key = True
        try:
            assert RAGAccessService.is_admin_user('any_user') is True
        finally:
            g.is_system_api_key = False

    def test_ACC_010_is_admin_user_permission_check(self, app, db, app_context):
        """
        [ACC-010] Admin Check via Permission

        User mit admin:permissions:manage soll als Admin erkannt werden.
        """
        from services.rag.access_service import RAGAccessService

        with patch('services.rag.access_service.PermissionService') as MockPerm:
            MockPerm.check_permission.return_value = True

            result = RAGAccessService.is_admin_user('admin_user')

            assert result is True
            MockPerm.check_permission.assert_called_with('admin_user', 'admin:permissions:manage')


class TestDocumentAccess:
    """
    Document Access Tests

    Tests for document-level access control.
    """

    def test_ACC_020_can_view_document_none_params(self, app, db, app_context):
        """
        [ACC-020] View Document ohne Parameter

        Ohne Username oder Document soll False zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument

        doc = MagicMock(spec=RAGDocument)

        assert RAGAccessService.can_view_document(None, doc) is False
        assert RAGAccessService.can_view_document('user', None) is False

    def test_ACC_021_can_view_document_admin(self, app, db, app_context):
        """
        [ACC-021] Admin kann alles sehen

        Admin soll alle Dokumente sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='test.pdf', original_filename='test.pdf',
            file_path='/tmp/test.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash1',
            collection_id=collection.id, uploaded_by='other_user',
            is_public=False
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=True):
            result = RAGAccessService.can_view_document('admin', doc)
            assert result is True

    def test_ACC_022_can_view_document_owner(self, app, db, app_context):
        """
        [ACC-022] Owner kann eigenes Dokument sehen

        Besitzer soll sein Dokument sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='owned.pdf', original_filename='owned.pdf',
            file_path='/tmp/owned.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_owned',
            collection_id=collection.id, uploaded_by='owner',
            is_public=False
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_document('owner', doc)
            assert result is True

    def test_ACC_023_can_view_document_public(self, app, db, app_context):
        """
        [ACC-023] Öffentliche Dokumente für alle sichtbar

        Öffentliche Dokumente sollen für alle sichtbar sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='public.pdf', original_filename='public.pdf',
            file_path='/tmp/public.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_public',
            collection_id=collection.id, uploaded_by='other',
            is_public=True
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_document('any_user', doc)
            assert result is True

    def test_ACC_024_can_view_document_no_access(self, app, db, app_context):
        """
        [ACC-024] Kein Zugriff auf privates Dokument

        Private Dokumente ohne Berechtigung sollen nicht sichtbar sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='private.pdf', original_filename='private.pdf',
            file_path='/tmp/private.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_private',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_document('unauthorized', doc)
            assert result is False

    def test_ACC_025_can_edit_document_owner(self, app, db, app_context):
        """
        [ACC-025] Owner kann eigenes Dokument bearbeiten

        Besitzer soll sein Dokument bearbeiten können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='edit.pdf', original_filename='edit.pdf',
            file_path='/tmp/edit.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_edit',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_edit_document('owner', doc)
            assert result is True

    def test_ACC_026_can_edit_document_no_access(self, app, db, app_context):
        """
        [ACC-026] Kein Edit-Zugriff ohne Berechtigung

        Ohne Berechtigung soll Edit nicht möglich sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='noedit.pdf', original_filename='noedit.pdf',
            file_path='/tmp/noedit.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_noedit',
            collection_id=collection.id, uploaded_by='other'
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_edit_document('unauthorized', doc)
            assert result is False

    def test_ACC_027_can_delete_document_owner(self, app, db, app_context):
        """
        [ACC-027] Owner kann eigenes Dokument löschen

        Besitzer soll sein Dokument löschen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='delete.pdf', original_filename='delete.pdf',
            file_path='/tmp/delete.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_delete',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_delete_document('owner', doc)
            assert result is True

    def test_ACC_028_can_share_document_owner(self, app, db, app_context):
        """
        [ACC-028] Owner kann eigenes Dokument teilen

        Besitzer soll sein Dokument teilen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='share.pdf', original_filename='share.pdf',
            file_path='/tmp/share.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_share',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_share_document('owner', doc)
            assert result is True

    def test_ACC_029_can_view_document_with_permission(self, app, db, app_context):
        """
        [ACC-029] View mit expliziter Permission

        User mit expliziter View-Permission soll Dokument sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='perm.pdf', original_filename='perm.pdf',
            file_path='/tmp/perm.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_perm',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add(doc)
        db.session.flush()

        # Grant view permission
        perm = RAGDocumentPermission(
            document_id=doc.id,
            permission_type='user',
            target_identifier='granted_user',
            can_view=True
        )
        db.session.add(perm)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_document('granted_user', doc)
            assert result is True


class TestCollectionAccess:
    """
    Collection Access Tests

    Tests for collection-level access control.
    """

    def test_ACC_040_can_view_collection_none_params(self, app, db, app_context):
        """
        [ACC-040] View Collection ohne Parameter

        Ohne Username oder Collection soll False zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        coll = MagicMock(spec=RAGCollection)

        assert RAGAccessService.can_view_collection(None, coll) is False
        assert RAGAccessService.can_view_collection('user', None) is False

    def test_ACC_041_can_view_collection_admin(self, app, db, app_context):
        """
        [ACC-041] Admin kann alle Collections sehen

        Admin soll alle Collections sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='private_coll', display_name='Private Collection',
            created_by='other', is_public=False
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=True):
            result = RAGAccessService.can_view_collection('admin', collection)
            assert result is True

    def test_ACC_042_can_view_collection_owner(self, app, db, app_context):
        """
        [ACC-042] Owner kann eigene Collection sehen

        Besitzer soll seine Collection sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='owned_coll', display_name='Owned Collection',
            created_by='owner', is_public=False
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_collection('owner', collection)
            assert result is True

    def test_ACC_043_can_view_collection_public(self, app, db, app_context):
        """
        [ACC-043] Öffentliche Collections für alle sichtbar

        Öffentliche Collections sollen für alle sichtbar sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='public_coll', display_name='Public Collection',
            created_by='other', is_public=True
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_collection('any_user', collection)
            assert result is True

    def test_ACC_044_can_edit_collection_owner(self, app, db, app_context):
        """
        [ACC-044] Owner kann eigene Collection bearbeiten

        Besitzer soll seine Collection bearbeiten können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='edit_coll', display_name='Edit Collection',
            created_by='owner'
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_edit_collection('owner', collection)
            assert result is True

    def test_ACC_045_can_edit_collection_no_access(self, app, db, app_context):
        """
        [ACC-045] Kein Edit-Zugriff ohne Berechtigung

        Ohne Berechtigung soll Edit nicht möglich sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='noedit_coll', display_name='No Edit Collection',
            created_by='other'
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_edit_collection('unauthorized', collection)
            assert result is False

    def test_ACC_046_can_delete_collection_owner(self, app, db, app_context):
        """
        [ACC-046] Owner kann eigene Collection löschen

        Besitzer soll seine Collection löschen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='delete_coll', display_name='Delete Collection',
            created_by='owner'
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_delete_collection('owner', collection)
            assert result is True

    def test_ACC_047_can_share_collection_owner(self, app, db, app_context):
        """
        [ACC-047] Owner kann eigene Collection teilen

        Besitzer soll seine Collection teilen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='share_coll', display_name='Share Collection',
            created_by='owner'
        )
        db.session.add(collection)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_share_collection('owner', collection)
            assert result is True

    def test_ACC_048_can_view_collection_with_permission(self, app, db, app_context):
        """
        [ACC-048] View mit expliziter Collection Permission

        User mit expliziter View-Permission soll Collection sehen können.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection, RAGCollectionPermission

        collection = RAGCollection(
            name='perm_coll', display_name='Permission Collection',
            created_by='other', is_public=False
        )
        db.session.add(collection)
        db.session.flush()

        # Grant view permission
        perm = RAGCollectionPermission(
            collection_id=collection.id,
            permission_type='user',
            target_identifier='granted_user',
            can_view=True
        )
        db.session.add(perm)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_collection('granted_user', collection)
            assert result is True


class TestPermissionManagement:
    """
    Permission Management Tests

    Tests for getting and setting permissions.
    """

    def test_ACC_060_get_document_permissions_empty(self, app, db, app_context):
        """
        [ACC-060] Document Permissions leer

        Ohne Permissions soll leere Liste zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='noperm.pdf', original_filename='noperm.pdf',
            file_path='/tmp/noperm.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_noperm',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = RAGAccessService.get_document_permissions(doc.id)

        assert result['users'] == []
        assert result['roles'] == []

    def test_ACC_061_get_document_permissions_with_data(self, app, db, app_context):
        """
        [ACC-061] Document Permissions abrufen

        Vorhandene Permissions sollen korrekt zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='perms.pdf', original_filename='perms.pdf',
            file_path='/tmp/perms.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_perms',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        # Add user permission
        user_perm = RAGDocumentPermission(
            document_id=doc.id,
            permission_type='user',
            target_identifier='user1',
            can_view=True, can_edit=True
        )
        # Add role permission
        role_perm = RAGDocumentPermission(
            document_id=doc.id,
            permission_type='role',
            target_identifier='researcher',
            can_view=True
        )
        db.session.add_all([user_perm, role_perm])
        db.session.commit()

        result = RAGAccessService.get_document_permissions(doc.id)

        assert len(result['users']) == 1
        assert result['users'][0]['target'] == 'user1'
        assert result['users'][0]['can_edit'] is True

        assert len(result['roles']) == 1
        assert result['roles'][0]['target'] == 'researcher'

    def test_ACC_062_set_document_permissions_new(self, app, db, app_context):
        """
        [ACC-062] Document Permissions setzen (neu)

        Neue Permissions sollen erstellt werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='setperm.pdf', original_filename='setperm.pdf',
            file_path='/tmp/setperm.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_setperm',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = RAGAccessService.set_document_permissions(
            document_id=doc.id,
            usernames=['user1', 'user2'],
            role_names=['researcher'],
            granted_by='admin',
            access={'can_view': True, 'can_edit': True}
        )

        assert 'user1' in result['usernames']
        assert 'user2' in result['usernames']
        assert 'researcher' in result['role_names']

        # Verify in database
        perms = RAGDocumentPermission.query.filter_by(document_id=doc.id).all()
        assert len(perms) == 3

    def test_ACC_063_set_document_permissions_update(self, app, db, app_context):
        """
        [ACC-063] Document Permissions aktualisieren

        Bestehende Permissions sollen aktualisiert werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='update.pdf', original_filename='update.pdf',
            file_path='/tmp/update.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_update',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        # Create initial permission
        perm = RAGDocumentPermission(
            document_id=doc.id,
            permission_type='user',
            target_identifier='user1',
            can_view=True, can_edit=False
        )
        db.session.add(perm)
        db.session.commit()

        # Update permission
        RAGAccessService.set_document_permissions(
            document_id=doc.id,
            usernames=['user1'],
            access={'can_view': True, 'can_edit': True}
        )

        # Verify update
        updated_perm = RAGDocumentPermission.query.filter_by(
            document_id=doc.id, target_identifier='user1'
        ).first()
        assert updated_perm.can_edit is True

    def test_ACC_064_set_document_permissions_remove(self, app, db, app_context):
        """
        [ACC-064] Document Permissions entfernen

        Nicht mehr gelistete Permissions sollen entfernt werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='remove.pdf', original_filename='remove.pdf',
            file_path='/tmp/remove.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_remove',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        # Create initial permissions
        perm1 = RAGDocumentPermission(
            document_id=doc.id, permission_type='user',
            target_identifier='user1', can_view=True
        )
        perm2 = RAGDocumentPermission(
            document_id=doc.id, permission_type='user',
            target_identifier='user2', can_view=True
        )
        db.session.add_all([perm1, perm2])
        db.session.commit()

        # Remove user2 by not including in list
        RAGAccessService.set_document_permissions(
            document_id=doc.id,
            usernames=['user1']
        )

        # Verify user2 removed
        perms = RAGDocumentPermission.query.filter_by(document_id=doc.id).all()
        assert len(perms) == 1
        assert perms[0].target_identifier == 'user1'

    def test_ACC_065_get_collection_permissions(self, app, db, app_context):
        """
        [ACC-065] Collection Permissions abrufen

        Collection Permissions sollen korrekt zurückgegeben werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection, RAGCollectionPermission

        collection = RAGCollection(name='coll_perm', display_name='Collection Perm', created_by='test')
        db.session.add(collection)
        db.session.flush()

        perm = RAGCollectionPermission(
            collection_id=collection.id,
            permission_type='user',
            target_identifier='evaluator',
            can_view=True
        )
        db.session.add(perm)
        db.session.commit()

        result = RAGAccessService.get_collection_permissions(collection.id)

        assert len(result['users']) == 1
        assert result['users'][0]['target'] == 'evaluator'

    def test_ACC_066_set_collection_permissions(self, app, db, app_context):
        """
        [ACC-066] Collection Permissions setzen

        Collection Permissions sollen erstellt werden.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection, RAGCollectionPermission

        collection = RAGCollection(name='set_coll_perm', display_name='Set Collection Perm', created_by='test')
        db.session.add(collection)
        db.session.commit()

        result = RAGAccessService.set_collection_permissions(
            collection_id=collection.id,
            usernames=['user1'],
            role_names=['evaluator'],
            granted_by='admin',
            access={'can_view': True, 'can_edit': False}
        )

        assert 'user1' in result['usernames']
        assert 'evaluator' in result['role_names']

        # Verify in database
        perms = RAGCollectionPermission.query.filter_by(collection_id=collection.id).all()
        assert len(perms) == 2


class TestApplyFilters:
    """
    Query Filter Tests

    Tests for applying access filters to queries.
    """

    def test_ACC_070_apply_document_filter_no_username(self, app, db, app_context):
        """
        [ACC-070] Document Filter ohne Username

        Ohne Username soll Query keine Ergebnisse liefern.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument

        query = RAGDocument.query
        filtered = RAGAccessService.apply_document_access_filter(query, None)

        result = filtered.all()
        assert result == []

    def test_ACC_071_apply_document_filter_admin(self, app, db, app_context):
        """
        [ACC-071] Document Filter für Admin

        Admin soll alle Dokumente sehen.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='all.pdf', original_filename='all.pdf',
            file_path='/tmp/all.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_all',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add(doc)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=True):
            query = RAGDocument.query
            filtered = RAGAccessService.apply_document_access_filter(query, 'admin')
            result = filtered.all()

            assert len(result) == 1

    def test_ACC_072_apply_document_filter_owner(self, app, db, app_context):
        """
        [ACC-072] Document Filter für Owner

        Owner soll eigene Dokumente sehen.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        # Owner's document
        doc1 = RAGDocument(
            filename='owned.pdf', original_filename='owned.pdf',
            file_path='/tmp/owned.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_owned1',
            collection_id=collection.id, uploaded_by='owner',
            is_public=False
        )
        # Other's document
        doc2 = RAGDocument(
            filename='other.pdf', original_filename='other.pdf',
            file_path='/tmp/other.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_other1',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add_all([doc1, doc2])
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            query = RAGDocument.query
            filtered = RAGAccessService.apply_document_access_filter(query, 'owner')
            result = filtered.all()

            assert len(result) == 1
            assert result[0].uploaded_by == 'owner'

    def test_ACC_073_apply_document_filter_public(self, app, db, app_context):
        """
        [ACC-073] Document Filter für öffentliche Dokumente

        Öffentliche Dokumente sollen für alle sichtbar sein.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        # Public document
        doc1 = RAGDocument(
            filename='public.pdf', original_filename='public.pdf',
            file_path='/tmp/public.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_pub1',
            collection_id=collection.id, uploaded_by='other',
            is_public=True
        )
        # Private document
        doc2 = RAGDocument(
            filename='private.pdf', original_filename='private.pdf',
            file_path='/tmp/private.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_priv1',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add_all([doc1, doc2])
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            query = RAGDocument.query
            filtered = RAGAccessService.apply_document_access_filter(query, 'any_user', access='view')
            result = filtered.all()

            # Should only see public document
            assert len(result) == 1
            assert result[0].is_public is True

    def test_ACC_074_apply_collection_filter_no_username(self, app, db, app_context):
        """
        [ACC-074] Collection Filter ohne Username

        Ohne Username soll Query keine Ergebnisse liefern.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        query = RAGCollection.query
        filtered = RAGAccessService.apply_collection_view_filter(query, None)

        result = filtered.all()
        assert result == []

    def test_ACC_075_apply_collection_filter_owner(self, app, db, app_context):
        """
        [ACC-075] Collection Filter für Owner

        Owner soll eigene Collections sehen.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection

        # Owner's collection
        coll1 = RAGCollection(
            name='owned_coll', display_name='Owned',
            created_by='owner', is_public=False
        )
        # Other's collection
        coll2 = RAGCollection(
            name='other_coll', display_name='Other',
            created_by='other', is_public=False
        )
        db.session.add_all([coll1, coll2])
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            query = RAGCollection.query
            filtered = RAGAccessService.apply_collection_view_filter(query, 'owner')
            result = filtered.all()

            assert len(result) == 1
            assert result[0].created_by == 'owner'


class TestRoleBasedAccess:
    """
    Role-Based Access Tests

    Tests for role-based permission checks.
    """

    def test_ACC_080_document_access_via_role(self, app, db, app_context):
        """
        [ACC-080] Document-Zugriff via Rolle

        User mit Rolle soll über Rollen-Permission Zugriff haben.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGDocument, RAGCollection, RAGDocumentPermission, Role, UserRole

        # Create role and user assignment (use unique role name to avoid conflicts)
        role = Role(role_name='test_doc_researcher', display_name='Test Researcher', description='Researcher role')
        db.session.add(role)
        db.session.flush()

        user_role = UserRole(username='researcher_user', role_id=role.id)
        db.session.add(user_role)

        # Create document
        collection = RAGCollection(name='test', display_name='Test', created_by='other')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='role.pdf', original_filename='role.pdf',
            file_path='/tmp/role.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_role',
            collection_id=collection.id, uploaded_by='other',
            is_public=False
        )
        db.session.add(doc)
        db.session.flush()

        # Grant role permission
        perm = RAGDocumentPermission(
            document_id=doc.id,
            permission_type='role',
            target_identifier='test_doc_researcher',
            can_view=True
        )
        db.session.add(perm)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_document('researcher_user', doc)
            assert result is True

    def test_ACC_081_collection_access_via_role(self, app, db, app_context):
        """
        [ACC-081] Collection-Zugriff via Rolle

        User mit Rolle soll über Rollen-Permission Zugriff haben.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection, RAGCollectionPermission, Role, UserRole

        # Create role and user assignment (use unique role name to avoid conflicts)
        role = Role(role_name='test_coll_evaluator', display_name='Test Evaluator', description='Evaluator role')
        db.session.add(role)
        db.session.flush()

        user_role = UserRole(username='evaluator_user', role_id=role.id)
        db.session.add(user_role)

        # Create collection
        collection = RAGCollection(
            name='role_coll', display_name='Role Collection',
            created_by='other', is_public=False
        )
        db.session.add(collection)
        db.session.flush()

        # Grant role permission
        perm = RAGCollectionPermission(
            collection_id=collection.id,
            permission_type='role',
            target_identifier='test_coll_evaluator',
            can_view=True
        )
        db.session.add(perm)
        db.session.commit()

        with patch.object(RAGAccessService, 'is_admin_user', return_value=False):
            result = RAGAccessService.can_view_collection('evaluator_user', collection)
            assert result is True
