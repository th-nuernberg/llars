"""
KAIMO Defaults Seeder

Seeds the KAIMO system with default categories, subcategories and standard cases.
Based on docs/docs/projekte/kaimo/konzept.md.
"""
from datetime import datetime, date


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


def seed_kaimo_demo_cases(db):
    """
    Seed KAIMO demo cases (Development mode only).

    This is called from run_all_seeders() only in development mode,
    similar to seed_demo_scenarios().

    Args:
        db: SQLAlchemy database instance
    """
    _seed_malaika_standard_case(db)


def _seed_malaika_standard_case(db):
    """
    Seed the standard Malaika case for KAIMO.

    This is the reference case for child welfare assessment training,
    based on the KAIMo_Final prototype. It includes:
    - 4 documents (Mitteilung, Telefonat, Hausbesuch, Gespräch)
    - 22 hints with expected category assignments
    - Ground truth ratings for evaluation

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import (
        KaimoCase, KaimoDocument, KaimoHint,
        KaimoCategory, KaimoCaseCategory
    )

    # Check if case already exists
    existing = KaimoCase.query.filter_by(name='malaika').first()
    if existing:
        return  # Already seeded, skip

    # Get categories (must exist from initialize_kaimo_defaults)
    cat_grundversorgung = KaimoCategory.query.filter_by(name='grundversorgung').first()
    cat_entwicklung = KaimoCategory.query.filter_by(name='entwicklungssituation').first()
    cat_familiensituation = KaimoCategory.query.filter_by(name='familiensituation').first()
    cat_eltern = KaimoCategory.query.filter_by(name='eltern_erziehungsberechtigte').first()

    if not all([cat_grundversorgung, cat_entwicklung, cat_familiensituation, cat_eltern]):
        print("⚠ KAIMO categories not found, skipping Malaika case seeding")
        return

    # Create case
    case = KaimoCase(
        name='malaika',
        display_name='Fall Malaika',
        description='Fallakte zur möglichen Kindeswohlgefährdung bei Malaika Boukari (8 Jahre). '
                    'Dieser Standardfall dient als Referenz für die Schulung von Fachkräften.',
        status='published',
        icon='👧',
        color='#9C27B0',
        created_by='system',
        published_at=datetime.utcnow()
    )
    db.session.add(case)
    db.session.flush()

    # Link all categories to case
    categories = [cat_grundversorgung, cat_entwicklung, cat_familiensituation, cat_eltern]
    for i, cat in enumerate(categories):
        link = KaimoCaseCategory(case_id=case.id, category_id=cat.id, sort_order=i)
        db.session.add(link)

    # Document 1: Mitteilung (Main document)
    doc1 = KaimoDocument(
        case_id=case.id,
        title='Mitteilung über eine mögliche Kindeswohlgefährdung',
        content=_MALAIKA_DOC_MITTEILUNG,
        document_type='bericht',
        document_date=date(2023, 2, 3),
        sort_order=0
    )
    db.session.add(doc1)

    # Document 2: Telefonat mit Klassenlehrerin
    doc2 = KaimoDocument(
        case_id=case.id,
        title='Telefonat mit Klassenlehrerin von Malaika',
        content=_MALAIKA_DOC_TELEFONAT,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 6),
        sort_order=1
    )
    db.session.add(doc2)

    # Document 3: Hausbesuch
    doc3 = KaimoDocument(
        case_id=case.id,
        title='Hausbesuch bei Familie Boukari',
        content=_MALAIKA_DOC_HAUSBESUCH,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 7),
        sort_order=2
    )
    db.session.add(doc3)

    # Document 4: Gespräch in der Dienststelle
    doc4 = KaimoDocument(
        case_id=case.id,
        title='Gespräch in der Dienststelle',
        content=_MALAIKA_DOC_GESPRAECH,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 16),
        sort_order=3
    )
    db.session.add(doc4)
    db.session.flush()

    # Create hints with expected categories and ratings
    # Format: (content, document, expected_category, expected_rating)
    hints_data = [
        # Grundversorgung hints (8) - Physical care and supervision
        ('Malaika hat oft stark verfilzte Haare und riecht streng.',
         doc1, cat_grundversorgung, 'risk'),
        ('Das Mädchen sieht schlecht gepflegt aus.',
         doc1, cat_grundversorgung, 'risk'),
        ('Malaika duscht/badet nur 2x die Woche.',
         doc3, cat_grundversorgung, 'unclear'),
        ('Das Haarewaschen ist für Malaika unangenehm, weshalb sie manchmal "Theater" macht.',
         doc3, cat_grundversorgung, 'unclear'),
        ('Malaika wirkte äußerlich gesund und altersgemäß entwickelt.',
         doc4, cat_grundversorgung, 'resource'),
        ('Ihre Haare waren frisch gewaschen und zu einem Zopf geflochten.',
         doc4, cat_grundversorgung, 'resource'),
        ('Spielzeug war wenig vorhanden im Kinderzimmer.',
         doc3, cat_grundversorgung, 'risk'),
        ('Malaika hat ihr eigenes Zimmer mit Bett und Kleiderschrank.',
         doc3, cat_grundversorgung, 'resource'),

        # Entwicklung hints (5) - Development and education
        ('Malaika ist in ihrer Arbeitshaltung eher langsam und braucht viel Zeit.',
         doc2, cat_entwicklung, 'risk'),
        ('Malaika muss voraussichtlich die 2. Klasse wiederholen.',
         doc4, cat_entwicklung, 'risk'),
        ('Malaika hat unter dem Lockdown gelitten, da die Eltern schulisch kaum unterstützen konnten.',
         doc2, cat_entwicklung, 'risk'),
        ('Malaika wirkte schüchtern und mied den direkten Blickkontakt.',
         doc4, cat_entwicklung, 'unclear'),
        ('Malaika erzählt vom "Schnipp-Schnapp-Spiel" mit dem Vater in Badewanne und Bett.',
         doc1, cat_entwicklung, 'risk'),

        # Familiensituation hints (6) - Family situation
        ('Die Familie bewohnt eine 2-Zimmer-Wohnung.',
         doc3, cat_familiensituation, 'unclear'),
        ('Die Wohnung ist insgesamt sehr sauber und aufgeräumt.',
         doc3, cat_familiensituation, 'resource'),
        ('Herr Boukari arbeitet als Koch von 14:00 bis 23:00 Uhr.',
         doc3, cat_familiensituation, 'unclear'),
        ('Frau Boukari arbeitet an zwei Tagen als Reinigungskraft.',
         doc3, cat_familiensituation, 'resource'),
        ('Die Eltern gehen wertschätzend und höflich miteinander um.',
         doc3, cat_familiensituation, 'resource'),
        ('Seit Corona haben sie die Kontakte größtmöglich reduziert.',
         doc3, cat_familiensituation, 'unclear'),

        # Eltern hints (3) - Parents/Caregivers
        ('Die Mutter ist in der Erziehung eher inkonsequent und kann sich nicht durchsetzen.',
         doc2, cat_eltern, 'risk'),
        ('Die Eltern drohen Malaika, wenn sie sich ihnen widersetzt.',
         doc1, cat_eltern, 'risk'),
        ('Herr Boukari lehnte es ab, dass mit Malaika alleine gesprochen wird.',
         doc4, cat_eltern, 'risk'),
    ]

    for i, (content, doc, category, rating) in enumerate(hints_data):
        hint = KaimoHint(
            case_id=case.id,
            document_id=doc.id,
            content=content,
            expected_category_id=category.id,
            expected_rating=rating,
            sort_order=i
        )
        db.session.add(hint)

    db.session.commit()
    print(f"✓ Seeded KAIMO standard case 'Malaika' (4 documents, {len(hints_data)} hints)")


# Document content constants (kept separate for readability)
_MALAIKA_DOC_MITTEILUNG = """Art der Meldung:
Anruf im Jugendamt

Angaben zum Kind:
Malaika Boukari, 8 Jahre alt, wohnhaft: Regenbogenstraße 7, 87654 Kleinstadt

Angaben zu Geschwistern:
Keine

Angaben zur Mutter:
Inaya Boukari, 43 Jahre alt, wohnhaft: Regenbogenstraße 7, 87654 Kleinstadt

Angaben zum Vater:
Amir Boukari, 56 Jahre alt, wohnhaft: Regenbogenstraße 7, 87654 Kleinstadt

Angaben zu anderen Personen im Haushalt:
Keine

Angaben zur mitteilenden Person:
Die Anruferin ist eine Mutter einer Mitschülerin und Spielkameradin von Malaika. Sie möchte anonym bleiben, um den Kontakt zwischen den Kindern nicht zu gefährden.

Angaben zum Sachverhalt:
Die Tochter der Anruferin und Malaika würden gemeinsam die Schule besuchen und seit einem Jahr immer wieder auf dem Spielplatz zusammen spielen. Dabei fiel der Anruferin von Beginn an auf, dass Malaika einerseits ein aufgeschlossenes, offenes, fast distanzloses Mädchen sei, das viel redet und fröhlich sein kann und gleichzeitig oftmals verschüchtert und ängstlich wirke und sich selbst wenig zutraue. In Gesprächen zwischen den beiden Mädchen kam immer wieder das Thema auf, dass Malaika große Angst vor dem „Teufel" habe. Die Eltern würden Malaika drohen, wenn sie sich ihnen widersetzte. Das Mädchen äußerte die Sorge, nicht "lieb genug" zu sein. Denn nur die lieben Mädchen würden von den "Engeln" beschützt werden. Die Anruferin berichtet zudem, dass Malaika oft stark verfilzte Haare habe. Auch rieche das Mädchen streng und sehe schlecht gepflegt aus. Malaika dürfe zudem ausschließlich auf dem Spielplatz mit ihrer Tochter spielen. Vor einer Woche konnte die Anruferin Frau Boukari einmal überreden, dass Malaika mit zu ihr nach Hause gehen durfte. Bei diesem Besuch habe das Mädchen ihr erzählt, dass sie mit dem Papa abends in der Badewanne und im Bett immer das „Schnipp-Schnapp-Spiel" spiele. Auf Nachfrage hat Malaika versucht das Spiel zu erklären. Sie ist dabei jedoch immer wieder in ihre Muttersprache verfallen, so dass die Anruferin sie nicht verstanden hat. Die Anruferin habe versucht Malaika zu stoppen und wieder ins Deutsch umzulenken. Malaika habe dann aber nur noch gesagt „dann vorbei und Papa geht zu Mama ins Bett". Als Malaika von ihrer Mutter abgeholt wurde, hat sie sich bei Frau Boukari erkundigt, was denn das „Schnipp-Schnapp-Spiel" sei. Frau Boukari gab jedoch darauf keine Antwort und verabschiedete sich schnell von allen.

Weiteres Vorgehen:
Für eine abschließende Einschätzung ist eine Überprüfung erforderlich. Eine weitere Abklärung erfolgt mittels eines Hausbesuches und Einholung weiterer Informationen über die Schule."""

_MALAIKA_DOC_TELEFONAT = """Die Klassenlehrerin von Malaika reagiert überrascht, dass zur Familie Boukari eine Mitteilung vorliegt. Sie stehe bereits wegen zwei Jungs aus ihrer Klasse mit dem Jugendamt im Kontakt. Aber eine Meldung zu einer ihren Schülerinnen sei ihr neu. Sie sehe keine Auffälligkeiten in Bezug auf Malaika. Sie sei wie ihre anderen Schülerinnen auch, ein sehr liebes Mädchen, ist stets freundlich und ein eher ruhiges Kind. Auch optisch sei ihr nichts aufgefallen. Das Mädchen hätte halt die typischen stark gekrausten, dichten Locken und trägt am liebsten jeden Tag ihr gelbes T-Shirt. Das Einzige was auffällig sei, ist das Malaika in ihrer Arbeitshaltung eher langsam ist und viel Zeit braucht. Sie sei auch eines der Kinder gewesen, die sehr unter dem Lockdown gelitten hätten, da die Eltern sie in den schulischen Aufgaben kaum unterstützen könnten. Die Klassenlehrerin hat auch den Eindruck, dass die Mutter von Malaika in der Erziehung eher inkonsequent ist und sich nicht durchsetzen kann."""

_MALAIKA_DOC_HAUSBESUCH = """Beim Hausbesuch konnten beide Eltern angetroffen werden. Malaika war zu diesem Zeitpunkt im Hort. Die Unterhaltung fand aufgrund der Sprachbarrieren überwiegend mit Herr Boukari statt. Beide Eltern verhielten sich im Gespräch eher reserviert, aber freundlich. Sie wirkten verunsichert und erkundigten sich mehrmals, warum es diesen Termin gebe.

Die Familie bewohnt eine 2-Zimmer-Wohnung. Das Wohnzimmer wurde vom Vater durch eine Wand getrennt, sodass Malaika ihr eigenes Zimmer hat. Das Zimmer von Malaika ist klein, allerdings befinden sich ein Bett und ein Kleiderschrank darin. Spielzeug war wenig vorhanden. Die Eltern erzählten auf Nachfrage, dass Malaika oft alleine in ihrem Zimmer schlafe, aber auch ab und zu noch bei ihnen im Bett schlafen würde. Das „Zu-Bett-Geh"-Ritual sei unterschiedlich. Unter der Woche wird Malaika von ihrer Mutter ins Bett gebracht. Am Wochenende übernehme das der Vater, der ihr dann gerne noch Geschichten zum Einschlafen erzähle. Die Wohnung ist insgesamt sehr sauber und aufgeräumt. Herr Boukari arbeitet als Koch. Seine Arbeitszeiten sind meistens nachmittags von 14:00 Uhr bis abends 23:00 Uhr. Frau Boukari arbeitet an zwei Tagen die Woche als Reinigungskraft. Malaika geht vormittags zur Schule und ist an den Tagen, wo Frau Boukari arbeitet, nach der Schule in einem Hort angebunden. Malaika wird von der Mutter morgens zur Schule gebracht und auch wieder abgeholt. Bei gutem Wetter gehen beide zusammen noch auf dem Spielplatz. Herr Boukari berichtet, dass sie auch guten Kontakt mit den Nachbarn hätten. Seit der Corona-Pandemie haben sie die Kontakte jedoch größtmöglich reduziert. Meistens würde die Frau Boukari mit Malaika spielen. Beide kochen und backen vor allem gerne zusammen. Malaika würde zudem von 17:30 bis 18:00 Uhr Islamunterricht im Internet bekommen. Danach darf sie noch fernsehen. Die tägliche Hygiene wird überwiegend von Frau Boukari sichergestellt. Malaika würde 2x die Woche duschen / baden gehen und täglich Zähne putzen. Die Mutter betont, wie wichtig ihr die Pflege und Reinlichkeit als Frau sei. Das Haarewaschen ist für Malaika aber aufgrund der langen Haare unangenehm, weshalb sie manchmal „Theater" mache.

Die Eltern gehen insgesamt wertschätzend und höflich miteinander um. Die Eltern berichten, dass Malaika ein gutes und gehorsames Kind sei und sie keine Probleme mit ihr hätten. Sie benötigen auch keine Beratung oder Unterstützung."""

_MALAIKA_DOC_GESPRAECH = """Um sich auch noch einen persönlichen Eindruck vom Malaika verschaffen zu können, wurde die Familie erneut zu einem Gespräch in die Dienstelle eingeladen. Zum vereinbarten Termin erschien Herr Boukari zusammen mit Malaika. Frau Boukari habe aktuell Rückenschmerzen und sei daher nicht zum Termin mitgekommen.

Herr Boukari wirkte angespannt und zeigte sich verärgert. Er berichtete erneut, dass es keine Probleme zu Hause gebe und er nicht verstehe, warum das Jugendamt erneut ein Gespräch wolle. Er betonte immer wieder, dass er sich dafür nun extra von der Arbeit habe frei nehmen müsse. Er zeigte immer wieder auf seine Tochter mit den Worten: „Sie sehen doch, dass es ihr gut geht". Malaika wirkte schüchtern und mied den direkten Blickkontakt. Sie sah sich immer wieder im Raum um. Malaika wirkte äußerlich gesund und altersgemäß entwickelt. Ihre Haare waren frisch gewaschen und zu einem Zopf geflochten. Dem Wunsch, mit Malaika alleine zu sprechen, kam Herr Boukari nicht nach. Er würde sein Kind nicht alleine lassen. Auf die Frage, wie denn die letzten Tage zu Hause waren, erzählte Malaika schließlich sichtlich fröhlich von ihrem neuen Puppenhaus. Das habe ihr Vater ihr kürzlich geschenkt. Sie haben auch gemeinsam schon viel damit gespielt. Sie gab im Weiteren an, dass sie gerne zu Hause sei. Auf die Frage, wie es in der Schule gehen würde, antwortete Malaika nicht gleich, sondern sah ihren Vater an und dann auf ihre Füße. Herr Boukari erklärt, dass seine Tochter ab März den Hort nicht mehr besuchen werde. Der Hort hat nicht die erhoffte schulische Unterstützung gebracht. Malika muss nach aktuellem Stand voraussichtlich die 2. Klasse wiederholen. Den Rest des Schuljahres wird sich daher vor allem die Mutter intensiv um alle schulische Nachhilfe kümmern. Erneute Angebote der Beratung und Unterstützung wurden klar abgelehnt. Die Familie komme alleine gut zurecht."""
