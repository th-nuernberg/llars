"""
Comparison Demo Data Seeder (IJCAI 2026 / Turing-Test Setup)

Creates pairwise comparison items for a counsellor-style Turing-Test:

  Item layout per row:
    1) EvaluationItem.messages = the dialogue context up to the point right
       before the next counsellor reply (Klient + Berater turns alternating).
    2) Two Features per item = the two candidate continuations for the
       missing counsellor reply, each labelled with a provenance model_id:
         - "human:counsellor"               (real practitioner from corpus)
         - "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506"  (pre-instruct)
         - "Global/Mistral/Magistral-Small-2509"                  (pre-instruct)
         - "Global/OpenAI/gpt-4o-mini"                            (pre-instruct)
         - "sft:mis24b-instrprofi"   (post-instruct SFT on counsellor data)
         - "sft:qwen25-72b-instrprofi"
         - "sft:mis24b-baseprofi"    (post-base SFT)
         - "base:mis24b"             (pre-base, no SFT)
         - "base:llaemmlein-v2profi" (LLaeMMlein DE)
    3) Rater chooses A / B / tie via ItemComparisonEvaluation.

Pair-kind classification (used later by analytics):
  - human-vs-machine  -> Turing pass-rate per model
  - machine-vs-machine -> pairwise quality between treatments

Chat IDs start at 31000 to avoid collisions with other demo seeders.
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Provenance model_id constants (used as Feature.model_id for downstream stats)
# ---------------------------------------------------------------------------
PROV_HUMAN = "human:counsellor"
PROV_MISTRAL_24B = "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506"
PROV_MAGISTRAL = "Global/Mistral/Magistral-Small-2509"
PROV_GPT4O_MINI = "Global/OpenAI/gpt-4o-mini"
PROV_SFT_MIS24B_INSTRPROFI = "sft:mis24b-instrprofi"
PROV_SFT_QWEN25_72B_INSTRPROFI = "sft:qwen25-72b-instrprofi"
PROV_SFT_MIS24B_BASEPROFI = "sft:mis24b-baseprofi"
PROV_BASE_MIS24B = "base:mis24b"
PROV_BASE_LLAEMMLEIN_V2 = "base:llaemmlein-v2profi"


# Each item: a counselling dialogue (multi-turn) + two candidate next-counsellor replies.
# Pair kinds rotate to cover human-vs-machine and machine-vs-machine across treatments.
COMPARISON_DEMO_DATA = [
    # 1) Human vs Pre-Instruct (Mistral-24B) — Turing test classic
    {
        "subject": "Pruefungsstress und Schlafprobleme",
        "messages": [
            ("Klient", "Hallo, ich bin total gestresst wegen meiner Pruefungen. Ich schlafe kaum noch und habe Angst zu versagen. Ich weiss nicht, was ich tun soll."),
            ("Berater", "Vielen Dank, dass Sie sich melden. Pruefungsangst kann sehr belastend sein und sich auf den Schlaf auswirken. Koennen Sie mir kurz erzaehlen, wie lange das schon so geht und ob es eine bestimmte Pruefung gibt, vor der Sie besonders Angst haben?"),
            ("Klient", "Es ist seit drei Wochen so, also seit der Klausurenphase begonnen hat. Mathematik macht mir am meisten Sorgen, weil ich da letztes Semester schon durchgefallen bin. Ich liege oft stundenlang wach und denke an die Pruefung."),
        ],
        "candidates": [
            {
                "provenance": PROV_HUMAN,
                "content": (
                    "Das klingt sehr belastend, vor allem die Verbindung zur letzten Pruefung. "
                    "Ein Misserfolg, den wir noch nicht verarbeitet haben, sitzt oft tief und "
                    "macht den naechsten Versuch besonders schwer. Mich wuerde interessieren: "
                    "wenn Sie nachts wach liegen — gibt es einen bestimmten Moment in der "
                    "letzten Pruefung, der immer wieder kommt? Und haben Sie schon einmal mit "
                    "jemandem aus Ihrem Umfeld darueber gesprochen, wie es Ihnen damit geht?"
                ),
            },
            {
                "provenance": PROV_MISTRAL_24B,
                "content": (
                    "Pruefungsangst ist ein haeufiges Problem. Hier sind einige Tipps: "
                    "1) Erstellen Sie einen Lernplan und teilen Sie den Stoff in kleine Einheiten auf. "
                    "2) Verwenden Sie Entspannungstechniken wie tiefes Atmen oder Meditation. "
                    "3) Vermeiden Sie Koffein am Abend. "
                    "4) Sorgen Sie fuer ausreichend Schlaf, indem Sie eine feste Schlafroutine etablieren. "
                    "5) Sprechen Sie mit einem Therapeuten, falls die Symptome anhalten."
                ),
            },
        ],
    },

    # 2) Human vs Post-Instruct-SFT — does fine-tuning close the gap?
    {
        "subject": "Konflikte mit jugendlicher Tochter",
        "messages": [
            ("Klient", "Meine 15-jaehrige Tochter und ich streiten staendig. Letzte Woche kam sie um 3 Uhr morgens nach Hause und hat geschrien, ich sei der schlimmste Vater. Ich verstehe nicht mehr, was los ist."),
            ("Berater", "Es klingt, als waere die Situation gerade sehr aufgeladen. Bevor wir auf das Verhalten Ihrer Tochter schauen — wie geht es Ihnen mit dem, was sie gesagt hat? Was hat dieser Satz in Ihnen ausgeloest?"),
            ("Klient", "Ehrlich gesagt, ich war erstmal wuetend und dann tieftraurig. Ich habe das Gefuehl, alles falsch gemacht zu haben in den letzten Jahren. Ihre Mutter und ich sind seit zwei Jahren getrennt, und seitdem ist sie sehr verschlossen."),
        ],
        "candidates": [
            {
                "provenance": PROV_SFT_MIS24B_INSTRPROFI,
                "content": (
                    "Diese beiden Gefuehle, Wut und Trauer, sagen sehr viel ueber die Tiefe der "
                    "Beziehung — wer einem egal ist, dessen Worte verletzen nicht so. Sie haben "
                    "zwei Dinge gleichzeitig erwaehnt: die Trennung vor zwei Jahren und ihre "
                    "Verschlossenheit seitdem. Manchmal aeussern Jugendliche unverarbeitete Trauer "
                    "ueber eine Trennung als Wut auf den verfuegbaren Elternteil. Bevor wir nach "
                    "Strategien suchen — gab es eine Zeit nach der Trennung, in der Sie und Ihre "
                    "Tochter konkret darueber gesprochen haben, was die Veraenderung fuer sie bedeutet?"
                ),
            },
            {
                "provenance": PROV_HUMAN,
                "content": (
                    "Was Sie da beschreiben — die Verbindung von Wut und tiefer Trauer — zeigt mir, "
                    "wie viel Ihnen Ihre Beziehung zur Tochter bedeutet. Es ist nicht ungewoehnlich, "
                    "dass Jugendliche in der Phase nach einer Trennung den Elternteil, bei dem sie "
                    "leben, am haertesten herausfordern. Das ist paradox, aber haeufig: gerade bei "
                    "demjenigen, dem sie noch vertrauen koennen, lassen sie alles raus. Ich frage "
                    "mich: gibt es Momente, in denen Sie und Ihre Tochter, jenseits der Konflikte, "
                    "kurz wirklich verbunden sind? Auch ganz kleine."
                ),
            },
        ],
    },

    # 3) Machine vs Machine — Pre-Instruct vs Post-Instruct-SFT (same base)
    {
        "subject": "Burnout-Symptome und Job",
        "messages": [
            ("Klient", "Ich fuehle mich seit Monaten ausgebrannt. Jeden Morgen kostet es mich enorme Ueberwindung, zur Arbeit zu gehen. Ich habe schon ueberlegt zu kuendigen, aber finanziell geht das eigentlich nicht."),
            ("Berater", "Das klingt nach einer wirklich erschoepfenden Situation, in der sich auch noch zwei Druecke vermischen — der gesundheitliche und der finanzielle. Was passiert konkret in Ihnen, wenn Sie morgens an die Arbeit denken?"),
            ("Klient", "Ein Druck auf der Brust, manchmal Uebelkeit. Ich habe das Gefuehl, alles falsch zu machen, obwohl meine Vorgesetzte sagt, ich bin gut. Ich kann Lob nicht annehmen, ich glaube es nicht."),
        ],
        "candidates": [
            {
                "provenance": PROV_MISTRAL_24B,
                "content": (
                    "Ihre Symptome — Druck auf der Brust, Uebelkeit, Unfaehigkeit Lob anzunehmen — "
                    "sind klassische Anzeichen von Burnout und moeglicherweise einer beginnenden "
                    "Depression. Hier sind einige Schritte: 1) Sprechen Sie mit Ihrem Hausarzt. "
                    "2) Erwaegen Sie eine Krankschreibung. 3) Suchen Sie therapeutische Unterstuetzung. "
                    "4) Reduzieren Sie kurzfristig Ihre Arbeitsbelastung. 5) Sprechen Sie mit Ihrer "
                    "Vorgesetzten ueber moegliche Anpassungen."
                ),
            },
            {
                "provenance": PROV_SFT_MIS24B_INSTRPROFI,
                "content": (
                    "Sie beschreiben einen Widerspruch, der mich aufhorchen laesst: aussen kommt "
                    "Anerkennung an, innen kommt sie nicht an. Das ist eine wichtige Information. "
                    "Manchmal lebt jemand mit einem inneren Massstab, an den er nie ganz heranreicht, "
                    "egal was die Aussenwelt rueckmeldet. Bevor wir ueber die Arbeit sprechen — "
                    "kennen Sie diesen Massstab schon laenger, oder ist er erst entstanden? Und "
                    "wessen Stimme klingt da mit?"
                ),
            },
        ],
    },

    # 4) Human vs Pre-Base (LLaeMMlein, no instruction tuning) — should be obvious
    {
        "subject": "Trauer nach Verlust der Mutter",
        "messages": [
            ("Klient", "Meine Mutter ist vor drei Monaten gestorben. Ich funktioniere im Alltag, gehe arbeiten, kuemmere mich um die Kinder, aber innerlich fuehle ich mich vollkommen leer. Ich frage mich, ob mit mir etwas nicht stimmt."),
            ("Berater", "Mein aufrichtiges Beileid. Drei Monate nach einem solchen Verlust ist noch sehr frisch — der Koerper funktioniert oft, weil er muss, waehrend das Innere noch nicht nachgekommen ist. Wann merken Sie diese Leere am deutlichsten?"),
            ("Klient", "Abends, wenn die Kinder schlafen. Dann setze ich mich aufs Sofa und es ist, als ob jemand einen Schalter umlegt. Ich heule nicht, ich starre nur. Mein Mann versteht nicht, warum ich so still bin."),
        ],
        "candidates": [
            {
                "provenance": PROV_HUMAN,
                "content": (
                    "Diese Leere am Abend, wenn der Tag die Schutzschicht nicht mehr braucht — "
                    "was Sie da beschreiben, ist keine Stoerung, das ist Trauer in einer ihrer "
                    "stilleren Formen. Manche Menschen weinen, andere werden still und leer. "
                    "Beides ist Trauer. Die Frage, was Ihr Mann nicht versteht, ist mir aber "
                    "auch wichtig: glauben Sie, er versucht zu verstehen, oder zieht er sich "
                    "zurueck? Und was wuerden Sie sich von ihm in diesen Abenden wuenschen, "
                    "wenn Sie es ihm sagen koennten?"
                ),
            },
            {
                "provenance": PROV_BASE_LLAEMMLEIN_V2,
                "content": (
                    "Trauer ist ein natuerlicher Prozess der durchschritten werden muss. Studien "
                    "zeigen dass etwa 7 Prozent der Trauernden eine komplizierte Trauer entwickeln. "
                    "Die fuenf Phasen nach Kuebler-Ross sind: Verleugnung, Wut, Verhandeln, "
                    "Depression, Akzeptanz. Es gibt verschiedene therapeutische Ansaetze. "
                    "Quellen: bundesgesundheitsministerium.de"
                ),
            },
        ],
    },

    # 5) Machine vs Machine — gpt-4o-mini vs Post-Base-SFT (cross-family)
    {
        "subject": "Beziehungsprobleme - Streit ueber Kleinigkeiten",
        "messages": [
            ("Klient", "Mein Partner und ich streiten staendig ueber Kleinigkeiten. Letzte Woche haben wir uns ueber den Zeitpunkt des Spuelmaschine-Ausraeumens fuer eine halbe Stunde angeschrien. Wir reden aneinander vorbei."),
            ("Berater", "Wenn Streit aus solchen Kleinigkeiten entsteht, sind das oft Ventile fuer etwas anderes, das gerade nicht direkt benannt wird. Wie haben Sie sich VOR dem Streit gefuehlt? Was war an dem Tag passiert?"),
            ("Klient", "Hmm. Ich war frustriert, weil ich ueberlegt hatte, ob ich mich beruflich umorientieren soll, und mein Partner hatte das Thema beim Abendessen weggewischt. Dann bin ich mit der Spuelmaschine explodiert."),
        ],
        "candidates": [
            {
                "provenance": PROV_GPT4O_MINI,
                "content": (
                    "Das ist ein wichtiges Muster, das Sie da erkennen. Wenn ein wichtiges Anliegen "
                    "— Ihre berufliche Neuorientierung — nicht ernst genommen wird, sucht sich der "
                    "Frust ein anderes Ventil. Die Spuelmaschine wurde zum Stellvertreter fuer ein "
                    "groesseres Gefuehl: nicht gehoert zu werden. Bevor Sie mit Ihrem Partner ueber "
                    "die Streiterei sprechen — wie waere es, wenn Sie das urspruengliche Thema "
                    "zurueckholen? Was haetten Sie sich am Abendessen von ihm gewuenscht?"
                ),
            },
            {
                "provenance": PROV_SFT_MIS24B_BASEPROFI,
                "content": (
                    "Sie haben gerade einen wichtigen Zusammenhang gesehen: das eigentliche Thema "
                    "war nicht die Spuelmaschine, sondern dass etwas Wichtiges fuer Sie weggewischt "
                    "wurde. Das ist eine bedeutsame Beobachtung. Ich frage mich: passiert es Ihnen "
                    "haeufiger, dass Anliegen von Ihnen am Esstisch nicht ankommen — und dass Sie "
                    "den Frust dann erst spaeter merken? Und wie reagieren Sie sonst, wenn das passiert?"
                ),
            },
        ],
    },

    # 6) Machine vs Machine — Pre-Base raw vs Post-Instruct-SFT (large gap)
    {
        "subject": "Schulverweigerung 14-jaehriger Sohn",
        "messages": [
            ("Klient", "Mein 14-jaehriger Sohn weigert sich seit drei Wochen, in die Schule zu gehen. Jeden Morgen klagt er ueber Bauchschmerzen. Der Kinderarzt sagt, koerperlich ist nichts. Ich bin alleinerziehender Vater und habe schon all meine Urlaubstage aufgebraucht."),
            ("Berater", "Schulverweigerung in dem Alter ist oft ein Signal, dass im sozialen Umfeld etwas Wichtiges passiert ist. Die koerperlichen Symptome sind real, sie sind eine Stressreaktion. Was haben Sie selbst beobachtet? Wie ist es, wenn Sie fragen, was los ist?"),
            ("Klient", "Er macht zu. Sagt nur 'lass mich in Ruhe'. Ich habe gestern mit der Klassenlehrerin gesprochen, sie meinte, eine Gruppe Jungs macht Bemerkungen ueber seine Klamotten und sein altes Handy. Er sitzt seit Wochen alleine in der Pause. Ich habe das nicht gesehen."),
        ],
        "candidates": [
            {
                "provenance": PROV_BASE_MIS24B,
                "content": (
                    "Mobbing in der Schule ist ein ernsthaftes Problem. Es kann zu langfristigen "
                    "psychischen Folgen fuehren. Ein Beispiel waere: 1. Mit der Schule sprechen "
                    "2. Vertrauenslehrer einschalten 3. Eventuell einen Therapeuten aufsuchen "
                    "4. Schulwechsel als letzte Option Wenn das Kind sich isoliert ist es wichtig "
                    "Vertrauen aufzubauen. Manchmal hilft auch eine Selbsthilfegruppe. Quelle: "
                    "schulpsychologie.de"
                ),
            },
            {
                "provenance": PROV_SFT_QWEN25_72B_INSTRPROFI,
                "content": (
                    "Was Sie zuletzt sagen — 'ich habe das nicht gesehen' — bleibt bei mir haengen. "
                    "Das ist Schmerz, der gerade mit dem Schmerz Ihres Sohnes konkurriert. Bitte "
                    "halten Sie diesen Moment kurz aus, ohne sich Vorwuerfe zu machen: wenn Kinder "
                    "in dem Alter Mobbing erleben, verstecken sie es oft systematisch — gerade vor "
                    "dem Elternteil, das es schmerzt. Bevor wir an konkrete Schritte gehen: fuer "
                    "Ihren Sohn ist es jetzt wahrscheinlich wichtiger, dass jemand seinen Schmerz "
                    "anerkennt, als dass jemand das Problem 'loest'. Wie waere es, ihm zu sagen, "
                    "dass Sie wissen, was passiert ist, und dass Sie an seiner Seite sind — ohne "
                    "im selben Atemzug einen Plan zu praesentieren?"
                ),
            },
        ],
    },

    # 7) Human vs Magistral (different pre-instruct family)
    {
        "subject": "Selbstwert und Hochstapler-Gefuehl",
        "messages": [
            ("Klient", "Ich habe immer das Gefuehl, nicht gut genug zu sein. Egal was ich erreiche, ich denke, es war nur Glueck. Ich wurde gerade befoerdert und kann mich nicht freuen, ich habe nur Angst, dass alle merken, dass ich es nicht wirklich kann."),
            ("Berater", "Was Sie beschreiben, klingt sehr belastend. Diese innere Stimme, die alles relativiert, was Sie erreichen — wann ist Ihnen das zum ersten Mal aufgefallen?"),
            ("Klient", "Schon in der Schule. Wenn ich eine 1 hatte, dachte ich, die Lehrerin war nachsichtig. Wenn ich eine 3 hatte, dachte ich, jetzt sehen alle, dass ich dumm bin. Meine Eltern haben immer gesagt 'gut, aber andere sind besser'. Ich glaube, ich habe das verinnerlicht."),
        ],
        "candidates": [
            {
                "provenance": PROV_HUMAN,
                "content": (
                    "Das ist eine sehr klare Beobachtung — Sie haben gerade eine Stimme aus Ihrer "
                    "Kindheit identifiziert, die heute noch in Ihnen weiterspricht. 'Gut, aber "
                    "andere sind besser' ist ein Satz, der einem Kind das Recht nimmt, sich an "
                    "sich selbst zu freuen. Bevor wir an Strategien denken, moechte ich kurz bei "
                    "diesem Befund bleiben: wie geht es Ihnen, wenn Sie das jetzt aussprechen? "
                    "Und gibt es irgendwo in Ihrem Leben einen Menschen, der Ihnen, ohne Vergleich, "
                    "sagt, dass Sie genug sind?"
                ),
            },
            {
                "provenance": PROV_MAGISTRAL,
                "content": (
                    "Ihre Beobachtung ist treffend. Was Sie beschreiben, nennt man in der Psychologie "
                    "das Hochstapler-Syndrom oder Impostor-Phaenomen. Es entsteht haeufig durch "
                    "elterliche Erwartungshaltungen. Hilfreich sind: Erfolgs-Tagebuch fuehren, "
                    "kognitive Umstrukturierung der inneren Stimme, Therapie. Es ist gut, dass Sie "
                    "den Zusammenhang zur Kindheit erkennen — das ist oft der erste Schritt zur "
                    "Veraenderung. Welche dieser Methoden moechten Sie ausprobieren?"
                ),
            },
        ],
    },

    # 8) Machine vs Machine — Pre-Instruct (gpt-4o-mini) vs Pre-Base (mis24b)
    {
        "subject": "Streit mit Vorgesetztem",
        "messages": [
            ("Klient", "Mein Chef hat mich gestern in einem Meeting vor allen Kollegen blossgestellt. Er sagte, mein Bericht sei 'die schlechteste Arbeit, die er seit Jahren gesehen hat'. Ich habe nichts gesagt, weil ich Angst hatte zu weinen. Jetzt traue ich mich nicht mehr ins Buero."),
            ("Berater", "Das ist eine sehr unangenehme und auch unprofessionelle Situation, die Sie beschreiben. Bevor wir an die Reaktion gehen — wie geht es Ihnen jetzt damit, einen Tag spaeter?"),
            ("Klient", "Beschaemt. Wuetend auf ihn, aber auch auf mich, weil ich nicht reagiert habe. Mein Mann sagt, ich solle es nicht so persoenlich nehmen, aber ich kann es nicht. Ich habe heute morgen versucht, mich krank zu melden, aber dann doch nicht."),
        ],
        "candidates": [
            {
                "provenance": PROV_GPT4O_MINI,
                "content": (
                    "Diese drei Reaktionen — Scham, Wut, Selbstkritik — zeigen, dass Sie die Situation "
                    "tief verarbeiten. Dass Ihr Mann das anders sieht, ist nicht unueblich, aber sein "
                    "'nimm es nicht persoenlich' verschiebt das Problem zu Ihnen, statt das Verhalten "
                    "des Chefs zu adressieren. Bevor wir ueberlegen, wie Sie reagieren — sollten wir "
                    "vielleicht zuerst klaeren: was haben Sie gebraucht, was Sie nicht bekommen haben? "
                    "Vom Chef? Von Ihrem Mann gestern Abend? Von sich selbst?"
                ),
            },
            {
                "provenance": PROV_BASE_MIS24B,
                "content": (
                    "Mobbing am Arbeitsplatz ist verboten und kann rechtliche Konsequenzen haben. "
                    "Sie sollten ein Gedaechtnisprotokoll erstellen, das Datum, Uhrzeit und Zeugen "
                    "enthaelt. Wenden Sie sich an den Betriebsrat oder die Personalabteilung. "
                    "Auch eine Beratungsstelle kann helfen. Bei laengerer psychischer Belastung "
                    "ist ein Arztbesuch ratsam. Quelle: bundesarbeitsministerium.de"
                ),
            },
        ],
    },
]


def _get_comparison_config():
    """Default pairwise comparison config matching ComparisonConfigEditor."""
    return {
        "evaluation": "comparison",
        "type": "pairwise",
        "question": {
            "de": "Welche der beiden Antworten passt besser als naechste Beraternachricht?",
            "en": "Which of the two replies fits better as the next counsellor message?"
        },
        "taskDescriptionMarkdown": {
            "de": (
                "Sie sehen den bisherigen Verlauf einer Online-Beratung. Direkt darunter "
                "stehen zwei Kandidaten fuer die naechste Beraternachricht (A und B). "
                "Bewerten Sie aus professioneller Sicht, welche der beiden Antworten "
                "besser passt. Sie wissen nicht, welche Antwort von einem menschlichen "
                "Berater oder einem KI-System stammt — die Reihenfolge ist verdeckt."
            ),
            "en": (
                "You see the conversation up to a point in an online counselling session. "
                "Directly below are two candidate next counsellor messages (A and B). "
                "Pick the one you consider professionally more appropriate. The "
                "human/AI authorship is blinded — you do not know which is which."
            )
        },
        "criteriaMarkdown": {
            "de": (
                "## Worauf sollte geachtet werden?\n"
                "- Empathie, Beziehungsaufbau und Resonanz mit dem zuvor Gesagten\n"
                "- Ressourcenorientierung statt Listen oder Belehrung\n"
                "- Stil, Klarheit und Tonalitaet (vermeidet Diagnose-Sprache)\n"
                "- Vermeidet vorschnelle Loesungen, bevor das Anliegen klar ist"
            ),
            "en": (
                "## What should be evaluated?\n"
                "- Empathy, rapport, and resonance with what was just said\n"
                "- Resource-orientation over lists or lectures\n"
                "- Style, clarity, and tone (avoids diagnostic language)\n"
                "- Avoids premature solutions before the issue is clear"
            )
        },
        "itemsPerComparison": 2,
        # Tie is opt-in (Turing-Test setup forces a directional choice by default).
        "allowTie": False,
        "showConfidence": False,
        "confidenceScale": {"min": 1, "max": 5},
        "criteria": [],
        "rounds": "auto",
    }


def seed_comparison_demo_scenario(db):
    """
    Create a Turing-Test-style pairwise comparison demo scenario.

    Idempotent: re-running updates config and adds any missing items/features.
    """
    from db.models import (
        User, EvaluationItem, Message, Feature, FeatureType,
        RatingScenarios, ScenarioUsers, ScenarioItems,
        ScenarioItemDistribution, ScenarioRoles, FeatureFunctionType
    )

    print("\n" + "=" * 60)
    print("Seeding Comparison Demo Scenario (Turing-Test pairwise A/B)...")
    print("=" * 60)

    evaluator = User.query.filter_by(username='evaluator').first()
    researcher = User.query.filter_by(username='researcher').first()
    admin = User.query.filter_by(username='admin').first()
    ijcai_reviewer_1 = User.query.filter_by(username='ijcai_reviewer_1').first()
    ijcai_reviewer_2 = User.query.filter_by(username='ijcai_reviewer_2').first()
    # Real LLARS users that should auto-receive access on environments where
    # they exist (e.g. the dev server after first Authentik login). Skipped
    # silently when the user record is absent (e.g. fresh local dev DB).
    extra_assessors = [
        u for u in [User.query.filter_by(username=name).first()
                    for name in ('ieb-steigerwald',)] if u
    ]

    if not evaluator or not researcher:
        print("  ERROR: Required users (evaluator/researcher) not found")
        return None

    comparison_type = FeatureFunctionType.query.filter_by(name='comparison').first()
    if not comparison_type:
        print("  ERROR: Comparison function type not found")
        return None

    # FeatureType is required for Feature rows; "Summary" is the generic
    # placeholder — comparison interface reads features in order regardless.
    feature_type = FeatureType.query.filter_by(name='Summary').first()
    if not feature_type:
        feature_type = FeatureType(name='Summary')
        db.session.add(feature_type)
        db.session.flush()

    existing = RatingScenarios.query.filter_by(
        scenario_name='Demo Comparison Szenario'
    ).first()

    def _ensure_item(idx: int, data: dict):
        """Create or repair an EvaluationItem with dialogue context + 2 candidate features."""
        chat_id = 31000 + idx
        item = EvaluationItem.query.filter_by(
            chat_id=chat_id,
            institut_id=1,
            function_type_id=comparison_type.function_type_id,
        ).first()
        if not item:
            item = EvaluationItem(
                chat_id=chat_id,
                institut_id=1,
                subject=data['subject'],
                sender='Klient',
                function_type_id=comparison_type.function_type_id,
            )
            db.session.add(item)
            db.session.flush()

        # Seed multi-turn dialogue context if no messages exist yet.
        if Message.query.filter_by(item_id=item.item_id).count() == 0:
            base_time = datetime.now() - timedelta(days=14 - idx, hours=2 * len(data['messages']))
            for msg_idx, (sender, content) in enumerate(data['messages']):
                db.session.add(Message(
                    item_id=item.item_id,
                    sender=sender,
                    content=content,
                    timestamp=base_time + timedelta(hours=msg_idx * 6),
                ))

        # Two candidate features (Option A = candidates[0], Option B = candidates[1]).
        existing_features = (Feature.query
                             .filter_by(item_id=item.item_id)
                             .order_by(Feature.feature_id.asc())
                             .all())
        if len(existing_features) < 2:
            existing_contents = {f.content for f in existing_features}
            for cand in data['candidates']:
                if cand['content'] in existing_contents:
                    continue
                db.session.add(Feature(
                    item_id=item.item_id,
                    type_id=feature_type.type_id,
                    model_id=cand['provenance'],
                    content=cand['content'],
                ))
        db.session.flush()
        return item

    items = [_ensure_item(i, data) for i, data in enumerate(COMPARISON_DEMO_DATA)]

    # researcher acts as the scenario owner: in the LLARS workflow it is the
    # researcher who designs evaluations, so they should own the scenario AND
    # also participate as an assessor (Owner + Assessor combo on the 2-axis
    # role model). created_by is set so other code paths that gate by owner
    # (e.g. dashboard "my scenarios") work correctly.
    owner_user = researcher

    if existing:
        existing.config_json = _get_comparison_config()
        if owner_user and not existing.created_by:
            existing.created_by = owner_user.username
        scenario = existing
        print("  Comparison demo scenario exists — config refreshed")
    else:
        scenario = RatingScenarios(
            scenario_name='Demo Comparison Szenario',
            function_type_id=comparison_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=90),
            timestamp=datetime.now(),
            config_json=_get_comparison_config(),
            created_by=owner_user.username if owner_user else None,
        )
        db.session.add(scenario)
        db.session.flush()
        print(f"  Created scenario: {scenario.scenario_name} (owner={scenario.created_by})")

    # Roles:
    #   researcher        → OWNER + ASSESSOR (creates and also evaluates)
    #   ijcai_reviewer_*  → ASSESSOR (Turing-Test reviewers)
    #   evaluator         → ASSESSOR
    #   admin             → VIEWER (cross-cutting oversight, no vote)
    role_assignments = [
        (researcher,        ScenarioRoles.OWNER,     'owner',  'assessor'),
        (ijcai_reviewer_1,  ScenarioRoles.ASSESSOR,  'none',   'assessor'),
        (ijcai_reviewer_2,  ScenarioRoles.ASSESSOR,  'none',   'assessor'),
        (evaluator,         ScenarioRoles.ASSESSOR,  'none',   'assessor'),
        (admin,             ScenarioRoles.VIEWER,    'viewer', 'none'),
    ]
    # Add real users (e.g. ieb-steigerwald on the dev environment) as
    # owner+assessor so they can both manage and rate the demo scenario.
    for extra in extra_assessors:
        role_assignments.append(
            (extra, ScenarioRoles.OWNER, 'owner', 'assessor')
        )
    for user, legacy_role, manager_role, evaluation_role in role_assignments:
        if not user:
            continue
        is_assessor = evaluation_role == 'assessor'
        is_viewer = manager_role == 'viewer'
        existing_su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id, user_id=user.id
        ).first()
        if existing_su:
            # Bring legacy roles into 2-axis alignment for older rows.
            existing_su.role = legacy_role
            existing_su.manager_role = manager_role
            existing_su.evaluation_role = evaluation_role
            existing_su.is_assessor = is_assessor
            existing_su.is_viewer = is_viewer
            continue
        db.session.add(ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            role=legacy_role,
            access_level='MEMBER',
            is_assessor=is_assessor,
            is_viewer=is_viewer,
            manager_role=manager_role,
            evaluation_role=evaluation_role,
        ))
    db.session.flush()

    scenario_items = []
    for item in items:
        si = ScenarioItems.query.filter_by(
            scenario_id=scenario.id, item_id=item.item_id
        ).first()
        if not si:
            si = ScenarioItems(scenario_id=scenario.id, item_id=item.item_id)
            db.session.add(si)
            db.session.flush()
        scenario_items.append(si)

    assessors = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario.id,
        db.or_(
            ScenarioUsers.is_assessor == True,
            ScenarioUsers.role == ScenarioRoles.EVALUATOR,
        )
    ).all()
    for su in assessors:
        for si in scenario_items:
            existing_dist = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id,
                scenario_user_id=su.id,
                scenario_item_id=si.id,
            ).first()
            if not existing_dist:
                db.session.add(ScenarioItemDistribution(
                    scenario_id=scenario.id,
                    scenario_user_id=su.id,
                    scenario_item_id=si.id,
                ))

    db.session.commit()

    pair_kinds = {'human-vs-machine': 0, 'machine-vs-machine': 0}
    for data in COMPARISON_DEMO_DATA:
        provs = [c['provenance'] for c in data['candidates']]
        pair_kinds['human-vs-machine' if PROV_HUMAN in provs else 'machine-vs-machine'] += 1

    print(f"  Comparison demo ready: {len(items)} items, "
          f"{len(assessors)} assessors")
    print(f"  Pair-kinds: {pair_kinds}")
    print("=" * 60)
    return scenario
