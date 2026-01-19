#!/usr/bin/env python3
"""
Process downloaded German datasets for LLARS demo data.

This script processes:
1. 10kGNAD - German news articles for labeling and rating
2. German Sentiment (SB10k, PotTS) - For comparison pairs
3. Creates structured data for different evaluation types

Output: Processed samples ready for demo_datasets.py
"""

import csv
import json
import random
from pathlib import Path
from collections import defaultdict

# Set random seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).parent


def load_10kgnad():
    """Load 10kGNAD German news dataset."""
    samples = []
    categories = defaultdict(list)

    train_file = BASE_DIR / "10kGNAD-master" / "train.csv"
    test_file = BASE_DIR / "10kGNAD-master" / "test.csv"

    for filepath in [train_file, test_file]:
        if not filepath.exists():
            print(f"Warning: {filepath} not found")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(';', 1)
                if len(parts) == 2:
                    category, text = parts
                    if len(text) > 100:  # Skip very short articles
                        categories[category].append({
                            'category': category,
                            'text': text[:2000]  # Limit length
                        })

    return categories


def load_sentiment_data():
    """Load German sentiment data (SB10k and PotTS)."""
    positive = []
    negative = []
    neutral = []

    # SB10k
    sb10k_file = BASE_DIR / "german-sentiment-master" / "source-data" / "SB10k" / "not-preprocessed" / "corpus_label_text.tsv"
    # PotTS
    potts_file = BASE_DIR / "german-sentiment-master" / "source-data" / "PotTS" / "not-preprocessed" / "corpus_label_text.tsv"

    for filepath in [sb10k_file, potts_file]:
        if not filepath.exists():
            print(f"Warning: {filepath} not found")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t', 1)
                if len(parts) == 2:
                    label, text = parts
                    # Skip very short or Twitter-like texts with lots of @mentions
                    if len(text) > 50 and text.count('@') < 3:
                        if label == 'positive':
                            positive.append(text)
                        elif label == 'negative':
                            negative.append(text)
                        elif label == 'neutral':
                            neutral.append(text)

    return positive, negative, neutral


def create_labeling_samples(categories, num_per_category=5):
    """Create labeling samples from 10kGNAD."""
    samples = []

    # Map German categories to English for consistency
    category_map = {
        'Sport': 'Sport',
        'Kultur': 'Kultur',
        'Web': 'Web/Technologie',
        'Wirtschaft': 'Wirtschaft',
        'Inland': 'Inland',
        'International': 'International',
        'Panorama': 'Panorama',
        'Wissenschaft': 'Wissenschaft',
        'Etat': 'Medien/Etat'
    }

    for category, articles in categories.items():
        if category in category_map:
            selected = random.sample(articles, min(num_per_category, len(articles)))
            for article in selected:
                # Create a subject from the first sentence
                first_sentence = article['text'].split('.')[0][:100]
                samples.append({
                    'subject': f"Nachricht: {first_sentence}...",
                    'content': article['text'],
                    'category': category_map[category],
                    'source': '10kGNAD'
                })

    return samples


def create_rating_samples(categories, num_samples=20):
    """Create rating samples from 10kGNAD for quality assessment."""
    samples = []
    all_articles = []

    for category, articles in categories.items():
        all_articles.extend(articles)

    selected = random.sample(all_articles, min(num_samples, len(all_articles)))

    for article in selected:
        first_sentence = article['text'].split('.')[0][:80]
        samples.append({
            'subject': f"Artikel bewerten: {first_sentence}...",
            'content': article['text'],
            'category': article['category'],
            'source': '10kGNAD',
            'task': 'Bewerten Sie die Qualität und Verständlichkeit dieses Nachrichtenartikels.'
        })

    return samples


def create_comparison_samples(positive, negative, num_pairs=15):
    """Create comparison pairs from sentiment data."""
    samples = []

    # Sample pairs of positive and negative texts
    num_pairs = min(num_pairs, len(positive), len(negative))
    pos_sample = random.sample(positive, num_pairs)
    neg_sample = random.sample(negative, num_pairs)

    topics = [
        "Produktbewertung",
        "Serviceerfahrung",
        "Nutzermeinung",
        "Kundenfeedback",
        "Rezension",
        "Erfahrungsbericht",
        "Bewertung",
        "Feedback",
        "Meinung",
        "Kommentar"
    ]

    for i, (pos, neg) in enumerate(zip(pos_sample, neg_sample)):
        topic = topics[i % len(topics)]
        # Randomize which is option A/B
        if random.random() > 0.5:
            option_a, option_b = pos, neg
            sentiment_a, sentiment_b = 'positiv', 'negativ'
        else:
            option_a, option_b = neg, pos
            sentiment_a, sentiment_b = 'negativ', 'positiv'

        samples.append({
            'subject': f'{topic}: Sentiment-Vergleich',
            'option_a': {
                'content': option_a,
                'sentiment': sentiment_a
            },
            'option_b': {
                'content': option_b,
                'sentiment': sentiment_b
            },
            'task': 'Welcher Text drückt eine positivere Stimmung aus?',
            'source': 'German Sentiment Corpus'
        })

    return samples


def create_authenticity_samples():
    """
    Create authenticity samples.
    Since GermanFakeNC only has URLs without content, we create mixed samples
    with clear indicators for training purposes.
    """
    # These are crafted examples that demonstrate typical fake vs real patterns
    samples = [
        {
            'subject': 'Wissenschaftliche Studie zu Klimawandel',
            'content': '''Eine neue Studie der Universität Hamburg, veröffentlicht im Journal "Nature Climate Change",
            zeigt einen Anstieg der globalen Durchschnittstemperatur um 0.8°C seit 1900. Die Forscher
            analysierten Daten von 4.500 Messstationen weltweit über einen Zeitraum von 120 Jahren.
            Professor Dr. Maria Schmidt, Leiterin der Studie, betont: "Die Ergebnisse sind konsistent
            mit früheren IPCC-Berichten." Die vollständige Studie ist unter DOI 10.1038/s41558-024-01234-5
            einsehbar.''',
            'is_fake': False,
            'indicators': ['Quellenangabe', 'DOI', 'Peer-Review Journal', 'Messbare Daten']
        },
        {
            'subject': 'SCHOCK: Geheime Regierungspläne enthüllt!!!',
            'content': '''EXKLUSIV!!! Insider berichten von GEHEIMEN Plänen der Regierung, die SIE
            nicht erfahren sollen! Ein anonymer Whistleblower hat uns brisante Dokumente zugespielt,
            die ALLES verändern werden! Teilen Sie diesen Artikel SOFORT, bevor er GELÖSCHT wird!
            Die Mainstream-Medien SCHWEIGEN zu diesem Skandal! WACHT ENDLICH AUF!!!''',
            'is_fake': True,
            'indicators': ['Clickbait', 'Anonyme Quellen', 'Verschwörungsnarrative', 'Emotionale Sprache']
        },
        {
            'subject': 'Bundestagsbeschluss zur Rentenreform',
            'content': '''Der Bundestag hat am gestrigen Donnerstag mit 412 zu 237 Stimmen das
            Rentenreformgesetz verabschiedet. Das Gesetz sieht eine schrittweise Anhebung des
            Renteneintrittsalters auf 67 Jahre bis 2031 vor. Bundesarbeitsminister Thomas Müller (SPD)
            erklärte in der Pressekonferenz: "Mit dieser Reform sichern wir die Renten für kommende
            Generationen." Die Opposition kritisierte den Beschluss als sozial unausgewogen.''',
            'is_fake': False,
            'indicators': ['Konkrete Zahlen', 'Namentliche Quellen', 'Sachlicher Ton', 'Beide Seiten']
        },
        {
            'subject': 'Ärzte WARNEN: Dieses Lebensmittel TÖTET Sie langsam!',
            'content': '''Führende Mediziner schlagen Alarm! Ein alltägliches Lebensmittel, das in
            JEDEM Haushalt zu finden ist, verursacht KREBS und andere tödliche Krankheiten!
            Die Pharma-Industrie VERHEIMLICHT diese Information seit Jahren! Klicken Sie HIER
            um zu erfahren, welches Lebensmittel Sie SOFORT aus Ihrem Kühlschrank verbannen müssen!''',
            'is_fake': True,
            'indicators': ['Gesundheitspanikmache', 'Verschwörung', 'Clickbait', 'Keine konkreten Quellen']
        },
        {
            'subject': 'Wirtschaftswachstum im dritten Quartal',
            'content': '''Das Statistische Bundesamt meldet für das dritte Quartal 2024 ein
            Wirtschaftswachstum von 0.3 Prozent gegenüber dem Vorquartal. Im Jahresvergleich
            stieg das Bruttoinlandsprodukt um 1.2 Prozent. Haupttreiber waren der private Konsum
            (+0.5%) und die Bauinvestitionen (+1.1%). Die Exporte gingen hingegen um 0.8 Prozent
            zurück. Das ifo-Institut bestätigte diese Entwicklung in seiner aktuellen Konjunkturprognose.''',
            'is_fake': False,
            'indicators': ['Offizielle Statistik', 'Prozentangaben', 'Mehrere Quellen', 'Differenzierte Analyse']
        },
        {
            'subject': 'Impfungen verursachen Autismus - Neue Beweise!',
            'content': '''Eine Facebook-Gruppe mit über 50.000 Mitgliedern hat "erschreckende Beweise"
            gesammelt, dass Impfungen direkt zu Autismus führen. "Mein Kind war völlig normal,
            bis es geimpft wurde", berichtet eine betroffene Mutter. Die Schulmedizin WEIGERT
            sich, diese Zusammenhänge anzuerkennen. Informieren Sie sich SELBST und schützen Sie
            Ihre Kinder vor der Impf-Mafia!''',
            'is_fake': True,
            'indicators': ['Wissenschaftlich widerlegt', 'Anekdotische Evidenz', 'Verschwörung', 'Anti-Wissenschaft']
        },
        {
            'subject': 'EZB erhöht Leitzins um 0.25 Prozentpunkte',
            'content': '''Die Europäische Zentralbank (EZB) hat heute den Leitzins um 0.25 Prozentpunkte
            auf 4.5 Prozent angehoben. EZB-Präsidentin Christine Lagarde begründete den Schritt mit
            der anhaltend hohen Inflation im Euroraum. "Wir werden die Geldpolitik so lange straffen,
            bis die Inflation nachhaltig auf unser Ziel von zwei Prozent sinkt", sagte Lagarde in
            Frankfurt. Ökonomen erwarten weitere Zinsschritte in den kommenden Monaten.''',
            'is_fake': False,
            'indicators': ['Offizielle Institution', 'Direkte Zitate', 'Konkrete Zahlen', 'Experteneinschätzung']
        },
        {
            'subject': 'EILMELDUNG: Deutschland führt Bargeldverbot ein!',
            'content': '''ACHTUNG! Ab nächstem Monat will die Bundesregierung HEIMLICH das Bargeld
            abschaffen! Das haben uns zuverlässige Quellen aus Regierungskreisen bestätigt. Der
            Great Reset beginnt! Bald werden ALLE Transaktionen überwacht! Horten Sie JETZT Bargeld,
            Gold und Lebensmittel! Die Medien werden diesen Artikel ZENSIEREN!''',
            'is_fake': True,
            'indicators': ['Panikmache', 'Anonyme Quellen', 'Verschwörungstheorie', 'Handlungsaufforderung']
        }
    ]

    return samples


def generate_demo_datasets_py():
    """Generate the demo_datasets.py file with real data."""

    print("Loading 10kGNAD...")
    categories = load_10kgnad()
    print(f"  Loaded {sum(len(v) for v in categories.values())} articles in {len(categories)} categories")

    print("Loading sentiment data...")
    positive, negative, neutral = load_sentiment_data()
    print(f"  Loaded {len(positive)} positive, {len(negative)} negative, {len(neutral)} neutral samples")

    print("Creating labeling samples...")
    labeling_samples = create_labeling_samples(categories, num_per_category=4)
    print(f"  Created {len(labeling_samples)} labeling samples")

    print("Creating rating samples...")
    rating_samples = create_rating_samples(categories, num_samples=15)
    print(f"  Created {len(rating_samples)} rating samples")

    print("Creating comparison samples...")
    comparison_samples = create_comparison_samples(positive, negative, num_pairs=12)
    print(f"  Created {len(comparison_samples)} comparison pairs")

    print("Creating authenticity samples...")
    authenticity_samples = create_authenticity_samples()
    print(f"  Created {len(authenticity_samples)} authenticity samples")

    # Generate Python code
    output = '''"""
German Demo Datasets for LLARS.

This file contains real German datasets for demo scenarios:
- 10kGNAD: German news articles from derStandard.at (CC BY-NC-SA 4.0)
- German Sentiment Corpus: SB10k and PotTS datasets
- Authenticity samples: Crafted examples for fake/real detection training

Sources:
- 10kGNAD: https://github.com/tblock/10kGNAD (CC BY-NC-SA 4.0)
- German Sentiment: https://github.com/oliverguhr/german-sentiment
- Authenticity: Manually crafted examples based on common patterns

Generated by process_datasets.py
"""

# =============================================================================
# LABELING SAMPLES - 10kGNAD News Categories
# Categories: Sport, Kultur, Web/Technologie, Wirtschaft, Inland, International,
#             Panorama, Wissenschaft, Medien/Etat
# =============================================================================

LABELING_SAMPLES = '''
    output += json.dumps(labeling_samples, ensure_ascii=False, indent=4)
    output += '''


# =============================================================================
# RATING SAMPLES - Article Quality Assessment
# Task: Rate the quality and clarity of news articles
# =============================================================================

RATING_SAMPLES = '''
    output += json.dumps(rating_samples, ensure_ascii=False, indent=4)
    output += '''


# =============================================================================
# COMPARISON SAMPLES - Sentiment Comparison Pairs
# Task: Compare two texts and determine which expresses more positive sentiment
# =============================================================================

COMPARISON_SAMPLES = '''
    output += json.dumps(comparison_samples, ensure_ascii=False, indent=4)
    output += '''


# =============================================================================
# AUTHENTICITY SAMPLES - Fake vs Real News Detection
# Task: Determine if a news article is likely fake or real
# =============================================================================

AUTHENTICITY_SAMPLES = '''
    output += json.dumps(authenticity_samples, ensure_ascii=False, indent=4)
    output += '''


# =============================================================================
# RANKING SAMPLES - Feature Importance Ranking (from news articles)
# =============================================================================

RANKING_SAMPLES = [
    {
        "subject": "Artikelanalyse: Wirtschaftsnachrichten",
        "content": "Analysieren Sie die wichtigsten Aspekte dieses Wirtschaftsartikels.",
        "features": [
            {"name": "Datenqualität", "description": "Verwendung von konkreten Zahlen und Statistiken"},
            {"name": "Quellenvielfalt", "description": "Zitation verschiedener Experten und Institutionen"},
            {"name": "Objektivität", "description": "Ausgewogene Darstellung verschiedener Perspektiven"},
            {"name": "Aktualität", "description": "Bezug zu aktuellen Ereignissen und Entwicklungen"},
            {"name": "Verständlichkeit", "description": "Klare Erklärung komplexer Zusammenhänge"}
        ],
        "source": "10kGNAD-derived"
    },
    {
        "subject": "Nachrichtenqualität bewerten",
        "content": "Ordnen Sie die Qualitätskriterien nach ihrer Wichtigkeit.",
        "features": [
            {"name": "Faktencheck", "description": "Überprüfbare und korrekte Informationen"},
            {"name": "Transparenz", "description": "Offenlegung von Quellen und Methoden"},
            {"name": "Relevanz", "description": "Bedeutung für die Zielgruppe"},
            {"name": "Tiefe", "description": "Ausführlichkeit der Analyse"},
            {"name": "Sprache", "description": "Professioneller und sachlicher Schreibstil"}
        ],
        "source": "10kGNAD-derived"
    }
]


# =============================================================================
# MAIL RATING SAMPLES - Synthetic counseling conversations
# These remain synthetic as no public German counseling datasets are available
# =============================================================================

MAIL_RATING_SAMPLES = [
    {
        "subject": "Beratungsanfrage: Berufliche Neuorientierung",
        "messages": [
            {"sender": "Klient", "content": "Guten Tag, ich bin 35 Jahre alt und arbeite seit 10 Jahren im Vertrieb. In letzter Zeit fühle ich mich zunehmend unzufrieden mit meiner Arbeit und denke über eine berufliche Neuorientierung nach. Können Sie mir dabei helfen?"},
            {"sender": "Berater", "content": "Vielen Dank für Ihre Nachricht. Es ist völlig normal, nach einigen Jahren im Beruf innezuhalten und die eigene Situation zu reflektieren. Können Sie mir mehr darüber erzählen, was genau Sie an Ihrer aktuellen Tätigkeit unzufrieden macht?"},
            {"sender": "Klient", "content": "Hauptsächlich fehlt mir der Sinn in meiner Arbeit. Ich verkaufe Produkte, von denen ich nicht überzeugt bin. Außerdem ist der Druck durch die Zielvorgaben sehr hoch. Ich interessiere mich eigentlich mehr für den sozialen Bereich."},
            {"sender": "Berater", "content": "Das verstehe ich gut. Der Wunsch nach sinnstiftender Arbeit ist ein wichtiger Motivator. Haben Sie schon konkrete Vorstellungen, in welche Richtung es gehen könnte? Welche Ihrer Fähigkeiten aus dem Vertrieb könnten Sie in einem neuen Bereich einsetzen?"}
        ],
        "source": "Synthetic"
    },
    {
        "subject": "Konflikt mit Vorgesetztem",
        "messages": [
            {"sender": "Klient", "content": "Ich habe ein ernstes Problem mit meinem Chef. Er kritisiert mich ständig vor Kollegen und nimmt meine Ideen nicht ernst. Die Situation belastet mich sehr."},
            {"sender": "Berater", "content": "Das klingt nach einer sehr belastenden Situation. Konflikte am Arbeitsplatz können erheblichen Stress verursachen. Können Sie mir ein konkretes Beispiel nennen, wann das letzte Mal so eine Situation aufgetreten ist?"},
            {"sender": "Klient", "content": "Letzte Woche im Meeting habe ich einen Verbesserungsvorschlag gemacht. Er hat mich sofort unterbrochen und gesagt, dass ich keine Ahnung habe. Alle anderen haben es gehört."},
            {"sender": "Berater", "content": "Das war sicher sehr unangenehm für Sie. Haben Sie schon versucht, das Gespräch unter vier Augen mit Ihrem Vorgesetzten zu suchen? Manchmal hilft eine direkte, sachliche Kommunikation, um Missverständnisse zu klären."}
        ],
        "source": "Synthetic"
    }
]


def get_all_categories():
    """Return all available news categories."""
    return [
        'Sport', 'Kultur', 'Web/Technologie', 'Wirtschaft',
        'Inland', 'International', 'Panorama', 'Wissenschaft', 'Medien/Etat'
    ]


def get_sample_count():
    """Return counts of available samples."""
    return {
        'labeling': len(LABELING_SAMPLES),
        'rating': len(RATING_SAMPLES),
        'comparison': len(COMPARISON_SAMPLES),
        'authenticity': len(AUTHENTICITY_SAMPLES),
        'ranking': len(RANKING_SAMPLES),
        'mail_rating': len(MAIL_RATING_SAMPLES)
    }
'''

    return output


def main():
    output = generate_demo_datasets_py()

    # Write to demo_datasets.py
    output_path = BASE_DIR.parent / "demo_datasets_real.py"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\nGenerated: {output_path}")
    print("Review the file and rename to demo_datasets.py when ready.")


if __name__ == "__main__":
    main()
