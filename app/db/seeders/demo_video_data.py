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
    # Analyst summaries (3 sentences — detailed with context and implications)
    "analyst": [
        "OpenAI has announced GPT-5 with unprecedented reasoning abilities including solving complex mathematical proofs, intensifying the race against competitors Google and Anthropic. Enterprise access begins next month while consumers wait until Q2 2026, giving OpenAI's business clients a strategic head start. The release raises open questions about energy consumption at scale and whether the reasoning improvements will generalize beyond curated benchmarks.",
        "The European Parliament has passed the AI Act, the world's first comprehensive framework that categorizes AI systems by risk level and imposes fines up to 7% of global revenue for violations. The regulation targets high-risk applications like hiring tools and credit scoring, creating major compliance burdens for multinational tech companies. A two-year implementation phase begins now, during which national regulators across the EU must build the enforcement infrastructure from scratch.",
        "MIT researchers have demonstrated quantum coherence for over 10 minutes using a novel combined hardware-software error-correction technique, far surpassing previous records. Both IBM and Google have expressed interest in licensing the framework, signaling strong industry confidence in the approach. The remaining challenge is scaling the technique from controlled laboratory conditions to commercially viable quantum hardware.",
        "Microsoft, Google, and Amazon collectively spent over $150 billion on AI infrastructure in 2025—a 340% jump from 2023—primarily targeting data centers, specialized chips, and cooling systems. The spending wave has triggered a secondary boom in construction and energy supply industries near planned data center sites. Whether enterprise AI revenue will grow fast enough to justify these capital expenditures remains the central question for investors.",
        "Researchers from Stanford and Johns Hopkins have built an AI system that detects early-stage cancers with 94% accuracy from routine blood tests by analyzing over 2,000 biomarkers simultaneously. Clinical trials with 50,000 patients showed the AI caught cancers an average of 18 months earlier than conventional screening methods. Major hospital networks and insurance providers are already exploring reimbursement models ahead of an expected FDA fast-track approval within six months.",
        "A cyberattack on cloud provider CloudSecure has exposed personal data of approximately 200 million users through a zero-day vulnerability in authentication systems, though financial account numbers appear unaffected. Security experts recommend immediate password changes and two-factor authentication, while CloudSecure faces potential regulatory investigations in multiple jurisdictions. The incident has reignited the debate around mandatory breach disclosure timelines and minimum security standards for cloud providers.",
        "Waymo's autonomous fleet has completed 50 million miles without a serious at-fault accident, compared to human drivers who average one per 1.5 million miles, as verified by independent auditors. Eight years of testing across 25 US cities have convinced several states to consider expanded permissions for autonomous operations. Open questions remain about performance in extreme weather conditions and whether the safety record will hold as deployments scale to denser urban areas.",
        "Mojo, Chris Lattner's programming language combining Python's usability with C++ performance, has reached 500,000 developers as NVIDIA and AMD add native support to their tool chains. Its ability to run existing Python code while delivering up to 35,000x speed improvements for compute-heavy tasks addresses a long-standing pain point in the ML community. The open question is whether Mojo's ecosystem can mature fast enough to challenge Python's entrenched position in data science education and research.",
        "NOAA has deployed an AI system that predicts extreme weather events seven days ahead with 85% accuracy, doubling previous forecasting capabilities by processing satellite, ocean, and atmospheric data in real time. The World Meteorological Organization has already expressed interest in adopting the technology, which could save thousands of lives and billions in damage annually. Deployment to agencies worldwide will require adapting the models to regional climate patterns, a process expected to take several years.",
        "Despite $500 billion in new semiconductor investments, chip shortages are projected to persist through 2027 because modern fabrication requires over 1,000 production steps that limit rapid capacity expansion. Geopolitical tensions between major chip-producing nations add further supply chain uncertainty, while automotive and electronics sectors face persistent 12-to-18-week delivery delays. The next milestone is the completion of TSMC's Arizona fab and Intel's Ohio facility, both expected to come online in late 2027.",
    ]
}


def seed_demo_video_prompts():
    """
    Creates the news summarization prompt for the demo video.
    """
    logger.info("Seeding demo video prompts...")

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping demo video prompt seeding")
        return []

    def build_blocks(role_text: str, task_text: str, data_text: str):
        return {
            "Role Definition": {
                "content": role_text,
                "position": 0
            },
            "Task Explanation": {
                "content": task_text,
                "position": 1
            },
            "Data Format Explanation": {
                "content": data_text,
                "position": 2
            }
        }

    prompts_data = [
        {
            "name": "News Summary Prompt",
            "content": {
                "blocks": build_blocks(
                    role_text=(
                        "Role definition: You are a senior news analyst working for an international press agency. "
                        "Your summaries are used by editors who need to decide whether a story deserves front-page coverage. "
                        "You have deep expertise in technology, science, and policy reporting. "
                        "Your writing style is precise, uses active voice, and avoids hedging language."
                    ),
                    task_text=(
                        "Task explanation: Analyze the article and produce a structured 3-sentence summary.\n\n"
                        "Sentence 1 — Lead: State the core news event with the most important fact or figure.\n"
                        "Sentence 2 — Context: Provide essential background that helps the reader understand why this matters.\n"
                        "Sentence 3 — Outlook: Mention next steps, open questions, or broader implications.\n\n"
                        "Guidelines:\n"
                        "- Use specific numbers and names from the article when available.\n"
                        "- Do not speculate beyond what the article states.\n"
                        "- Keep each sentence under 30 words.\n"
                        "- Write in present tense for the lead, past tense for background, and future tense for outlook.\n\n"
                        "Few-shot examples:\n\n"
                        "Example input: 'SpaceX Successfully Lands Starship After Orbital Flight'\n"
                        "Example output: SpaceX lands its Starship rocket after a full orbital flight, achieving a key milestone "
                        "for the program. The company spent three years and an estimated $2 billion developing the reusable "
                        "heavy-lift vehicle. NASA now considers Starship the leading candidate for its Artemis lunar cargo missions.\n\n"
                        "Example input: 'Japan Approves First Gene-Edited Food for Consumer Sale'\n"
                        "Example output: Japan becomes the first country to approve a gene-edited tomato for direct sale to "
                        "consumers. Regulators determined that CRISPR-based edits carry no additional risk compared to conventional "
                        "breeding. The decision is expected to accelerate gene-editing approvals across Asia and influence ongoing "
                        "EU regulatory debates."
                    ),
                    data_text=(
                        "Data format explanation:\n"
                        "Input:\n"
                        "Title: {{title}}\n\n"
                        "Article:\n"
                        "{{content}}\n\n"
                        "Output:\n"
                        "Exactly 3 sentences in plain text following the Lead-Context-Outlook structure above. "
                        "No bullet points. No headings. No extra commentary."
                    )
                )
            }
        },
        {
            "name": "News Summary Eval",
            "content": {
                "blocks": build_blocks(
                    role_text="Role definition: You are an analytical journalist who provides thorough context alongside factual reporting.",
                    task_text="Task explanation: Write a 3-sentence summary of the article. Include relevant background, mention key stakeholders, and explain broader implications beyond the headline.",
                    data_text=(
                        "Data format explanation:\n"
                        "Input:\n"
                        "Title: {{title}}\n\n"
                        "Article:\n"
                        "{{content}}\n\n"
                        "Output:\n"
                        "Exactly 3 sentences in plain text. No bullet points. No extra commentary."
                    )
                )
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
    prompt_eval = UserPrompt.query.filter_by(
        user_id=admin_user.id,
        name="News Summary Eval"
    ).first()
    if not prompt_concise or not prompt_eval:
        logger.warning("Demo prompts not found, creating them first...")
        prompts = seed_demo_video_prompts()
        prompts_by_name = {p.name: p for p in prompts}
        prompt_concise = prompt_concise or prompts_by_name.get("News Summary Prompt")
        prompt_eval = prompt_eval or prompts_by_name.get("News Summary Eval")
        if not prompt_concise or not prompt_eval:
            logger.error("Failed to create demo prompts")
            return None

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
                {"template_name": prompt_eval.name}
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
    def get_block_content(prompt, block_name):
        blocks = (prompt.content or {}).get('blocks', {})
        block = blocks.get(block_name, {})
        return block.get('content', '') if isinstance(block, dict) else ''

    def render_system_prompt(prompt):
        parts = [
            get_block_content(prompt, "Role Definition"),
            get_block_content(prompt, "Task Explanation")
        ]
        return "\n\n".join([p for p in parts if p])

    def render_user_prompt(prompt, article):
        template = get_block_content(prompt, "Data Format Explanation")
        if not template:
            return f"Title: {article['title']}\n\n{article['content']}"
        return (
            template
            .replace("{{title}}", article["title"])
            .replace("{{content}}", article["content"])
        )

    for article_idx, article in enumerate(news_articles):
        for prompt_type, prompt, summary_key in [
            ("concise", prompt_concise, "concise"),
            ("analyst", prompt_eval, "analyst"),
        ]:
            for model in [mistral_small, magistral_small]:
                summary = SAMPLE_SUMMARIES[summary_key][article_idx]

                output = GeneratedOutput(
                    job_id=job.id,
                    prompt_template_id=None,  # user_prompts != prompt_templates
                    llm_model_id=model.id,
                    llm_model_name=model.model_id,
                    prompt_variant_name=prompt.name,
                    prompt_variables_json={
                        'source_index': article_idx,
                        'source_title': article['title']
                    },
                    generated_content=summary,
                    rendered_system_prompt=render_system_prompt(prompt),
                    rendered_user_prompt=render_user_prompt(prompt, article),
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
