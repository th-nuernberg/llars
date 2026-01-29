"""
LLM-as-Judge Demo Data Seeder

Creates demo data for testing the multi-dimensional rating system.
Items are LLM-generated responses that can be evaluated on:
- Kohärenz (Coherence)
- Flüssigkeit (Fluency)
- Relevanz (Relevance)
- Konsistenz (Consistency)
"""

from datetime import datetime, timedelta


# Demo LLM responses for evaluation
# Each item represents an LLM response to a user question
LLM_JUDGE_DEMO_DATA = [
    {
        "subject": "Was ist maschinelles Lernen?",
        "response": """Maschinelles Lernen ist ein Teilbereich der künstlichen Intelligenz, der es Computersystemen ermöglicht, aus Erfahrungen zu lernen und sich zu verbessern, ohne explizit programmiert zu werden.

Der Grundgedanke ist einfach: Anstatt einem Computer genaue Regeln vorzugeben, füttert man ihn mit Daten und lässt ihn selbst Muster erkennen. Es ist wie beim Lernen einer Sprache - man zeigt dem System viele Beispiele, und es lernt die zugrunde liegenden Regeln selbst.

Es gibt drei Hauptkategorien:
1. **Überwachtes Lernen**: Das System lernt aus markierten Beispielen (z.B. Bilder mit Labels)
2. **Unüberwachtes Lernen**: Das System findet selbstständig Strukturen in unmarkierten Daten
3. **Bestärkendes Lernen**: Das System lernt durch Belohnungen und Bestrafungen

Praktische Anwendungen finden sich überall: Sprachassistenten wie Siri, Empfehlungssysteme bei Netflix, Spam-Filter in E-Mails oder die automatische Übersetzung von Texten.""",
        "quality": "high"
    },
    {
        "subject": "Wie funktioniert Photosynthese?",
        "response": """Photosynthese Prozess wichtig Pflanzen. Sonne Licht kommt Blätter grün Chlorophyll. Wasser Wurzeln aufnehmen Boden.

CO2 Luft Blätter Stomata. Dann passiert Reaktion. Glucose entsteht Zucker Energie. Sauerstoff Nebenprodukt freigesetzt.

6CO2 + 6H2O → C6H12O6 + 6O2

Formel zeigt was passiert. Pflanzen brauchen für Leben. Menschen atmen Sauerstoff ein Pflanzen produzieren.

Wichtig Ökosystem. Ohne Photosynthese kein Leben Erde möglich.""",
        "quality": "low"
    },
    {
        "subject": "Erkläre die Relativitätstheorie",
        "response": """Die Relativitätstheorie von Albert Einstein revolutionierte unser Verständnis von Raum, Zeit und Gravitation.

**Spezielle Relativitätstheorie (1905)**
Diese Theorie gilt für gleichförmig bewegte Bezugssysteme. Zwei zentrale Erkenntnisse:
- Die Lichtgeschwindigkeit ist konstant (ca. 300.000 km/s) und für alle Beobachter gleich
- Zeit und Raum sind relativ - sie hängen vom Bewegungszustand des Beobachters ab

Ein faszinierender Effekt: Je schneller sich etwas bewegt, desto langsamer vergeht für es die Zeit (Zeitdilatation). Bei Lichtgeschwindigkeit würde die Zeit theoretisch stillstehen.

**Allgemeine Relativitätstheorie (1915)**
Hier erweitert Einstein die Theorie auf beschleunigte Systeme und erklärt Gravitation neu: Masse krümmt den Raum um sich herum. Objekte fallen nicht, weil eine Kraft sie zieht, sondern weil sie der Krümmung des Raumes folgen.

Dies wurde mehrfach bestätigt, etwa durch GPS-Satelliten, die relativistische Korrekturen benötigen, um präzise zu funktionieren.""",
        "quality": "high"
    },
    {
        "subject": "Was sind die Vorteile von Solarenergie?",
        "response": """Solarenergie hat viele Vorteile, die sie zu einer attraktiven Alternative machen.

Erstens ist Solarenergie erneuerbar. Die Sonne scheint jeden Tag und wird noch Milliarden Jahre scheinen. Im Gegensatz zu fossilen Brennstoffen, die endlich sind.

Zweitens ist sie umweltfreundlich. Bei der Stromerzeugung entstehen keine direkten CO2-Emissionen. Das hilft beim Kampf gegen den Klimawandel.

Drittens sind die Betriebskosten niedrig. Nach der Installation sind die laufenden Kosten minimal. Sonnenlicht ist kostenlos verfügbar.

Allerdings gibt es auch Nachteile: Die anfänglichen Installationskosten sind hoch. Außerdem ist die Energieerzeugung wetterabhängig und nachts nicht möglich. Speicherlösungen sind noch teuer.

Trotzdem wächst der Markt stark. Die Preise für Solarmodule sind in den letzten 10 Jahren um über 80% gefallen. Viele Länder fördern den Ausbau durch Subventionen.""",
        "quality": "medium"
    },
    {
        "subject": "Wie backe ich einen Schokoladenkuchen?",
        "response": """Zunächst möchte ich auf die Geschichte der Quantenmechanik eingehen. Werner Heisenberg entwickelte 1927 die Unschärferelation.

Für den Kuchen brauchen Sie 200g Mehl. Die Unschärferelation besagt, dass man Ort und Impuls nicht gleichzeitig messen kann.

Mischen Sie das Mehl mit 150g Zucker. Einstein war skeptisch gegenüber der Quantenmechanik und sagte: "Gott würfelt nicht."

Nun geben Sie 100g geschmolzene Butter hinzu. Die Schrödinger-Gleichung beschreibt die zeitliche Entwicklung eines Quantensystems.

Backen Sie den Kuchen bei 180°C für 30 Minuten. Schrödingers Katze ist ein Gedankenexperiment, das die Superposition veranschaulicht.

Der Kuchen sollte nun fertig sein. Quantencomputer nutzen diese Prinzipien für Berechnungen.""",
        "quality": "low"
    },
    {
        "subject": "Was ist künstliche Intelligenz?",
        "response": """Künstliche Intelligenz (KI) bezeichnet die Fähigkeit von Computersystemen, Aufgaben zu erledigen, die normalerweise menschliche Intelligenz erfordern.

Die Entwicklung der KI begann in den 1950er Jahren. Alan Turing stellte die berühmte Frage: "Können Maschinen denken?" Der Turing-Test wurde zum Maßstab für maschinelle Intelligenz.

Heute unterscheiden wir verschiedene Typen:

**Schwache KI (Narrow AI)**
- Spezialisiert auf bestimmte Aufgaben
- Beispiele: Sprachassistenten, Schachcomputer, Bilderkennunng
- Bereits weit verbreitet im Alltag

**Starke KI (General AI)**
- Könnte alle intellektuellen Aufgaben eines Menschen bewältigen
- Existiert noch nicht
- Intensives Forschungsgebiet

Ethische Fragen werden zunehmend wichtig: Wie gehen wir mit Vorurteilen in KI-Systemen um? Wer ist verantwortlich, wenn eine KI Fehler macht? Diese Diskussionen sind zentral für die verantwortungsvolle Entwicklung der Technologie.""",
        "quality": "high"
    },
    {
        "subject": "Warum ist der Himmel blau?",
        "response": """Der Himmel erscheint blau aufgrund eines Phänomens namens Rayleigh-Streuung.

Sonnenlicht besteht aus verschiedenen Wellenlängen. Wenn es in die Atmosphäre eintritt, trifft es auf Gasmoleküle wie Stickstoff und Sauerstoff. Diese Moleküle streuen kürzere Wellenlängen (blau und violett) stärker als längere (rot und orange).

Violettes Licht wird zwar noch stärker gestreut, aber unsere Augen sind empfindlicher für Blau. Außerdem absorbiert die obere Atmosphäre einen Teil des violetten Lichts. Deshalb sehen wir den Himmel blau und nicht violett.

Bei Sonnenaufgang und -untergang ist der Weg des Lichts durch die Atmosphäre länger. Das meiste blaue Licht wird weggestreut, bevor es uns erreicht. Nur die längerwelligen roten und orangen Anteile kommen durch - daher die spektakulären Farben.

An wolkenlosen Tagen erscheint der Himmel tiefblau. Mit mehr Staub oder Feuchtigkeit wird er blasser, weil diese größeren Partikel alle Wellenlängen gleichmäßiger streuen.""",
        "quality": "high"
    },
    {
        "subject": "Wie funktioniert das Internet?",
        "response": """Internet funktioniert Computer verbunden Netzwerk.

Daten gesendet Pakete kleine Teile. Router leiten weiter Ziel. TCP/IP Protokoll wichtig.

Server speichern Webseiten. Browser lädt herunter. HTTP Anfrage Antwort Schema.

DNS übersetzt Domainnamen IP-Adressen. Zum Beispiel google.com wird 142.250.185.14.

Glasfaserkabel schnell Übertragung. WiFi auch möglich kabellos. Mobilfunk 4G 5G.

Sicherheit wichtig Verschlüsselung HTTPS. Firewall schützt vor Angriffe. VPN zusätzliche Privatsphäre.""",
        "quality": "low"
    },
    {
        "subject": "Was ist Demokratie?",
        "response": """Demokratie ist eine Regierungsform, in der die Staatsgewalt vom Volk ausgeht. Der Begriff stammt aus dem Griechischen: "demos" (Volk) und "kratein" (herrschen).

**Kernprinzipien:**
- Volkssouveränität: Alle Macht geht vom Volk aus
- Freie und faire Wahlen in regelmäßigen Abständen
- Gewaltenteilung zwischen Legislative, Exekutive und Judikative
- Schutz von Grundrechten und Minderheiten
- Presse- und Meinungsfreiheit

**Formen der Demokratie:**

*Direkte Demokratie*: Bürger entscheiden selbst über Gesetze (z.B. Schweizer Volksabstimmungen)

*Repräsentative Demokratie*: Bürger wählen Vertreter, die in ihrem Namen entscheiden (z.B. Deutschland)

**Herausforderungen heute:**
Die Demokratie steht vor neuen Herausforderungen: Desinformation in sozialen Medien, sinkende Wahlbeteiligung und populistische Bewegungen. Dennoch bleibt sie das erfolgreichste Modell für gesellschaftliche Organisation - Winston Churchill nannte sie "die schlechteste Regierungsform, abgesehen von allen anderen".""",
        "quality": "high"
    },
    {
        "subject": "Wie kann ich besser schlafen?",
        "response": """Guter Schlaf ist essentiell für Gesundheit und Wohlbefinden. Hier sind bewährte Strategien für besseren Schlaf:

**Schlafhygiene verbessern:**
1. Regelmäßige Schlafzeiten - auch am Wochenende
2. Das Schlafzimmer nur zum Schlafen nutzen
3. Kühle Temperatur (16-18°C) im Schlafraum
4. Verdunkelung und Ruhe gewährleisten

**Abendrituale:**
- Bildschirme mindestens 1 Stunde vor dem Schlafen meiden
- Entspannungstechniken wie Meditation oder leichtes Yoga
- Ein warmes Bad kann die Körpertemperatur regulieren
- Leichte Lektüre statt aufregende Inhalte

**Tagsüber beachten:**
- Koffein nach 14 Uhr vermeiden
- Regelmäßige Bewegung, aber nicht kurz vor dem Schlafen
- Kurze Power-Naps (max. 20 Min.) wenn nötig, nicht zu spät

**Ernährung:**
- Keine schweren Mahlzeiten abends
- Alkohol reduzieren - er stört den Tiefschlaf
- Kamillentee oder warme Milch können beruhigend wirken

Bei anhaltenden Problemen sollten Sie einen Arzt konsultieren, um Schlafstörungen auszuschließen.""",
        "quality": "high"
    },
    {
        "subject": "Erkläre den Klimawandel",
        "response": """Klimawandel bezieht sich auf langfristige Änderungen der globalen Temperaturen und Wettermuster.

Der aktuelle menschengemachte Klimawandel wird hauptsächlich durch Treibhausgase verursacht. Diese entstehen bei der Verbrennung fossiler Brennstoffe wie Kohle, Öl und Gas. Die Konzentration von CO2 in der Atmosphäre ist seit der Industrialisierung um etwa 50% gestiegen.

Der Treibhauseffekt funktioniert so: Sonnenstrahlung erwärmt die Erde. Die Erde strahlt Wärme ab. Treibhausgase in der Atmosphäre halten einen Teil dieser Wärme zurück - wie das Glas eines Gewächshauses.

Folgen sind bereits sichtbar:
• Steigende Meeresspiegel durch schmelzende Gletscher
• Häufigere Extremwetter wie Hitzewellen und Stürme
• Verschiebung von Jahreszeiten und Lebensräumen
• Ozeanversauerung bedroht Meeresökosysteme

Das Pariser Abkommen von 2015 setzt das Ziel, die Erwärmung auf 1,5°C zu begrenzen. Dafür müssen wir Emissionen drastisch senken und auf erneuerbare Energien umsteigen.""",
        "quality": "medium"
    },
    {
        "subject": "Was sind Schwarze Löcher?",
        "response": """Schwarze Löcher sind faszinierende kosmische Objekte, deren Gravitationskraft so stark ist, dass nicht einmal Licht ihnen entkommen kann.

**Entstehung:**
Wenn ein massereicher Stern (mindestens 20-25 Sonnenmassen) seinen Brennstoff verbraucht hat, kollabiert sein Kern unter der eigenen Schwerkraft. Die gesamte Masse wird in einem unendlich kleinen Punkt konzentriert - der Singularität.

**Aufbau:**
- **Singularität**: Der zentrale Punkt mit unendlicher Dichte
- **Ereignishorizont**: Die Grenze, ab der nichts mehr entkommen kann
- **Akkretionsscheibe**: Spiralförmige Materiescheibe um das Schwarze Loch

**Arten:**
1. Stellare Schwarze Löcher (einige Sonnenmassen)
2. Supermassive Schwarze Löcher (Millionen bis Milliarden Sonnenmassen, in Galaxienzentren)
3. Intermediäre Schwarze Löcher (dazwischen, noch wenig erforscht)

**Nachweis:**
Obwohl wir sie nicht direkt sehen können, verraten sie sich durch:
- Gravitationseffekte auf nahe Sterne
- Röntgenstrahlung der Akkretionsscheibe
- Gravitationswellen bei Kollisionen

2019 gelang mit dem Event Horizon Telescope das erste "Foto" eines Schwarzen Lochs im Zentrum der Galaxie M87.""",
        "quality": "high"
    }
]


def seed_llm_judge_demo_scenario(db):
    """
    Create a new LLM-as-Judge demo scenario with text content for evaluation.

    Args:
        db: SQLAlchemy database instance
    """
    from db.models import (
        User, EvaluationItem, Message, RatingScenarios,
        ScenarioUsers, ScenarioItems, ScenarioItemDistribution,
        ScenarioRoles, FeatureFunctionType
    )

    print("\n" + "=" * 60)
    print("Seeding LLM-as-Judge Demo Scenario...")
    print("=" * 60)

    # Get users
    evaluator = User.query.filter_by(username='evaluator').first()
    researcher = User.query.filter_by(username='researcher').first()
    admin = User.query.filter_by(username='admin').first()

    if not evaluator or not researcher:
        print("  ERROR: Required users not found")
        return

    # Get rating function type
    rating_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_type:
        print("  ERROR: Rating function type not found")
        return

    # Check if scenario already exists
    existing = RatingScenarios.query.filter_by(
        scenario_name='LLM-as-Judge Demo'
    ).first()

    if existing:
        print("  LLM-as-Judge Demo scenario already exists")
        # Update config to ensure it's multi-dimensional
        existing.config_json = _get_llm_judge_config()
        db.session.commit()
        print("  Updated config to multi-dimensional")
        return existing

    # Create evaluation items with LLM response content
    # Using chat_ids starting at 20000 to avoid conflicts with other demo data
    items = []
    for i, data in enumerate(LLM_JUDGE_DEMO_DATA):
        chat_id = 20000 + i

        # Check if item already exists
        existing_item = EvaluationItem.query.filter_by(
            chat_id=chat_id,
            institut_id=1,
            function_type_id=rating_type.function_type_id
        ).first()

        if existing_item:
            items.append(existing_item)
            print(f"  Item exists: {data['subject'][:40]}...")
            continue

        # Create EvaluationItem
        item = EvaluationItem(
            chat_id=chat_id,
            institut_id=1,
            subject=data['subject'],
            sender='LLM',
            function_type_id=rating_type.function_type_id
        )
        db.session.add(item)
        db.session.flush()

        # Create a single message with the response content
        message = Message(
            item_id=item.item_id,
            sender='LLM-Antwort',
            content=data['response'],
            timestamp=datetime.now() - timedelta(days=7-i, hours=i),
            generated_by='GPT-4'
        )
        db.session.add(message)
        items.append(item)

        print(f"  Created item: {data['subject'][:40]}...")

    db.session.flush()

    # Create scenario
    scenario = RatingScenarios(
        scenario_name='LLM-as-Judge Demo',
        function_type_id=rating_type.function_type_id,
        begin=datetime.now() - timedelta(days=7),
        end=datetime.now() + timedelta(days=60),
        timestamp=datetime.now(),
        config_json=_get_llm_judge_config()
    )
    db.session.add(scenario)
    db.session.flush()

    # Add users to scenario
    # EVALUATOR can interact (rate/evaluate), VIEWER is read-only
    for user, role in [
        (evaluator, ScenarioRoles.VIEWER),
        (researcher, ScenarioRoles.EVALUATOR)
    ]:
        scenario_user = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            role=role
        )
        db.session.add(scenario_user)

    if admin:
        admin_scenario_user = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=admin.id,
            role=ScenarioRoles.VIEWER
        )
        db.session.add(admin_scenario_user)

    db.session.flush()

    # Add items to scenario
    scenario_items = []
    for item in items:
        scenario_item = ScenarioItems(
            scenario_id=scenario.id,
            item_id=item.item_id
        )
        db.session.add(scenario_item)
        scenario_items.append(scenario_item)

    db.session.flush()

    # Create distributions for all users
    evaluator_user = ScenarioUsers.query.filter_by(
        scenario_id=scenario.id,
        role=ScenarioRoles.EVALUATOR
    ).first()

    if evaluator_user:
        for scenario_item in scenario_items:
            dist = ScenarioItemDistribution(
                scenario_id=scenario.id,
                scenario_user_id=evaluator_user.id,
                scenario_item_id=scenario_item.id
            )
            db.session.add(dist)

    db.session.commit()

    print(f"\n  Created LLM-as-Judge Demo with {len(items)} items")
    print(f"  Scenario ID: {scenario.id}")
    print("=" * 60)

    return scenario


def _get_llm_judge_config():
    """Get the multi-dimensional config for LLM-as-Judge evaluation."""
    return {
        "evaluation": "rating",
        "type": "multi-dimensional",
        "enable_llm_evaluation": True,
        "llm_evaluators": [
            "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
            "mistralai/Magistral-Small-2509"
        ],
        "min": 1,
        "max": 5,
        "step": 1,
        "showOverallScore": True,
        "allowFeedback": True,
        "dimensions": [
            {
                "id": "coherence",
                "name": {"de": "Kohärenz", "en": "Coherence"},
                "description": {
                    "de": "Ist der Text logisch aufgebaut? Sind die Ideen klar miteinander verbunden? Folgt die Argumentation einem roten Faden?",
                    "en": "Is the text logically structured? Are ideas clearly connected? Does the argument follow a clear thread?"
                },
                "weight": 0.25
            },
            {
                "id": "fluency",
                "name": {"de": "Flüssigkeit", "en": "Fluency"},
                "description": {
                    "de": "Ist der Text grammatikalisch korrekt? Liest er sich flüssig und natürlich? Ist die Sprache klar und präzise?",
                    "en": "Is the text grammatically correct? Does it read smoothly and naturally? Is the language clear and precise?"
                },
                "weight": 0.25
            },
            {
                "id": "relevance",
                "name": {"de": "Relevanz", "en": "Relevance"},
                "description": {
                    "de": "Beantwortet der Text die gestellte Frage? Werden die wichtigsten Aspekte behandelt? Ist der Inhalt nützlich und informativ?",
                    "en": "Does the text answer the question asked? Are the most important aspects covered? Is the content useful and informative?"
                },
                "weight": 0.25
            },
            {
                "id": "consistency",
                "name": {"de": "Konsistenz", "en": "Consistency"},
                "description": {
                    "de": "Widersprechen sich Aussagen im Text? Sind die Fakten korrekt? Ist die Information zuverlässig und widerspruchsfrei?",
                    "en": "Do statements in the text contradict each other? Are the facts correct? Is the information reliable and consistent?"
                },
                "weight": 0.25
            }
        ],
        "labels": {
            "1": {"de": "Sehr schlecht", "en": "Very poor"},
            "2": {"de": "Schlecht", "en": "Poor"},
            "3": {"de": "Akzeptabel", "en": "Acceptable"},
            "4": {"de": "Gut", "en": "Good"},
            "5": {"de": "Sehr gut", "en": "Very good"}
        }
    }
