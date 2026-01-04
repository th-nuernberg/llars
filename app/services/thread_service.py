"""
Thread Service

Handles all email thread-related business logic including:
- Thread creation and management
- Message management
- Feature management
- Thread access control
- Thread filtering by scenarios
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dateutil import parser as date_parser

from db.database import db


class ThreadService:
    """
    Core service for email thread management.

    Provides methods for thread CRUD operations, message handling,
    feature management, and access control.
    """

    @staticmethod
    def get_thread_by_id(thread_id: int, function_type_id: Optional[int] = None) -> Optional['EmailThread']:
        """
        Get thread by ID.

        Args:
            thread_id: The thread ID to look up
            function_type_id: Optional function type ID to filter by

        Returns:
            EmailThread object if found, None otherwise
        """
        if not thread_id:
            return None

        from db.models import EmailThread

        query = EmailThread.query.filter_by(thread_id=thread_id)

        if function_type_id is not None:
            query = query.filter_by(function_type_id=function_type_id)

        return query.first()

    @staticmethod
    def get_threads_by_function_type(function_type_id: int) -> List['EmailThread']:
        """
        Get all threads for a specific function type.

        Args:
            function_type_id: The function type ID (1=ranking, 2=rating, 3=mail_rating)

        Returns:
            List of EmailThread objects
        """
        from db.models import EmailThread

        return EmailThread.query.filter_by(function_type_id=function_type_id).all()

    @staticmethod
    def get_threads_for_user(user_id: int, function_type_id: int) -> List['EmailThread']:
        """
        Get all threads accessible by a user for a specific function type.

        Uses scenario-based access control to determine which threads
        the user can access.

        Args:
            user_id: The user ID
            function_type_id: The function type ID

        Returns:
            List of EmailThread objects the user can access
        """
        from routes.HelperFunctions import get_user_threads

        return get_user_threads(user_id, function_type_id)

    @staticmethod
    def can_user_access_thread(user_id: int, thread_id: int, function_type_id: int) -> bool:
        """
        Check if a user can access a specific thread.

        Uses scenario-based access control.

        Args:
            user_id: The user ID
            thread_id: The thread ID
            function_type_id: The function type ID

        Returns:
            True if user can access thread, False otherwise
        """
        from routes.HelperFunctions import can_access_thread

        return can_access_thread(user_id, thread_id, function_type_id)

    @staticmethod
    def create_or_update_thread(
        chat_id: str,
        institut_id: str,
        function_type_id: int,
        subject: str,
        sender: str = "Alias"
    ) -> Tuple[bool, Optional['EmailThread'], Optional[str]]:
        """
        Create a new email thread or update existing one.

        Args:
            chat_id: Chat ID from external system
            institut_id: Institution ID
            function_type_id: Function type (1=ranking, 2=rating, 3=mail_rating)
            subject: Email subject
            sender: Email sender (default: "Alias")

        Returns:
            Tuple of (success, thread, error_message)
            - success: True if thread was created/updated
            - thread: EmailThread object if successful, None otherwise
            - error_message: Error message if failed, None otherwise
        """
        from db.models import EmailThread

        try:
            # Check if thread already exists
            email_thread = EmailThread.query.filter_by(
                chat_id=chat_id,
                institut_id=institut_id,
                function_type_id=function_type_id
            ).first()

            if not email_thread:
                # Create new thread
                email_thread = EmailThread(
                    chat_id=chat_id,
                    institut_id=institut_id,
                    subject=subject,
                    sender=sender,
                    function_type_id=function_type_id
                )
                db.session.add(email_thread)
            else:
                # Update existing thread
                email_thread.subject = subject
                email_thread.sender = sender

            db.session.commit()
            return True, email_thread, None

        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating/updating thread: {str(e)}"

    @staticmethod
    def add_message_to_thread(
        thread_id: int,
        sender: str,
        content: str,
        timestamp: datetime,
        generated_by: str = "human"
    ) -> Tuple[bool, Optional['Message'], Optional[str]]:
        """
        Add a message to a thread.

        Checks for duplicates based on thread_id, timestamp, and content.

        Args:
            thread_id: The thread ID
            sender: Message sender
            content: Message content
            timestamp: Message timestamp
            generated_by: Who generated the message (default: "human")

        Returns:
            Tuple of (success, message, error_message)
            - success: True if message was added
            - message: Message object if successful, None otherwise
            - error_message: Error message if failed, None otherwise
        """
        from db.models import Message

        try:
            # Check if message already exists
            existing_message = Message.query.filter_by(
                thread_id=thread_id,
                timestamp=timestamp,
                content=content
            ).first()

            if existing_message:
                return True, existing_message, None

            # Create new message
            message = Message(
                thread_id=thread_id,
                sender=sender,
                content=content,
                timestamp=timestamp,
                generated_by=generated_by if generated_by else "Human"
            )
            db.session.add(message)
            db.session.commit()

            return True, message, None

        except Exception as e:
            db.session.rollback()
            return False, None, f"Error adding message: {str(e)}"

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """
        Parse a timestamp string into a datetime object.

        Tries multiple formats to handle various timestamp formats.

        Args:
            timestamp_str: The timestamp string to parse

        Returns:
            datetime object if successful, None otherwise
        """
        if not timestamp_str:
            return None

        try:
            # Try standard format first
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try flexible parser
                return date_parser.parse(timestamp_str)
            except ValueError:
                return None

    @staticmethod
    def add_feature_to_thread(
        thread_id: int,
        llm_name: str,
        feature_type_name: str,
        content: Any
    ) -> Tuple[bool, Optional['Feature'], Optional[str]]:
        """
        Add a feature to a thread.

        Creates LLM and FeatureType entries if they don't exist.
        Checks for duplicates.

        Args:
            thread_id: The thread ID
            llm_name: Name of the LLM that generated the feature
            feature_type_name: Type of the feature (e.g., "situation_summary")
            content: Feature content (will be JSON encoded if dict/list)

        Returns:
            Tuple of (success, feature, error_message)
            - success: True if feature was added
            - feature: Feature object if successful, None otherwise
            - error_message: Error message if failed, None otherwise
        """
        from db.models import LLM, FeatureType, Feature
        import json

        try:
            # Get or create LLM
            llm = LLM.query.filter_by(name=llm_name).first()
            if not llm:
                llm = LLM(name=llm_name)
                db.session.add(llm)
                db.session.flush()

            # Get or create FeatureType
            feature_type = FeatureType.query.filter_by(name=feature_type_name).first()
            if not feature_type:
                feature_type = FeatureType(name=feature_type_name)
                db.session.add(feature_type)
                db.session.flush()

            # Check if feature already exists
            existing_feature = Feature.query.filter_by(
                thread_id=thread_id,
                type_id=feature_type.type_id,
                llm_id=llm.llm_id
            ).first()

            if existing_feature:
                return True, existing_feature, None

            # Convert content to JSON if necessary
            if isinstance(content, (dict, list)):
                content = json.dumps(content)

            # Create new feature
            feature = Feature(
                thread_id=thread_id,
                type_id=feature_type.type_id,
                llm_id=llm.llm_id,
                content=content
            )
            db.session.add(feature)
            db.session.commit()

            return True, feature, None

        except Exception as e:
            db.session.rollback()
            return False, None, f"Error adding feature: {str(e)}"

    @staticmethod
    def get_thread_with_messages_and_features(thread_id: int, function_type_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a thread with all its messages and features.

        Args:
            thread_id: The thread ID
            function_type_id: The function type ID

        Returns:
            Dictionary with thread data, messages, and features, or None if not found
        """
        from db.models import EmailThread

        email_thread = ThreadService.get_thread_by_id(thread_id, function_type_id)
        if not email_thread:
            return None

        return {
            'thread_id': email_thread.thread_id,
            'chat_id': email_thread.chat_id,
            'institut_id': email_thread.institut_id,
            'subject': email_thread.subject,
            'sender': email_thread.sender,
            'messages': [
                {
                    'message_id': msg.message_id,
                    'sender': msg.sender,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'generated_by': msg.generated_by
                } for msg in email_thread.messages
            ],
            'features': [
                {
                    'feature_id': feature.feature_id,
                    'model_name': feature.llm.name,
                    'type': feature.feature_type.name,
                    'content': feature.content
                } for feature in email_thread.features
            ]
        }

    @staticmethod
    def get_thread_count_by_function_type(function_type_id: int) -> int:
        """
        Get count of threads for a specific function type.

        Args:
            function_type_id: The function type ID

        Returns:
            Number of threads
        """
        from db.models import EmailThread

        return db.session.query(EmailThread).filter_by(function_type_id=function_type_id).count()

    @staticmethod
    def get_feature_count_for_thread(thread_id: int) -> int:
        """
        Get count of features for a specific thread.

        Args:
            thread_id: The thread ID

        Returns:
            Number of features
        """
        from db.models import Feature

        return db.session.query(Feature).filter_by(thread_id=thread_id).count()

    @staticmethod
    def map_function_type_input(function_type_input: str) -> Optional[int]:
        """
        Map function type input to function type ID.

        Args:
            function_type_input: Input string (e.g., "ranking", "1", "mail_rating")

        Returns:
            Function type ID (1, 2, or 3) if valid, None otherwise
        """
        valid_function_types = {
            '1': 1,
            '2': 2,
            '3': 3,
            'ranking': 1,
            'rating': 2,
            'mail_rating': 3,
            'rank': 1,
            'rate': 2,
            'rankings': 1,
            'ratings': 2,
            'mail_ratings': 3
        }

        return valid_function_types.get(function_type_input.lower())

    @staticmethod
    def get_consulting_category_types() -> List[Dict[str, Any]]:
        """
        Get all consulting category types.

        Returns:
            List of consulting category type dictionaries
        """
        from db.models import ConsultingCategoryType

        categories = ConsultingCategoryType.query.all()

        return [
            {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
            for category in categories
        ]
