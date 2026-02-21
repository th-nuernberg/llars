# chatbot_service.py
"""
Service for managing chatbot CRUD operations and collection assignments.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from db.database import db
from db.tables import (
    Chatbot, ChatbotCollection, ChatbotConversation, ChatbotMessage,
    RAGCollection, ChatbotPromptSettings
)
from db.models.llm_model import LLMModel
from services.llm.llm_access_service import LLMAccessService

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for chatbot management operations"""

    USER_PROVIDER_PREFIX = "user-provider:"

    @staticmethod
    def _resolve_llm_model_id(model_name: Optional[str]) -> Optional[str]:
        if not model_name:
            return None
        if isinstance(model_name, str) and model_name.startswith(ChatbotService.USER_PROVIDER_PREFIX):
            rest = model_name[len(ChatbotService.USER_PROVIDER_PREFIX):]
            parts = rest.split(':', 2)
            if len(parts) < 2:
                raise ValueError("Invalid user-provider model id")
            try:
                int(parts[0])
            except (TypeError, ValueError):
                raise ValueError("Invalid user-provider model id")
            # New format: provider_id:username:model (3 parts)
            # Old format: provider_id:model (2 parts)
            actual_model = parts[2] if len(parts) == 3 else parts[1]
            if not actual_model.strip():
                raise ValueError("Invalid user-provider model id")
            return model_name
        model = LLMModel.get_by_model_id(model_name)
        if not model or not model.is_active or model.model_type != LLMModel.MODEL_TYPE_LLM:
            raise ValueError(f"Model '{model_name}' is not an active LLM model")
        return model.model_id

    @staticmethod
    def _serialize_prompt_settings(bot: Chatbot) -> Dict[str, Any]:
        settings = getattr(bot, 'prompt_settings', None)
        return settings.to_dict() if settings else None

    @staticmethod
    def _upsert_prompt_settings(bot: Chatbot, data: Dict[str, Any]) -> None:
        payload = data.get('prompt_settings') or {}
        # Backwards compatible: accept flat keys too
        flat_keys = [
            'rag_require_citations',
            'rag_unknown_answer',
            'rag_citation_instructions',
            'rag_context_prefix',
            'rag_context_item_template',
        ]
        for key in flat_keys:
            if key in data and key not in payload:
                payload[key] = data[key]

        if not payload:
            return

        # Query DB directly to avoid lazy-loading issues with duplicate inserts
        settings = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
        if not settings:
            settings = ChatbotPromptSettings(chatbot_id=bot.id)
            db.session.add(settings)
            db.session.flush()  # Ensure it's in the session before setting attributes

        for key, value in payload.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        # Citations need sources for clickable [n] references.
        if getattr(settings, 'rag_require_citations', False):
            bot.rag_include_sources = True

    @staticmethod
    def get_all_chatbots(include_inactive: bool = False, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all chatbots with their collection counts and conversation stats.
        """
        if username:
            from services.chatbot.chatbot_access_service import ChatbotAccessService
            chatbots = ChatbotAccessService.get_accessible_chatbots(username, include_inactive=include_inactive)
        else:
            query = Chatbot.query
            if not include_inactive:
                query = query.filter(Chatbot.is_active == True)

            chatbots = query.order_by(Chatbot.created_at.desc()).all()

        result = []
        for bot in chatbots:
            # Get collection count
            collection_count = ChatbotCollection.query.filter_by(chatbot_id=bot.id).count()

            # Get conversation count
            conversation_count = ChatbotConversation.query.filter_by(chatbot_id=bot.id).count()

            # Get collections info
            collections = []
            for cc in bot.collections:
                collections.append({
                    'id': cc.collection.id,
                    'name': cc.collection.name,
                    'display_name': cc.collection.display_name,
                    'document_count': cc.collection.document_count,
                    'priority': cc.priority,
                    'is_primary': cc.is_primary
                })

            result.append({
                'id': bot.id,
                'name': bot.name,
                'display_name': bot.display_name,
                'description': bot.description,
                'icon': bot.icon,
                'color': bot.color,
                'system_prompt': bot.system_prompt,
                'model_name': bot.model_name,
                'temperature': bot.temperature,
                'max_tokens': bot.max_tokens,
                'top_p': bot.top_p,
                'rag_enabled': bot.rag_enabled,
                'rag_retrieval_k': bot.rag_retrieval_k,
                'rag_min_relevance': bot.rag_min_relevance,
                'rag_include_sources': bot.rag_include_sources,
                'rag_reranker_model': bot.rag_reranker_model,
                'rag_use_cross_encoder': bot.rag_use_cross_encoder,
                'welcome_message': bot.welcome_message,
                'fallback_message': bot.fallback_message,
                'max_context_messages': bot.max_context_messages,
                'is_active': bot.is_active,
                'is_public': bot.is_public,
                'allowed_roles': bot.allowed_roles,
                'created_by': bot.created_by,
                'created_at': bot.created_at.isoformat() if bot.created_at else None,
                'updated_at': bot.updated_at.isoformat() if bot.updated_at else None,
                'collection_count': collection_count,
                'conversation_count': conversation_count,
                'collections': collections,
                # Build status fields (for Chatbot Builder)
                'build_status': bot.build_status,
                'build_error': bot.build_error,
                'source_url': bot.source_url,
                'primary_collection_id': bot.primary_collection_id,
                'prompt_settings': ChatbotService._serialize_prompt_settings(bot)
            })

        return result

    @staticmethod
    def get_chatbot(chatbot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single chatbot by ID with full details.
        """
        bot = Chatbot.query.get(chatbot_id)
        if not bot:
            return None

        # Get collections info
        collections = []
        for cc in bot.collections:
            collections.append({
                'id': cc.collection.id,
                'name': cc.collection.name,
                'display_name': cc.collection.display_name,
                'document_count': cc.collection.document_count,
                'priority': cc.priority,
                'weight': cc.weight,
                'is_primary': cc.is_primary
            })

        # Get conversation count
        conversation_count = ChatbotConversation.query.filter_by(chatbot_id=bot.id).count()

        return {
            'id': bot.id,
            'name': bot.name,
            'display_name': bot.display_name,
            'description': bot.description,
            'icon': bot.icon,
            'avatar_url': bot.avatar_url,
            'color': bot.color,
            'system_prompt': bot.system_prompt,
            'model_name': bot.model_name,
            'temperature': bot.temperature,
            'max_tokens': bot.max_tokens,
            'top_p': bot.top_p,
            'rag_enabled': bot.rag_enabled,
            'rag_retrieval_k': bot.rag_retrieval_k,
            'rag_min_relevance': bot.rag_min_relevance,
            'rag_include_sources': bot.rag_include_sources,
            'rag_reranker_model': bot.rag_reranker_model,
            'rag_use_cross_encoder': bot.rag_use_cross_encoder,
            'welcome_message': bot.welcome_message,
            'fallback_message': bot.fallback_message,
            'max_context_messages': bot.max_context_messages,
            'is_active': bot.is_active,
            'is_public': bot.is_public,
            'allowed_roles': bot.allowed_roles,
            'created_by': bot.created_by,
            'created_at': bot.created_at.isoformat() if bot.created_at else None,
            'updated_at': bot.updated_at.isoformat() if bot.updated_at else None,
            'collections': collections,
            'conversation_count': conversation_count,
            # Build status fields (for Chatbot Builder)
            'build_status': bot.build_status,
            'build_error': bot.build_error,
            'source_url': bot.source_url,
            'primary_collection_id': bot.primary_collection_id,
            'prompt_settings': ChatbotService._serialize_prompt_settings(bot)
        }

    @staticmethod
    def _coerce_model_name(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, dict):
            for key in ("value", "model_id", "id", "name"):
                raw = value.get(key)
                if isinstance(raw, str) and raw.strip():
                    return raw.strip()
            return None
        try:
            text = str(value)
        except Exception:
            return None
        return text.strip() or None

    @staticmethod
    def create_chatbot(data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """
        Create a new chatbot.
        """
        # Validate required fields
        required_fields = ['name', 'display_name', 'system_prompt']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Check if name already exists
        existing = Chatbot.query.filter_by(name=data['name']).first()
        if existing:
            raise ValueError(f"Chatbot with name '{data['name']}' already exists")

        model_name = ChatbotService._coerce_model_name(data.get('model_name'))
        if model_name:
            model_name = ChatbotService._resolve_llm_model_id(model_name)
            if not LLMAccessService.user_can_access_model(username, model_name):
                raise ValueError(f"Model '{model_name}' is not available for this user")
        else:
            accessible = LLMAccessService.get_accessible_models(
                username,
                active_only=True,
                model_type=LLMModel.MODEL_TYPE_LLM,
            )
            if not accessible:
                raise ValueError("No accessible LLM model configured for this user")
            default_model = next((m for m in accessible if m.is_default), accessible[0])
            model_name = default_model.model_id

        # Create chatbot
        chatbot = Chatbot(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description'),
            icon=data.get('icon', 'mdi-robot'),
            avatar_url=data.get('avatar_url'),
            color=data.get('color', '#5d7a4a'),
            system_prompt=data['system_prompt'],
            model_name=model_name,
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 2048),
            top_p=data.get('top_p', 0.9),
            rag_enabled=data.get('rag_enabled', True),
            rag_retrieval_k=data.get('rag_retrieval_k', 8),
            rag_min_relevance=data.get('rag_min_relevance', 0.3),
            rag_include_sources=data.get('rag_include_sources', True),
            rag_reranker_model=data.get('rag_reranker_model'),  # None = use system default
            rag_use_cross_encoder=data.get('rag_use_cross_encoder', False),  # Default: off
            welcome_message=data.get('welcome_message'),
            fallback_message=data.get('fallback_message', 'Ich konnte leider keine passende Antwort finden.'),
            max_context_messages=data.get('max_context_messages', 10),
            is_active=data.get('is_active', True),
            is_public=data.get('is_public', False),
            allowed_roles=data.get('allowed_roles'),
            created_by=username
        )

        db.session.add(chatbot)
        db.session.flush()

        # _upsert_prompt_settings handles creating settings if needed
        ChatbotService._upsert_prompt_settings(chatbot, data)

        # Assign collections if provided
        collection_ids = data.get('collection_ids', [])
        for i, coll_id in enumerate(collection_ids):
            collection = RAGCollection.query.get(coll_id)
            if collection:
                cc = ChatbotCollection(
                    chatbot_id=chatbot.id,
                    collection_id=coll_id,
                    priority=i,
                    is_primary=(i == 0),
                    assigned_by=username
                )
                db.session.add(cc)

        db.session.commit()
        logger.info(f"Created chatbot '{chatbot.name}' with {len(collection_ids)} collections")

        return ChatbotService.get_chatbot(chatbot.id)

    @staticmethod
    def update_chatbot(chatbot_id: int, data: Dict[str, Any], username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing chatbot.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return None
        if 'model_name' in data:
            model_name = ChatbotService._coerce_model_name(data.get('model_name'))
            if model_name:
                data['model_name'] = ChatbotService._resolve_llm_model_id(model_name)
                if username and not LLMAccessService.user_can_access_model(username, data['model_name']):
                    raise ValueError(f"Model '{data['model_name']}' is not available for this user")
            else:
                data.pop('model_name', None)

        # Update fields
        updatable_fields = [
            'display_name', 'description', 'icon', 'avatar_url', 'color',
            'system_prompt', 'model_name', 'temperature', 'max_tokens', 'top_p',
            'rag_enabled', 'rag_retrieval_k', 'rag_min_relevance', 'rag_include_sources',
            'rag_reranker_model', 'rag_use_cross_encoder',
            'welcome_message', 'fallback_message', 'max_context_messages',
            'is_active', 'is_public', 'allowed_roles'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(chatbot, field, data[field])

        # Update name only if it doesn't conflict
        if 'name' in data and data['name'] != chatbot.name:
            existing = Chatbot.query.filter_by(name=data['name']).first()
            if existing:
                raise ValueError(f"Chatbot with name '{data['name']}' already exists")
            chatbot.name = data['name']

        ChatbotService._upsert_prompt_settings(chatbot, data)

        db.session.commit()
        logger.info(f"Updated chatbot '{chatbot.name}'")

        return ChatbotService.get_chatbot(chatbot_id)

    @staticmethod
    def delete_chatbot(chatbot_id: int, delete_collections: bool = False) -> bool:
        """
        Delete a chatbot and all related data.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return False

        name = chatbot.name

        try:
            # Optionally delete associated collections (primary + linked)
            if delete_collections:
                ChatbotService._delete_associated_collections(chatbot)

            # Delete chatbot (ChatbotCollection relations cascade via FK/ondelete)
            db.session.delete(chatbot)
            db.session.commit()
            logger.info(f"Deleted chatbot '{name}' (delete_collections={delete_collections})")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting chatbot '{name}': {e}")
            return False

    @staticmethod
    def _delete_associated_collections(chatbot: Chatbot):
        """
        Cascade delete collections associated to the chatbot (primary + linked).
        Deletes documents/chunks as well.
        """
        from db.tables import (
            RAGCollection,
            RAGDocument,
            RAGDocumentChunk,
            CollectionDocumentLink,
            ChatbotCollection
        )

        # Collect collection IDs (primary + any linked)
        collection_ids = set()
        if chatbot.primary_collection_id:
            collection_ids.add(chatbot.primary_collection_id)

        linked = ChatbotCollection.query.filter_by(chatbot_id=chatbot.id).all()
        for link in linked:
            if link.collection_id:
                collection_ids.add(link.collection_id)

        for cid in collection_ids:
            collection = RAGCollection.query.get(cid)
            if not collection:
                continue

            # Delete chunks -> documents -> links -> collection
            documents = RAGDocument.query.filter_by(collection_id=cid).all()
            for doc in documents:
                RAGDocumentChunk.query.filter_by(document_id=doc.id).delete()
            RAGDocument.query.filter_by(collection_id=cid).delete()
            CollectionDocumentLink.query.filter_by(collection_id=cid).delete()
            ChatbotCollection.query.filter_by(collection_id=cid).delete()
            db.session.delete(collection)

        db.session.commit()

    @staticmethod
    def duplicate_chatbot(chatbot_id: int, username: str) -> Optional[Dict[str, Any]]:
        """
        Create a copy of an existing chatbot.
        """
        original = Chatbot.query.get(chatbot_id)
        if not original:
            return None

        # Generate unique name
        base_name = f"{original.name}-copy"
        counter = 1
        new_name = base_name
        while Chatbot.query.filter_by(name=new_name).first():
            new_name = f"{base_name}-{counter}"
            counter += 1

        # Create copy
        copy_data = {
            'name': new_name,
            'display_name': f"{original.display_name} (Kopie)",
            'description': original.description,
            'icon': original.icon,
            'avatar_url': original.avatar_url,
            'color': original.color,
            'system_prompt': original.system_prompt,
            'model_name': original.model_name,
            'temperature': original.temperature,
            'max_tokens': original.max_tokens,
            'top_p': original.top_p,
            'rag_enabled': original.rag_enabled,
            'rag_retrieval_k': original.rag_retrieval_k,
            'rag_min_relevance': original.rag_min_relevance,
            'rag_include_sources': original.rag_include_sources,
            'rag_reranker_model': original.rag_reranker_model,
            'rag_use_cross_encoder': original.rag_use_cross_encoder,
            'welcome_message': original.welcome_message,
            'fallback_message': original.fallback_message,
            'max_context_messages': original.max_context_messages,
            'is_active': False,  # Start inactive
            'is_public': original.is_public,
            'allowed_roles': original.allowed_roles,
            'collection_ids': [cc.collection_id for cc in original.collections],
            'prompt_settings': ChatbotService._serialize_prompt_settings(original),
        }

        return ChatbotService.create_chatbot(copy_data, username)

    # ========== Collection Assignment Methods ==========

    @staticmethod
    def get_collections(chatbot_id: int) -> List[Dict[str, Any]]:
        """
        Get all collections assigned to a chatbot.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return []

        collections = []
        for cc in sorted(chatbot.collections, key=lambda x: x.priority):
            collections.append({
                'id': cc.id,
                'collection_id': cc.collection.id,
                'name': cc.collection.name,
                'display_name': cc.collection.display_name,
                'description': cc.collection.description,
                'document_count': cc.collection.document_count,
                'total_chunks': cc.collection.total_chunks,
                'priority': cc.priority,
                'weight': cc.weight,
                'is_primary': cc.is_primary,
                'assigned_at': cc.assigned_at.isoformat() if cc.assigned_at else None
            })

        return collections

    @staticmethod
    def assign_collection(
        chatbot_id: int,
        collection_id: int,
        username: str,
        priority: int = 0,
        weight: float = 1.0,
        is_primary: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Assign a collection to a chatbot.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        collection = RAGCollection.query.get(collection_id)

        if not chatbot or not collection:
            return None

        # Check if already assigned
        existing = ChatbotCollection.query.filter_by(
            chatbot_id=chatbot_id,
            collection_id=collection_id
        ).first()

        if existing:
            raise ValueError("Collection is already assigned to this chatbot")

        # If setting as primary, unset other primaries
        if is_primary:
            ChatbotCollection.query.filter_by(
                chatbot_id=chatbot_id,
                is_primary=True
            ).update({'is_primary': False})

        cc = ChatbotCollection(
            chatbot_id=chatbot_id,
            collection_id=collection_id,
            priority=priority,
            weight=weight,
            is_primary=is_primary,
            assigned_by=username
        )

        db.session.add(cc)
        db.session.commit()

        logger.info(f"Assigned collection '{collection.name}' to chatbot '{chatbot.name}'")

        return {
            'id': cc.id,
            'collection_id': collection.id,
            'name': collection.name,
            'display_name': collection.display_name,
            'priority': cc.priority,
            'weight': cc.weight,
            'is_primary': cc.is_primary
        }

    @staticmethod
    def update_collection_assignment(
        chatbot_id: int,
        collection_id: int,
        priority: int = None,
        weight: float = None,
        is_primary: bool = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a collection assignment's priority or weight.
        """
        cc = ChatbotCollection.query.filter_by(
            chatbot_id=chatbot_id,
            collection_id=collection_id
        ).first()

        if not cc:
            return None

        if priority is not None:
            cc.priority = priority
        if weight is not None:
            cc.weight = weight
        if is_primary is not None:
            if is_primary:
                # Unset other primaries
                ChatbotCollection.query.filter_by(
                    chatbot_id=chatbot_id,
                    is_primary=True
                ).update({'is_primary': False})
            cc.is_primary = is_primary

        db.session.commit()

        return {
            'id': cc.id,
            'collection_id': cc.collection_id,
            'priority': cc.priority,
            'weight': cc.weight,
            'is_primary': cc.is_primary
        }

    @staticmethod
    def remove_collection(chatbot_id: int, collection_id: int) -> bool:
        """
        Remove a collection from a chatbot.
        """
        cc = ChatbotCollection.query.filter_by(
            chatbot_id=chatbot_id,
            collection_id=collection_id
        ).first()

        if not cc:
            return False

        db.session.delete(cc)
        db.session.commit()

        logger.info(f"Removed collection {collection_id} from chatbot {chatbot_id}")

        return True

    # ========== Statistics Methods ==========

    @staticmethod
    def get_stats(chatbot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific chatbot.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return None

        # Conversation stats
        total_conversations = ChatbotConversation.query.filter_by(chatbot_id=chatbot_id).count()
        active_conversations = ChatbotConversation.query.filter_by(
            chatbot_id=chatbot_id,
            is_active=True
        ).count()

        # Message stats
        total_messages = db.session.query(func.count(ChatbotMessage.id)).join(
            ChatbotConversation
        ).filter(ChatbotConversation.chatbot_id == chatbot_id).scalar() or 0

        # Average response time
        avg_response_time = db.session.query(func.avg(ChatbotMessage.response_time_ms)).join(
            ChatbotConversation
        ).filter(
            ChatbotConversation.chatbot_id == chatbot_id,
            ChatbotMessage.response_time_ms.isnot(None)
        ).scalar() or 0

        # Collection stats
        collection_count = ChatbotCollection.query.filter_by(chatbot_id=chatbot_id).count()
        total_documents = sum(cc.collection.document_count for cc in chatbot.collections)

        return {
            'chatbot_id': chatbot_id,
            'chatbot_name': chatbot.display_name,
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'total_messages': total_messages,
            'avg_response_time_ms': round(avg_response_time, 2),
            'collection_count': collection_count,
            'total_documents': total_documents
        }

    @staticmethod
    def get_overview_stats() -> Dict[str, Any]:
        """
        Get global chatbot statistics.
        """
        total_chatbots = Chatbot.query.count()
        active_chatbots = Chatbot.query.filter_by(is_active=True).count()
        total_conversations = ChatbotConversation.query.count()
        total_messages = ChatbotMessage.query.count()

        # Get top chatbots by usage
        top_chatbots = db.session.query(
            Chatbot.id,
            Chatbot.display_name,
            func.count(ChatbotConversation.id).label('conv_count')
        ).outerjoin(ChatbotConversation).group_by(Chatbot.id).order_by(
            func.count(ChatbotConversation.id).desc()
        ).limit(5).all()

        return {
            'total_chatbots': total_chatbots,
            'active_chatbots': active_chatbots,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'top_chatbots': [
                {'id': t[0], 'name': t[1], 'conversations': t[2]}
                for t in top_chatbots
            ]
        }
