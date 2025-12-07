"""KAIMO Category Service.

Business logic for managing KAIMO categories and subcategories.
"""

from typing import List, Dict

from db.models import KaimoCategory, KaimoSubcategory


class KaimoCategoryService:
    """Service for managing KAIMO categories."""

    @staticmethod
    def get_all_categories_with_subcategories() -> List[Dict]:
        """Get all KAIMO categories with their subcategories.

        Returns:
            List of category dictionaries with nested subcategories.
        """
        categories = KaimoCategory.query.order_by(KaimoCategory.sort_order).all()

        result = []
        for cat in categories:
            subcategories = (
                KaimoSubcategory.query
                .filter_by(category_id=cat.id)
                .order_by(KaimoSubcategory.sort_order)
                .all()
            )

            result.append({
                "id": cat.id,
                "name": cat.name,
                "display_name": cat.display_name,
                "description": cat.description,
                "icon": cat.icon,
                "color": cat.color,
                "sort_order": cat.sort_order,
                "is_default": cat.is_default,
                "subcategories": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "display_name": sub.display_name,
                        "description": sub.description,
                        "sort_order": sub.sort_order,
                        "is_default": sub.is_default,
                    } for sub in subcategories
                ]
            })

        return result
