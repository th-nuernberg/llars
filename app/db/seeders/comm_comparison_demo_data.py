"""
Communication-Comparison demo scenario (function_type_id = 8).

A small built-in counselling dataset that exercises the
``communication_comparison`` interface variant. Same A/B mechanics as
the regular Comparison demo; differs in the UI shell: distinct option
colours, a "send" framing on the CTA, fly-out animation, and an
optional response-prompt + rater-note block under the conversation.

Idempotent — running this seeder twice updates the config but never
duplicates items, features, messages or memberships.
"""

from datetime import datetime, timedelta


# Small hand-crafted German counselling slice. Each entry is one
# conversation context (~2 turns) plus two candidate next-counsellor
# replies. Designed so the difference between A and B is real but
# non-trivial — perfect for exercising the new UI flow without
# requiring an external dataset.
COMM_COMPARISON_DEMO_DATA = [
    {
        "subject": "Erstkontakt: Stress in der Ausbildung",
        "messages": [
            ("Klient*in",
             "Hi, ich mache gerade eine Ausbildung und es wächst mir komplett über den Kopf. "
             "Schlafen kann ich auch kaum noch. Weiß nicht, ob das hier richtig ist?"),
        ],
        "candidates": [
            {
                "provenance": "human",
                "content": (
                    "Danke, dass du das so offen teilst. Schlafprobleme zusammen mit dem Druck "
                    "der Ausbildung sind ein Zeichen dafür, dass dein System gerade auf Hochtouren "
                    "läuft. Ich würde gerne erstmal mit dir schauen, was sich konkret bei dir "
                    "stapelt — auf der Arbeit und drumherum. Welche Aufgaben fühlen sich gerade "
                    "am schwersten an, und seit wann ist das so?"
                ),
            },
            {
                "provenance": "mis24b-instruct",
                "content": (
                    "Stress in der Ausbildung ist ein häufiges Phänomen. Es gibt verschiedene "
                    "Strategien zum Stressmanagement: 1) regelmäßige Pausen, 2) Sport, 3) "
                    "Atemübungen, 4) klare Tagesstruktur. Schlafhygiene ist ebenfalls wichtig — "
                    "fester Schlafrhythmus, kein Bildschirm vor dem Schlafen. Probiere diese "
                    "Tipps für zwei Wochen aus und melde dich gerne wieder."
                ),
            },
        ],
    },
    {
        "subject": "Streit mit Eltern wegen Konsum",
        "messages": [
            ("Klient*in",
             "Meine Eltern haben rausgefunden, dass ich kiffe. Jetzt eskaliert das voll. "
             "Ich kiff seit zwei Jahren ab und zu am Wochenende, das ist doch nicht so wild?"),
        ],
        "candidates": [
            {
                "provenance": "human",
                "content": (
                    "Klingt, als ob da gerade ziemlich viel auf einmal aufeinanderprallt. "
                    "Was dich mit deinen Eltern gerade beschäftigt, ist das eine — und davon "
                    "trennen würde ich erstmal die Frage, wie sich der Konsum für dich anfühlt. "
                    "Du hast den Rahmen ja selbst beschrieben: ab und zu am Wochenende. Was wäre "
                    "denn dein eigenes Empfinden, wenn du gerade ehrlich auf den Konsum schaust — "
                    "passt das für dich noch, oder hat sich da was verändert?"
                ),
            },
            {
                "provenance": "qwen25-72b-instrprofi",
                "content": (
                    "Es ist verständlich, dass du dich von deinen Eltern angegriffen fühlst. "
                    "Cannabis-Konsum ist tatsächlich gesundheitlich nicht unbedenklich — "
                    "auch gelegentlicher Konsum kann das Gehirn im jugendlichen Alter beeinflussen. "
                    "Hast du dir Gedanken gemacht, was deine Eltern eigentlich genau bewegt? Manchmal "
                    "geht es weniger um das Kiffen selbst, sondern um Vertrauen und Sorge."
                ),
            },
        ],
    },
    {
        "subject": "Trennung — und jetzt?",
        "messages": [
            ("Klient*in",
             "Mein Freund hat letzte Woche Schluss gemacht, einfach so. Ich funktioniere "
             "irgendwie noch im Job, aber abends fang ich an zu weinen und kann gar nicht mehr aufhören."),
        ],
        "candidates": [
            {
                "provenance": "human",
                "content": (
                    "Danke, dass du dich gemeldet hast — gerade jetzt, wo du tagsüber funktionierst, "
                    "ist es nicht selbstverständlich, sich abends nochmal zu trauen, das Ganze "
                    "anzuschauen. Diese Wellen, die abends kommen, sind in der Akutphase einer "
                    "Trennung typisch — auch wenn das natürlich nicht weniger anstrengend macht. "
                    "Was würde dir gerade helfen: erstmal über das letzte Gespräch sprechen, "
                    "oder eher überlegen, wie du die Abende für dich gestaltest?"
                ),
            },
            {
                "provenance": "min8b-instrprofi",
                "content": (
                    "Trennungen gehören zu den schmerzhaftesten Erfahrungen im Leben. Es ist normal, "
                    "dass du jetzt traurig bist. Achte gut auf dich: viel trinken, ausreichend schlafen, "
                    "mit Freundinnen sprechen. In ein paar Wochen wird es besser. Falls die Tränen "
                    "nicht aufhören, könntest du auch eine längere Therapie in Erwägung ziehen."
                ),
            },
        ],
    },
    {
        "subject": "Mobbing am Arbeitsplatz",
        "messages": [
            ("Klient*in",
             "Auf der Arbeit werde ich seit Monaten ausgeschlossen, Witze auf meine Kosten, niemand "
             "redet im Pausenraum mit mir. Mein Chef sagt, ich soll mich nicht so anstellen."),
        ],
        "candidates": [
            {
                "provenance": "human",
                "content": (
                    "Was du erlebst, hat einen Namen — und ich glaube dir, dass das nicht "
                    "übertrieben ist. 'Sich nicht so anstellen' verschiebt die Verantwortung "
                    "auf dich, dabei beschreibst du ein Verhalten der anderen, das deine "
                    "Gesundheit beeinträchtigt. Wie sehr beeinträchtigt dich das aktuell — "
                    "auch außerhalb der Arbeitszeit? Und gibt es im Betrieb jemanden, "
                    "neben deinem Chef, mit dem du sprechen könntest — Betriebsrat, "
                    "Vertrauensperson, Personalabteilung?"
                ),
            },
            {
                "provenance": "chatpsychiatrist-vicuna-7b",
                "content": (
                    "Es klingt, als würdest du unter Mobbing leiden. Mobbing am Arbeitsplatz "
                    "ist illegal und es gibt rechtliche Schritte, die du unternehmen kannst. "
                    "Ich empfehle dir, ein Mobbing-Tagebuch zu führen und einen Anwalt zu "
                    "kontaktieren. Außerdem solltest du dich krankschreiben lassen, "
                    "wenn die Belastung zu groß wird."
                ),
            },
        ],
    },
    {
        "subject": "Sorge um Freundin",
        "messages": [
            ("Klient*in",
             "Meine beste Freundin redet seit ein paar Wochen davon, dass alles sinnlos sei. "
             "Ich weiß nicht, ob ich das ernst nehmen soll oder ob ich übertreibe."),
        ],
        "candidates": [
            {
                "provenance": "human",
                "content": (
                    "Ich nehme deine Sorge sehr ernst. Solche Sätze über längere Zeit hinweg "
                    "sind ein Signal, dem man nachgehen darf — auch wenn du nicht sicher bist, "
                    "wie sie es meint. Hast du schon mal direkt mit ihr darüber gesprochen? "
                    "Konkret, also ungefähr so: 'Ich frage mich, wenn du sagst alles sei sinnlos — "
                    "wie meinst du das genau?'. Manchmal entlastet so eine direkte Frage, "
                    "und manchmal öffnet sich dadurch auch erst der Raum."
                ),
            },
            {
                "provenance": "mis24b-instruct",
                "content": (
                    "Das ist eine schwierige Situation. Bei Suizidgedanken sollte man immer "
                    "professionelle Hilfe holen — am besten direkt den Krisendienst oder die "
                    "Telefonseelsorge unter 0800/1110111. Du kannst deiner Freundin auch raten, "
                    "sich an ihren Hausarzt zu wenden. Wenn akute Gefahr besteht, ruf den "
                    "Notarzt unter 112."
                ),
            },
        ],
    },
]


def _get_comm_comparison_config():
    """Static config blob persisted on the RatingScenarios row."""
    return {
        "type": "communication_comparison",
        "eval_config": {
            "type": "communication_comparison",
            "config": {
                "question": {
                    "de": "Welche der beiden Antworten würden Sie als Berater*in eher senden?",
                    "en": "Which of the two responses would you as a counsellor sooner send?",
                },
                "task_description_markdown": {
                    "de": (
                        "## Aufgabe\n"
                        "Sie sehen einen kurzen Gesprächsverlauf und zwei Vorschläge für die "
                        "**nächste Berater\\*innen-Antwort**. Wählen Sie die Antwort, die Sie "
                        "selbst als geschulte Kolleg\\*in senden würden — und schreiben Sie "
                        "in einem Satz, warum.\n\n"
                        "**Achten Sie auf:** Empathie, professionelle Haltung, Resonanz mit "
                        "dem zuvor Gesagten, Vermeidung vorschneller Lösungen."
                    ),
                    "en": (
                        "## Task\n"
                        "You see a short conversation and two candidate **next-counsellor "
                        "responses**. Pick the response you yourself would send as a trained "
                        "colleague — and jot down briefly why.\n\n"
                        "**Watch for:** empathy, professional stance, resonance with what was "
                        "just said, avoiding premature solutions."
                    ),
                },
                "response_prompt": {
                    "de": "Wie würden Sie hier antworten?",
                    "en": "How would you respond here?",
                },
                "rater_note_enabled": True,
                "rater_note_placeholder": {
                    "de": "z. B. warmer Einstieg, passt zur Phase (optional)",
                    "en": "e.g. warm opener, matches the phase (optional)",
                },
                "allow_tie": False,
                "show_source": False,
                "gamification_enabled": True,
                "gamification_first_milestone": 3,
                "gamification_recurring_milestone": 2,
                "progressive_reveal": False,
            },
        },
        "allow_tie": False,
        "show_source": False,
    }


def seed_comm_comparison_demo_scenario(db):
    """Create a Communication-Comparison demo scenario (function_type_id=8).

    Idempotent — re-running updates the config and tops up missing items
    / features / messages without duplicating rows.
    """
    from db.models import (
        User, EvaluationItem, Message, Feature, FeatureType,
        RatingScenarios, ScenarioUsers, ScenarioItems,
        ScenarioRoles, FeatureFunctionType,
    )

    print("\n" + "=" * 60)
    print("Seeding Communication-Comparison Demo (function_type_id=8)...")
    print("=" * 60)

    researcher = User.query.filter_by(username='researcher').first()
    admin = User.query.filter_by(username='admin').first()
    if not researcher:
        print("  ERROR: researcher user not found — skipping comm-comparison demo")
        return None

    comm_type = FeatureFunctionType.query.filter_by(
        name='communication_comparison'
    ).first()
    if not comm_type:
        print("  ERROR: communication_comparison function type not found")
        return None

    feature_type = FeatureType.query.filter_by(name='Summary').first()
    if not feature_type:
        feature_type = FeatureType(name='Summary')
        db.session.add(feature_type)
        db.session.flush()

    def _ensure_item(idx: int, data: dict):
        """One EvaluationItem with 2 messages + 2 candidate features."""
        # institut_id=1 is the dev-default institute. chat_id offset 32000
        # so we don't collide with the existing 31000-range comparison demo.
        chat_id = 32000 + idx
        item = EvaluationItem.query.filter_by(
            chat_id=chat_id,
            institut_id=1,
            function_type_id=comm_type.function_type_id,
        ).first()
        if not item:
            item = EvaluationItem(
                chat_id=chat_id,
                institut_id=1,
                subject=data['subject'],
                sender='Klient',
                function_type_id=comm_type.function_type_id,
            )
            db.session.add(item)
            db.session.flush()

        if Message.query.filter_by(item_id=item.item_id).count() == 0:
            base_time = datetime.now() - timedelta(days=10 - idx, hours=4)
            for msg_idx, (sender, content) in enumerate(data['messages']):
                db.session.add(Message(
                    item_id=item.item_id,
                    sender=sender,
                    content=content,
                    timestamp=base_time + timedelta(hours=msg_idx * 3),
                ))

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

    items = [_ensure_item(i, d) for i, d in enumerate(COMM_COMPARISON_DEMO_DATA)]

    existing = RatingScenarios.query.filter_by(
        scenario_name='Demo Kommunikationsvergleich'
    ).first()

    if existing:
        existing.config_json = _get_comm_comparison_config()
        if not existing.created_by:
            existing.created_by = researcher.username
        scenario = existing
        print("  Demo scenario exists — config refreshed")
    else:
        # IMPORTANT: use utcnow(), not now(). The status-derivation in
        # scenario_manager_api.py compares `scenario.begin` against
        # `datetime.utcnow()` — if we seed `begin` in local time (which
        # in CET/CEST is 1-2 h ahead of UTC), the API sees the scenario
        # as "starts in the future" and returns status='draft', which the
        # EvaluationHub filter then hides. Using utcnow keeps both sides
        # of the comparison in the same naive-UTC frame so the scenario
        # is immediately picked up as 'evaluating'.
        utc_now = datetime.utcnow()
        scenario = RatingScenarios(
            scenario_name='Demo Kommunikationsvergleich',
            function_type_id=comm_type.function_type_id,
            begin=utc_now,
            end=utc_now + timedelta(days=90),
            timestamp=utc_now,
            config_json=_get_comm_comparison_config(),
            created_by=researcher.username,
        )
        db.session.add(scenario)
        db.session.flush()
        print(f"  Created scenario id={scenario.id}")

    # Link items to scenario (idempotent: skip already-linked).
    linked_item_ids = {
        si.item_id for si in ScenarioItems.query.filter_by(
            scenario_id=scenario.id
        ).all()
    }
    for item in items:
        if item.item_id not in linked_item_ids:
            db.session.add(ScenarioItems(
                scenario_id=scenario.id, item_id=item.item_id
            ))

    # Memberships — researcher is owner+assessor (designs evaluations,
    # participates in rating). Admin gets owner-level rights too so the
    # demo is reachable from the bootstrap admin account.
    def _ensure_member(user, manager_role, evaluation_role):
        existing_su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id, user_id=user.id
        ).first()
        if existing_su:
            existing_su.manager_role = manager_role
            existing_su.evaluation_role = evaluation_role
            existing_su.is_assessor = evaluation_role == 'assessor'
            return
        db.session.add(ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            manager_role=manager_role,
            evaluation_role=evaluation_role,
            is_assessor=evaluation_role == 'assessor',
            invitation_status='ACCEPTED',
            invited_at=datetime.now(),
            responded_at=datetime.now(),
            invited_by='system',
            membership_status='ACTIVE',
        ))

    _ensure_member(researcher, manager_role='owner', evaluation_role='assessor')
    if admin and admin.id != researcher.id:
        _ensure_member(admin, manager_role='owner', evaluation_role='none')

    db.session.commit()
    print(f"  Communication-Comparison demo ready: "
          f"{len(items)} items, researcher (owner+assessor) on scenario {scenario.id}")
    print("=" * 60)
    return scenario
