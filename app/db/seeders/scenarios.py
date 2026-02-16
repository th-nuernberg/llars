"""
Scenario Seeder for Development

Seeds example Rating and Ranking scenarios with sample email threads,
messages, and LLM-generated features for testing purposes.

Maps scenarios to 'evaluator' and 'researcher' users.

In development mode (PROJECT_STATE=development), seeds 20-30 samples per
scenario type for realistic demos.
"""

from datetime import datetime, timedelta
import hashlib
import os


DEMO_PROVENANCE_GENERATION_MODELS = [
    "Mistral Small",
    "Magistral Small",
    "GPT-5 Nano",
    "GPT-5 Mini",
]

DEMO_PROVENANCE_PROMPTS = [
    "Situation Summary",
    "Client Needs",
    "Recommended Actions",
    "Risk Assessment",
]

DEMO_PROVENANCE_EVALUATORS = [
    "Global/Mistral/Magistral-Small-2509",
    "Global/OpenAI/gpt-5-mini",
]


def _is_development_mode() -> bool:
    """Check if running in development mode for extended demo data."""
    project_state = os.environ.get('PROJECT_STATE', '').lower()
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    return project_state == 'development' or flask_env == 'development'


def _deterministic_bucket(item_id: int, feature_id: int, evaluator_model_id: str) -> str:
    """
    Deterministically assign a bucket for demo LLM rankings.

    Keeps results stable across restarts while still creating realistic spread.
    """
    token = f"{item_id}:{feature_id}:{evaluator_model_id}".encode("utf-8")
    score = int(hashlib.sha256(token).hexdigest()[:8], 16) % 100
    if score < 46:
        return "gut"
    if score < 82:
        return "mittel"
    return "schlecht"


def _build_demo_feature_content(prompt_name: str, model_name: str, source_text: str) -> str:
    """Build concise synthetic ranking feature content for demo provenance."""
    compact_source = " ".join((source_text or "").split())
    if len(compact_source) > 220:
        compact_source = f"{compact_source[:217]}..."

    templates = {
        "Situation Summary": (
            f"{model_name}: Die Situation zeigt eine komplexe Belastung mit mehreren "
            f"gleichzeitigen Anforderungen. {compact_source}"
        ),
        "Client Needs": (
            f"{model_name}: Im Fokus stehen Klärung, Struktur und alltagstaugliche "
            f"Unterstützungsschritte. {compact_source}"
        ),
        "Recommended Actions": (
            f"{model_name}: Empfohlen werden priorisierte Sofortmaßnahmen, "
            f"ein klarer Ablaufplan und verbindliche Follow-ups. {compact_source}"
        ),
        "Risk Assessment": (
            f"{model_name}: Das Risiko ist moderat bis erhöht, wenn keine "
            f"zeitnahe Stabilisierung erfolgt. {compact_source}"
        ),
    }
    return templates.get(prompt_name, f"{model_name}: {compact_source}")


def _is_demo_ranking_already_balanced(
    *,
    scenario,
    scenario_items,
    feature_model_by_name,
    feature_type_by_name,
    Feature,
    LLMTaskResult,
) -> bool:
    """Check whether the demo ranking scenario already matches the balanced cartesian setup."""
    item_ids = [si.item_id for si in scenario_items if si.item_id is not None]
    if not item_ids:
        return False

    expected_features_per_item = len(feature_model_by_name) * len(feature_type_by_name)
    expected_total_features = len(item_ids) * expected_features_per_item

    item_features = (
        Feature.query
        .filter(Feature.item_id.in_(item_ids))
        .all()
    )
    if len(item_features) != expected_total_features:
        return False

    model_ids = {llm.llm_id for llm in feature_model_by_name.values()}
    type_ids = {ft.type_id for ft in feature_type_by_name.values()}

    per_item_combo_count = {}
    for feature in item_features:
        if feature.llm_id not in model_ids or feature.type_id not in type_ids:
            return False
        key = (feature.item_id, feature.llm_id, feature.type_id)
        per_item_combo_count[key] = per_item_combo_count.get(key, 0) + 1

    if any(count != 1 for count in per_item_combo_count.values()):
        return False

    expected_rows = len(item_ids) * len(DEMO_PROVENANCE_EVALUATORS)
    existing_rows = (
        LLMTaskResult.query
        .filter_by(scenario_id=scenario.id, task_type='ranking')
        .count()
    )
    return existing_rows == expected_rows


def _rebalance_demo_ranking_provenance(db, ranking_scenario):
    """
    Rebuild demo ranking features/rankings into a balanced cartesian setup.

    This replaces legacy SummEval-heavy demo data for scenario provenance demos.
    """
    from ..tables import Feature, FeatureType, LLM, Message, UserFeatureRanking
    from db.models.scenario import ScenarioItems
    from db.models.llm_task_result import LLMTaskResult

    if not ranking_scenario or ranking_scenario.scenario_name != 'Demo Ranking Szenario':
        return

    scenario_items = (
        ScenarioItems.query
        .filter_by(scenario_id=ranking_scenario.id)
        .order_by(ScenarioItems.id.asc())
        .all()
    )
    item_ids = [si.item_id for si in scenario_items if si.item_id is not None]
    if not item_ids:
        return

    # Ensure feature-generation model labels exist (legacy llms table, used by features).
    feature_model_by_name = {}
    for model_name in DEMO_PROVENANCE_GENERATION_MODELS:
        llm = LLM.query.filter_by(name=model_name).first()
        if not llm:
            llm = LLM(name=model_name)
            db.session.add(llm)
            db.session.flush()
        feature_model_by_name[model_name] = llm

    # Ensure prompt types exist.
    feature_type_by_name = {}
    for prompt_name in DEMO_PROVENANCE_PROMPTS:
        ft = FeatureType.query.filter_by(name=prompt_name).first()
        if not ft:
            ft = FeatureType(name=prompt_name)
            db.session.add(ft)
            db.session.flush()
        feature_type_by_name[prompt_name] = ft

    if _is_demo_ranking_already_balanced(
        scenario=ranking_scenario,
        scenario_items=scenario_items,
        feature_model_by_name=feature_model_by_name,
        feature_type_by_name=feature_type_by_name,
        Feature=Feature,
        LLMTaskResult=LLMTaskResult,
    ):
        return

    existing_features = Feature.query.filter(Feature.item_id.in_(item_ids)).all()
    existing_feature_ids = [f.feature_id for f in existing_features]

    if existing_feature_ids:
        UserFeatureRanking.query.filter(
            UserFeatureRanking.feature_id.in_(existing_feature_ids)
        ).delete(synchronize_session=False)

    LLMTaskResult.query.filter_by(
        scenario_id=ranking_scenario.id,
        task_type='ranking'
    ).delete(synchronize_session=False)

    Feature.query.filter(Feature.item_id.in_(item_ids)).delete(synchronize_session=False)
    db.session.flush()

    # Recreate balanced cartesian feature set.
    features_by_item = {}
    for item_id in item_ids:
        latest_message = (
            Message.query
            .filter_by(item_id=item_id)
            .order_by(Message.message_id.desc())
            .first()
        )
        source_text = latest_message.content if latest_message and latest_message.content else ""

        created_feature_ids = []
        for model_name in DEMO_PROVENANCE_GENERATION_MODELS:
            llm = feature_model_by_name[model_name]
            for prompt_name in DEMO_PROVENANCE_PROMPTS:
                ft = feature_type_by_name[prompt_name]
                feature = Feature(
                    item_id=item_id,
                    type_id=ft.type_id,
                    llm_id=llm.llm_id,
                    content=_build_demo_feature_content(prompt_name, model_name, source_text),
                )
                db.session.add(feature)
                db.session.flush()
                created_feature_ids.append(feature.feature_id)

        features_by_item[item_id] = created_feature_ids

    # Recreate LLM ranking results for demo evaluators.
    now = datetime.utcnow()
    for evaluator_model_id in DEMO_PROVENANCE_EVALUATORS:
        for item_id in item_ids:
            payload = {"gut": [], "mittel": [], "schlecht": [], "neutral": []}
            for feature_id in features_by_item.get(item_id, []):
                bucket = _deterministic_bucket(item_id, feature_id, evaluator_model_id)
                payload[bucket].append(feature_id)

            db.session.add(LLMTaskResult(
                scenario_id=ranking_scenario.id,
                item_id=item_id,
                model_id=evaluator_model_id,
                task_type='ranking',
                payload_json=payload,
                error=None,
                created_at=now,
                updated_at=now,
            ))

    # Keep scenario config aligned with demo evaluators and metadata.
    config = ranking_scenario.config_json or {}
    config['evaluation'] = 'ranking'
    config['enable_llm_evaluation'] = True
    config['llm_evaluators'] = DEMO_PROVENANCE_EVALUATORS
    config['demo_generation_models'] = DEMO_PROVENANCE_GENERATION_MODELS
    config['demo_generation_prompts'] = DEMO_PROVENANCE_PROMPTS
    ranking_scenario.config_json = config

    db.session.commit()
    print(
        "  Rebalanced Demo Ranking Szenario provenance "
        f"({len(item_ids)} items, {len(item_ids) * len(DEMO_PROVENANCE_GENERATION_MODELS) * len(DEMO_PROVENANCE_PROMPTS)} features)"
    )


def seed_demo_scenarios(db):
    """
    Seed demo scenarios for Rating and Ranking with sample data.

    Creates:
    - Sample email threads with messages
    - LLM-generated features for the threads
    - A Rating scenario mapped to evaluator/researcher
    - A Ranking scenario mapped to evaluator/researcher

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import (
        User, UserGroup, EmailThread, Message, Feature, FeatureType, LLM,
        FeatureFunctionType, RatingScenarios, ScenarioUsers,
        ScenarioThreads, ScenarioThreadDistribution, ScenarioRoles,
        AuthenticityConversation,
    )

    print("Seeding demo scenarios...")

    import uuid

    # Get or create users for demo scenarios
    evaluator_user = User.query.filter_by(username='evaluator').first()
    researcher_user = User.query.filter_by(username='researcher').first()
    ijcai_reviewer_1 = User.query.filter_by(username='ijcai_reviewer_1').first()
    ijcai_reviewer_2 = User.query.filter_by(username='ijcai_reviewer_2').first()
    admin_user = User.query.filter_by(username='admin').first()

    # Get default user group
    default_group = UserGroup.query.filter_by(name='Standard').first()
    if not default_group:
        default_group = UserGroup(name='Standard')
        db.session.add(default_group)
        db.session.flush()

    if not evaluator_user:
        evaluator_user = User(
            username='evaluator',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(evaluator_user)
        print("  Created user: evaluator")

    if not researcher_user:
        researcher_user = User(
            username='researcher',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(researcher_user)
        print("  Created user: researcher")

    if not ijcai_reviewer_1:
        ijcai_reviewer_1 = User(
            username='ijcai_reviewer_1',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(ijcai_reviewer_1)
        print("  Created user: ijcai_reviewer_1")

    if not ijcai_reviewer_2:
        ijcai_reviewer_2 = User(
            username='ijcai_reviewer_2',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(ijcai_reviewer_2)
        print("  Created user: ijcai_reviewer_2")

    db.session.flush()
    if admin_user:
        print(
            "  Users ready: evaluator (id=%s), researcher (id=%s), "
            "ijcai_reviewer_1 (id=%s), ijcai_reviewer_2 (id=%s), admin (id=%s)"
            % (evaluator_user.id, researcher_user.id, ijcai_reviewer_1.id, ijcai_reviewer_2.id, admin_user.id)
        )
    else:
        print(
            "  Users ready: evaluator (id=%s), researcher (id=%s), "
            "ijcai_reviewer_1 (id=%s), ijcai_reviewer_2 (id=%s)"
            % (evaluator_user.id, researcher_user.id, ijcai_reviewer_1.id, ijcai_reviewer_2.id)
        )

    # Get function types
    rating_type = FeatureFunctionType.query.filter_by(name='rating').first()
    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    mail_rating_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
    authenticity_type = FeatureFunctionType.query.filter_by(name='authenticity').first()
    labeling_type = FeatureFunctionType.query.filter_by(name='labeling').first()
    if not labeling_type:
        labeling_type = FeatureFunctionType.query.filter_by(name='text_classification').first()

    if not rating_type or not ranking_type or not mail_rating_type or not authenticity_type or not labeling_type:
        print("  ERROR: FeatureFunctionTypes not found. Run initialize_feature_function_types first.")
        return

    # Create or get LLMs
    llm_gpt4 = LLM.query.filter_by(name='GPT-4').first()
    if not llm_gpt4:
        llm_gpt4 = LLM(name='GPT-4')
        db.session.add(llm_gpt4)

    llm_claude = LLM.query.filter_by(name='Claude-3').first()
    if not llm_claude:
        llm_claude = LLM(name='Claude-3')
        db.session.add(llm_claude)

    llm_mistral = LLM.query.filter_by(name='Mistral-7B').first()
    if not llm_mistral:
        llm_mistral = LLM(name='Mistral-7B')
        db.session.add(llm_mistral)

    # Create LLM entry for SummEval dataset (for ranking features)
    llm_summeval = LLM.query.filter_by(name='SummEval').first()
    if not llm_summeval:
        llm_summeval = LLM(name='SummEval')
        db.session.add(llm_summeval)

    db.session.flush()

    # Create or get Feature Types
    feature_types = {}
    for ft_name in ['Situation Summary', 'Client Needs', 'Recommended Actions', 'Risk Assessment', 'Summary']:
        ft = FeatureType.query.filter_by(name=ft_name).first()
        if not ft:
            ft = FeatureType(name=ft_name)
            db.session.add(ft)
        feature_types[ft_name] = ft

    db.session.flush()

    # Check if demo scenarios already exist
    existing_ranking = RatingScenarios.query.filter_by(scenario_name='Demo Ranking Szenario').first()
    existing_mail_rating = RatingScenarios.query.filter_by(scenario_name='Demo Verlauf Bewerter Szenario').first()
    existing_authenticity = RatingScenarios.query.filter_by(scenario_name='Demo Fake/Echt Szenario').first()
    existing_labeling = RatingScenarios.query.filter_by(scenario_name='Demo Labeling Szenario').first()

    def _ensure_scenario_user(scenario_id: int, user_id: int, role: ScenarioRoles) -> None:
        existing = ScenarioUsers.query.filter_by(scenario_id=scenario_id, user_id=user_id).first()
        if existing:
            return
        db.session.add(
            ScenarioUsers(
                scenario_id=scenario_id,
                user_id=user_id,
                role=role,
            )
        )
        db.session.flush()

    # Create sample email threads
    threads = []

    # Thread 1: Beratungsanfrage Berufsorientierung
    thread1 = EmailThread.query.filter_by(chat_id=9001, institut_id=1, function_type_id=rating_type.function_type_id).first()
    if not thread1:
        thread1 = EmailThread(
            chat_id=9001,
            institut_id=1,
            subject='Beratungsanfrage: Berufliche Neuorientierung',
            sender='klient1@example.com',
            function_type_id=rating_type.function_type_id
        )
        db.session.add(thread1)
        db.session.flush()

        # Messages for Thread 1
        messages1 = [
            Message(
                thread_id=thread1.thread_id,
                sender='Klient',
                content='Guten Tag, ich bin 35 Jahre alt und arbeite seit 10 Jahren im Vertrieb. In letzter Zeit fühle ich mich zunehmend unzufrieden mit meiner Arbeit und denke über eine berufliche Neuorientierung nach. Können Sie mir dabei helfen?',
                timestamp=datetime.now() - timedelta(days=5, hours=10)
            ),
            Message(
                thread_id=thread1.thread_id,
                sender='Berater',
                content='Vielen Dank für Ihre Nachricht. Es ist völlig normal, nach einigen Jahren im Beruf innezuhalten und die eigene Situation zu reflektieren. Können Sie mir mehr darüber erzählen, was genau Sie an Ihrer aktuellen Tätigkeit unzufrieden macht?',
                timestamp=datetime.now() - timedelta(days=5, hours=8)
            ),
            Message(
                thread_id=thread1.thread_id,
                sender='Klient',
                content='Hauptsächlich fehlt mir der Sinn in meiner Arbeit. Ich verkaufe Produkte, von denen ich nicht überzeugt bin. Außerdem ist der Druck durch die Zielvorgaben sehr hoch. Ich interessiere mich eigentlich mehr für den sozialen Bereich.',
                timestamp=datetime.now() - timedelta(days=4, hours=14)
            ),
            Message(
                thread_id=thread1.thread_id,
                sender='Berater',
                content='Das verstehe ich gut. Der Wunsch nach sinnstiftender Arbeit ist ein wichtiger Motivator. Haben Sie schon konkrete Vorstellungen, in welche Richtung es gehen könnte? Welche Ihrer Fähigkeiten aus dem Vertrieb könnten Sie in einem neuen Bereich einsetzen?',
                timestamp=datetime.now() - timedelta(days=4, hours=10)
            ),
        ]
        for msg in messages1:
            db.session.add(msg)

    threads.append(thread1)

    # Thread 2: Konflikt am Arbeitsplatz
    thread2 = EmailThread.query.filter_by(chat_id=9002, institut_id=1, function_type_id=rating_type.function_type_id).first()
    if not thread2:
        thread2 = EmailThread(
            chat_id=9002,
            institut_id=1,
            subject='Dringend: Konflikt mit Vorgesetztem',
            sender='klient2@example.com',
            function_type_id=rating_type.function_type_id
        )
        db.session.add(thread2)
        db.session.flush()

        messages2 = [
            Message(
                thread_id=thread2.thread_id,
                sender='Klient',
                content='Hallo, ich brauche dringend Hilfe. Seit mein neuer Chef vor 3 Monaten angefangen hat, gibt es ständig Probleme. Er kritisiert meine Arbeit vor dem ganzen Team und ignoriert meine Vorschläge komplett.',
                timestamp=datetime.now() - timedelta(days=3, hours=16)
            ),
            Message(
                thread_id=thread2.thread_id,
                sender='Berater',
                content='Das klingt nach einer sehr belastenden Situation. Solche Konflikte können sich stark auf das Wohlbefinden auswirken. Haben Sie schon versucht, das Gespräch mit Ihrem Vorgesetzten zu suchen?',
                timestamp=datetime.now() - timedelta(days=3, hours=12)
            ),
            Message(
                thread_id=thread2.thread_id,
                sender='Klient',
                content='Ja, einmal. Aber er hat alles abgestritten und gemeint, ich solle nicht so empfindlich sein. Seitdem ist es noch schlimmer geworden. Ich schlafe schlecht und habe Angst vor jedem Arbeitstag.',
                timestamp=datetime.now() - timedelta(days=2, hours=18)
            ),
        ]
        for msg in messages2:
            db.session.add(msg)

    threads.append(thread2)

    # Thread 3 for Ranking (different function type)
    thread3 = EmailThread.query.filter_by(chat_id=9003, institut_id=1, function_type_id=ranking_type.function_type_id).first()
    if not thread3:
        thread3 = EmailThread(
            chat_id=9003,
            institut_id=1,
            subject='Beratung: Work-Life-Balance',
            sender='klient3@example.com',
            function_type_id=ranking_type.function_type_id
        )
        db.session.add(thread3)
        db.session.flush()

        messages3 = [
            Message(
                thread_id=thread3.thread_id,
                sender='Klient',
                content='Ich arbeite als Projektmanagerin und mache regelmäßig 50-60 Stunden die Woche. Meine Familie leidet darunter und ich selbst bin oft erschöpft. Wie kann ich das ändern?',
                timestamp=datetime.now() - timedelta(days=2, hours=10)
            ),
            Message(
                thread_id=thread3.thread_id,
                sender='Berater',
                content='Vielen Dank für Ihr Vertrauen. Eine dauerhafte Überarbeitung kann ernsthafte Folgen haben. Lassen Sie uns gemeinsam schauen, welche Faktoren zu dieser Situation beitragen und was Sie verändern können.',
                timestamp=datetime.now() - timedelta(days=2, hours=6)
            ),
        ]
        for msg in messages3:
            db.session.add(msg)

    threads.append(thread3)

    # Thread 4 for Mail Rating (Verlauf Bewerter)
    thread4 = EmailThread.query.filter_by(chat_id=9004, institut_id=1, function_type_id=mail_rating_type.function_type_id).first()
    if not thread4:
        thread4 = EmailThread(
            chat_id=9004,
            institut_id=1,
            subject='Beratung: Studienabbruch und Neustart',
            sender='klient4@example.com',
            function_type_id=mail_rating_type.function_type_id
        )
        db.session.add(thread4)
        db.session.flush()

        messages4 = [
            Message(
                thread_id=thread4.thread_id,
                sender='Klient',
                content='Hallo, ich bin 22 und habe gerade mein Informatikstudium im 5. Semester abgebrochen. Meine Eltern sind enttäuscht und ich weiß nicht, wie es weitergehen soll. Programmieren macht mir keinen Spaß mehr.',
                timestamp=datetime.now() - timedelta(days=6, hours=14)
            ),
            Message(
                thread_id=thread4.thread_id,
                sender='Berater',
                content='Danke, dass Sie sich an uns wenden. Ein Studienabbruch ist keine Seltenheit und kein Weltuntergang. Wichtig ist, dass Sie jetzt herausfinden, was Sie wirklich interessiert. Was hat Sie ursprünglich zur Informatik geführt?',
                timestamp=datetime.now() - timedelta(days=6, hours=10)
            ),
            Message(
                thread_id=thread4.thread_id,
                sender='Klient',
                content='Ehrlich gesagt war es der Druck meiner Eltern. Sie meinten, damit verdient man gut. Aber ich interessiere mich viel mehr für kreative Dinge - Design, Fotografie, vielleicht auch Marketing.',
                timestamp=datetime.now() - timedelta(days=5, hours=16)
            ),
            Message(
                thread_id=thread4.thread_id,
                sender='Berater',
                content='Das ist eine wichtige Erkenntnis! Es gibt viele Berufe, die Kreativität und technisches Verständnis verbinden. Haben Sie schon einmal über Mediengestaltung oder UX/UI Design nachgedacht? Dort könnten Sie beides vereinen.',
                timestamp=datetime.now() - timedelta(days=5, hours=12)
            ),
            Message(
                thread_id=thread4.thread_id,
                sender='Klient',
                content='UX Design klingt interessant! Kann ich das auch ohne fertiges Studium machen? Und wie erkläre ich das meinen Eltern?',
                timestamp=datetime.now() - timedelta(days=4, hours=20)
            ),
            Message(
                thread_id=thread4.thread_id,
                sender='Berater',
                content='Es gibt verschiedene Wege ins UX Design - Bootcamps, Weiterbildungen oder ein neues Studium. Was Ihre Eltern betrifft: Zeigen Sie ihnen konkrete Berufsperspektiven und Gehaltsmöglichkeiten in diesem Bereich. Sollen wir gemeinsam einen Plan erarbeiten?',
                timestamp=datetime.now() - timedelta(days=4, hours=14)
            ),
        ]
        for msg in messages4:
            db.session.add(msg)

    # Thread 5 for Mail Rating (zweiter Fall)
    thread5 = EmailThread.query.filter_by(chat_id=9005, institut_id=1, function_type_id=mail_rating_type.function_type_id).first()
    if not thread5:
        thread5 = EmailThread(
            chat_id=9005,
            institut_id=1,
            subject='Wiedereinstieg nach Elternzeit',
            sender='klient5@example.com',
            function_type_id=mail_rating_type.function_type_id
        )
        db.session.add(thread5)
        db.session.flush()

        messages5 = [
            Message(
                thread_id=thread5.thread_id,
                sender='Klient',
                content='Guten Tag, nach 3 Jahren Elternzeit möchte ich wieder ins Berufsleben einsteigen. Ich war vorher Buchhalterin, aber die Digitalisierung hat vieles verändert. Bin ich noch auf dem aktuellen Stand?',
                timestamp=datetime.now() - timedelta(days=4, hours=9)
            ),
            Message(
                thread_id=thread5.thread_id,
                sender='Berater',
                content='Willkommen zurück! Ihre Bedenken sind verständlich, aber 3 Jahre sind gut aufzuholen. Die Grundlagen der Buchhaltung bleiben gleich, nur die Tools haben sich weiterentwickelt. Welche Software haben Sie zuletzt genutzt?',
                timestamp=datetime.now() - timedelta(days=4, hours=5)
            ),
            Message(
                thread_id=thread5.thread_id,
                sender='Klient',
                content='Hauptsächlich DATEV und Excel. Ich höre aber, dass jetzt viel mit Cloud-Lösungen gearbeitet wird und alles automatisiert ist. Macht mir das nicht Angst?',
                timestamp=datetime.now() - timedelta(days=3, hours=15)
            ),
            Message(
                thread_id=thread5.thread_id,
                sender='Berater',
                content='DATEV-Kenntnisse sind nach wie vor sehr gefragt! Die Cloud-Version ist intuitiv zu erlernen. Automatisierung betrifft vor allem repetitive Aufgaben - qualifizierte Buchhalter werden weiterhin gebraucht für Analyse und Beratung. Ich empfehle einen Auffrischungskurs.',
                timestamp=datetime.now() - timedelta(days=3, hours=11)
            ),
        ]
        for msg in messages5:
            db.session.add(msg)

    mail_rating_threads = [thread4, thread5]

    # Threads for Fake/Echt (Authenticity)
    authenticity_threads = []

    thread6 = EmailThread.query.filter_by(chat_id=9101, institut_id=3, function_type_id=authenticity_type.function_type_id).first()
    if not thread6:
        thread6 = EmailThread(
            chat_id=9101,
            institut_id=3,
            subject='Fake/Echt – Demo Fall (Echt)',
            sender='demo@example.com',
            function_type_id=authenticity_type.function_type_id
        )
        db.session.add(thread6)
        db.session.flush()

        messages6 = [
            Message(
                thread_id=thread6.thread_id,
                sender='Ratsuchende',
                content='Hallo, ich habe ein Problem mit meinem Chef und weiß nicht, wie ich damit umgehen soll.',
                timestamp=datetime.now() - timedelta(days=2, hours=10),
                generated_by='Human'
            ),
            Message(
                thread_id=thread6.thread_id,
                sender='Beratende',
                content='Danke für deine Nachricht. Magst du kurz beschreiben, was genau passiert ist und wie oft es vorkommt?',
                timestamp=datetime.now() - timedelta(days=2, hours=9, minutes=30),
                generated_by='Human'
            ),
        ]
        for msg in messages6:
            db.session.add(msg)

    authenticity_threads.append(thread6)

    if thread6 and not AuthenticityConversation.query.filter_by(thread_id=thread6.thread_id).first():
        meta6 = {
            "conversation_id": 9101,
            "augmentation_type": "reg_single_any",
            "replaced_positions": [],
            "num_replacements": 0,
            "total_messages": 2,
            "saeule": "3",
            "split": "train",
            "model": None,
            "model_short": None,
            "generated_at": datetime.now().isoformat(),
            "format_version": "v6",
        }
        db.session.add(
            AuthenticityConversation(
                thread_id=thread6.thread_id,
                sample_key="v6:demo-auth-9101",
                conversation_id=9101,
                augmentation_type=meta6.get("augmentation_type"),
                replaced_positions=meta6.get("replaced_positions"),
                num_replacements=meta6.get("num_replacements"),
                total_messages=meta6.get("total_messages"),
                saeule=meta6.get("saeule"),
                split=meta6.get("split"),
                model=meta6.get("model"),
                model_short=meta6.get("model_short"),
                generated_at=datetime.fromisoformat(meta6.get("generated_at")),
                format_version=meta6.get("format_version"),
                is_fake=False,
                metadata_json=meta6,
            )
        )

    thread7 = EmailThread.query.filter_by(chat_id=9102, institut_id=3, function_type_id=authenticity_type.function_type_id).first()
    if not thread7:
        thread7 = EmailThread(
            chat_id=9102,
            institut_id=3,
            subject='Fake/Echt – Demo Fall (Fake)',
            sender='demo@example.com',
            function_type_id=authenticity_type.function_type_id
        )
        db.session.add(thread7)
        db.session.flush()

        messages7 = [
            Message(
                thread_id=thread7.thread_id,
                sender='Ratsuchende',
                content='Hi, ich bin total überfordert mit meinem Studium und habe Angst zu versagen.',
                timestamp=datetime.now() - timedelta(days=1, hours=18),
                generated_by='Human'
            ),
            Message(
                thread_id=thread7.thread_id,
                sender='Beratende',
                content='Es tut mir leid, dass du dich so fühlst. Lass uns gemeinsam schauen, was dich am meisten belastet und welche nächsten Schritte möglich sind.',
                timestamp=datetime.now() - timedelta(days=1, hours=17, minutes=40),
                generated_by='gpt-5.1'
            ),
        ]
        for msg in messages7:
            db.session.add(msg)

    authenticity_threads.append(thread7)

    if thread7 and not AuthenticityConversation.query.filter_by(thread_id=thread7.thread_id).first():
        meta7 = {
            "conversation_id": 9102,
            "augmentation_type": "reg_single_any",
            "replaced_positions": [1],
            "num_replacements": 1,
            "total_messages": 2,
            "saeule": "3",
            "split": "train",
            "model": "gpt-5.1",
            "model_short": "gpt51",
            "generated_at": datetime.now().isoformat(),
            "format_version": "v6",
        }
        db.session.add(
            AuthenticityConversation(
                thread_id=thread7.thread_id,
                sample_key="v6:demo-auth-9102",
                conversation_id=9102,
                augmentation_type=meta7.get("augmentation_type"),
                replaced_positions=meta7.get("replaced_positions"),
                num_replacements=meta7.get("num_replacements"),
                total_messages=meta7.get("total_messages"),
                saeule=meta7.get("saeule"),
                split=meta7.get("split"),
                model=meta7.get("model"),
                model_short=meta7.get("model_short"),
                generated_at=datetime.fromisoformat(meta7.get("generated_at")),
                format_version=meta7.get("format_version"),
                is_fake=True,
                metadata_json=meta7,
            )
        )

    # Threads for Labeling (generalized text categorization)
    labeling_threads = []

    # Thread 8: Customer feedback for sentiment labeling
    thread8 = EmailThread.query.filter_by(chat_id=9201, institut_id=1, function_type_id=labeling_type.function_type_id).first()
    if not thread8:
        thread8 = EmailThread(
            chat_id=9201,
            institut_id=1,
            subject='Labeling Demo: Kundenfeedback',
            sender='demo@labeling.com',
            function_type_id=labeling_type.function_type_id
        )
        db.session.add(thread8)
        db.session.flush()

        messages8 = [
            Message(
                thread_id=thread8.thread_id,
                sender='Kunde',
                content='Ich bin sehr zufrieden mit dem Service! Die Beratung war kompetent und freundlich. Vielen Dank für die schnelle Hilfe.',
                timestamp=datetime.now() - timedelta(days=3, hours=14)
            ),
        ]
        for msg in messages8:
            db.session.add(msg)

    labeling_threads.append(thread8)

    # Thread 9: Mixed feedback
    thread9 = EmailThread.query.filter_by(chat_id=9202, institut_id=1, function_type_id=labeling_type.function_type_id).first()
    if not thread9:
        thread9 = EmailThread(
            chat_id=9202,
            institut_id=1,
            subject='Labeling Demo: Gemischtes Feedback',
            sender='demo@labeling.com',
            function_type_id=labeling_type.function_type_id
        )
        db.session.add(thread9)
        db.session.flush()

        messages9 = [
            Message(
                thread_id=thread9.thread_id,
                sender='Kunde',
                content='Die Wartezeit war leider sehr lang, aber als ich dann dran kam, war die Beratung hilfreich. Könnte besser organisiert sein.',
                timestamp=datetime.now() - timedelta(days=2, hours=11)
            ),
        ]
        for msg in messages9:
            db.session.add(msg)

    labeling_threads.append(thread9)

    # Thread 10: Negative feedback
    thread10 = EmailThread.query.filter_by(chat_id=9203, institut_id=1, function_type_id=labeling_type.function_type_id).first()
    if not thread10:
        thread10 = EmailThread(
            chat_id=9203,
            institut_id=1,
            subject='Labeling Demo: Kritisches Feedback',
            sender='demo@labeling.com',
            function_type_id=labeling_type.function_type_id
        )
        db.session.add(thread10)
        db.session.flush()

        messages10 = [
            Message(
                thread_id=thread10.thread_id,
                sender='Kunde',
                content='Enttäuschend. Niemand konnte mir weiterhelfen und ich wurde mehrfach weitergeleitet. Mein Problem ist immer noch nicht gelöst.',
                timestamp=datetime.now() - timedelta(days=1, hours=9)
            ),
        ]
        for msg in messages10:
            db.session.add(msg)

    labeling_threads.append(thread10)

    db.session.flush()

    # Create Features for each thread
    llms = [llm_gpt4, llm_claude, llm_mistral]

    feature_contents = {
        'Situation Summary': [
            'Der Klient befindet sich in einer beruflichen Umbruchphase. Nach 10 Jahren im Vertrieb verspürt er Unzufriedenheit aufgrund mangelnder Sinnhaftigkeit und hohem Leistungsdruck. Er zeigt Interesse am sozialen Bereich.',
            'Ein 35-jähriger Vertriebsmitarbeiter sucht nach beruflicher Neuorientierung. Die Hauptgründe sind: fehlende Identifikation mit den Produkten, hoher Zieldruck und der Wunsch nach sinnstiftender Arbeit im sozialen Sektor.',
            'Klient, männlich, 35 Jahre, dekadenlange Vertriebserfahrung. Aktuelle Problematik: Sinnkrise im Beruf, Interesse an Wechsel in soziale Arbeit. Reflexionsbereitschaft vorhanden.',
        ],
        'Client Needs': [
            'Der Klient benötigt Unterstützung bei der Identifikation übertragbarer Kompetenzen, Orientierung über Möglichkeiten im sozialen Bereich sowie emotionale Begleitung während des Veränderungsprozesses.',
            'Primäre Bedürfnisse: Karriereberatung, Kompetenzanalyse, Information über Umschulungsmöglichkeiten. Sekundär: Bestätigung der Entscheidung, Abbau von Veränderungsängsten.',
            'Beratungsbedarf in drei Dimensionen: 1) Berufliche Neuorientierung, 2) Transferfähigkeiten identifizieren, 3) Praktische Schritte zur Veränderung planen.',
        ],
        'Recommended Actions': [
            'Empfohlen wird: 1) Kompetenzprofil erstellen, 2) Informationsgespräche im sozialen Bereich arrangieren, 3) Weiterbildungsmöglichkeiten recherchieren, 4) Finanzielle Überbrückung planen.',
            'Nächste Schritte: Stärken-Schwächen-Analyse durchführen, Hospitationsmöglichkeiten im sozialen Bereich erkunden, Berufsberatung der Arbeitsagentur konsultieren.',
            'Handlungsempfehlungen: Reflexionsübungen zu Werten und Zielen, Netzwerkaufbau im Zielbereich, Prüfung von Fördermöglichkeiten für Berufswechsler.',
        ],
        'Risk Assessment': [
            'Risiken: Finanzielle Einbußen bei Branchenwechsel, längere Übergangsphase, mögliche Enttäuschung wenn Erwartungen nicht erfüllt werden. Chancen überwiegen bei guter Planung.',
            'Moderate Risikoeinschätzung. Hauptrisiko: Einkommensverlust. Mitigierende Faktoren: Berufserfahrung, Motivation, Planungsbereitschaft. Psychische Stabilität scheint gegeben.',
            'Risikoanalyse: Finanzielles Risiko (mittel), emotionales Risiko bei Misserfolg (niedrig-mittel), Risiko der Überforderung in neuem Feld (niedrig). Gesamtbewertung: vertretbares Risiko.',
        ],
    }

    # Add features to rating/ranking threads
    for thread in threads:
        for ft_name, contents in feature_contents.items():
            ft = feature_types[ft_name]
            for i, llm in enumerate(llms):
                # Check if feature already exists
                existing = Feature.query.filter_by(
                    thread_id=thread.thread_id,
                    type_id=ft.type_id,
                    llm_id=llm.llm_id
                ).first()

                if not existing:
                    feature = Feature(
                        thread_id=thread.thread_id,
                        type_id=ft.type_id,
                        llm_id=llm.llm_id,
                        content=contents[i]
                    )
                    db.session.add(feature)

    # Add features to mail rating threads (thread4 and thread5)
    mail_rating_feature_contents = {
        'Situation Summary': [
            'Ein 22-jähriger Klient hat sein Informatikstudium abgebrochen. Der ursprüngliche Studienwahl lag elterlicher Druck zugrunde. Der Klient zeigt Interesse an kreativen Berufsfeldern wie Design und Fotografie.',
            'Junger Erwachsener nach Studienabbruch in Orientierungsphase. Konflikt zwischen elterlichen Erwartungen und eigenen Interessen. Kreative Neigungen werden erkennbar.',
            'Studienabbrecher, 22 Jahre, sucht neue Richtung. Ursache: fehlende intrinsische Motivation für IT. Potential: kreativ-technische Berufe wie UX Design.',
        ],
        'Client Needs': [
            'Der Klient benötigt: 1) Berufsorientierung im kreativen Bereich, 2) Informationen zu alternativen Bildungswegen, 3) Unterstützung bei der Kommunikation mit den Eltern.',
            'Bedürfnisse: Validierung der eigenen Interessen, konkrete Karrierewege aufzeigen, Strategien zur Konfliktlösung mit Familie entwickeln.',
            'Kernbedürfnisse: Neuorientierung, Selbstvertrauen stärken, praktische Schritte für Berufseinstieg im kreativen Bereich.',
        ],
        'Recommended Actions': [
            'Empfehlungen: 1) Portfolio-Aufbau beginnen, 2) UX Design Bootcamps recherchieren, 3) Elterngespräch mit konkreten Berufsperspektiven vorbereiten.',
            'Nächste Schritte: Interessentests durchführen, Praktika im Designbereich erkunden, finanzielle Optionen für Weiterbildung prüfen.',
            'Handlungsplan: Kreative Projekte starten, Online-Kurse belegen, Netzwerk in der Design-Community aufbauen.',
        ],
        'Risk Assessment': [
            'Risiken: Zeitverlust, finanzielle Abhängigkeit, Familienkonflikt. Chancen: Höhere Berufszufriedenheit, bessere Work-Life-Balance in kreativem Feld.',
            'Moderate Risiken durch Neuanfang, aber gute Chancen durch junges Alter und vorhandene technische Grundkenntnisse.',
            'Geringes Risiko bei schneller Neuorientierung. IT-Grundkenntnisse können in UX Design wertvoll sein.',
        ],
    }

    for thread in mail_rating_threads:
        for ft_name, contents in mail_rating_feature_contents.items():
            ft = feature_types[ft_name]
            for i, llm in enumerate(llms):
                existing = Feature.query.filter_by(
                    thread_id=thread.thread_id,
                    type_id=ft.type_id,
                    llm_id=llm.llm_id
                ).first()

                if not existing:
                    feature = Feature(
                        thread_id=thread.thread_id,
                        type_id=ft.type_id,
                        llm_id=llm.llm_id,
                        content=contents[i]
                    )
                    db.session.add(feature)

    db.session.flush()

    # Default LLM evaluators for demo scenarios
    demo_llm_evaluators = [
        "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506",
        "Global/Mistral/Magistral-Small-2509"
    ]

    # Create Ranking Scenario
    if not existing_ranking:
        ranking_scenario = RatingScenarios(
            scenario_name='Demo Ranking Szenario',
            function_type_id=ranking_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now(),
            config_json={
                "evaluation": "ranking",
                "enable_llm_evaluation": True,
                "llm_evaluators": demo_llm_evaluators,
            }
        )
        db.session.add(ranking_scenario)
        db.session.flush()

        # Add users to scenario
        for user, role in [(evaluator_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.EVALUATOR)]:
            scenario_user = ScenarioUsers(
                scenario_id=ranking_scenario.id,
                user_id=user.id,
                role=role
            )
            db.session.add(scenario_user)

        db.session.flush()

        # Add ranking thread to scenario
        st = ScenarioThreads(
            scenario_id=ranking_scenario.id,
            thread_id=thread3.thread_id
        )
        db.session.add(st)
        db.session.flush()

        # Distribute to rater
        rater_scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=ranking_scenario.id,
            role=ScenarioRoles.EVALUATOR
        ).first()

        if rater_scenario_user:
            dist = ScenarioThreadDistribution(
                scenario_id=ranking_scenario.id,
                scenario_user_id=rater_scenario_user.id,
                scenario_thread_id=st.id
            )
            db.session.add(dist)

        print(f"  Created Ranking Scenario: {ranking_scenario.scenario_name}")
    else:
        ranking_scenario = existing_ranking
        # Update existing scenario with LLM evaluators if not set
        config = ranking_scenario.config_json or {}
        if not config.get('llm_evaluators'):
            config['evaluation'] = 'ranking'
            config['enable_llm_evaluation'] = True
            config['llm_evaluators'] = demo_llm_evaluators
            ranking_scenario.config_json = config
            print(f"  Updated Ranking Scenario with LLM evaluators")

    if admin_user and ranking_scenario:
        _ensure_scenario_user(ranking_scenario.id, admin_user.id, ScenarioRoles.VIEWER)

    # Create Mail Rating Scenario (Verlauf Bewerter)
    if not existing_mail_rating:
        mail_rating_scenario = RatingScenarios(
            scenario_name='Demo Verlauf Bewerter Szenario',
            function_type_id=mail_rating_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now(),
            config_json={
                "evaluation": "mail_rating",
                "enable_llm_evaluation": True,
                "llm_evaluators": demo_llm_evaluators,
            }
        )
        db.session.add(mail_rating_scenario)
        db.session.flush()

        # Add users to scenario
        for user, role in [(evaluator_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.EVALUATOR)]:
            scenario_user = ScenarioUsers(
                scenario_id=mail_rating_scenario.id,
                user_id=user.id,
                role=role
            )
            db.session.add(scenario_user)

        db.session.flush()

        # Add mail rating threads to scenario
        scenario_thread_objs = []
        for thread in mail_rating_threads:
            st = ScenarioThreads(
                scenario_id=mail_rating_scenario.id,
                thread_id=thread.thread_id
            )
            db.session.add(st)
            scenario_thread_objs.append(st)

        db.session.flush()

        # Distribute to rater
        rater_scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=mail_rating_scenario.id,
            role=ScenarioRoles.EVALUATOR
        ).first()

        if rater_scenario_user:
            for st in scenario_thread_objs:
                dist = ScenarioThreadDistribution(
                    scenario_id=mail_rating_scenario.id,
                    scenario_user_id=rater_scenario_user.id,
                    scenario_thread_id=st.id
                )
                db.session.add(dist)

        print(f"  Created Mail Rating Scenario: {mail_rating_scenario.scenario_name}")
    else:
        mail_rating_scenario = existing_mail_rating
        # Update existing scenario with LLM evaluators if not set
        config = mail_rating_scenario.config_json or {}
        if not config.get('llm_evaluators'):
            config['evaluation'] = 'mail_rating'
            config['enable_llm_evaluation'] = True
            config['llm_evaluators'] = demo_llm_evaluators
            mail_rating_scenario.config_json = config
            print(f"  Updated Mail Rating Scenario with LLM evaluators")

    if admin_user and mail_rating_scenario:
        _ensure_scenario_user(mail_rating_scenario.id, admin_user.id, ScenarioRoles.VIEWER)

    # Create Fake/Echt Scenario (Authenticity)
    if not existing_authenticity:
        authenticity_scenario = RatingScenarios(
            scenario_name='Demo Fake/Echt Szenario',
            function_type_id=authenticity_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now(),
            config_json={
                "evaluation": "authenticity",
                "labels": {"real": "Echt", "fake": "Fake"},
                "format_version": "v6",
                "enable_llm_evaluation": True,
                "llm_evaluators": demo_llm_evaluators,
            },
        )
        db.session.add(authenticity_scenario)
        db.session.flush()

        for user, role in [(evaluator_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.EVALUATOR)]:
            scenario_user = ScenarioUsers(
                scenario_id=authenticity_scenario.id,
                user_id=user.id,
                role=role
            )
            db.session.add(scenario_user)

        db.session.flush()

        scenario_thread_objs = []
        for thread in authenticity_threads:
            st = ScenarioThreads(
                scenario_id=authenticity_scenario.id,
                thread_id=thread.thread_id
            )
            db.session.add(st)
            scenario_thread_objs.append(st)

        db.session.flush()

        rater_scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=authenticity_scenario.id,
            role=ScenarioRoles.EVALUATOR
        ).first()

        if rater_scenario_user:
            for st in scenario_thread_objs:
                dist = ScenarioThreadDistribution(
                    scenario_id=authenticity_scenario.id,
                    scenario_user_id=rater_scenario_user.id,
                    scenario_thread_id=st.id
                )
                db.session.add(dist)

        print(f"  Created Authenticity Scenario: {authenticity_scenario.scenario_name}")
    else:
        authenticity_scenario = existing_authenticity
        # Update existing scenario with LLM evaluators if not set
        config = authenticity_scenario.config_json or {}
        if not config.get('llm_evaluators'):
            config['enable_llm_evaluation'] = True
            config['llm_evaluators'] = demo_llm_evaluators
            authenticity_scenario.config_json = config
            print(f"  Updated Authenticity Scenario with LLM evaluators")

    if admin_user and authenticity_scenario:
        _ensure_scenario_user(authenticity_scenario.id, admin_user.id, ScenarioRoles.VIEWER)

    # Create Labeling Scenario (generalized text categorization)
    if not existing_labeling:
        labeling_scenario = RatingScenarios(
            scenario_name='Demo Labeling Szenario',
            function_type_id=labeling_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now(),
            config_json={
                "evaluation": "labeling",
                "preset": "sentiment-3",
                "categories": [
                    {"id": "positive", "name": "Positiv", "color": "#98d4bb"},
                    {"id": "neutral", "name": "Neutral", "color": "#D1BC8A"},
                    {"id": "negative", "name": "Negativ", "color": "#e8a087"}
                ],
                "multiLabel": False,
                "allowUnsure": False,
                "enable_llm_evaluation": True,
                "llm_evaluators": demo_llm_evaluators,
            },
        )
        db.session.add(labeling_scenario)
        db.session.flush()

        for user, role in [(evaluator_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.EVALUATOR)]:
            db.session.add(
                ScenarioUsers(
                    scenario_id=labeling_scenario.id,
                    user_id=user.id,
                    role=role
                )
            )

        db.session.flush()

        # Add labeling threads to scenario
        scenario_thread_objs = []
        for thread in labeling_threads:
            st = ScenarioThreads(
                scenario_id=labeling_scenario.id,
                thread_id=thread.thread_id
            )
            db.session.add(st)
            scenario_thread_objs.append(st)

        db.session.flush()

        rater_scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=labeling_scenario.id,
            role=ScenarioRoles.EVALUATOR
        ).first()

        if rater_scenario_user:
            for st in scenario_thread_objs:
                dist = ScenarioThreadDistribution(
                    scenario_id=labeling_scenario.id,
                    scenario_user_id=rater_scenario_user.id,
                    scenario_thread_id=st.id
                )
                db.session.add(dist)

        print(f"  Created Labeling Scenario: {labeling_scenario.scenario_name}")
    else:
        labeling_scenario = existing_labeling
        # Update existing scenario with LLM evaluators if not set
        config = labeling_scenario.config_json or {}
        if not config.get('llm_evaluators'):
            config['evaluation'] = 'labeling'
            config['enable_llm_evaluation'] = True
            config['llm_evaluators'] = demo_llm_evaluators
            labeling_scenario.config_json = config
            print(f"  Updated Labeling Scenario with LLM evaluators")

    if admin_user and labeling_scenario:
        _ensure_scenario_user(labeling_scenario.id, admin_user.id, ScenarioRoles.VIEWER)

    db.session.commit()
    print("Demo scenarios seeded successfully.")

    # In development mode, seed extended demo data
    if _is_development_mode():
        _seed_extended_demo_data(db, ranking_scenario, mail_rating_scenario,
                                  authenticity_scenario, labeling_scenario,
                                  evaluator_user, researcher_user, admin_user)

    # Ensure Demo Ranking Szenario remains cartesian-balanced for provenance demos.
    try:
        _rebalance_demo_ranking_provenance(db, ranking_scenario)
    except Exception as e:
        db.session.rollback()
        print(f"  WARNING: Could not rebalance Demo Ranking Szenario provenance: {e}")

    # Seed LLM-as-Judge demo scenario (always, as it's for the new rating UI)
    try:
        from .llm_judge_demo_data import seed_llm_judge_demo_scenario
        seed_llm_judge_demo_scenario(db)
    except Exception as e:
        print(f"  WARNING: Could not seed LLM-as-Judge demo: {e}")

    # Seed SummEval demo scenario (text summarization evaluation)
    try:
        from .summeval_demo_data import seed_summeval_demo_scenario
        seed_summeval_demo_scenario(db)
    except Exception as e:
        print(f"  WARNING: Could not seed SummEval demo: {e}")


def _seed_extended_demo_data(db, ranking_scenario, mail_rating_scenario,
                              authenticity_scenario, labeling_scenario,
                              evaluator_user, researcher_user, admin_user):
    """
    Seed extended demo data (20-30 samples per scenario) for development mode.

    Only runs when PROJECT_STATE=development or FLASK_ENV=development.
    """
    from .demo_datasets import get_demo_data_for_scenario_type
    from ..tables import (
        EmailThread, Message, Feature, FeatureType, LLM, ScenarioThreads,
        ScenarioThreadDistribution, ScenarioUsers, ScenarioRoles,
        AuthenticityConversation, FeatureFunctionType,
    )

    print("\n[Dev Mode] Seeding extended demo data (20-30 samples per scenario)...")

    # Get function types
    rating_type = FeatureFunctionType.query.filter_by(name='rating').first()
    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    mail_rating_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()
    authenticity_type = FeatureFunctionType.query.filter_by(name='authenticity').first()
    labeling_type = FeatureFunctionType.query.filter_by(name='labeling').first()
    if not labeling_type:
        labeling_type = FeatureFunctionType.query.filter_by(name='text_classification').first()

    # Get or create LLMs
    llm_gpt4 = LLM.query.filter_by(name='GPT-4').first()
    llm_claude = LLM.query.filter_by(name='Claude-3').first()
    llm_mistral = LLM.query.filter_by(name='Mistral-7B').first()
    llms = [l for l in [llm_gpt4, llm_claude, llm_mistral] if l]

    # Get or create Feature Types
    feature_types = {}
    for ft_name in ['Situation Summary', 'Client Needs', 'Recommended Actions', 'Risk Assessment', 'Summary']:
        ft = FeatureType.query.filter_by(name=ft_name).first()
        if ft:
            feature_types[ft_name] = ft

    # Helper to get rater scenario user
    def _get_rater_user(scenario_id):
        return ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            role=ScenarioRoles.EVALUATOR
        ).first()

    # =========================================================================
    # 1. RANKING SCENARIO - Extended threads with features to rank
    # =========================================================================
    if ranking_scenario and ranking_type:
        ranking_samples = get_demo_data_for_scenario_type('ranking', count=25)
        existing_count = ScenarioThreads.query.filter_by(scenario_id=ranking_scenario.id).count()

        if existing_count < 10:
            print(f"  Seeding {len(ranking_samples)} ranking samples...")
            rater_user = _get_rater_user(ranking_scenario.id)

            for idx, sample in enumerate(ranking_samples):
                chat_id = 11000 + idx
                existing_thread = EmailThread.query.filter_by(
                    chat_id=chat_id,
                    function_type_id=ranking_type.function_type_id
                ).first()

                if existing_thread:
                    continue

                thread = EmailThread(
                    chat_id=chat_id,
                    institut_id=1,
                    subject=sample['subject'],
                    sender=f'demo_ranking_{idx}@example.com',
                    function_type_id=ranking_type.function_type_id
                )
                db.session.add(thread)
                db.session.flush()

                # Add source text as first message
                db.session.add(Message(
                    thread_id=thread.thread_id,
                    sender='Source Article',
                    content=sample['source_text'],
                    timestamp=datetime.now() - timedelta(days=idx, hours=5)
                ))

                # Get Summary FeatureType and SummEval LLM for ranking features
                summary_ft = feature_types.get('Summary')
                summeval_llm = LLM.query.filter_by(name='SummEval').first()

                # Add each summary ONLY as a Feature (for ranking in left panel)
                # Do NOT create Messages for summaries - they should only appear
                # in the left panel as rankable items, not in the right panel
                for sum_idx, summary in enumerate(sample.get('summaries', [])):
                    # Create Feature for ranking (this is what users actually rank)
                    if summary_ft and summeval_llm:
                        db.session.add(Feature(
                            thread_id=thread.thread_id,
                            type_id=summary_ft.type_id,
                            llm_id=summeval_llm.llm_id,
                            content=summary['content']
                        ))

                st = ScenarioThreads(
                    scenario_id=ranking_scenario.id,
                    thread_id=thread.thread_id
                )
                db.session.add(st)
                db.session.flush()

                if rater_user:
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=ranking_scenario.id,
                        scenario_user_id=rater_user.id,
                        scenario_thread_id=st.id
                    ))

            print(f"    Created {len(ranking_samples)} ranking threads")

    # =========================================================================
    # 2. MAIL RATING SCENARIO - Extended conversation threads
    # =========================================================================
    if mail_rating_scenario and mail_rating_type:
        mail_rating_samples = get_demo_data_for_scenario_type('mail_rating', count=10)
        existing_count = ScenarioThreads.query.filter_by(scenario_id=mail_rating_scenario.id).count()

        if existing_count < 5:
            print(f"  Seeding {len(mail_rating_samples)} mail rating samples...")
            rater_user = _get_rater_user(mail_rating_scenario.id)

            for idx, sample in enumerate(mail_rating_samples):
                chat_id = 12000 + idx
                existing_thread = EmailThread.query.filter_by(
                    chat_id=chat_id,
                    function_type_id=mail_rating_type.function_type_id
                ).first()

                if existing_thread:
                    continue

                thread = EmailThread(
                    chat_id=chat_id,
                    institut_id=1,
                    subject=sample['subject'],
                    sender=f'demo_mail_{idx}@example.com',
                    function_type_id=mail_rating_type.function_type_id
                )
                db.session.add(thread)
                db.session.flush()

                for msg_idx, msg in enumerate(sample['messages']):
                    db.session.add(Message(
                        thread_id=thread.thread_id,
                        sender=msg['sender'],
                        content=msg['content'],
                        timestamp=datetime.now() - timedelta(days=14-idx, hours=10-msg_idx)
                    ))

                st = ScenarioThreads(
                    scenario_id=mail_rating_scenario.id,
                    thread_id=thread.thread_id
                )
                db.session.add(st)
                db.session.flush()

                if rater_user:
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=mail_rating_scenario.id,
                        scenario_user_id=rater_user.id,
                        scenario_thread_id=st.id
                    ))

            print(f"    Created {len(mail_rating_samples)} mail rating threads")

    # =========================================================================
    # 3. AUTHENTICITY SCENARIO - Real vs AI-generated samples
    # =========================================================================
    if authenticity_scenario and authenticity_type:
        auth_samples = get_demo_data_for_scenario_type('authenticity', count=20)
        existing_count = ScenarioThreads.query.filter_by(scenario_id=authenticity_scenario.id).count()

        if existing_count < 10:
            print(f"  Seeding {len(auth_samples)} authenticity samples...")
            rater_user = _get_rater_user(authenticity_scenario.id)

            for idx, sample in enumerate(auth_samples):
                chat_id = 13000 + idx
                existing_thread = EmailThread.query.filter_by(
                    chat_id=chat_id,
                    function_type_id=authenticity_type.function_type_id
                ).first()

                if existing_thread:
                    continue

                is_fake = sample.get('is_fake', False)
                thread = EmailThread(
                    chat_id=chat_id,
                    institut_id=3,
                    subject=f"Authenticity Sample {'(Fake)' if is_fake else '(Real)'} - {idx+1}",
                    sender='demo@authenticity.com',
                    function_type_id=authenticity_type.function_type_id
                )
                db.session.add(thread)
                db.session.flush()

                for msg_idx, msg in enumerate(sample['messages']):
                    db.session.add(Message(
                        thread_id=thread.thread_id,
                        sender=msg['sender'],
                        content=msg['content'],
                        timestamp=datetime.now() - timedelta(days=idx, hours=msg_idx),
                        generated_by=msg.get('generated_by', 'Human')
                    ))

                # Create AuthenticityConversation entry
                metadata = sample.get('metadata', {})
                metadata['conversation_id'] = chat_id
                metadata['generated_at'] = datetime.now().isoformat()
                metadata['format_version'] = 'v6'
                metadata['total_messages'] = len(sample['messages'])

                db.session.add(AuthenticityConversation(
                    thread_id=thread.thread_id,
                    sample_key=f"v6:demo-auth-{chat_id}",
                    conversation_id=chat_id,
                    augmentation_type=metadata.get('augmentation_type', 'reg_single_any'),
                    replaced_positions=metadata.get('replaced_positions', [1] if is_fake else []),
                    num_replacements=metadata.get('num_replacements', 1 if is_fake else 0),
                    total_messages=metadata.get('total_messages', 2),
                    saeule='3',
                    split='train',
                    model=metadata.get('model'),
                    model_short=metadata.get('model', '').split('-')[0] if metadata.get('model') else None,
                    generated_at=datetime.now(),
                    format_version='v6',
                    is_fake=is_fake,
                    metadata_json=metadata,
                ))

                st = ScenarioThreads(
                    scenario_id=authenticity_scenario.id,
                    thread_id=thread.thread_id
                )
                db.session.add(st)
                db.session.flush()

                if rater_user:
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=authenticity_scenario.id,
                        scenario_user_id=rater_user.id,
                        scenario_thread_id=st.id
                    ))

            print(f"    Created {len(auth_samples)} authenticity threads")

    # =========================================================================
    # 4. LABELING SCENARIO - Extended text categorization samples
    # =========================================================================
    if labeling_scenario and labeling_type:
        labeling_samples = get_demo_data_for_scenario_type('labeling', count=15)
        existing_count = ScenarioThreads.query.filter_by(scenario_id=labeling_scenario.id).count()

        if existing_count < 10:
            print(f"  Seeding {len(labeling_samples)} labeling samples...")
            rater_user = _get_rater_user(labeling_scenario.id)

            for idx, sample in enumerate(labeling_samples):
                chat_id = 14000 + idx
                existing_thread = EmailThread.query.filter_by(
                    chat_id=chat_id,
                    function_type_id=labeling_type.function_type_id
                ).first()

                if existing_thread:
                    continue

                thread = EmailThread(
                    chat_id=chat_id,
                    institut_id=1,
                    subject=sample.get('subject', f'Labeling Sample {idx+1}'),
                    sender=f'demo_labeling_{idx}@example.com',
                    function_type_id=labeling_type.function_type_id
                )
                db.session.add(thread)
                db.session.flush()

                # Create message with text to be labeled
                db.session.add(Message(
                    thread_id=thread.thread_id,
                    sender=sample.get('sender', 'User'),
                    content=sample.get('text', sample.get('content', '')),
                    timestamp=datetime.now() - timedelta(days=idx)
                ))

                st = ScenarioThreads(
                    scenario_id=labeling_scenario.id,
                    thread_id=thread.thread_id
                )
                db.session.add(st)
                db.session.flush()

                if rater_user:
                    db.session.add(ScenarioThreadDistribution(
                        scenario_id=labeling_scenario.id,
                        scenario_user_id=rater_user.id,
                        scenario_thread_id=st.id
                    ))

            print(f"    Created {len(labeling_samples)} labeling threads")

    db.session.commit()
    print("[Dev Mode] Extended demo data seeded successfully.")
