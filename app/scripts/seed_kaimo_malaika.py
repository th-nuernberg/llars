"""Seed script for KAIMO Malaika case from prototype.

This script creates the Malaika case with all documents and hints
exactly as shown in the KAIMo_Final prototype.

Run with: docker exec llars_flask_service python scripts/seed_kaimo_malaika.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from db.db import db
from db.models import (
    KaimoCase,
    KaimoDocument,
    KaimoHint,
    KaimoCategory,
    KaimoSubcategory,
    KaimoCaseCategory,
)
from main import app


def seed_categories():
    """Create the 4 main categories with subcategories from prototype."""
    categories_data = [
        {
            'name': 'grundversorgung',
            'display_name': 'Grundversorgung des jungen Menschen',
            'sort_order': 0,
            'is_default': True,
            'subcategories': [
                {'name': 'koerperliche_gesundheit', 'display_name': 'Körperliche Gesundheit des Kindes'},
                {'name': 'psychische_gesundheit', 'display_name': 'Psychische Gesundheit des Kindes'},
                {'name': 'medikamenten_substanzkonsum', 'display_name': 'Medikamenten- und Substanzkonsum des Kindes'},
                {'name': 'aufsicht_betreuung', 'display_name': 'Aufsicht / Betreuungssituation des Kindes'},
            ]
        },
        {
            'name': 'entwicklung',
            'display_name': 'Entwicklungssituation des jungen Menschen',
            'sort_order': 1,
            'is_default': True,
            'subcategories': [
                {'name': 'biografie', 'display_name': 'Biografie des Kindes (inkl. Maßnahmen der Jugendhilfe)'},
                {'name': 'sozialverhalten', 'display_name': 'Sozialverhalten / Sozialkontakte des Kindes'},
                {'name': 'sexualentwicklung', 'display_name': 'Sexualentwicklung des Kindes'},
                {'name': 'bildung_leistung', 'display_name': 'Bildung- und Leistungsbereich des Kindes'},
            ]
        },
        {
            'name': 'familiensituation',
            'display_name': 'Familiensituation',
            'sort_order': 2,
            'is_default': True,
            'subcategories': [
                {'name': 'wohnsituation', 'display_name': 'Wohnsituation'},
                {'name': 'wirtschaftliche_situation', 'display_name': 'Wirtschaftliche Situation (inkl. Erwerbstätigkeit)'},
                {'name': 'familiaere_beziehungen', 'display_name': 'Familiäre Beziehungen (inkl. Häusliche Gewalt)'},
            ]
        },
        {
            'name': 'eltern',
            'display_name': 'Eltern / Erziehungsberechtigte',
            'sort_order': 3,
            'is_default': True,
            'subcategories': [
                {'name': 'biografie_eltern', 'display_name': 'Biografie der Erziehungsberechtigten'},
                {'name': 'gesundheit_eltern', 'display_name': 'Gesundheit der Erziehungsberechtigten'},
                {'name': 'wohlbefinden_eltern', 'display_name': 'Wohlbefinden der Erziehungsberechtigten'},
                {'name': 'sozialverhalten_eltern', 'display_name': 'Sozialverhalten / Sozialkontakte der Erziehungsberechtigten'},
            ]
        },
    ]

    created_categories = []

    for cat_data in categories_data:
        # Check if category already exists
        existing = KaimoCategory.query.filter_by(name=cat_data['name']).first()
        if existing:
            print(f"Category '{cat_data['name']}' already exists, skipping...")
            created_categories.append(existing)
            continue

        category = KaimoCategory(
            name=cat_data['name'],
            display_name=cat_data['display_name'],
            sort_order=cat_data['sort_order'],
            is_default=cat_data['is_default']
        )
        db.session.add(category)
        db.session.flush()  # Get ID

        for i, sub_data in enumerate(cat_data['subcategories']):
            subcategory = KaimoSubcategory(
                category_id=category.id,
                name=sub_data['name'],
                display_name=sub_data['display_name'],
                sort_order=i,
                is_default=True
            )
            db.session.add(subcategory)

        created_categories.append(category)
        print(f"Created category: {cat_data['display_name']}")

    return created_categories


def seed_malaika_case(categories):
    """Create the Malaika case with all documents from prototype."""

    # Check if case already exists
    existing = KaimoCase.query.filter_by(name='malaika').first()
    if existing:
        print("Malaika case already exists, deleting and recreating...")
        db.session.delete(existing)
        db.session.flush()

    # Create case
    case = KaimoCase(
        name='malaika',
        display_name='Malaika',
        description='Fallakte zur möglichen Kindeswohlgefährdung bei Malaika Boukari (8 Jahre)',
        status='published',
        icon='👧',
        created_by='system',
        published_at=datetime.utcnow()
    )
    db.session.add(case)
    db.session.flush()

    # Link categories to case
    for i, cat in enumerate(categories):
        link = KaimoCaseCategory(
            case_id=case.id,
            category_id=cat.id,
            sort_order=i
        )
        db.session.add(link)

    # Document 1: Mitteilung (Main document)
    doc1_content = """Art der Meldung:
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

    doc1 = KaimoDocument(
        case_id=case.id,
        title='Mitteilung über eine mögliche Kindeswohlgefährdung',
        content=doc1_content,
        document_type='bericht',
        document_date=date(2023, 2, 3),
        sort_order=0
    )
    db.session.add(doc1)

    # Document 2: Telefonat mit Klassenlehrerin
    doc2_content = """Die Klassenlehrerin von Malaika reagiert überrascht, dass zur Familie Boukari eine Mitteilung vorliegt. Sie stehe bereits wegen zwei Jungs aus ihrer Klasse mit dem Jugendamt im Kontakt. Aber eine Meldung zu einer ihren Schülerinnen sei ihr neu. Sie sehe keine Auffälligkeiten in Bezug auf Malaika. Sie sei wie ihre anderen Schülerinnen auch, ein sehr liebes Mädchen, ist stets freundlich und ein eher ruhiges Kind. Auch optisch sei ihr nichts aufgefallen. Das Mädchen hätte halt die typischen stark gekrausten, dichten Locken und trägt am liebsten jeden Tag ihr gelbes T-Shirt. Das Einzige was auffällig sei, ist das Malaika in ihrer Arbeitshaltung eher langsam ist und viel Zeit braucht. Sie sei auch eines der Kinder gewesen, die sehr unter dem Lockdown gelitten hätten, da die Eltern sie in den schulischen Aufgaben kaum unterstützen könnten. Die Klassenlehrerin hat auch den Eindruck, dass die Mutter von Malaika in der Erziehung eher inkonsequent ist und sich nicht durchsetzen kann."""

    doc2 = KaimoDocument(
        case_id=case.id,
        title='Telefonat mit Klassenlehrerin von Malaika',
        content=doc2_content,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 6),
        sort_order=1
    )
    db.session.add(doc2)

    # Document 3: Hausbesuch
    doc3_content = """Beim Hausbesuch konnten beide Eltern angetroffen werden. Malaika war zu diesem Zeitpunkt im Hort. Die Unterhaltung fand aufgrund der Sprachbarrieren überwiegend mit Herr Boukari statt. Beide Eltern verhielten sich im Gespräch eher reserviert, aber freundlich. Sie wirkten verunsichert und erkundigten sich mehrmals, warum es diesen Termin gebe.

Die Familie bewohnt eine 2-Zimmer-Wohnung. Das Wohnzimmer wurde vom Vater durch eine Wand getrennt, sodass Malaika ihr eigenes Zimmer hat. Das Zimmer von Malaika ist klein, allerdings befinden sich ein Bett und ein Kleiderschrank darin. Spielzeug war wenig vorhanden. Die Eltern erzählten auf Nachfrage, dass Malaika oft alleine in ihrem Zimmer schlafe, aber auch ab und zu noch bei ihnen im Bett schlafen würde. Das „Zu-Bett-Geh"-Ritual sei unterschiedlich. Unter der Woche wird Malaika von ihrer Mutter ins Bett gebracht. Am Wochenende übernehme das der Vater, der ihr dann gerne noch Geschichten zum Einschlafen erzähle. Die Wohnung ist insgesamt sehr sauber und aufgeräumt. Herr Boukari arbeitet als Koch. Seine Arbeitszeiten sind meistens nachmittags von 14:00 Uhr bis abends 23:00 Uhr. Frau Boukari arbeitet an zwei Tagen die Woche als Reinigungskraft. Malaika geht vormittags zur Schule und ist an den Tagen, wo Frau Boukari arbeitet, nach der Schule in einem Hort angebunden. Malaika wird von der Mutter morgens zur Schule gebracht und auch wieder abgeholt. Bei gutem Wetter gehen beide zusammen noch auf dem Spielplatz. Herr Boukari berichtet, dass sie auch guten Kontakt mit den Nachbarn hätten. Seit der Corona-Pandemie haben sie die Kontakte jedoch größtmöglich reduziert. Meistens würde die Frau Boukari mit Malaika spielen. Beide kochen und backen vor allem gerne zusammen. Malaika würde zudem von 17:30 bis 18:00 Uhr Islamunterricht im Internet bekommen. Danach darf sie noch fernsehen. Die tägliche Hygiene wird überwiegend von Frau Boukari sichergestellt. Malaika würde 2x die Woche duschen / baden gehen und täglich Zähne putzen. Die Mutter betont, wie wichtig ihr die Pflege und Reinlichkeit als Frau sei. Das Haarewaschen ist für Malaika aber aufgrund der langen Haare unangenehm, weshalb sie manchmal „Theater" mache.

Die Eltern gehen insgesamt wertschätzend und höflich miteinander um. Die Eltern berichten, dass Malaika ein gutes und gehorsames Kind sei und sie keine Probleme mit ihr hätten. Sie benötigen auch keine Beratung oder Unterstützung."""

    doc3 = KaimoDocument(
        case_id=case.id,
        title='Hausbesuch bei Familie Boukari',
        content=doc3_content,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 7),
        sort_order=2
    )
    db.session.add(doc3)

    # Document 4: Gespräch in der Dienststelle
    doc4_content = """Um sich auch noch einen persönlichen Eindruck vom Malaika verschaffen zu können, wurde die Familie erneut zu einem Gespräch in die Dienstelle eingeladen. Zum vereinbarten Termin erschien Herr Boukari zusammen mit Malaika. Frau Boukari habe aktuell Rückenschmerzen und sei daher nicht zum Termin mitgekommen.

Herr Boukari wirkte angespannt und zeigte sich verärgert. Er berichtete erneut, dass es keine Probleme zu Hause gebe und er nicht verstehe, warum das Jugendamt erneut ein Gespräch wolle. Er betonte immer wieder, dass er sich dafür nun extra von der Arbeit habe frei nehmen müsse. Er zeigte immer wieder auf seine Tochter mit den Worten: „Sie sehen doch, dass es ihr gut geht". Malaika wirkte schüchtern und mied den direkten Blickkontakt. Sie sah sich immer wieder im Raum um. Malaika wirkte äußerlich gesund und altersgemäß entwickelt. Ihre Haare waren frisch gewaschen und zu einem Zopf geflochten. Dem Wunsch, mit Malaika alleine zu sprechen, kam Herr Boukari nicht nach. Er würde sein Kind nicht alleine lassen. Auf die Frage, wie denn die letzten Tage zu Hause waren, erzählte Malaika schließlich sichtlich fröhlich von ihrem neuen Puppenhaus. Das habe ihr Vater ihr kürzlich geschenkt. Sie haben auch gemeinsam schon viel damit gespielt. Sie gab im Weiteren an, dass sie gerne zu Hause sei. Auf die Frage, wie es in der Schule gehen würde, antwortete Malaika nicht gleich, sondern sah ihren Vater an und dann auf ihre Füße. Herr Boukari erklärt, dass seine Tochter ab März den Hort nicht mehr besuchen werde. Der Hort hat nicht die erhoffte schulische Unterstützung gebracht. Malika muss nach aktuellem Stand voraussichtlich die 2. Klasse wiederholen. Den Rest des Schuljahres wird sich daher vor allem die Mutter intensiv um alle schulische Nachhilfe kümmern. Erneute Angebote der Beratung und Unterstützung wurden klar abgelehnt. Die Familie komme alleine gut zurecht."""

    doc4 = KaimoDocument(
        case_id=case.id,
        title='Gespräch in der Dienststelle',
        content=doc4_content,
        document_type='aktenvermerk',
        document_date=date(2023, 2, 16),
        sort_order=3
    )
    db.session.add(doc4)
    db.session.flush()

    # Get category IDs for assigning expected categories
    cat_grundversorgung = categories[0].id
    cat_entwicklung = categories[1].id
    cat_familiensituation = categories[2].id
    cat_eltern = categories[3].id

    # Create hints with expected_category_id matching prototype counts:
    # Grundversorgung: 8 hints, Entwicklung: 5 hints, Familiensituation: 6 hints, Eltern: 3 hints
    hints_data = [
        # Grundversorgung hints (8)
        {'content': 'Malaika hat oft stark verfilzte Haare und riecht streng.', 'doc_id': doc1.id, 'cat_id': cat_grundversorgung},
        {'content': 'Das Mädchen sieht schlecht gepflegt aus.', 'doc_id': doc1.id, 'cat_id': cat_grundversorgung},
        {'content': 'Malaika duscht/badet nur 2x die Woche.', 'doc_id': doc3.id, 'cat_id': cat_grundversorgung},
        {'content': 'Das Haarewaschen ist für Malaika unangenehm.', 'doc_id': doc3.id, 'cat_id': cat_grundversorgung},
        {'content': 'Malaika wirkte äußerlich gesund und altersgemäß entwickelt.', 'doc_id': doc4.id, 'cat_id': cat_grundversorgung},
        {'content': 'Ihre Haare waren frisch gewaschen und zu einem Zopf geflochten.', 'doc_id': doc4.id, 'cat_id': cat_grundversorgung},
        {'content': 'Spielzeug war wenig vorhanden im Kinderzimmer.', 'doc_id': doc3.id, 'cat_id': cat_grundversorgung},
        {'content': 'Malaika hat ihr eigenes Zimmer mit Bett und Kleiderschrank.', 'doc_id': doc3.id, 'cat_id': cat_grundversorgung},

        # Entwicklung hints (5)
        {'content': 'Malaika ist in ihrer Arbeitshaltung eher langsam und braucht viel Zeit.', 'doc_id': doc2.id, 'cat_id': cat_entwicklung},
        {'content': 'Malaika muss voraussichtlich die 2. Klasse wiederholen.', 'doc_id': doc4.id, 'cat_id': cat_entwicklung},
        {'content': 'Malaika hat unter dem Lockdown gelitten, da die Eltern schulisch kaum unterstützen konnten.', 'doc_id': doc2.id, 'cat_id': cat_entwicklung},
        {'content': 'Malaika wirkte schüchtern und mied den direkten Blickkontakt.', 'doc_id': doc4.id, 'cat_id': cat_entwicklung},
        {'content': 'Malaika erzählt vom „Schnipp-Schnapp-Spiel" mit dem Vater in Badewanne und Bett.', 'doc_id': doc1.id, 'cat_id': cat_entwicklung},

        # Familiensituation hints (6)
        {'content': 'Die Familie bewohnt eine 2-Zimmer-Wohnung.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},
        {'content': 'Die Wohnung ist insgesamt sehr sauber und aufgeräumt.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},
        {'content': 'Herr Boukari arbeitet als Koch von 14:00 bis 23:00 Uhr.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},
        {'content': 'Frau Boukari arbeitet an zwei Tagen als Reinigungskraft.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},
        {'content': 'Die Eltern gehen wertschätzend und höflich miteinander um.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},
        {'content': 'Seit Corona haben sie die Kontakte größtmöglich reduziert.', 'doc_id': doc3.id, 'cat_id': cat_familiensituation},

        # Eltern hints (3)
        {'content': 'Die Mutter ist in der Erziehung eher inkonsequent und kann sich nicht durchsetzen.', 'doc_id': doc2.id, 'cat_id': cat_eltern},
        {'content': 'Die Eltern drohen Malaika, wenn sie sich ihnen widersetzt.', 'doc_id': doc1.id, 'cat_id': cat_eltern},
        {'content': 'Herr Boukari lehnte es ab, dass mit Malaika alleine gesprochen wird.', 'doc_id': doc4.id, 'cat_id': cat_eltern},
    ]

    for i, hint_data in enumerate(hints_data):
        hint = KaimoHint(
            case_id=case.id,
            document_id=hint_data['doc_id'],
            content=hint_data['content'],
            expected_category_id=hint_data['cat_id'],
            sort_order=i
        )
        db.session.add(hint)

    print(f"Created Malaika case with {len(hints_data)} hints and 4 documents")
    return case


def main():
    with app.app_context():
        print("Starting KAIMO Malaika seed...")

        # Create categories first
        categories = seed_categories()

        # Create Malaika case
        case = seed_malaika_case(categories)

        # Commit all changes
        db.session.commit()

        print("\n✅ KAIMO Malaika case seeded successfully!")
        print(f"   Case ID: {case.id}")
        print(f"   Status: {case.status}")
        print(f"   Documents: 4")
        print(f"   Hints: 22")
        print(f"   Categories: 4")


if __name__ == '__main__':
    main()
