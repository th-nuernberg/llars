"""
Conference Manager Seeder

Seeds conference and paper data for the research group.
Uses real user accounts (ieb-steigerwald, ieb-rudolph, ieb-albrecht) as authors.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Author username mapping
AUTHOR_STEIGERWALD = "ieb-steigerwald"
AUTHOR_RUDOLPH = "ieb-rudolph"
AUTHOR_ALBRECHT = "ieb-albrecht"


def seed_demo_conferences(db):
    """
    Seed conferences and papers for the Conference Manager.
    Idempotent: skips if conferences already exist.
    """
    from db.models.conference import (
        Conference, Paper, PaperAuthor, PaperSubmission,
        CoreRanking, PaperStatus, SubmissionStatus,
        ResearchGroup,
    )
    from db.tables import User

    # Skip if data already exists
    if Conference.query.first():
        logger.info("Conference data already exists, skipping")
        return

    logger.info("Seeding conference data...")

    # Resolve NLP-Group for group_id assignment
    nlp_group = ResearchGroup.query.filter_by(slug="nlp-group").first()
    nlp_group_id = nlp_group.id if nlp_group else None

    # Resolve user IDs
    user_map = {}
    for username in [AUTHOR_STEIGERWALD, AUTHOR_RUDOLPH, AUTHOR_ALBRECHT]:
        user = User.query.filter_by(username=username).first()
        if user:
            user_map[username] = user.id
        else:
            logger.warning(f"User '{username}' not found, will use external_name")

    created_by = AUTHOR_STEIGERWALD

    # ── Conferences ──────────────────────────────────────────────

    conferences_data = [
        {
            "name": "International Workshop on Fair and Ethical AI in Education and Beyond",
            "acronym": "FAIEMA",
            "year": 2024,
            "core_ranking": CoreRanking.UNRANKED,
            "submission_deadline": datetime(2024, 8, 7),
            "notification_date": datetime(2024, 9, 25),
            "start_date": datetime(2024, 9, 18),
            "end_date": datetime(2024, 9, 19),
            "city": "Athen",
            "country": "Griechenland",
            "website_url": "https://faiema.org",
            "keywords": ["AI", "Ethics"],
        },
        {
            "name": "International Conference on Information and Communication Technologies for Ageing Well and e-Health",
            "acronym": "ICT4AWE",
            "year": 2025,
            "core_ranking": CoreRanking.C,
            "submission_deadline": datetime(2024, 11, 21),
            "notification_date": datetime(2025, 1, 6),
            "start_date": datetime(2025, 4, 6),
            "end_date": datetime(2025, 4, 8),
            "city": "Porto",
            "country": "Portugal",
            "website_url": "https://ict4awe.scitevents.org/?y=2025",
            "keywords": ["AI", "Evaluation"],
        },
        {
            "name": "International Conference on Educational Data Mining",
            "acronym": "EDM",
            "year": 2025,
            "core_ranking": CoreRanking.B,
            "submission_deadline": datetime(2025, 2, 20),
            "notification_date": datetime(2025, 4, 10),
            "start_date": datetime(2025, 7, 20),
            "end_date": datetime(2025, 7, 23),
            "city": "Palermo",
            "country": "Italien",
            "website_url": "https://educationaldatamining.org/edm2025/",
            "keywords": ["AI", "Education"],
        },
        {
            "name": "International Workshop on Fair and Ethical AI in Education and Beyond",
            "acronym": "FAIEMA",
            "year": 2025,
            "core_ranking": CoreRanking.UNRANKED,
            "submission_deadline": datetime(2025, 6, 30),
            "notification_date": datetime(2025, 6, 30),
            "start_date": datetime(2025, 9, 18),
            "end_date": datetime(2025, 9, 19),
            "city": "Stavanger",
            "country": "Norwegen",
            "website_url": "https://faiema.org",
            "keywords": ["AI", "Ethics"],
        },
        {
            "name": "IEEE International Conference on Tools with Artificial Intelligence",
            "acronym": "ICTAI",
            "year": 2025,
            "core_ranking": CoreRanking.B,
            "submission_deadline": datetime(2025, 6, 30),
            "notification_date": datetime(2025, 8, 20),
            "start_date": datetime(2025, 11, 3),
            "end_date": datetime(2025, 11, 5),
            "city": "Athen",
            "country": "Griechenland",
            "website_url": "https://easyconferences.eu/ictai2025/",
            "keywords": ["AI Systems"],
        },
        {
            "name": "PostPub ICT4AWE Journal Extension",
            "acronym": "PostPub ICT4AWE",
            "year": 2025,
            "core_ranking": CoreRanking.C,
            "submission_deadline": datetime(2025, 8, 12),
            "notification_date": datetime(2025, 12, 31),
            "start_date": datetime(2025, 4, 6),
            "end_date": datetime(2025, 5, 8),
            "keywords": ["AI", "Evaluation"],
        },
        {
            "name": "International Conference on Language Resources and Evaluation",
            "acronym": "LREC",
            "year": 2026,
            "core_ranking": CoreRanking.B,
            "submission_deadline": datetime(2025, 10, 17),
            "notification_date": datetime(2026, 2, 13),
            "start_date": datetime(2026, 6, 11),
            "end_date": datetime(2026, 6, 16),
            "city": "Palma Mallorca",
            "country": "Spain",
            "website_url": "https://lrec2026.info/third-call-for-papers/",
            "keywords": ["AI"],
        },
        {
            "name": "ACL Rolling Review",
            "acronym": "ARR",
            "year": 2026,
            "core_ranking": CoreRanking.A,
            "submission_deadline": datetime(2026, 1, 4),
            "notification_date": datetime(2026, 2, 15),
            "keywords": ["AI"],
            "notes": "Rolling review for ACL venues",
        },
        {
            "name": "International Joint Conference on Artificial Intelligence",
            "acronym": "IJCAI",
            "year": 2026,
            "core_ranking": CoreRanking.A_STAR,
            "submission_deadline": datetime(2026, 2, 16),
            "notification_date": datetime(2026, 4, 29),
            "start_date": datetime(2026, 8, 15),
            "end_date": datetime(2026, 8, 21),
            "city": "Bremen",
            "country": "Deutschland",
            "website_url": "https://2026.ijcai.org",
            "keywords": ["Demo"],
        },
        {
            "name": "Learning @ Scale / AI in Education",
            "acronym": "L@S/AIED",
            "year": 2026,
            "core_ranking": CoreRanking.A,
            "keywords": ["AI", "Education"],
        },
        {
            "name": "CSS ACL Workshop",
            "acronym": "CSS ACL Workshop",
            "year": 2026,
            "core_ranking": CoreRanking.A,
            "keywords": ["AI", "Computational Social Science"],
        },
    ]

    conf_map = {}  # acronym+year → Conference object
    for data in conferences_data:
        conf = Conference(
            name=data["name"],
            acronym=data["acronym"],
            year=data["year"],
            group_id=nlp_group_id,
            core_ranking=data["core_ranking"],
            submission_deadline=data.get("submission_deadline"),
            notification_date=data.get("notification_date"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            city=data.get("city"),
            country=data.get("country"),
            website_url=data.get("website_url"),
            keywords=data.get("keywords"),
            notes=data.get("notes"),
            created_by=created_by,
        )
        db.session.add(conf)
        db.session.flush()
        conf_map[f"{data['acronym']}_{data['year']}"] = conf

    # ── Papers ───────────────────────────────────────────────────

    # Helper: create author entry with user_id if available, else external_name
    def _make_author(paper_id, username, order, is_corresponding=False):
        uid = user_map.get(username)
        return PaperAuthor(
            paper_id=paper_id,
            user_id=uid,
            external_name=username if not uid else None,
            author_order=order,
            is_corresponding=is_corresponding,
        )

    # Find IJCAI LaTeX workspace (if exists)
    from db.models.latex_collab import LatexWorkspace
    ijcai_workspace = LatexWorkspace.query.filter(
        LatexWorkspace.name.contains("LLARS")
    ).first()

    papers_data = [
        # ── Accepted Papers ──
        {
            "title": "Enhancing Psychosocial Counselling with AI: A Multifaceted Support System for Professionals",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "FAIEMA_2024",
            "authors": [(AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Ethics", "Psychotherapy"],
            "notes": "KIA Idee vorstellen",
            "overleaf_url": "https://www.overleaf.com/project/6669c279720512af0a84a729",
            "submission_date": datetime(2024, 8, 7),
        },
        {
            "title": "Comparing Large Language Models for Automated Subject Line Generation in e-Mental Health: A Performance Study",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "ICT4AWE_2025",
            "authors": [(AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Evaluation", "LLM"],
            "notes": "LLM Comparison",
            "overleaf_url": "https://www.overleaf.com/project/673c4846281ac28c5ae3f387",
            "submission_date": datetime(2024, 11, 21),
        },
        {
            "title": "Comparing Human Role-Players and LLM-Simulated Clients in Online Counselling Training: An Analysis of Counselling Patterns",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "EDM_2025",
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Education"],
            "notes": "Vikl und Oncoco",
            "overleaf_url": "https://www.overleaf.com/project/67adfa59e2d2ec80613a8e10",
            "submission_date": datetime(2025, 2, 20),
        },
        {
            "title": "Ethical Considerations in Text-Based e-Mental Health: Assessing the Role of AI from Assistive to Autonomous Systems",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "FAIEMA_2025",
            "authors": [(AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Ethics"],
            "notes": "Ethik Paper zu KI in der Beratung",
            "overleaf_url": "https://www.overleaf.com/project/67b83eb55639bfa8824453d9",
            "submission_date": datetime(2025, 6, 30),
        },
        {
            "title": "CAIA in Practice: Field Evaluation of an AI-Assisted Support System for Psychosocial E-mail Counselling",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "ICTAI_2025",
            "authors": [(AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI Systems"],
            "notes": "KIA Testung",
            "overleaf_url": "https://www.overleaf.com/project/683706ba066d2d532c80b486",
            "submission_date": datetime(2025, 6, 30),
        },
        {
            "title": "PostPub ICT4AWE",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "PostPub ICT4AWE_2025",
            "authors": [(AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Evaluation"],
            "overleaf_url": "https://www.overleaf.com/project/6821dc465be88c83a49ade2e",
            "submission_date": datetime(2025, 8, 12),
        },
        # ── Submitted Papers ──
        {
            "title": "OnCoCo 1.0: A Public Dataset for Fine-Grained Message Classification in Online Counseling Conversations",
            "status": PaperStatus.SUBMITTED,
            "conference_key": "LREC_2026",
            "authors": [(AUTHOR_ALBRECHT, False), (AUTHOR_RUDOLPH, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI"],
            "notes": "Gecco Introduction",
            "overleaf_url": "https://www.overleaf.com/project/67a8d0c35ce0979066409dba",
            "submission_date": datetime(2025, 10, 17),
        },
        {
            "title": "Transition-Matrix Regularization for Next Dialogue Act Prediction in Counselling Conversations",
            "status": PaperStatus.SUBMITTED,
            "conference_key": "ARR_2026",
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "NLP"],
            "submission_date": datetime(2026, 1, 4),
        },
        # ── In Progress Papers ──
        {
            "title": "LLARS: A Platform for Evaluating LLM Outputs with Human and Machine Evaluators",
            "status": PaperStatus.IN_PROGRESS,
            "conference_key": "IJCAI_2026",
            "authors": [(AUTHOR_STEIGERWALD, True), (AUTHOR_RUDOLPH, False)],
            "keywords": ["Demo", "LLM", "Evaluation"],
            "notes": "LLars Vorstellen",
            "latex_workspace_id": ijcai_workspace.id if ijcai_workspace else None,
            "submission_date": datetime(2026, 2, 16),
        },
        {
            "title": "Social Network Graph Evaluation",
            "status": PaperStatus.IN_PROGRESS,
            "conference_key": "ARR_2026",
            "authors": [(AUTHOR_STEIGERWALD, True), (AUTHOR_RUDOLPH, False)],
            "keywords": ["AI", "Social Networks"],
        },
        # ── Planning Papers ──
        {
            "title": "Feedback 2.0",
            "status": PaperStatus.PLANNING,
            "conference_key": "ARR_2026",
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Feedback"],
        },
        {
            "title": "ViKl Dataset",
            "status": PaperStatus.PLANNING,
            "conference_key": "L@S/AIED_2026",
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Education", "Dataset"],
        },
        {
            "title": "EDM Paper Next (Echtdaten + mehrere LLMs) - ViKl Dataset",
            "status": PaperStatus.PLANNING,
            "conference_key": "CSS ACL Workshop_2026",
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_ALBRECHT, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "CSS"],
        },
        {
            "title": "Oncoco + OncocoNext vs. Fine-Tuning",
            "status": PaperStatus.PLANNING,
            "conference_key": None,
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_ALBRECHT, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "NLP"],
        },
        {
            "title": "Systemvorstellung Personagenerierung",
            "status": PaperStatus.PLANNING,
            "conference_key": None,
            "authors": [(AUTHOR_RUDOLPH, False), (AUTHOR_ALBRECHT, False), (AUTHOR_STEIGERWALD, True)],
            "keywords": ["AI", "Systems"],
        },
    ]

    for data in papers_data:
        conf = conf_map.get(data.get("conference_key")) if data.get("conference_key") else None

        paper = Paper(
            title=data["title"],
            status=data["status"],
            group_id=nlp_group_id,
            conference_id=conf.id if conf else None,
            keywords=data.get("keywords"),
            notes=data.get("notes"),
            description=data.get("notes"),
            overleaf_url=data.get("overleaf_url"),
            latex_workspace_id=data.get("latex_workspace_id"),
            created_by=created_by,
        )
        db.session.add(paper)
        db.session.flush()

        # Add authors (linked to user accounts)
        for order, (username, is_corresponding) in enumerate(data.get("authors", [])):
            db.session.add(_make_author(paper.id, username, order, is_corresponding))

        # Add submission entry for submitted/accepted papers
        submission_date = data.get("submission_date")
        if conf and submission_date and data["status"] in (PaperStatus.SUBMITTED, PaperStatus.ACCEPTED):
            sub_status = (
                SubmissionStatus.ACCEPTED if data["status"] == PaperStatus.ACCEPTED
                else SubmissionStatus.SUBMITTED
            )
            db.session.add(PaperSubmission(
                paper_id=paper.id,
                conference_id=conf.id,
                status=sub_status,
                submitted_at=submission_date,
                decided_at=conf.notification_date if sub_status == SubmissionStatus.ACCEPTED else None,
            ))

    db.session.commit()
    logger.info(
        f"Conference data seeded: {len(conferences_data)} conferences, "
        f"{len(papers_data)} papers"
    )
