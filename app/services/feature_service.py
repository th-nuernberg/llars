"""
Feature Service

Handles all feature-related business logic including:
- Feature function types
- Feature types
- LLM management
- Feature queries
"""

from typing import Optional, List, Dict, Any

from db.db import db


class FeatureService:
    """
    Core service for feature management.

    Provides methods for managing feature function types,
    feature types, and LLMs.
    """

    @staticmethod
    def get_function_type_by_name(name: str) -> Optional['FeatureFunctionType']:
        """
        Get feature function type by name.

        Args:
            name: Function type name (e.g., "ranking", "rating", "mail_rating")

        Returns:
            FeatureFunctionType object if found, None otherwise
        """
        from db.models import FeatureFunctionType

        return FeatureFunctionType.query.filter_by(name=name).first()

    @staticmethod
    def get_function_type_by_id(function_type_id: int) -> Optional['FeatureFunctionType']:
        """
        Get feature function type by ID.

        Args:
            function_type_id: Function type ID

        Returns:
            FeatureFunctionType object if found, None otherwise
        """
        from db.models import FeatureFunctionType

        return FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()

    @staticmethod
    def get_all_function_types() -> List['FeatureFunctionType']:
        """
        Get all feature function types.

        Returns:
            List of FeatureFunctionType objects
        """
        from db.models import FeatureFunctionType

        return FeatureFunctionType.query.all()

    @staticmethod
    def get_feature_type_by_name(name: str) -> Optional['FeatureType']:
        """
        Get feature type by name.

        Args:
            name: Feature type name (e.g., "situation_summary")

        Returns:
            FeatureType object if found, None otherwise
        """
        from db.models import FeatureType

        return FeatureType.query.filter_by(name=name).first()

    @staticmethod
    def get_or_create_feature_type(name: str) -> 'FeatureType':
        """
        Get or create a feature type.

        Args:
            name: Feature type name

        Returns:
            FeatureType object
        """
        from db.models import FeatureType

        feature_type = FeatureService.get_feature_type_by_name(name)
        if not feature_type:
            feature_type = FeatureType(name=name)
            db.session.add(feature_type)
            db.session.flush()

        return feature_type

    @staticmethod
    def get_all_feature_types() -> List['FeatureType']:
        """
        Get all feature types.

        Returns:
            List of FeatureType objects
        """
        from db.models import FeatureType

        return FeatureType.query.all()

    @staticmethod
    def get_llm_by_name(name: str) -> Optional['LLM']:
        """
        Get LLM by name.

        Args:
            name: LLM name (e.g., "gpt-4", "claude-3")

        Returns:
            LLM object if found, None otherwise
        """
        from db.models import LLM

        return LLM.query.filter_by(name=name).first()

    @staticmethod
    def get_or_create_llm(name: str) -> 'LLM':
        """
        Get or create an LLM.

        Args:
            name: LLM name

        Returns:
            LLM object
        """
        from db.models import LLM

        llm = FeatureService.get_llm_by_name(name)
        if not llm:
            llm = LLM(name=name)
            db.session.add(llm)
            db.session.flush()

        return llm

    @staticmethod
    def get_all_llms() -> List['LLM']:
        """
        Get all LLMs.

        Returns:
            List of LLM objects
        """
        from db.models import LLM

        return LLM.query.all()

    @staticmethod
    def get_feature_by_id(feature_id: int) -> Optional['Feature']:
        """
        Get feature by ID.

        Args:
            feature_id: The feature ID

        Returns:
            Feature object if found, None otherwise
        """
        from db.models import Feature

        return Feature.query.filter_by(feature_id=feature_id).first()

    @staticmethod
    def get_features_by_thread(thread_id: int) -> List['Feature']:
        """
        Get all features for a thread.

        Args:
            thread_id: The thread ID

        Returns:
            List of Feature objects
        """
        from db.models import Feature

        return Feature.query.filter_by(thread_id=thread_id).all()

    @staticmethod
    def get_feature_by_attributes(
        thread_id: int,
        type_id: int,
        llm_id: int,
        content: Optional[str] = None
    ) -> Optional['Feature']:
        """
        Get feature by specific attributes.

        Args:
            thread_id: The thread ID
            type_id: The feature type ID
            llm_id: The LLM ID
            content: Optional content to match

        Returns:
            Feature object if found, None otherwise
        """
        from db.models import Feature

        query = Feature.query.filter_by(
            thread_id=thread_id,
            type_id=type_id,
            llm_id=llm_id
        )

        if content is not None:
            query = query.filter_by(content=content)

        return query.first()

    @staticmethod
    def get_features_count_by_thread(thread_id: int) -> int:
        """
        Get count of features for a thread.

        Args:
            thread_id: The thread ID

        Returns:
            Number of features
        """
        from db.models import Feature

        return db.session.query(Feature).filter_by(thread_id=thread_id).count()

    @staticmethod
    def get_features_by_type(thread_id: int, feature_type_name: str) -> List['Feature']:
        """
        Get features for a thread filtered by type.

        Args:
            thread_id: The thread ID
            feature_type_name: The feature type name

        Returns:
            List of Feature objects
        """
        from db.models import Feature, FeatureType

        feature_type = FeatureService.get_feature_type_by_name(feature_type_name)
        if not feature_type:
            return []

        return Feature.query.filter_by(
            thread_id=thread_id,
            type_id=feature_type.type_id
        ).all()

    @staticmethod
    def get_features_by_llm(thread_id: int, llm_name: str) -> List['Feature']:
        """
        Get features for a thread filtered by LLM.

        Args:
            thread_id: The thread ID
            llm_name: The LLM name

        Returns:
            List of Feature objects
        """
        from db.models import Feature, LLM

        llm = FeatureService.get_llm_by_name(llm_name)
        if not llm:
            return []

        return Feature.query.filter_by(
            thread_id=thread_id,
            llm_id=llm.llm_id
        ).all()
