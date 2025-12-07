"""
KAIMO Defaults Seeder

Seeds the KAIMO system with default categories and subcategories.
Based on docs/docs/projekte/kaimo/konzept.md.
"""


def initialize_kaimo_defaults(db):
    """
    Seed default KAIMO categories and subcategories (idempotent).

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import KaimoCategory, KaimoSubcategory

    default_categories = [
        {
            'name': 'grundversorgung',
            'display_name': 'Grundversorgung des jungen Menschen',
            'icon': None,
            'color': '#4CAF50',
            'subcategories': [
                ('koerperliche_gesundheit_kind', 'Körperliche Gesundheit des Kindes'),
                ('psychische_gesundheit_kind', 'Psychische Gesundheit des Kindes'),
                ('substanzen_kind', 'Medikamenten- und Substanzkonsum des Kindes'),
                ('aufsicht_betreuung', 'Aufsicht / Betreuungssituation des Kindes'),
            ]
        },
        {
            'name': 'entwicklungssituation',
            'display_name': 'Entwicklungssituation des jungen Menschen',
            'icon': None,
            'color': '#2196F3',
            'subcategories': [
                ('biografie_kind', 'Biografie des Kindes (inkl. Maßnahmen der Jugendhilfe)'),
                ('sozialverhalten_kind', 'Sozialverhalten / Sozialkontakte des Kindes'),
                ('sexualentwicklung', 'Sexualentwicklung des Kindes'),
                ('bildung_leistung', 'Bildung- und Leistungsbereich des Kindes'),
            ]
        },
        {
            'name': 'familiensituation',
            'display_name': 'Familiensituation',
            'icon': None,
            'color': '#9C27B0',
            'subcategories': [
                ('wohnsituation', 'Wohnsituation'),
                ('wirtschaftliche_situation', 'Wirtschaftliche Situation (inkl. Erwerbstätigkeit)'),
                ('familiaere_beziehungen', 'Familiäre Beziehungen (inkl. Häusliche Gewalt)'),
            ]
        },
        {
            'name': 'eltern_erziehungsberechtigte',
            'display_name': 'Eltern / Erziehungsberechtigte',
            'icon': None,
            'color': '#FF9800',
            'subcategories': [
                ('biografie_eltern', 'Biografie der Erziehungsberechtigten'),
                ('gesundheit_eltern', 'Gesundheit der Erziehungsberechtigten'),
                ('wohlbefinden_eltern', 'Wohlbefinden der Erziehungsberechtigten'),
                ('sozialverhalten_eltern', 'Sozialverhalten / Sozialkontakte der Erziehungsberechtigten'),
            ]
        },
    ]

    created_categories = 0
    created_subcategories = 0

    for idx, cat_data in enumerate(default_categories, start=1):
        category = KaimoCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = KaimoCategory(
                name=cat_data['name'],
                display_name=cat_data['display_name'],
                description=None,
                icon=cat_data.get('icon'),
                color=cat_data.get('color'),
                sort_order=idx,
                is_default=True,
            )
            db.session.add(category)
            db.session.flush()
            created_categories += 1
        else:
            category.is_default = True
            if category.sort_order is None:
                category.sort_order = idx

        for sub_idx, (sub_name, sub_display) in enumerate(cat_data['subcategories'], start=1):
            sub = KaimoSubcategory.query.filter_by(category_id=category.id, name=sub_name).first()
            if not sub:
                sub = KaimoSubcategory(
                    category_id=category.id,
                    name=sub_name,
                    display_name=sub_display,
                    description=None,
                    sort_order=sub_idx,
                    is_default=True,
                )
                db.session.add(sub)
                created_subcategories += 1
            else:
                sub.is_default = True
                if sub.sort_order is None:
                    sub.sort_order = sub_idx

    if created_categories or created_subcategories:
        db.session.commit()
        print(f"✓ Seeded KAIMO defaults (categories: {created_categories}, subcategories: {created_subcategories})")
