"""
Consulting Category Types Seeder

Seeds the ConsultingCategoryType table with default consulting categories.
"""


def initialize_consulting_category_types(db):
    """
    Initialize consulting category types (10 categories for consultation classification).

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import ConsultingCategoryType

    categories_data = [
        {
            'id': 1,
            'name': 'Unversorgtheit des jungen Menschen',
            'description': 'Ausfall der Bezugspersonen wegen Krankheit, stationärer Unterbringung, Inhaftierung, Tod; unbegleitet eingereiste Minderjährige',
        },
        {
            'id': 2,
            'name': 'Unzureichende Förderung / Betreuung / Versorgung des jungen Menschen in der Familie',
            'description': 'soziale, gesundheitliche, wirtschaftliche Probleme',
        },
        {
            'id': 3,
            'name': 'Gefährdung des Kindeswohls',
            'description': 'Vernachlässigung, körperliche, psychische, sexuelle Gewalt in der Familie',
        },
        {
            'id': 4,
            'name': 'Eingeschränkte Erziehungskompetenz der Eltern/Personensorgeberechtigten',
            'description': 'Erziehungsunsicherheit, pädagogische Überforderung, unangemessene Verwöhnung',
        },
        {
            'id': 5,
            'name': 'Belastungen des jungen Menschen durch Problemlagen der Eltern ',
            'description': 'Suchtverhalten, geistige oder seelische Behinderung',
        },
        {
            'id': 6,
            'name': 'Belastungen des jungen Menschen durch familiäre Konflikte',
            'description': 'Partnerkonflikte, Trennung und Scheidung, Umgangs- / Sorgerechtsstreitigkeiten, Eltern- / Stiefeltern-Kind-Konflikte, migrationsbedingte Konfliktlagen',
        },
        {
            'id': 7,
            'name': 'Auffälligkeiten im sozialen Verhalten (dissoziales Verhalten) des jungen Menschen',
            'description': 'Gehemmtheit, Isolation, Geschwisterrivalität, Weglaufen, Aggressivität, Drogen- / Alkoholkonsum, Delinquenz / Straftat',
        },
        {
            'id': 8,
            'name': 'Entwicklungsauffälligkeiten/seelische Probleme des jungen Menschen ',
            'description': 'Entwicklungsrückstand, Ängste, Zwänge, selbst verletzendes Verhalten, suizidale Tendenzen',
        },
        {
            'id': 9,
            'name': 'Schulische / berufliche Probleme des jungen Menschen',
            'description': 'Schwierigkeiten mit Leistungsanforderungen, Konzentrationsprobleme (ADS, Hyperaktivität), schulvermeidendes Verhalten (Schwänzen), Hochbegabung',
        },
        {
            'id': 10,
            'name': 'Sonstiges',
            'description': None,
        },
    ]

    for cat_data in categories_data:
        if not ConsultingCategoryType.query.filter_by(id=cat_data['id']).first():
            category = ConsultingCategoryType(**cat_data)
            db.session.add(category)

    db.session.commit()
