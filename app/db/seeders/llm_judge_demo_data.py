"""
LLM-as-Judge Demo Data Seeder

Creates demo data for testing the multi-dimensional rating system.
Items are responses from different sources (Human expert, GPT-4, Mistral)
that can be evaluated on:
- Kohärenz (Coherence)
- Flüssigkeit (Fluency)
- Relevanz (Relevance)
- Konsistenz (Consistency)

Generator distribution (20 items):
  Mensch (Human expert):   7 items  (4 high, 2 medium, 1 low)
  GPT-4:                   7 items  (3 high, 2 medium, 2 low)
  Mistral-Small-3.2:       6 items  (2 high, 2 medium, 2 low)
"""

from datetime import datetime, timedelta


# Demo responses for evaluation.
# Each item has a `generator` field used as Message.generated_by
# so the provenance analysis can compare quality across sources.
LLM_JUDGE_DEMO_DATA = [
    # =========================================================================
    # MENSCH (Human expert) — 7 items
    # =========================================================================
    {
        "subject": "Was ist maschinelles Lernen?",
        "generator": "Mensch",
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
        "subject": "Was ist Demokratie?",
        "generator": "Mensch",
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
        "generator": "Mensch",
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
        "subject": "Wie funktioniert ein Elektromotor?",
        "generator": "Mensch",
        "response": """Ein Elektromotor wandelt elektrische Energie in mechanische Bewegung um. Das Grundprinzip beruht auf der Wechselwirkung zwischen Magnetfeldern und stromdurchflossenen Leitern.

**Das physikalische Prinzip:**
Wenn Strom durch einen Leiter fließt, der sich in einem Magnetfeld befindet, wirkt auf ihn eine Kraft (Lorentzkraft). Diese Kraft steht senkrecht sowohl zur Stromrichtung als auch zum Magnetfeld. Bei einem rotierenden Aufbau entsteht daraus ein Drehmoment.

**Aufbau eines einfachen Gleichstrommotors:**
- **Stator**: Der feststehende Teil mit Permanentmagneten oder Elektromagneten
- **Rotor (Anker)**: Die drehbare Spule im Inneren
- **Kommutator**: Schaltet die Stromrichtung um, damit die Drehung kontinuierlich bleibt
- **Bürsten**: Übertragen den Strom auf den rotierenden Kommutator

**Motortypen im Überblick:**
1. *Gleichstrommotor* — einfach regelbar, z.B. in Spielzeug und Elektrowerkzeugen
2. *Wechselstrommotor (Asynchron)* — robust und wartungsarm, Standard in der Industrie
3. *Bürstenloser Gleichstrommotor (BLDC)* — effizient und langlebig, in Drohnen und E-Bikes

Moderne Elektroautos verwenden meist Permanentmagnet-Synchronmotoren, die Wirkungsgrade über 95 % erreichen.""",
        "quality": "high"
    },
    {
        "subject": "Was ist der Unterschied zwischen Wetter und Klima?",
        "generator": "Mensch",
        "response": """Wetter und Klima werden oft verwechselt, beschreiben aber unterschiedliche Zeitskalen atmosphärischer Zustände.

**Wetter** ist der kurzfristige Zustand der Atmosphäre an einem bestimmten Ort. Es umfasst Temperatur, Niederschlag, Wind und Bewölkung über Stunden bis wenige Tage. Wetter kann sich schnell ändern.

**Klima** hingegen beschreibt den statistischen Durchschnitt des Wetters über mindestens 30 Jahre in einer Region. Es zeigt langfristige Muster und Trends.

Ein einfaches Bild: Wetter ist das, was man beim Blick aus dem Fenster sieht. Klima ist das, was man erwartet, wenn man den Koffer für eine Reise packt.

Die Unterscheidung ist wichtig für die Klimadebatte. Einzelne kalte Winter widerlegen den Klimawandel nicht — sie sind Wetterereignisse. Der Klimawandel zeigt sich in Jahrzehnte-Trends: steigende Durchschnittstemperaturen, veränderte Niederschlagsmuster und häufigere Extremereignisse.""",
        "quality": "medium"
    },
    {
        "subject": "Was sind die Grundlagen gesunder Ernährung?",
        "generator": "Mensch",
        "response": """Gesunde Ernährung basiert auf einigen grundlegenden Prinzipien. Man sollte abwechslungsreich essen, viel Gemüse und Obst, Vollkornprodukte und ausreichend Wasser.

Proteine sind wichtig für Muskeln. Kohlenhydrate liefern Energie. Fette braucht der Körper auch, besonders ungesättigte. Vitamine und Mineralstoffe sind essentiell.

Man sagt fünf Portionen Obst und Gemüse am Tag. Zucker und stark verarbeitete Lebensmittel sollte man reduzieren. Auf ausreichend Ballaststoffe achten.

Jeder Mensch ist anders. Was für den einen gut ist, muss nicht für jeden passen. Bei Unsicherheiten am besten einen Ernährungsberater fragen.""",
        "quality": "medium"
    },
    {
        "subject": "Erkläre das Konzept der Inflation",
        "generator": "Mensch",
        "response": """Inflation ist wenn Preise steigen. Geld weniger wert wird. Passiert überall.

Die Zentralbank, also EZB bei uns, die machen die Zinsen. Wenn Zinsen niedrig dann mehr Geld im Umlauf und Preise steigen. Wenn hoch dann weniger. Ziel sind 2% pro Jahr ungefähr.

Es gibt verschiedene Gründe: Nachfrage zu hoch, Angebot zu niedrig, oder einfach zu viel Geld gedruckt. Rohstoffpreise spielen auch Rolle. Energie teurer dann alles teurer.

Die Leute merken das beim Einkaufen. Brot kostet mehr, Miete steigt. Löhne steigen aber nicht immer gleich schnell mit. Deswegen können sich manche Leute weniger leisten obwohl sie gleich viel verdienen.""",
        "quality": "low"
    },
    # =========================================================================
    # GPT-4 — 7 items
    # =========================================================================
    {
        "subject": "Erkläre die Relativitätstheorie",
        "generator": "GPT-4",
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
        "subject": "Was ist künstliche Intelligenz?",
        "generator": "GPT-4",
        "response": """Künstliche Intelligenz (KI) bezeichnet die Fähigkeit von Computersystemen, Aufgaben zu erledigen, die normalerweise menschliche Intelligenz erfordern.

Die Entwicklung der KI begann in den 1950er Jahren. Alan Turing stellte die berühmte Frage: "Können Maschinen denken?" Der Turing-Test wurde zum Maßstab für maschinelle Intelligenz.

Heute unterscheiden wir verschiedene Typen:

**Schwache KI (Narrow AI)**
- Spezialisiert auf bestimmte Aufgaben
- Beispiele: Sprachassistenten, Schachcomputer, Bilderkennung
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
        "generator": "GPT-4",
        "response": """Der Himmel erscheint blau aufgrund eines Phänomens namens Rayleigh-Streuung.

Sonnenlicht besteht aus verschiedenen Wellenlängen. Wenn es in die Atmosphäre eintritt, trifft es auf Gasmoleküle wie Stickstoff und Sauerstoff. Diese Moleküle streuen kürzere Wellenlängen (blau und violett) stärker als längere (rot und orange).

Violettes Licht wird zwar noch stärker gestreut, aber unsere Augen sind empfindlicher für Blau. Außerdem absorbiert die obere Atmosphäre einen Teil des violetten Lichts. Deshalb sehen wir den Himmel blau und nicht violett.

Bei Sonnenaufgang und -untergang ist der Weg des Lichts durch die Atmosphäre länger. Das meiste blaue Licht wird weggestreut, bevor es uns erreicht. Nur die längerwelligen roten und orangen Anteile kommen durch - daher die spektakulären Farben.

An wolkenlosen Tagen erscheint der Himmel tiefblau. Mit mehr Staub oder Feuchtigkeit wird er blasser, weil diese größeren Partikel alle Wellenlängen gleichmäßiger streuen.""",
        "quality": "high"
    },
    {
        "subject": "Was sind die Vorteile von Solarenergie?",
        "generator": "GPT-4",
        "response": """Solarenergie hat viele Vorteile, die sie zu einer attraktiven Alternative machen.

Erstens ist Solarenergie erneuerbar. Die Sonne scheint jeden Tag und wird noch Milliarden Jahre scheinen. Im Gegensatz zu fossilen Brennstoffen, die endlich sind.

Zweitens ist sie umweltfreundlich. Bei der Stromerzeugung entstehen keine direkten CO2-Emissionen. Das hilft beim Kampf gegen den Klimawandel.

Drittens sind die Betriebskosten niedrig. Nach der Installation sind die laufenden Kosten minimal. Sonnenlicht ist kostenlos verfügbar.

Allerdings gibt es auch Nachteile: Die anfänglichen Installationskosten sind hoch. Außerdem ist die Energieerzeugung wetterabhängig und nachts nicht möglich. Speicherlösungen sind noch teuer.

Trotzdem wächst der Markt stark. Die Preise für Solarmodule sind in den letzten 10 Jahren um über 80% gefallen. Viele Länder fördern den Ausbau durch Subventionen.""",
        "quality": "medium"
    },
    {
        "subject": "Erkläre den Klimawandel",
        "generator": "GPT-4",
        "response": """Klimawandel bezieht sich auf langfristige Änderungen der globalen Temperaturen und Wettermuster.

Der aktuelle menschengemachte Klimawandel wird hauptsächlich durch Treibhausgase verursacht. Diese entstehen bei der Verbrennung fossiler Brennstoffe wie Kohle, Öl und Gas. Die Konzentration von CO2 in der Atmosphäre ist seit der Industrialisierung um etwa 50% gestiegen.

Der Treibhauseffekt funktioniert so: Sonnenstrahlung erwärmt die Erde. Die Erde strahlt Wärme ab. Treibhausgase in der Atmosphäre halten einen Teil dieser Wärme zurück - wie das Glas eines Gewächshauses.

Folgen sind bereits sichtbar:
- Steigende Meeresspiegel durch schmelzende Gletscher
- Häufigere Extremwetter wie Hitzewellen und Stürme
- Verschiebung von Jahreszeiten und Lebensräumen
- Ozeanversauerung bedroht Meeresökosysteme

Das Pariser Abkommen von 2015 setzt das Ziel, die Erwärmung auf 1,5°C zu begrenzen. Dafür müssen wir Emissionen drastisch senken und auf erneuerbare Energien umsteigen.""",
        "quality": "medium"
    },
    {
        "subject": "Wie funktioniert Photosynthese?",
        "generator": "GPT-4",
        "response": """Photosynthese Prozess wichtig Pflanzen. Sonne Licht kommt Blätter grün Chlorophyll. Wasser Wurzeln aufnehmen Boden.

CO2 Luft Blätter Stomata. Dann passiert Reaktion. Glucose entsteht Zucker Energie. Sauerstoff Nebenprodukt freigesetzt.

6CO2 + 6H2O → C6H12O6 + 6O2

Formel zeigt was passiert. Pflanzen brauchen für Leben. Menschen atmen Sauerstoff ein Pflanzen produzieren.

Wichtig Ökosystem. Ohne Photosynthese kein Leben Erde möglich.""",
        "quality": "low"
    },
    {
        "subject": "Wie backe ich einen Schokoladenkuchen?",
        "generator": "GPT-4",
        "response": """Zunächst möchte ich auf die Geschichte der Quantenmechanik eingehen. Werner Heisenberg entwickelte 1927 die Unschärferelation.

Für den Kuchen brauchen Sie 200g Mehl. Die Unschärferelation besagt, dass man Ort und Impuls nicht gleichzeitig messen kann.

Mischen Sie das Mehl mit 150g Zucker. Einstein war skeptisch gegenüber der Quantenmechanik und sagte: "Gott würfelt nicht."

Nun geben Sie 100g geschmolzene Butter hinzu. Die Schrödinger-Gleichung beschreibt die zeitliche Entwicklung eines Quantensystems.

Backen Sie den Kuchen bei 180°C für 30 Minuten. Schrödingers Katze ist ein Gedankenexperiment, das die Superposition veranschaulicht.

Der Kuchen sollte nun fertig sein. Quantencomputer nutzen diese Prinzipien für Berechnungen.""",
        "quality": "low"
    },
    # =========================================================================
    # Mistral-Small-3.2 — 6 items
    # =========================================================================
    {
        "subject": "Was sind Schwarze Löcher?",
        "generator": "Mistral-Small-3.2",
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
    },
    {
        "subject": "Wie funktioniert das Immunsystem?",
        "generator": "Mistral-Small-3.2",
        "response": """Das Immunsystem ist das körpereigene Abwehrsystem gegen Krankheitserreger wie Bakterien, Viren und Parasiten. Es besteht aus zwei Hauptkomponenten, die zusammenarbeiten.

**Angeborenes Immunsystem (unspezifisch):**
Die erste Verteidigungslinie reagiert sofort, aber unspezifisch:
- **Physische Barrieren**: Haut und Schleimhäute verhindern das Eindringen von Erregern
- **Fresszellen (Makrophagen)**: Verschlingen und verdauen Eindringlinge
- **Entzündungsreaktion**: Erhöht Durchblutung, bringt Immunzellen zum Infektionsort
- **Fieber**: Erhöhte Temperatur hemmt die Vermehrung vieler Erreger

**Erworbenes Immunsystem (spezifisch):**
Reagiert langsamer, aber gezielt und merkt sich Erreger:
- **T-Zellen**: Erkennen infizierte Körperzellen und zerstören sie
- **B-Zellen**: Produzieren Antikörper, die Erreger markieren
- **Gedächtniszellen**: Speichern Informationen über vergangene Infektionen — die Grundlage für Impfungen

**Impfungen** trainieren das erworbene Immunsystem mit harmlosen Teilen eines Erregers, sodass es bei einer echten Infektion schneller reagieren kann.

Ein gesundes Immunsystem braucht ausreichend Schlaf, Bewegung, eine ausgewogene Ernährung und wenig chronischen Stress.""",
        "quality": "high"
    },
    {
        "subject": "Was ist Blockchain-Technologie?",
        "generator": "Mistral-Small-3.2",
        "response": """Blockchain ist eine Technologie zur dezentralen Datenspeicherung. Die Daten werden in Blöcken gespeichert, die miteinander verkettet sind.

Jeder Block enthält Transaktionsdaten, einen Zeitstempel und einen Hash des vorherigen Blocks. Das macht die Kette fälschungssicher — ändert man einen Block, stimmen alle nachfolgenden Hashes nicht mehr.

Das Netzwerk wird von vielen Computern (Nodes) betrieben. Es gibt keinen zentralen Server. Neue Blöcke werden durch einen Konsensmechanismus validiert, beispielsweise Proof-of-Work bei Bitcoin oder Proof-of-Stake bei Ethereum.

Die bekannteste Anwendung sind Kryptowährungen. Aber die Technologie hat auch Potenzial für Lieferketten-Tracking, digitale Identitäten und Smart Contracts.

Nachteile sind der hohe Energieverbrauch bei Proof-of-Work und die begrenzte Transaktionsgeschwindigkeit. Neuere Ansätze versuchen, diese Probleme zu lösen.""",
        "quality": "medium"
    },
    {
        "subject": "Erkläre die Evolutionstheorie",
        "generator": "Mistral-Small-3.2",
        "response": """Evolution ist der Prozess, durch den sich Lebewesen über Generationen verändern. Die Theorie geht auf Charles Darwin zurück.

Der Kernmechanismus ist natürliche Selektion: Individuen mit Eigenschaften, die besser an ihre Umgebung angepasst sind, überleben häufiger und geben ihre Gene weiter. Über viele Generationen führt das zu Veränderungen in der Population.

Wichtige Konzepte sind Mutation (zufällige Änderungen in der DNA), genetische Drift und Genfluss zwischen Populationen. Manchmal führt räumliche Trennung zur Entstehung neuer Arten (Artbildung).

Die Belege für Evolution sind vielfältig: Fossilien zeigen die Entwicklung über Millionen Jahre. DNA-Vergleiche belegen Verwandtschaftsbeziehungen. Und Evolution lässt sich bei schnell reproduzierenden Organismen wie Bakterien sogar beobachten — etwa bei der Entstehung von Antibiotikaresistenzen.""",
        "quality": "medium"
    },
    {
        "subject": "Wie funktioniert das Internet?",
        "generator": "Mistral-Small-3.2",
        "response": """Internet funktioniert Computer verbunden Netzwerk.

Daten gesendet Pakete kleine Teile. Router leiten weiter Ziel. TCP/IP Protokoll wichtig.

Server speichern Webseiten. Browser lädt herunter. HTTP Anfrage Antwort Schema.

DNS übersetzt Domainnamen IP-Adressen. Zum Beispiel google.com wird 142.250.185.14.

Glasfaserkabel schnell Übertragung. WiFi auch möglich kabellos. Mobilfunk 4G 5G.

Sicherheit wichtig Verschlüsselung HTTPS. Firewall schützt vor Angriffe. VPN zusätzliche Privatsphäre.""",
        "quality": "low"
    },
    {
        "subject": "Was ist Quantencomputing?",
        "generator": "Mistral-Small-3.2",
        "response": """Quantencomputer rechnen mit Qubits. Normal Computer benutzt Bits, also 0 oder 1. Qubit kann beides gleichzeitig sein, das heißt Superposition.

Wenn viele Qubits zusammen dann Verschränkung. Das bedeutet sie hängen zusammen egal wie weit weg. Einstein hat das "spukhafte Fernwirkung" genannt aber es ist echt bewiesen.

Quantencomputer sind schneller für bestimmte Probleme. Zum Beispiel Verschlüsselung knacken. RSA Verschlüsselung die heute benutzt wird kann Quantencomputer leicht brechen. Aber nur wenn genug Qubits vorhanden. Heute sind es noch nicht genug.

Google hat Quantenüberlegenheit gezeigt 2019 mit Sycamore Prozessor. 53 Qubits haben Aufgabe in 200 Sekunden gelöst die normaler Computer 10.000 Jahre brauchen würde. Aber die Aufgabe war nicht besonders nützlich.

Probleme: Qubits sind sehr empfindlich. Temperatur muss fast absoluter Nullpunkt sein. Fehlerkorrektur ist schwer. Noch nicht praktisch für meiste Anwendungen.""",
        "quality": "low"
    },
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
    ijcai_reviewer_1 = User.query.filter_by(username='ijcai_reviewer_1').first()
    ijcai_reviewer_2 = User.query.filter_by(username='ijcai_reviewer_2').first()

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

    # Create evaluation items with response content
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
        generator = data.get('generator', 'GPT-4')
        item = EvaluationItem(
            chat_id=chat_id,
            institut_id=1,
            subject=data['subject'],
            sender=generator,
            function_type_id=rating_type.function_type_id
        )
        db.session.add(item)
        db.session.flush()

        # Create a single message with the response content
        # generated_by is the key field for provenance analysis
        message = Message(
            item_id=item.item_id,
            sender=generator,
            content=data['response'],
            timestamp=datetime.now() - timedelta(days=20 - i, hours=i),
            generated_by=generator
        )
        db.session.add(message)
        items.append(item)

        print(f"  Created item [{generator}]: {data['subject'][:40]}...")

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

    # Add users to scenario: ijcai_reviewer_1=OWNER, ijcai_reviewer_2=EVALUATOR
    for user, role in [
        (ijcai_reviewer_1, ScenarioRoles.OWNER),
        (ijcai_reviewer_2, ScenarioRoles.EVALUATOR),
        (evaluator, ScenarioRoles.VIEWER),
        (researcher, ScenarioRoles.EVALUATOR),
        (admin, ScenarioRoles.VIEWER),
    ]:
        if user:
            db.session.add(ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=role
            ))

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

    # Create distributions for all evaluator users
    evaluator_users = ScenarioUsers.query.filter_by(
        scenario_id=scenario.id,
        role=ScenarioRoles.EVALUATOR
    ).all()

    for eu in evaluator_users:
        for scenario_item in scenario_items:
            dist = ScenarioItemDistribution(
                scenario_id=scenario.id,
                scenario_user_id=eu.id,
                scenario_item_id=scenario_item.id
            )
            db.session.add(dist)

    db.session.commit()

    print(f"\n  Created LLM-as-Judge Demo with {len(items)} items")
    print(f"  Generators: Mensch(7), GPT-4(7), Mistral-Small-3.2(6)")
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
            "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506",
            "Global/Mistral/Magistral-Small-2509"
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
