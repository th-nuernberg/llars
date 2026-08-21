"""
Anonymization Pipeline Demo Data Seeder

Seeds sample counselling conversations for the anonymization pipeline,
based on real production data from the LLARS server.

Creates:
- 1 completed conversation with NER entities + manual edit (Elke case A)
- 1 in-progress conversation without NER (Elke case B)
- 3 pending conversations for pipeline testing
"""
import logging
from datetime import datetime

from db.database import db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation 1 – completed, NER done, quality rated, 1 manual edit
# ---------------------------------------------------------------------------
CONV_COMPLETED = {
    "title": "Elke - 04.11.2024",
    "original_chat_id": "1465",
    "status": "completed",
    "quality_rating": 4,
    "messages": [
        ("vikl", "Hallo, ich weiß nicht, wie ich anfangen soll. Ich mache mir Sorgen um meinen Sohn Max. Seine Noten haben nachgelassen und ich denke, er hat Probleme mit Drogen.",
         "Hallo, ich weiß nicht, wie ich anfangen soll. Ich mache mir Sorgen um meinen Sohn Dieter. Seine Noten haben nachgelassen und ich denke, er hat Probleme mit Drogen."),
        ("user", "Hallo Elke, ich freue mich, dass sie zu mir gefunden haben. Das sind natürlich mehrere Probleme auf einmal. Vielleicht können wir uns ja langsam an die Probleme rantasten.",
         "Hallo Chloé, ich freue mich, dass sie zu mir gefunden haben. Das sind natürlich mehrere Probleme auf einmal. Vielleicht können wir uns ja langsam an die Probleme rantasten."),
        ("vikl", "Ja, ich bin einverstanden. Ich heiße Elke, bin 37 Jahre alt und verheiratet mit drei Kindern. Mein ältester Sohn, Max, ist 16 Jahre alt und besucht das Gymnasium.",
         "Ja, ich bin einverstanden. Ich heiße Chloé, bin \u2593\u2593 alt und verheiratet mit drei Kindern. Mein ältester Sohn, Dieter, ist \u2593\u2593 alt und besucht das Gymnasium."),
        ("user", "Mein Name ist Caro und ich arbeite nun seit gut 10 Jahren hier in der Familienberatung. Daher kann ich ihnen schonmal mitteilen, dass ich es schön finde, dass sie sich freiwillig gemeldet haben.",
         "Mein Name ist Océane und ich arbeite nun seit gut 10 Jahren hier in der Familienberatung. Daher kann ich ihnen schonmal mitteilen, dass ich es schön finde, dass sie sich freiwillig gemeldet haben."),
        ("vikl", "Ich hoffe, dass Sie mir konkrete Ratschläge geben können, wie ich mit der Situation umgehen soll und wie ich meinen Sohn dazu bringen kann, offen über sein Verhalten zu sprechen.",
         "Ich hoffe, dass Sie mir konkrete Ratschläge geben können, wie ich mit der Situation umgehen soll und wie ich meinen Sohn dazu bringen kann, offen über sein Verhalten zu sprechen."),
        ("user", "Okay, dann versuchen wir uns mal langsam an die Problematik heranzutasten. Wie haben sie denn mitbekommen, dass sich bei ihrem Sohn etwas verändert hat?",
         "Okay, dann versuchen wir uns mal langsam an die Problematik heranzutasten. Wie haben sie denn mitbekommen, dass sich bei ihrem Sohn etwas verändert hat?"),
        ("vikl", "Wir haben zu Hause mehrmals verdächtigen Marihuana-Geruch wahrgenommen. Außerdem haben sich seine Noten verschlechtert und er verändert sich zusehends in seinem Verhalten.",
         "Wir haben zu Hause mehrmals verdächtigen Marihuana-Geruch wahrgenommen. Außerdem haben sich seine Noten verschlechtert und er verändert sich zusehends in seinem Verhalten."),
        ("user", "Da kann ich ihre Bedenken mit den Drogen natürlich verstehen. Eltern haben oft ein gutes Gefühl für ihre Kinder. Hat sich denn in seinem oder ihrem Privatleben in letzter Zeit etwas verändert?",
         "Da kann ich ihre Bedenken mit den Drogen natürlich verstehen. Eltern haben oft ein gutes Gefühl für ihre Kinder. Hat sich denn in seinem oder ihrem Privatleben in letzter Zeit etwas verändert?"),
        ("vikl", "Nein, im Privatleben von Max hat sich nichts verändert. Zumindest ist mir nichts bekannt.",
         "Nein, im Privatleben von Dieter hat sich nichts verändert. Zumindest ist mir nichts bekannt."),
        ("user", "Und in der Schule? Gab es dort neue Herausforderungen oder Situationen?",
         "Und in der Schule? Gab es dort neue Herausforderungen oder Situationen?"),
        ("vikl", "Nein, in der Schule hat sich nichts Wesentliches geändert. Die Noten haben sich einfach verschlechtert, ohne dass es einen offensichtlichen Grund gibt.",
         "Nein, in der Schule hat sich nichts Wesentliches geändert. Die Noten haben sich einfach verschlechtert, ohne dass es einen offensichtlichen Grund gibt."),
        ("user", "In Ordnung, dann versuche ich mich daran zu halten. Ist das auch so, wenn sie sich mit ihrem Sohn unterhalten?",
         "In Ordnung, dann versuche ich mich daran zu halten. Ist das auch so, wenn sie sich mit ihrem Sohn unterhalten?"),
        ("vikl", "Ja, ich bevorzuge generell kurze Konversationen. Selbst mit meinem Sohn kommuniziere ich lieber direkt und ohne Umschweife.",
         "Ja, ich bevorzuge generell kurze Konversationen. Selbst mit meinem Sohn kommuniziere ich lieber direkt und ohne Umschweife."),
        ("user", "Ich würde vorschlagen, dass sie vielleicht trotzdem versuchen mit ihrem Sohn offener zu sprechen. Vielleicht kann auch ihr Mann ein Gespräch suchen?",
         "Ich würde vorschlagen, dass sie vielleicht trotzdem versuchen mit ihrem Sohn offener zu sprechen. Vielleicht kann auch ihr Mann ein Gespräch suchen?"),
        ("vikl", "Danke für den Vorschlag. Wir haben bereits versucht, mit Max offen zu sprechen, aber er blockt ab. Vielleicht kann ein gemeinsames Treffen mit meinem Mann und Ihnen als Moderator helfen.",
         "Danke für den Vorschlag. Wir haben bereits versucht, mit Dieter offen zu sprechen, aber er blockt ab. Vielleicht kann ein gemeinsames Treffen mit meinem Mann und Ihnen als Moderator helfen."),
        ("user", "Dann lassen sie uns gerne einen Termin festhalten. Haben sie denn sonst noch weitere Dinge, die sie besprechen möchten?",
         "Dann lassen sie uns gerne einen Termin festhalten. Haben sie denn sonst noch weitere Dinge, die sie besprechen möchten?"),
        ("vikl", "Nein, ein Termin für ein gemeinsames Gespräch wäre erstmal ausreichend. Danke.",
         "Nein, ein Termin für ein gemeinsames Gespräch wäre erstmal ausreichend. Danke."),
        ("user", "Gerne, dann würde ich nächste Woche um die gleiche Uhrzeit vorschlagen?",
         "Gerne, dann würde ich nächste Woche um die gleiche Uhrzeit vorschlagen?"),
        ("vikl", "Ja, nächste Woche zur gleichen Uhrzeit ist gut. Danke.",
         "Ja, nächste Woche zur gleichen Uhrzeit ist gut. Danke."),
        ("user", "Super, bis dahin wünsche ich ihnen noch eine schöne Woche.",
         "Super, bis dahin wünsche ich ihnen noch eine schöne Woche."),
        ("vikl", "Danke, ich freue mich auch auf den nächsten Termin. Tschüss.",
         "Danke, ich freue mich auch auf den nächsten Termin. Tschüss."),
    ],
    # (msg_index, label, original, replacement, start, end, db_hit)
    "entities": [
        (0, "PER", "Max", "Dieter", 82, 88, True),
        (1, "PER", "Elke", "Chloé", 6, 11, True),
        (2, "PER", "Elke", "Chloé", 37, 42, True),
        (2, "AGE", "37 Jahre", "\u2593\u2593", 48, 50, False),
        (2, "PER", "Max", "Dieter", 109, 115, True),
        (2, "AGE", "16 Jahre", "\u2593\u2593", 121, 123, False),
        (3, "PER", "Caro", "Océane", 13, 19, True),
        (8, "PER", "Max", "Dieter", 25, 31, True),
        (14, "PER", "Max", "Dieter", 57, 63, True),
    ],
    # Message 4 (index 3) was manually edited (has versions)
    "edited_message_index": 3,
    "edit_versions": [
        "Mein Name ist Océane und ich arbeite nun seit gut 10 Jahren hier in der Familienberatung. Daher kann ich ihnen schonmal mitteilen, dass ich es schön finde, dass sie sich freiwillig gemeldet haben.",
        "Mein Name ist Océane und ich arbeite nun seit gut 10 Jahren hier in der Familienberatung. Daher kann ich ihnen schonmal mitteilen, dass ich es schön finde, dass sie sich freiwillig gemeldet haben.",
    ],
}

# ---------------------------------------------------------------------------
# Conversation 2 – in_progress, no NER, raw data
# ---------------------------------------------------------------------------
CONV_IN_PROGRESS = {
    "title": "Elke - 04.11.2024 (B)",
    "original_chat_id": "1467",
    "status": "in_progress",
    "messages": [
        ("vikl", "Hallo, ich bin Elke. Ich mache mir Sorgen um meinen Sohn Max. Seine Noten haben nachgelassen und ich denke, er raucht Marihuana."),
        ("user", "Wie sind seine Noten aktuell? Inwiefern hat er sich verändert?"),
        ("vikl", "Max' Noten haben sich deutlich verschlechtert, insbesondere in den Fächern Englisch und Mathematik. Er zeigt weniger Interesse am Lernen und verbringt mehr Zeit mit seinen Freunden."),
        ("user", "Gibt es Dinge, die ihm aktuell Spaß machen?"),
        ("vikl", "Ja, er spielt immer noch gerne Fußball, aber seit kurzem nur noch sehr selten. Stattdessen hängt er viel mit seinen Freunden ab."),
        ("user", "Haben Sie schon einmal probiert mehr über seine Aktivitäten zu erfahren?"),
        ("vikl", "Ja, ich habe versucht mit Max über seine Aktivitäten zu sprechen, aber er will nicht darüber reden. Er blockt das Thema immer wieder ab."),
        ("user", "Gibt es Menschen mit denen er gerne drüber redet?"),
        ("vikl", "Nein, er teilt sich nicht wirklich anderen mit. Ich denke, er hat Angst vor meiner Reaktion."),
        ("user", "Was erhoffen Sie sich aus meiner Unterstützung heraus?"),
        ("vikl", "Ich erhoffe mir Tipps, wie ich mit meinem Sohn über sein verändertes Verhalten und den Verdacht auf Drogenkonsum sprechen kann."),
        ("user", "Haben Sie schonmal versucht ihn darauf anzusprechen?"),
        ("vikl", "Ja, ich habe bereits versucht, das Thema mit Max anzusprechen. Leider blockt er immer wieder ab."),
        ("user", "Woran machen Sie es aus, dass Max Marihuana nimmt?"),
        ("vikl", "Max verhält sich anders als früher, er ist oft müde, apathisch und isst wenig. Zudem hat er aufgehört, regelmäßig Fußball zu spielen."),
        ("user", "Sollte Max Angst vor Ihnen haben, falls sich der Verdacht bestätigt?"),
        ("vikl", "Nein, ich hoffe, dass er versteht, dass ich professionelle Hilfe suche, um ihm besser helfen zu können."),
        ("user", "Suchen Sie aktiv das Gespräch zu Max und legen Sie ihm Ihre Vermutungen offen dar."),
        ("vikl", "Ich werde aktiv ein Gespräch mit Max suchen und meine Vermutungen offenlegen."),
        ("user", "Wie hoch sehen Sie Ihre Erfolgschancen dass Max sich Ihnen öffnet?"),
        ("vikl", "Ich schätze meine Erfolgschancen als eher gering ein, da Max bisher zurückhaltend war, sich zu öffnen."),
        ("user", "Was denken Sie würde die Erfolgschancen höher werden lassen?"),
        ("vikl", "Eine Kombination aus offener, wertschätzender Kommunikation und gezielter Förderung von Vertrauen."),
        ("user", "Dann wenden Sie dies an."),
        ("vikl", "Ich werde offene und wertschätzende Kommunikation mit Max suchen, um sein Vertrauen zu gewinnen."),
        ("user", "Gerne"),
        ("vikl", "Danke für Ihre Unterstützung."),
    ],
}

# ---------------------------------------------------------------------------
# Pending conversations – short snippets for pipeline variety
# ---------------------------------------------------------------------------
CONV_PENDING = [
    {
        "title": "Sorgerecht nach Trennung - 12.11.2024",
        "original_chat_id": "1480",
        "messages": [
            ("vikl", "Hallo, mein Partner und ich haben uns vor drei Wochen getrennt. Wir haben zwei Kinder, eine Tochter mit 7 und einen Sohn mit 4 Jahren. Ich bin mit den Kindern zu meiner Mutter gezogen."),
            ("user", "Vielen Dank, dass Sie sich melden. Das klingt nach einer sehr belastenden Situation. Wie geht es den Kindern mit der Veränderung?"),
            ("vikl", "Mein Sohn nässt wieder ein seit dem Umzug. Meine Tochter weigert sich, am Wochenende zum Vater zu gehen. Sie sagt, sie ist wütend auf ihn."),
            ("user", "Einnässen bei kleinen Kindern nach großen Veränderungen ist sehr häufig und meist vorübergehend. Die Wut Ihrer Tochter drückt oft einen Loyalitätskonflikt aus."),
            ("vikl", "Es ist jetzt noch schlimmer geworden. Mein Ex ist unangemeldet bei meiner Mutter aufgetaucht und es gab einen Streit vor den Kindern."),
        ],
    },
    {
        "title": "Schulverweigerung und Mobbing - 15.11.2024",
        "original_chat_id": "1485",
        "messages": [
            ("vikl", "Mein 14-jähriger Sohn weigert sich seit drei Wochen in die Schule zu gehen. Jeden Morgen klagt er über Kopf- und Bauchschmerzen."),
            ("user", "Schulverweigerung in diesem Alter signalisiert oft, dass sich etwas im sozialen Umfeld verändert hat. Die körperlichen Symptome sind eine Stressreaktion."),
            ("vikl", "Seine Klassenlehrerin hat erwähnt, dass eine Gruppe Jungen Kommentare über seine Kleidung macht. Als ich ihn vorsichtig gefragt habe, hat er angefangen zu weinen."),
            ("user", "Das klingt nach einer sehr belastenden Erfahrung für Ihren Sohn. Es ist wichtig, dass er merkt, dass Sie ihn ernst nehmen."),
        ],
    },
    {
        "title": "Bildschirmzeit und Schulleistungen - 18.11.2024",
        "original_chat_id": "1492",
        "messages": [
            ("vikl", "Mein 12-jähriger Sohn verbringt fünf bis sechs Stunden täglich am Computer mit einem Online-Spiel. Seine Noten sind deutlich abgerutscht."),
            ("user", "Das Muster, das Sie beschreiben – zunehmende Spielzeit, Rückzug von früheren Aktivitäten und sinkende Schulleistungen – geht über ein typisches Hobby hinaus."),
            ("vikl", "Seine Mathelehrerin sagt, er schläft im Unterricht ein und hat seit drei Wochen keine Hausaufgaben abgegeben. Zu Hause hat er ein Loch in die Tür geschlagen als ich den Router ausgeschaltet habe."),
        ],
    },
]

_METADATA_TEMPLATE = {
    "source": {"message_collection_key": "learn_counselling_messages"},
    "derived": {
        "models": [],
        "providers": [],
        "courses": ["Grüneberg - HDBA - Konzepte Beruflicher Beratung"],
        "authors": ["user", "vikl"],
    },
}

_PERSONA_ELKE = {
    "id": 1,
    "name": "Elke",
    "enabled": True,
    "properties": {
        "Steckbrief": {
            "Alter": 37,
            "Familienstand": "verheiratet, mehrere Kinder",
            "Geschlecht": "weiblich",
            "Job": "Hausfrau",
        },
        "Hauptanliegen": (
            "Elke macht sich Sorgen um ihren Sohn. Sie vermutet, dass er aufgrund "
            "seines Freundeskreises Drogen konsumiert bzw. Marihuana raucht."
        ),
    },
}


def seed_anonymization_demo_data(db_instance):
    """Seed anonymization pipeline demo conversations (idempotent, dev-only)."""
    from db.models.anonymization import (
        AnonymizationConversation,
        AnonymizationMessage,
        AnonymizationEntity,
        AnonymizationMessageVersion,
    )
    from db.tables import User

    if AnonymizationConversation.query.filter(
        AnonymizationConversation.source_file_path.like("seed://anonymization-demo%")
    ).first():
        logger.info("Anonymization demo data already seeded – skipping.")
        return

    admin = User.query.filter_by(username="admin").first()
    admin_id = admin.id if admin else None

    now = datetime.utcnow()
    created = []

    # --- Conversation 1: completed with entities ---
    conv1 = AnonymizationConversation(
        source_file_path="seed://anonymization-demo/elke-a",
        original_chat_id=CONV_COMPLETED["original_chat_id"],
        title=CONV_COMPLETED["title"],
        status="completed",
        message_count=len(CONV_COMPLETED["messages"]),
        entity_count=len(CONV_COMPLETED["entities"]),
        quality_rating=CONV_COMPLETED["quality_rating"],
        exclude_from_export=False,
        persona_json=_PERSONA_ELKE,
        metadata_json={
            **_METADATA_TEMPLATE,
            "derived": {**_METADATA_TEMPLATE["derived"], "message_count": len(CONV_COMPLETED["messages"])},
        },
        imported_at=now,
        imported_by=admin_id,
        updated_at=now,
        updated_by=admin_id,
        completed_at=now,
    )
    db_instance.session.add(conv1)
    db_instance.session.flush()

    msg_objects = []
    for idx, (author, original, anonymized) in enumerate(CONV_COMPLETED["messages"]):
        is_edited = idx == CONV_COMPLETED["edited_message_index"]
        msg = AnonymizationMessage(
            conversation_id=conv1.id,
            message_number=idx + 1,
            author=author,
            original_content=original,
            anonymized_content=anonymized,
            current_version=3 if is_edited else 1,
            is_manually_edited=is_edited,
        )
        db_instance.session.add(msg)
        msg_objects.append(msg)
    db_instance.session.flush()

    # Entities
    for msg_idx, label, orig, repl, start, end, db_hit in CONV_COMPLETED["entities"]:
        entity = AnonymizationEntity(
            message_id=msg_objects[msg_idx].id,
            label=label,
            original_text=orig,
            replacement_text=repl,
            start_pos=start,
            end_pos=end,
            group_key=f"PER:{orig}" if label == "PER" else None,
            group_mode="consistent" if label == "PER" else None,
            db_hit=db_hit,
        )
        db_instance.session.add(entity)

    # Message versions for the edited message
    edited_msg = msg_objects[CONV_COMPLETED["edited_message_index"]]
    for v_num, v_content in enumerate(CONV_COMPLETED["edit_versions"], start=1):
        version = AnonymizationMessageVersion(
            message_id=edited_msg.id,
            version_number=v_num,
            content=v_content,
            change_description="" if v_num == 1 else "Manual correction",
            changed_by=admin_id or 1,
            changed_at=now,
        )
        db_instance.session.add(version)

    created.append(f"'{conv1.title}' (completed, {conv1.entity_count} entities)")

    # --- Conversation 2: in_progress, no NER ---
    conv2 = AnonymizationConversation(
        source_file_path="seed://anonymization-demo/elke-b",
        original_chat_id=CONV_IN_PROGRESS["original_chat_id"],
        title=CONV_IN_PROGRESS["title"],
        status="in_progress",
        message_count=len(CONV_IN_PROGRESS["messages"]),
        entity_count=0,
        persona_json=_PERSONA_ELKE,
        metadata_json={
            **_METADATA_TEMPLATE,
            "derived": {**_METADATA_TEMPLATE["derived"], "message_count": len(CONV_IN_PROGRESS["messages"])},
        },
        imported_at=now,
        imported_by=admin_id,
        updated_at=now,
    )
    db_instance.session.add(conv2)
    db_instance.session.flush()

    for idx, (author, content) in enumerate(CONV_IN_PROGRESS["messages"]):
        msg = AnonymizationMessage(
            conversation_id=conv2.id,
            message_number=idx + 1,
            author=author,
            original_content=content,
            anonymized_content=content,  # no NER yet
        )
        db_instance.session.add(msg)

    created.append(f"'{conv2.title}' (in_progress, no NER)")

    # --- Pending conversations ---
    for pending in CONV_PENDING:
        conv = AnonymizationConversation(
            source_file_path=f"seed://anonymization-demo/{pending['original_chat_id']}",
            original_chat_id=pending["original_chat_id"],
            title=pending["title"],
            status="pending",
            message_count=len(pending["messages"]),
            entity_count=0,
            metadata_json={
                **_METADATA_TEMPLATE,
                "derived": {**_METADATA_TEMPLATE["derived"], "message_count": len(pending["messages"])},
            },
            imported_at=now,
            imported_by=admin_id,
            updated_at=now,
        )
        db_instance.session.add(conv)
        db_instance.session.flush()

        for idx, (author, content) in enumerate(pending["messages"]):
            msg = AnonymizationMessage(
                conversation_id=conv.id,
                message_number=idx + 1,
                author=author,
                original_content=content,
                anonymized_content=content,
            )
            db_instance.session.add(msg)

        created.append(f"'{conv.title}' (pending)")

    db_instance.session.commit()
    logger.info("✅ Anonymization demo data seeded: %s", ", ".join(created))
