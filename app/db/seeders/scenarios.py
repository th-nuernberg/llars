"""
Scenario Seeder for Development

Seeds example Rating and Ranking scenarios with sample email threads,
messages, and LLM-generated features for testing purposes.

Maps scenarios to 'viewer' and 'researcher' users.
"""

from datetime import datetime, timedelta


def seed_demo_scenarios(db):
    """
    Seed demo scenarios for Rating and Ranking with sample data.

    Creates:
    - Sample email threads with messages
    - LLM-generated features for the threads
    - A Rating scenario mapped to viewer/researcher
    - A Ranking scenario mapped to viewer/researcher

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import (
        User, UserGroup, EmailThread, Message, Feature, FeatureType, LLM,
        FeatureFunctionType, RatingScenarios, ScenarioUsers,
        ScenarioThreads, ScenarioThreadDistribution, ScenarioRoles
    )

    print("Seeding demo scenarios...")

    import uuid

    # Get or create users for demo scenarios
    viewer_user = User.query.filter_by(username='viewer').first()
    researcher_user = User.query.filter_by(username='researcher').first()

    # Get default user group
    default_group = UserGroup.query.filter_by(name='Standard').first()
    if not default_group:
        default_group = UserGroup(name='Standard')
        db.session.add(default_group)
        db.session.flush()

    if not viewer_user:
        viewer_user = User(
            username='viewer',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(viewer_user)
        print("  Created user: viewer")

    if not researcher_user:
        researcher_user = User(
            username='researcher',
            password_hash='',  # Auth via Authentik, no local password
            api_key=str(uuid.uuid4()),
            group_id=default_group.id
        )
        db.session.add(researcher_user)
        print("  Created user: researcher")

    db.session.flush()
    print(f"  Users ready: viewer (id={viewer_user.id}), researcher (id={researcher_user.id})")

    # Get function types
    rating_type = FeatureFunctionType.query.filter_by(name='rating').first()
    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    mail_rating_type = FeatureFunctionType.query.filter_by(name='mail_rating').first()

    if not rating_type or not ranking_type or not mail_rating_type:
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

    db.session.flush()

    # Create or get Feature Types
    feature_types = {}
    for ft_name in ['Situation Summary', 'Client Needs', 'Recommended Actions', 'Risk Assessment']:
        ft = FeatureType.query.filter_by(name=ft_name).first()
        if not ft:
            ft = FeatureType(name=ft_name)
            db.session.add(ft)
        feature_types[ft_name] = ft

    db.session.flush()

    # Check if demo scenarios already exist
    existing_rating = RatingScenarios.query.filter_by(scenario_name='Demo Rating Szenario').first()
    existing_ranking = RatingScenarios.query.filter_by(scenario_name='Demo Ranking Szenario').first()
    existing_mail_rating = RatingScenarios.query.filter_by(scenario_name='Demo Verlauf Bewerter Szenario').first()

    if existing_rating and existing_ranking and existing_mail_rating:
        print("  Demo scenarios already exist. Skipping.")
        return

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

    # Create Rating Scenario
    if not existing_rating:
        rating_scenario = RatingScenarios(
            scenario_name='Demo Rating Szenario',
            function_type_id=rating_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now()
        )
        db.session.add(rating_scenario)
        db.session.flush()

        # Add users to scenario
        for user, role in [(viewer_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.RATER)]:
            scenario_user = ScenarioUsers(
                scenario_id=rating_scenario.id,
                user_id=user.id,
                role=role
            )
            db.session.add(scenario_user)

        db.session.flush()

        # Add threads to scenario (only rating threads)
        rating_threads = [t for t in threads[:2]]  # thread1 and thread2
        scenario_thread_objs = []
        for thread in rating_threads:
            st = ScenarioThreads(
                scenario_id=rating_scenario.id,
                thread_id=thread.thread_id
            )
            db.session.add(st)
            scenario_thread_objs.append(st)

        db.session.flush()

        # Distribute threads to raters
        rater_scenario_user = ScenarioUsers.query.filter_by(
            scenario_id=rating_scenario.id,
            role=ScenarioRoles.RATER
        ).first()

        if rater_scenario_user:
            for st in scenario_thread_objs:
                dist = ScenarioThreadDistribution(
                    scenario_id=rating_scenario.id,
                    scenario_user_id=rater_scenario_user.id,
                    scenario_thread_id=st.id
                )
                db.session.add(dist)

        print(f"  Created Rating Scenario: {rating_scenario.scenario_name}")

    # Create Ranking Scenario
    if not existing_ranking:
        ranking_scenario = RatingScenarios(
            scenario_name='Demo Ranking Szenario',
            function_type_id=ranking_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now()
        )
        db.session.add(ranking_scenario)
        db.session.flush()

        # Add users to scenario
        for user, role in [(viewer_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.RATER)]:
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
            role=ScenarioRoles.RATER
        ).first()

        if rater_scenario_user:
            dist = ScenarioThreadDistribution(
                scenario_id=ranking_scenario.id,
                scenario_user_id=rater_scenario_user.id,
                scenario_thread_id=st.id
            )
            db.session.add(dist)

        print(f"  Created Ranking Scenario: {ranking_scenario.scenario_name}")

    # Create Mail Rating Scenario (Verlauf Bewerter)
    if not existing_mail_rating:
        mail_rating_scenario = RatingScenarios(
            scenario_name='Demo Verlauf Bewerter Szenario',
            function_type_id=mail_rating_type.function_type_id,
            begin=datetime.now() - timedelta(days=7),
            end=datetime.now() + timedelta(days=30),
            timestamp=datetime.now()
        )
        db.session.add(mail_rating_scenario)
        db.session.flush()

        # Add users to scenario
        for user, role in [(viewer_user, ScenarioRoles.VIEWER), (researcher_user, ScenarioRoles.RATER)]:
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
            role=ScenarioRoles.RATER
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

    db.session.commit()
    print("Demo scenarios seeded successfully.")
