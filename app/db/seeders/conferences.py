"""
Conference Manager Demo Seeder

Seeds conference and paper data for development mode.
Data based on the research group's actual conference tracking.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def seed_demo_conferences(db):
    """
    Seed demo conferences and papers for the Conference Manager.
    Idempotent: skips if conferences already exist.
    """
    from db.models.conference import Conference, Paper, PaperAuthor, CoreRanking, PaperStatus

    # Skip if data already exists
    if Conference.query.first():
        logger.info("Conference demo data already exists, skipping")
        return

    logger.info("Seeding conference demo data...")

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
            "website_url": "https://ict4awe.scitevents.org",
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
            "website_url": "https://educationaldatamining.org",
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
            "website_url": "https://easyconferences.eu/ictai2025",
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
            "city": "Palma",
            "country": "Mallorca",
            "website_url": "https://lrec2026.info",
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
            "keywords": ["demo"],
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
            created_by="researcher",
        )
        db.session.add(conf)
        db.session.flush()
        conf_map[f"{data['acronym']}_{data['year']}"] = conf

    # ── Papers ───────────────────────────────────────────────────

    papers_data = [
        {
            "title": "Enhancing Psychotherapy Process Analysis with AI-Assisted Evaluation",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "FAIEMA_2024",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI", "Ethics", "Psychotherapy"],
            "notes": "KIA Idee vorstellen",
        },
        {
            "title": "Comparing Language Models for Counselling Conversation Evaluation",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "ICT4AWE_2025",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI", "Evaluation", "LLM"],
            "notes": "LLM Comparison",
        },
        {
            "title": "Comparing Human and AI-Based Evaluation in Educational Data Mining",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "EDM_2025",
            "authors": [("Eric Rudolph", False), ("Philipp Steigerwald", True)],
            "keywords": ["AI", "Education"],
            "notes": "Viki und Oncoco",
        },
        {
            "title": "Ethical Considerations of AI in Counselling Practice",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "FAIEMA_2025",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI", "Ethics"],
            "notes": "Ethik Paper zu KI in der Beratung",
        },
        {
            "title": "CAIA in Practice: Evaluating Conversational AI Assessment Tools",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "ICTAI_2025",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI Systems"],
            "notes": "KIA Testung",
        },
        {
            "title": "Extended Journal Paper: Comparing Language Models for ICT4AWE",
            "status": PaperStatus.ACCEPTED,
            "conference_key": "PostPub ICT4AWE_2025",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI", "Evaluation"],
        },
        {
            "title": "OnCoCo 1.0: A Corpus and Framework for Online Counselling Conversation Analysis",
            "status": PaperStatus.SUBMITTED,
            "conference_key": "LREC_2026",
            "authors": [("Jens Albrecht", False), ("Eric Rudolph", True)],
            "keywords": ["AI", "NLP", "Corpus"],
            "notes": "Gecco Introduction",
        },
        {
            "title": "Transition-Matrix Analysis for Counselling Conversation Dynamics",
            "status": PaperStatus.SUBMITTED,
            "conference_key": "ARR_2026",
            "authors": [("Eric Rudolph", False), ("Philipp Steigerwald", True)],
            "keywords": ["AI", "NLP"],
        },
        {
            "title": "LLARS: A Platform for Collaborative LLM-Assisted Research and Evaluation",
            "status": PaperStatus.IN_PROGRESS,
            "conference_key": "IJCAI_2026",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["demo", "LLM", "Evaluation"],
            "notes": "LLARS Vorstellen",
            "overleaf_url": None,
        },
        {
            "title": "Social Network Analysis of Online Counselling Interactions",
            "status": PaperStatus.IN_PROGRESS,
            "conference_key": "ARR_2026",
            "authors": [("Philipp Steigerwald", True)],
            "keywords": ["AI", "Social Networks"],
        },
        {
            "title": "Feedback 2.0: AI-Enhanced Feedback Mechanisms in Counselling",
            "status": PaperStatus.PLANNING,
            "conference_key": "ARR_2026",
            "authors": [("Eric Rudolph", False), ("Philipp Steigerwald", True)],
            "keywords": ["AI", "Feedback"],
        },
        {
            "title": "Viki Dataset: A Benchmark for AI-Assisted Educational Assessment",
            "status": PaperStatus.PLANNING,
            "conference_key": "L@S/AIED_2026",
            "authors": [("Eric Rudolph", False), ("Philipp Steigerwald", True)],
            "keywords": ["AI", "Education", "Dataset"],
        },
        {
            "title": "EDM Paper: New Approaches to Computational Social Science in Education",
            "status": PaperStatus.PLANNING,
            "conference_key": "CSS ACL Workshop_2026",
            "authors": [("Eric Rudolph", False), ("Jens Albrecht", True)],
            "keywords": ["AI", "CSS"],
        },
        {
            "title": "OnCoCo + OnCoCo: Combining Conversation Analysis Approaches",
            "status": PaperStatus.PLANNING,
            "conference_key": None,
            "authors": [("Eric Rudolph", False), ("Jens Albrecht", True)],
            "keywords": ["AI", "NLP"],
        },
        {
            "title": "Systemvorstellung: Architecture and Design of the LLARS Platform",
            "status": PaperStatus.PLANNING,
            "conference_key": None,
            "authors": [("Eric Rudolph", False), ("Jens Albrecht", True)],
            "keywords": ["AI", "Systems"],
        },
    ]

    for data in papers_data:
        conf = conf_map.get(data.get("conference_key")) if data.get("conference_key") else None

        paper = Paper(
            title=data["title"],
            status=data["status"],
            conference_id=conf.id if conf else None,
            keywords=data.get("keywords"),
            notes=data.get("notes"),
            overleaf_url=data.get("overleaf_url"),
            description=data.get("notes"),
            created_by="researcher",
        )
        db.session.add(paper)
        db.session.flush()

        # Add authors
        for order, (name, is_corresponding) in enumerate(data.get("authors", [])):
            author = PaperAuthor(
                paper_id=paper.id,
                external_name=name,
                author_order=order,
                is_corresponding=is_corresponding,
            )
            db.session.add(author)

    db.session.commit()
    logger.info(
        f"Conference demo data seeded: {len(conferences_data)} conferences, "
        f"{len(papers_data)} papers"
    )
