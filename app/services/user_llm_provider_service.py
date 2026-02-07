"""
User LLM Provider Service.

Manages user-owned LLM API keys and their sharing.
Enables users to connect their own API keys (OpenAI, Anthropic, etc.)
and optionally share them with other users.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from db.database import db
from db.models.user_llm_provider import UserLLMProvider, UserLLMProviderShare
from services.llm.secret_encryption import encrypt_api_key, decrypt_api_key

logger = logging.getLogger(__name__)


class UserLLMProviderService:
    """Service for managing user-owned LLM providers."""

    @staticmethod
    def _encrypt_api_key(api_key: str) -> str:
        """Encrypt an API key for storage."""
        if not api_key:
            return None
        return encrypt_api_key(api_key)

    @staticmethod
    def _decrypt_api_key(encrypted_key: str) -> str:
        """Decrypt an API key for use."""
        if not encrypted_key:
            return None
        try:
            return decrypt_api_key(encrypted_key)
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return None

    # ==================== Provider CRUD ====================

    @staticmethod
    def create_provider(
        user_id: int,
        provider_type: str,
        name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Dict] = None,
        is_default: bool = False,
        priority: int = 0
    ) -> UserLLMProvider:
        """
        Create a new user LLM provider.

        Args:
            user_id: Owner user ID
            provider_type: Provider type (openai, anthropic, etc.)
            name: User-friendly name
            api_key: Plain text API key (will be encrypted)
            base_url: Optional base URL for custom endpoints
            config: Optional configuration dict
            is_default: Set as user's default provider
            priority: Priority for fallback ordering

        Returns:
            Created UserLLMProvider instance
        """
        from decorators.error_handler import ConflictError

        # Check for duplicate name
        existing = UserLLMProvider.query.filter_by(
            user_id=user_id, name=name
        ).first()
        if existing:
            raise ConflictError(f"Provider with name '{name}' already exists")

        # If setting as default, unset other defaults
        if is_default:
            UserLLMProvider.query.filter_by(
                user_id=user_id, is_default=True
            ).update({'is_default': False})

        provider = UserLLMProvider(
            user_id=user_id,
            provider_type=provider_type,
            name=name,
            api_key_encrypted=UserLLMProviderService._encrypt_api_key(api_key) if api_key else None,
            base_url=base_url,
            config_json=config or {},
            is_default=is_default,
            priority=priority
        )
        db.session.add(provider)
        db.session.commit()

        logger.info(f"Created user LLM provider '{name}' (id={provider.id}) for user {user_id}")
        return provider

    @staticmethod
    def get_provider(provider_id: int) -> Optional[UserLLMProvider]:
        """Get a provider by ID."""
        return UserLLMProvider.query.get(provider_id)

    @staticmethod
    def get_provider_with_key(provider_id: int) -> Tuple[Optional[UserLLMProvider], Optional[str]]:
        """Get a provider and decrypted API key (if any)."""
        provider = UserLLMProvider.query.get(provider_id)
        if not provider or not provider.is_active:
            return None, None
        api_key = UserLLMProviderService._decrypt_api_key(provider.api_key_encrypted)
        return provider, api_key

    @staticmethod
    def get_user_providers(
        user_id: int,
        provider_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[UserLLMProvider]:
        """
        Get all providers for a user.

        Args:
            user_id: User ID
            provider_type: Optional filter by type
            include_inactive: Include inactive providers

        Returns:
            List of UserLLMProvider instances
        """
        query = UserLLMProvider.query.filter_by(user_id=user_id)

        if not include_inactive:
            query = query.filter_by(is_active=True)

        if provider_type:
            query = query.filter_by(provider_type=provider_type)

        return query.order_by(
            UserLLMProvider.is_default.desc(),
            UserLLMProvider.priority,
            UserLLMProvider.created_at
        ).all()

    @staticmethod
    def update_provider(
        provider_id: int,
        user_id: int,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Dict] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Optional[UserLLMProvider]:
        """
        Update a user LLM provider.

        Args:
            provider_id: Provider ID
            user_id: User ID (for ownership verification)
            name: New name (optional)
            api_key: New API key (optional, pass empty string to clear)
            base_url: New base URL (optional)
            config: New config (optional)
            is_active: New active status (optional)
            is_default: New default status (optional)
            priority: New priority (optional)

        Returns:
            Updated provider or None if not found/unauthorized
        """
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            return None

        if name is not None:
            provider.name = name

        if api_key is not None:
            if api_key == '':
                provider.api_key_encrypted = None
            else:
                provider.api_key_encrypted = UserLLMProviderService._encrypt_api_key(api_key)

        if base_url is not None:
            provider.base_url = base_url if base_url else None

        if config is not None:
            provider.config_json = config

        if is_active is not None:
            provider.is_active = is_active

        if is_default is not None:
            if is_default:
                # Unset other defaults first
                UserLLMProvider.query.filter(
                    UserLLMProvider.user_id == user_id,
                    UserLLMProvider.id != provider_id
                ).update({'is_default': False})
            provider.is_default = is_default

        if priority is not None:
            provider.priority = priority

        db.session.commit()
        logger.info(f"Updated user LLM provider {provider_id}")
        return provider

    @staticmethod
    def delete_provider(provider_id: int, user_id: int) -> bool:
        """
        Delete a user LLM provider.

        Args:
            provider_id: Provider ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found/unauthorized
        """
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            return False

        db.session.delete(provider)
        db.session.commit()
        logger.info(f"Deleted user LLM provider {provider_id}")
        return True

    @staticmethod
    def test_provider(provider_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Test a provider's API connection.

        Args:
            provider_id: Provider ID
            user_id: User ID (for ownership verification)

        Returns:
            Tuple of (success, message)
        """
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            return False, "Provider nicht gefunden"

        api_key = UserLLMProviderService._decrypt_api_key(provider.api_key_encrypted)
        if not api_key:
            return False, "Kein API-Key konfiguriert"

        try:
            from services.llm.llm_service import LLMService

            # Test with a simple request
            test_result = LLMService.test_provider_connection(
                provider_type=provider.provider_type,
                api_key=api_key,
                base_url=provider.base_url,
                config=provider.config_json
            )

            if test_result.get('success'):
                provider.last_error = None
                db.session.commit()
                return True, "Verbindung erfolgreich"
            else:
                error = test_result.get('error', 'Unbekannter Fehler')
                provider.last_error = error
                db.session.commit()
                return False, error

        except Exception as e:
            error = str(e)
            provider.last_error = error
            db.session.commit()
            logger.error(f"Provider test failed for {provider_id}: {e}")
            return False, error

    # ==================== Provider Sharing ====================

    @staticmethod
    def share_provider(
        provider_id: int,
        user_id: int,
        share_type: str,
        target_identifier: str,
        usage_limit_tokens: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> UserLLMProviderShare:
        """
        Share a provider with another user or role.

        Args:
            provider_id: Provider ID
            user_id: Owner user ID (for verification)
            share_type: 'user' or 'role'
            target_identifier: Username or role name
            usage_limit_tokens: Optional monthly token limit
            expires_at: Optional expiration date

        Returns:
            Created share instance
        """
        from decorators.error_handler import ValidationError, ConflictError, NotFoundError

        # Verify ownership
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            raise NotFoundError("Provider nicht gefunden")

        if share_type not in ('user', 'role'):
            raise ValidationError("share_type muss 'user' oder 'role' sein")

        # Check for existing share
        existing = UserLLMProviderShare.query.filter_by(
            provider_id=provider_id,
            share_type=share_type,
            target_identifier=target_identifier
        ).first()

        if existing:
            raise ConflictError(f"Provider ist bereits mit {target_identifier} geteilt")

        # Validate target exists
        if share_type == 'user':
            from db.models.user import User
            target_user = User.query.filter_by(username=target_identifier).first()
            if not target_user:
                raise ValidationError(f"Benutzer '{target_identifier}' nicht gefunden")

        share = UserLLMProviderShare(
            provider_id=provider_id,
            share_type=share_type,
            target_identifier=target_identifier,
            usage_limit_tokens=usage_limit_tokens,
            shared_by=user_id,
            expires_at=expires_at
        )

        # Mark provider as shared
        provider.is_shared = True

        db.session.add(share)
        db.session.commit()

        logger.info(f"Shared provider {provider_id} with {share_type}:{target_identifier}")
        return share

    @staticmethod
    def unshare_provider(
        share_id: int,
        user_id: int
    ) -> bool:
        """
        Remove a provider share.

        Args:
            share_id: Share ID
            user_id: Owner user ID (for verification)

        Returns:
            True if removed, False if not found/unauthorized
        """
        share = UserLLMProviderShare.query.get(share_id)
        if not share:
            return False

        # Verify ownership
        if share.provider.user_id != user_id:
            return False

        provider = share.provider
        db.session.delete(share)

        # Check if provider still has shares
        remaining = UserLLMProviderShare.query.filter_by(
            provider_id=provider.id
        ).count()

        if remaining == 0:
            provider.is_shared = False
            provider.share_with_all = False

        db.session.commit()
        logger.info(f"Removed share {share_id}")
        return True

    @staticmethod
    def get_provider_shares(
        provider_id: int,
        user_id: int
    ) -> List[UserLLMProviderShare]:
        """
        Get all shares for a provider.

        Args:
            provider_id: Provider ID
            user_id: Owner user ID (for verification)

        Returns:
            List of shares
        """
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            return []

        return provider.shares

    @staticmethod
    def toggle_share_with_all(
        provider_id: int,
        user_id: int,
        share_with_all: bool
    ) -> bool:
        """
        Toggle sharing with all users.

        Args:
            provider_id: Provider ID
            user_id: Owner user ID
            share_with_all: New value

        Returns:
            True if updated, False if not found/unauthorized
        """
        provider = UserLLMProvider.query.filter_by(
            id=provider_id, user_id=user_id
        ).first()

        if not provider:
            return False

        provider.share_with_all = share_with_all
        provider.is_shared = share_with_all or bool(provider.shares)
        db.session.commit()

        logger.info(f"Set share_with_all={share_with_all} for provider {provider_id}")
        return True

    # ==================== Provider Resolution ====================

    @staticmethod
    def get_available_providers_for_user(
        user_id: int,
        username: str,
        user_roles: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get all providers available to a user (own + shared).

        Args:
            user_id: User ID
            username: Username
            user_roles: User's role names

        Returns:
            List of provider dicts with source info
        """
        result = []

        # User's own providers
        own_providers = UserLLMProvider.query.filter_by(
            user_id=user_id, is_active=True
        ).all()

        for p in own_providers:
            result.append({
                **p.to_dict(),
                'source': 'own',
                'can_modify': True
            })

        # Providers shared with this specific user
        shared_with_user = db.session.query(UserLLMProvider).join(
            UserLLMProviderShare
        ).filter(
            UserLLMProviderShare.share_type == 'user',
            UserLLMProviderShare.target_identifier == username,
            UserLLMProviderShare.can_use == True,
            UserLLMProvider.is_active == True
        ).all()

        for p in shared_with_user:
            if p.user_id != user_id:  # Not own provider
                result.append({
                    **p.to_dict(),
                    'source': 'shared_user',
                    'can_modify': False,
                    'shared_by': p.user.username if p.user else None
                })

        # Providers shared with user's roles
        if user_roles:
            shared_with_roles = db.session.query(UserLLMProvider).join(
                UserLLMProviderShare
            ).filter(
                UserLLMProviderShare.share_type == 'role',
                UserLLMProviderShare.target_identifier.in_(user_roles),
                UserLLMProviderShare.can_use == True,
                UserLLMProvider.is_active == True
            ).all()

            seen_ids = {p['id'] for p in result}
            for p in shared_with_roles:
                if p.id not in seen_ids:
                    result.append({
                        **p.to_dict(),
                        'source': 'shared_role',
                        'can_modify': False,
                        'shared_by': p.user.username if p.user else None
                    })
                    seen_ids.add(p.id)

        # Providers shared with all
        shared_with_all = UserLLMProvider.query.filter_by(
            share_with_all=True, is_active=True
        ).all()

        seen_ids = {p['id'] for p in result}
        for p in shared_with_all:
            if p.id not in seen_ids:
                result.append({
                    **p.to_dict(),
                    'source': 'shared_all',
                    'can_modify': False,
                    'shared_by': p.user.username if p.user else None
                })

        return result

    @staticmethod
    def get_provider_for_use(
        provider_id: int,
        user_id: int,
        username: str,
        user_roles: List[str]
    ) -> Tuple[Optional[UserLLMProvider], Optional[str]]:
        """
        Get a provider ready for use (with decrypted API key).

        Verifies the user has access to the provider.

        Args:
            provider_id: Provider ID
            user_id: User ID
            username: Username
            user_roles: User's role names

        Returns:
            Tuple of (provider, decrypted_api_key) or (None, None) if not accessible
        """
        provider = UserLLMProvider.query.get(provider_id)
        if not provider or not provider.is_active:
            return None, None

        # Check access
        has_access = False

        # Own provider
        if provider.user_id == user_id:
            has_access = True

        # Shared with all
        elif provider.share_with_all:
            has_access = True

        # Shared with user
        elif UserLLMProviderShare.query.filter_by(
            provider_id=provider_id,
            share_type='user',
            target_identifier=username,
            can_use=True
        ).first():
            has_access = True

        # Shared with role
        elif user_roles and UserLLMProviderShare.query.filter(
            UserLLMProviderShare.provider_id == provider_id,
            UserLLMProviderShare.share_type == 'role',
            UserLLMProviderShare.target_identifier.in_(user_roles),
            UserLLMProviderShare.can_use == True
        ).first():
            has_access = True

        if not has_access:
            return None, None

        api_key = UserLLMProviderService._decrypt_api_key(provider.api_key_encrypted)
        return provider, api_key

    @staticmethod
    def record_usage(
        provider_id: int,
        tokens: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        Record usage statistics for a provider.

        Args:
            provider_id: Provider ID
            tokens: Number of tokens used
            error: Error message if any
        """
        provider = UserLLMProvider.query.get(provider_id)
        if provider:
            provider.record_usage(tokens=tokens, error=error)
            db.session.commit()
