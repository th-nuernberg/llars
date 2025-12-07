"""
Ranking Service

Handles all ranking-related business logic including:
- User feature rankings
- Thread ranking status
- Ranking statistics
- CSV export for rankings
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from db.db import db


class RankingService:
    """
    Core service for ranking management.

    Provides methods for managing user feature rankings,
    checking ranking status, and generating statistics.
    """

    @staticmethod
    def get_user_rankings_for_thread(user_id: int, thread_id: int) -> List['UserFeatureRanking']:
        """
        Get all rankings by a user for a specific thread.

        Args:
            user_id: The user ID
            thread_id: The thread ID

        Returns:
            List of UserFeatureRanking objects
        """
        from db.models import UserFeatureRanking, Feature

        rankings = UserFeatureRanking.query.filter_by(user_id=user_id).join(Feature).filter(
            Feature.thread_id == thread_id
        ).all()

        return rankings

    @staticmethod
    def has_user_ranked_thread(user_id: int, thread_id: int) -> bool:
        """
        Check if user has ranked any features in a thread.

        Args:
            user_id: The user ID
            thread_id: The thread ID

        Returns:
            True if user has ranked at least one feature, False otherwise
        """
        rankings = RankingService.get_user_rankings_for_thread(user_id, thread_id)
        return len(rankings) > 0

    @staticmethod
    def has_user_fully_ranked_thread(user_id: int, thread_id: int) -> bool:
        """
        Check if user has ranked all features in a thread.

        Args:
            user_id: The user ID
            thread_id: The thread ID

        Returns:
            True if all features are ranked, False otherwise
        """
        from db.models import Feature

        # Get total features
        total_features = db.session.query(Feature).filter_by(thread_id=thread_id).count()

        if total_features == 0:
            return False

        # Get ranked features count
        rankings = RankingService.get_user_rankings_for_thread(user_id, thread_id)
        ranked_count = len(rankings)

        return ranked_count == total_features

    @staticmethod
    def get_current_rankings_by_type(user_id: int, thread_id: int) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get current rankings organized by feature type and bucket.

        Returns a structure like:
        {
            "situation_summary": {
                "goodList": [...],
                "averageList": [...],
                "badList": [...],
                "neutralList": [...]
            }
        }

        Args:
            user_id: The user ID
            thread_id: The thread ID

        Returns:
            Dictionary of rankings organized by type and bucket
        """
        from db.models import UserFeatureRanking, Feature, FeatureType

        # Get all rankings for this user and thread
        rankings = RankingService.get_user_rankings_for_thread(user_id, thread_id)

        # Get all feature types
        feature_types = FeatureType.query.all()

        # Initialize structure
        rankings_data = {
            feature_type.name: {
                "goodList": [],
                "averageList": [],
                "badList": [],
                "neutralList": []
            }
            for feature_type in feature_types
        }

        # Populate with ranked features
        for ranking in rankings:
            feature_data = {
                'model_name': ranking.llm.name,
                'content': ranking.feature.content,
                'feature_id': ranking.feature_id,
                'position': int(ranking.ranking_content),
                'minimized': True
            }

            feature_type = ranking.feature_type.name

            if feature_type in rankings_data:
                if ranking.bucket == 'Gut':
                    rankings_data[feature_type]['goodList'].append(feature_data)
                elif ranking.bucket == 'Mittel':
                    rankings_data[feature_type]['averageList'].append(feature_data)
                elif ranking.bucket == 'Schlecht':
                    rankings_data[feature_type]['badList'].append(feature_data)
                else:
                    rankings_data[feature_type]['neutralList'].append(feature_data)

        # Add unranked features to neutralList
        ranked_feature_ids = [ranking.feature_id for ranking in rankings]
        all_features = Feature.query.filter_by(thread_id=thread_id).all()

        for feature in all_features:
            if feature.feature_id not in ranked_feature_ids:
                feature_data = {
                    'model_name': feature.llm.name,
                    'content': feature.content,
                    'feature_id': feature.feature_id,
                    'position': None,
                    'minimized': True
                }

                feature_type = feature.feature_type.name
                if feature_type in rankings_data:
                    rankings_data[feature_type]['neutralList'].append(feature_data)

        # Sort lists by position
        for feature_type, data in rankings_data.items():
            for bucket in ['goodList', 'averageList', 'badList', 'neutralList']:
                data[bucket] = sorted(
                    data[bucket],
                    key=lambda x: x['position'] if x['position'] is not None else float('inf')
                )

        return rankings_data

    @staticmethod
    def save_ranking(
        user_id: int,
        thread_id: int,
        feature_id: int,
        type_id: int,
        llm_id: int,
        position: int,
        bucket: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Save or update a ranking.

        Args:
            user_id: The user ID
            thread_id: The thread ID (used for validation)
            feature_id: The feature ID
            type_id: The feature type ID
            llm_id: The LLM ID
            position: Position in the ranking
            bucket: Bucket name ("Gut", "Mittel", "Schlecht")

        Returns:
            Tuple of (success, error_message)
            - success: True if ranking was saved
            - error_message: Error message if failed, None otherwise
        """
        from db.models import UserFeatureRanking

        try:
            # Check if ranking already exists
            existing_ranking = UserFeatureRanking.query.filter_by(
                user_id=user_id,
                feature_id=feature_id,
                type_id=type_id,
                llm_id=llm_id
            ).first()

            if existing_ranking:
                # Update existing ranking
                existing_ranking.ranking_content = position
                existing_ranking.bucket = bucket
            else:
                # Create new ranking
                new_ranking = UserFeatureRanking(
                    user_id=user_id,
                    feature_id=feature_id,
                    ranking_content=position,
                    bucket=bucket,
                    type_id=type_id,
                    llm_id=llm_id
                )
                db.session.add(new_ranking)

            db.session.commit()
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, f"Error saving ranking: {str(e)}"

    @staticmethod
    def get_user_ranking_stats_for_all_users() -> List[Dict[str, Any]]:
        """
        Get ranking statistics for all users.

        Returns statistics about how many threads each user has ranked
        completely vs. partially.

        Returns:
            List of user statistics dictionaries
        """
        from db.models import User, EmailThread, Feature, UserFeatureRanking

        user_stats = []

        # Get total threads with function_type_id = 1 (ranking)
        total_threads = db.session.query(EmailThread).filter_by(function_type_id=1).count()

        for user in User.query.all():
            ranked_threads_list = []
            unranked_threads_list = []
            total_ranked_threads = 0

            # Iterate through ranking threads
            for thread in EmailThread.query.filter_by(function_type_id=1).all():
                # Count total features in thread
                total_features_in_thread = db.session.query(Feature).filter_by(
                    thread_id=thread.thread_id
                ).count()

                # Count ranked features by user in thread
                ranked_features_count = db.session.query(UserFeatureRanking).join(Feature).filter(
                    UserFeatureRanking.user_id == user.id,
                    Feature.thread_id == thread.thread_id
                ).count()

                if ranked_features_count == total_features_in_thread and total_features_in_thread > 0:
                    # Fully ranked
                    total_ranked_threads += 1
                    ranked_threads_list.append({
                        'thread_id': thread.thread_id,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                        'subject': thread.subject,
                        'ranked_features_count': ranked_features_count,
                        'total_features_in_thread': total_features_in_thread
                    })
                else:
                    # Partially or not ranked
                    unranked_threads_list.append({
                        'thread_id': thread.thread_id,
                        'chat_id': thread.chat_id,
                        'institut_id': thread.institut_id,
                        'subject': thread.subject,
                        'ranked_features_count': ranked_features_count,
                        'total_features_in_thread': total_features_in_thread
                    })

            user_stats.append({
                'username': user.username,
                'ranked_threads_count': total_ranked_threads,
                'total_threads': total_threads,
                'ranked_threads': ranked_threads_list,
                'unranked_threads': unranked_threads_list
            })

        return user_stats

    @staticmethod
    def get_all_rankings_for_csv_export() -> List['UserFeatureRanking']:
        """
        Get all rankings sorted for CSV export.

        Returns rankings sorted by thread_id, feature type, user, bucket, and position.

        Returns:
            List of UserFeatureRanking objects
        """
        from db.models import UserFeatureRanking, Feature, EmailThread

        rankings = UserFeatureRanking.query.join(Feature).join(EmailThread).order_by(
            Feature.thread_id,
            Feature.type_id,
            UserFeatureRanking.user_id,
            UserFeatureRanking.bucket,
            UserFeatureRanking.ranking_content
        ).all()

        return rankings

    @staticmethod
    def generate_rankings_csv_data() -> List[List[Any]]:
        """
        Generate CSV data for rankings export.

        Returns:
            List of rows for CSV export, including header
        """
        rankings = RankingService.get_all_rankings_for_csv_export()

        # Group rankings by thread, feature type, and user
        feature_type_rankings = {}

        for ranking in rankings:
            key = (
                ranking.feature.email_thread.thread_id,
                ranking.feature_type.name,
                ranking.user.username
            )
            if key not in feature_type_rankings:
                feature_type_rankings[key] = {
                    'Gut': [],
                    'Mittel': [],
                    'Schlecht': []
                }
            feature_type_rankings[key][ranking.bucket].append(ranking)

        # Build CSV rows
        csv_rows = [[
            'Thread ID', 'Feature Type', 'User', 'Complete Feature Ranking',
            'Bucket', 'Bucket Position', 'Feature ID', 'Chat ID', 'Institut ID', 'LLM Name'
        ]]

        for (thread_id, feature_type_name, username), bucket_rankings in feature_type_rankings.items():
            complete_ranking_position = 1

            # Process buckets in order
            for bucket in ['Gut', 'Mittel', 'Schlecht']:
                # Sort within bucket
                bucket_rankings[bucket].sort(key=lambda x: x.ranking_content)

                # Add rows
                for bucket_position, ranking in enumerate(bucket_rankings[bucket], start=1):
                    csv_rows.append([
                        thread_id,
                        feature_type_name,
                        username,
                        complete_ranking_position,
                        bucket,
                        bucket_position,
                        ranking.feature_id,
                        ranking.feature.email_thread.chat_id,
                        ranking.feature.email_thread.institut_id,
                        ranking.llm.name
                    ])
                    complete_ranking_position += 1

        return csv_rows
