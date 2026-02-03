"""
Demo Video Data Seeder

Creates pre-seeded data for the IJCAI 2026 demo video:
1. Two news summarization prompts
2. A completed batch generation job with outputs
3. Sample outputs for all 10 news articles x 2 prompts x 2 models

This ensures the demo video can show completed results without waiting
for actual LLM generation during recording.
"""
import logging
from datetime import datetime, timedelta

from db.database import db
from db.tables import User, UserPrompt
from db.models.generation import GenerationJob, GeneratedOutput, GenerationJobStatus, GeneratedOutputStatus
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)

# News articles embedded directly (avoids file path issues in Docker)
NEWS_ARTICLES = [
    {
        "title": "OpenAI Announces GPT-5 with Revolutionary Reasoning Capabilities",
        "content": "OpenAI unveiled GPT-5 today, marking a significant leap in artificial intelligence. The new model demonstrates unprecedented reasoning abilities, solving complex mathematical proofs and showing improved factual accuracy. CEO Sam Altman stated that GPT-5 represents 'a new paradigm in AI capabilities.' The model will be available to enterprise customers starting next month, with consumer access planned for Q2 2026."
    },
    {
        "title": "European Union Passes Comprehensive AI Regulation Framework",
        "content": "The European Parliament has approved the AI Act, the world's most comprehensive artificial intelligence regulation. The legislation categorizes AI systems by risk level and imposes strict requirements on high-risk applications including hiring tools and credit scoring systems. Companies face fines up to 7% of global revenue for violations. Tech industry leaders expressed mixed reactions, with some praising clarity while others warned of innovation barriers."
    },
    {
        "title": "Breakthrough in Quantum Computing Achieves New Milestone",
        "content": "Researchers at MIT have demonstrated a quantum computer maintaining coherence for over 10 minutes, shattering previous records. This breakthrough addresses one of quantum computing's fundamental challenges: qubit stability. The team used a novel error-correction technique combining hardware and software approaches. Industry experts suggest this could accelerate practical quantum computing applications by several years."
    },
    {
        "title": "Global Tech Giants Report Record AI Infrastructure Spending",
        "content": "Microsoft, Google, and Amazon collectively invested over $150 billion in AI infrastructure during 2025, according to new financial reports. The spending primarily targeted data centers, specialized chips, and cooling systems. Analysts note this represents a 340% increase from 2023 levels. Despite concerns about profitability, executives maintain that AI infrastructure is essential for long-term competitiveness."
    },
    {
        "title": "Scientists Develop AI System for Early Cancer Detection",
        "content": "A collaborative team from Stanford and Johns Hopkins has created an AI diagnostic tool detecting early-stage cancers with 94% accuracy from routine blood tests. The system analyzes over 2,000 biomarkers simultaneously, identifying patterns invisible to traditional methods. Clinical trials involving 50,000 patients showed the AI caught cancers an average of 18 months earlier than conventional screening. FDA fast-track approval is expected within six months."
    },
    {
        "title": "Major Cybersecurity Breach Affects 200 Million Users",
        "content": "A sophisticated cyberattack on cloud provider CloudSecure has exposed personal data of approximately 200 million users worldwide. The breach, discovered last week, exploited a zero-day vulnerability in authentication systems. Affected data includes email addresses, encrypted passwords, and billing information. Security experts recommend immediate password changes and enabling two-factor authentication across all accounts."
    },
    {
        "title": "Autonomous Vehicle Industry Reaches Safety Milestone",
        "content": "Waymo announced that its autonomous vehicles have completed 50 million miles without a single at-fault accident resulting in serious injury. The achievement comes after eight years of public road testing across 25 US cities. Independent safety auditors verified the data, noting that human drivers average one serious accident per 1.5 million miles. Several states are now considering expanded autonomous vehicle permissions."
    },
    {
        "title": "New Programming Language Designed for AI Development Gains Traction",
        "content": "Mojo, a programming language specifically designed for AI and machine learning development, has surpassed 500,000 active developers. Created by Chris Lattner, the language combines Python's ease of use with performance rivaling C++. Major tech companies including NVIDIA and AMD have announced native Mojo support in their development tools. The language's ability to run Python code while offering 35,000x speed improvements for compute-intensive tasks has driven rapid adoption."
    },
    {
        "title": "Climate Scientists Use AI to Predict Extreme Weather Events",
        "content": "The National Oceanic and Atmospheric Administration has deployed an AI system that predicts extreme weather events seven days in advance with 85% accuracy, doubling previous forecasting capabilities. The system processes satellite imagery, ocean temperature data, and atmospheric readings in real-time. Early warnings for hurricanes, floods, and heat waves could save thousands of lives annually. The technology will be shared with meteorological agencies worldwide."
    },
    {
        "title": "Tech Industry Faces Global Chip Shortage Recovery Challenges",
        "content": "Despite $500 billion in new semiconductor manufacturing investments, industry analysts predict chip shortages will persist through 2027. The complexity of modern chip fabrication, requiring over 1,000 production steps, limits rapid capacity expansion. Geopolitical tensions between major chip-producing nations add supply chain uncertainty. Automotive and consumer electronics sectors continue experiencing delivery delays averaging 12-18 weeks."
    }
]

# Sample generated summaries for the demo (pre-generated)
SAMPLE_SUMMARIES = {
    # Concise summaries (2 sentences)
    "concise": [
        "OpenAI has unveiled GPT-5, featuring unprecedented reasoning abilities and improved factual accuracy. Enterprise access begins next month, with consumer availability planned for Q2 2026.",
        "The European Parliament has approved the AI Act, the world's most comprehensive AI regulation categorizing systems by risk level. Companies face fines up to 7% of global revenue for violations.",
        "MIT researchers achieved a breakthrough with a quantum computer maintaining coherence for over 10 minutes. This could accelerate practical quantum computing applications by several years.",
        "Microsoft, Google, and Amazon invested over $150 billion in AI infrastructure during 2025, a 340% increase from 2023. The spending primarily targets data centers and specialized chips.",
        "Stanford and Johns Hopkins researchers developed an AI tool detecting early-stage cancers with 94% accuracy from blood tests. FDA fast-track approval is expected within six months.",
        "A cyberattack on CloudSecure exposed personal data of 200 million users through a zero-day vulnerability. Security experts recommend immediate password changes and two-factor authentication.",
        "Waymo's autonomous vehicles completed 50 million miles without a serious at-fault accident. Human drivers average one serious accident per 1.5 million miles by comparison.",
        "Mojo programming language has surpassed 500,000 active developers with its combination of Python ease and C++ performance. It offers up to 35,000x speed improvements for compute-intensive tasks.",
        "NOAA deployed an AI system predicting extreme weather events seven days ahead with 85% accuracy. The technology will be shared with meteorological agencies worldwide.",
        "Despite $500 billion in semiconductor investments, chip shortages will persist through 2027. Automotive and electronics sectors face delivery delays averaging 12-18 weeks.",
    ],
    # Detailed summaries (3-4 sentences)
    "detailed": [
        "OpenAI has announced GPT-5, representing what CEO Sam Altman calls 'a new paradigm in AI capabilities.' The model demonstrates unprecedented reasoning abilities, including solving complex mathematical proofs with improved factual accuracy. Enterprise customers will gain access starting next month, while general consumer availability is planned for the second quarter of 2026.",
        "The European Parliament has passed the AI Act, establishing the world's first comprehensive artificial intelligence regulatory framework. The legislation categorizes AI systems by risk level, imposing strict requirements on high-risk applications such as hiring tools and credit scoring systems. Violations can result in fines of up to 7% of global revenue. Industry reactions have been mixed, with some praising the regulatory clarity while others express concerns about potential innovation barriers.",
        "Researchers at MIT have achieved a significant quantum computing breakthrough, demonstrating coherence for over 10 minutes—far exceeding previous records. The team employed a novel error-correction technique combining both hardware and software approaches to address qubit stability challenges. Industry experts suggest this advancement could accelerate practical quantum computing applications by several years.",
        "The three major tech giants—Microsoft, Google, and Amazon—collectively invested over $150 billion in AI infrastructure throughout 2025, representing a remarkable 340% increase from 2023 levels. Investment priorities include data centers, specialized AI chips, and advanced cooling systems. Despite ongoing profitability concerns, company executives maintain that this infrastructure spending is essential for maintaining long-term competitive advantage in the AI race.",
        "A collaborative research team from Stanford and Johns Hopkins has developed an AI diagnostic system capable of detecting early-stage cancers with 94% accuracy using routine blood tests. The system analyzes over 2,000 biomarkers simultaneously, identifying patterns that are invisible to traditional diagnostic methods. Clinical trials with 50,000 patients demonstrated that the AI detected cancers an average of 18 months earlier than conventional screening. FDA fast-track approval is anticipated within the next six months.",
        "A sophisticated cyberattack targeting cloud provider CloudSecure has resulted in the exposure of personal data belonging to approximately 200 million users worldwide. The breach, discovered last week, exploited a zero-day vulnerability in the company's authentication systems. Compromised data includes email addresses, encrypted passwords, and billing information. Security experts are urging all affected users to immediately change their passwords and enable two-factor authentication across all accounts.",
        "Waymo has announced a significant safety milestone: its autonomous vehicles have completed 50 million miles of public road driving without a single at-fault accident resulting in serious injury. This achievement comes after eight years of testing across 25 US cities and has been verified by independent safety auditors. For comparison, human drivers average one serious accident per 1.5 million miles. Several states are now considering expanded permissions for autonomous vehicle operations.",
        "Mojo, the programming language designed specifically for AI and machine learning development, has reached 500,000 active developers. Created by Chris Lattner, Mojo uniquely combines Python's ease of use with performance levels rivaling C++. Major technology companies including NVIDIA and AMD have announced native Mojo support in their development tools. The language's ability to run existing Python code while delivering up to 35,000x speed improvements for compute-intensive tasks has driven its rapid adoption.",
        "The National Oceanic and Atmospheric Administration has deployed a new AI system capable of predicting extreme weather events seven days in advance with 85% accuracy, effectively doubling previous forecasting capabilities. The system processes satellite imagery, ocean temperature data, and atmospheric readings in real-time. Early warnings for hurricanes, floods, and heat waves generated by this system could save thousands of lives annually. NOAA plans to share this technology with meteorological agencies around the world.",
        "Despite unprecedented investment of $500 billion in new semiconductor manufacturing facilities, industry analysts predict that global chip shortages will persist through 2027. The extraordinary complexity of modern chip fabrication, which requires over 1,000 precise production steps, severely limits how quickly manufacturing capacity can be expanded. Ongoing geopolitical tensions between major chip-producing nations add further uncertainty to global supply chains. The automotive and consumer electronics sectors continue to experience delivery delays averaging 12-18 weeks.",
    ]
}


def seed_demo_video_prompts():
    """
    Creates the two news summarization prompts for the demo video.
    """
    logger.info("Seeding demo video prompts...")

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping demo video prompt seeding")
        return []

    prompts_data = [
        {
            "name": "News Summary Prompt",
            "content": {
                "blocks": {
                    "system": {
                        "content": """You are an expert news editor.

Create summaries that are:
- Exactly 2 sentences
- Factually accurate
- Neutral in tone""",
                        "position": 0
                    },
                    "user": {
                        "content": """Summarize this article:

Title: {{title}}

{{content}}""",
                        "position": 1
                    }
                }
            }
        },
        {
            "name": "Detailed Summary Prompt",
            "content": {
                "blocks": {
                    "system": {
                        "content": """You are a senior journalist creating article summaries for a news digest.

Your summaries should:
- Be 3-4 sentences long
- Capture the key facts and implications
- Use professional journalistic language
- Remain objective and factual""",
                        "position": 0
                    },
                    "user": {
                        "content": """Create a detailed summary of this news article:

Headline: {{title}}

Full Article:
{{content}}

Provide a comprehensive summary:""",
                        "position": 1
                    }
                }
            }
        }
    ]

    created_prompts = []
    for prompt_data in prompts_data:
        existing = UserPrompt.query.filter_by(
            user_id=admin_user.id,
            name=prompt_data["name"]
        ).first()

        if existing:
            logger.debug(f"Prompt '{prompt_data['name']}' already exists")
            created_prompts.append(existing)
            continue

        new_prompt = UserPrompt(
            user_id=admin_user.id,
            name=prompt_data["name"],
            content=prompt_data["content"]
        )
        db.session.add(new_prompt)
        db.session.flush()  # Get the ID
        created_prompts.append(new_prompt)
        logger.info(f"Created demo prompt: {prompt_data['name']}")

    db.session.commit()
    return created_prompts


def seed_demo_video_generation_job():
    """
    Creates a completed batch generation job with all outputs
    for the demo video.
    """
    logger.info("Seeding demo video generation job...")

    # Check if job already exists
    existing_job = GenerationJob.query.filter_by(name="News Summary Demo Job").first()
    if existing_job:
        logger.info("Demo video generation job already exists, skipping")
        return existing_job

    # Get LLM models
    mistral_small = LLMModel.query.filter_by(
        model_id='mistralai/Mistral-Small-3.2-24B-Instruct-2506'
    ).first()
    magistral_small = LLMModel.query.filter_by(
        model_id='mistralai/Magistral-Small-2509'
    ).first()

    if not mistral_small or not magistral_small:
        logger.warning("Required LLM models not found, skipping demo job seeding")
        return None

    # Get prompts
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping demo job seeding")
        return None

    prompt_concise = UserPrompt.query.filter_by(
        user_id=admin_user.id,
        name="News Summary Prompt"
    ).first()
    prompt_detailed = UserPrompt.query.filter_by(
        user_id=admin_user.id,
        name="Detailed Summary Prompt"
    ).first()

    if not prompt_concise or not prompt_detailed:
        logger.warning("Demo prompts not found, creating them first...")
        prompts = seed_demo_video_prompts()
        if len(prompts) < 2:
            logger.error("Failed to create demo prompts")
            return None
        prompt_concise, prompt_detailed = prompts[0], prompts[1]

    # Use embedded news articles
    news_articles = NEWS_ARTICLES

    # Create the generation job
    now = datetime.utcnow()
    total_outputs = len(news_articles) * 2 * 2  # 10 articles x 2 prompts x 2 models = 40

    job = GenerationJob(
        name="News Summary Demo Job",
        description="Demo batch generation job comparing two prompts across two LLM models on 10 news articles.",
        status=GenerationJobStatus.COMPLETED,
        config_json={
            "mode": "matrix",
            "sources": {
                "type": "manual",
                "items": news_articles
            },
            "prompts": [
                {"template_name": prompt_concise.name},
                {"template_name": prompt_detailed.name}
            ],
            "llm_models": [mistral_small.model_id, magistral_small.model_id],
            "generation_params": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        total_items=total_outputs,
        completed_items=total_outputs,
        failed_items=0,
        total_tokens=total_outputs * 800,  # Estimated
        total_cost_usd=0.05,  # Estimated
        created_by='admin',
        created_at=now - timedelta(hours=2),
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=45)
    )
    db.session.add(job)
    db.session.flush()

    # Create outputs for each combination
    output_id = 0
    for article_idx, article in enumerate(news_articles):
        for prompt_type, prompt in [("concise", prompt_concise), ("detailed", prompt_detailed)]:
            for model in [mistral_small, magistral_small]:
                summary = SAMPLE_SUMMARIES[prompt_type][article_idx]

                output = GeneratedOutput(
                    job_id=job.id,
                    prompt_template_id=None,  # user_prompts != prompt_templates
                    llm_model_id=model.id,
                    llm_model_name=model.model_id,
                    prompt_variant_name=prompt.name,
                    generated_content=summary,
                    rendered_system_prompt=prompt.content.get('blocks', {}).get('system', {}).get('content', ''),
                    rendered_user_prompt=f"Title: {article['title']}\n\n{article['content']}",
                    status=GeneratedOutputStatus.COMPLETED,
                    input_tokens=len(article['content'].split()) + 50,  # Rough estimate
                    output_tokens=len(summary.split()),
                    total_cost_usd=0.001,
                    processing_time_ms=1500 + (output_id * 50),  # Vary slightly
                    attempt_count=1,
                    created_at=now - timedelta(hours=2),
                    completed_at=now - timedelta(hours=1, minutes=50 - output_id)
                )
                db.session.add(output)
                output_id += 1

    db.session.commit()
    logger.info(f"Created demo generation job with {total_outputs} outputs")
    return job


def seed_demo_video_data(db_instance=None):
    """
    Main entry point: Seeds all demo video data.
    Call this from the seeders __init__.py
    """
    logger.info("=" * 60)
    logger.info("SEEDING DEMO VIDEO DATA")
    logger.info("=" * 60)

    # 1. Create prompts
    prompts = seed_demo_video_prompts()
    logger.info(f"Demo prompts ready: {len(prompts)} prompts")

    # 2. Create completed generation job
    job = seed_demo_video_generation_job()
    if job:
        logger.info(f"Demo generation job ready: {job.name} (ID: {job.id})")

    logger.info("=" * 60)
    logger.info("DEMO VIDEO DATA SEEDING COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    # For standalone testing
    from app.main import create_app
    app = create_app()
    with app.app_context():
        seed_demo_video_data()
