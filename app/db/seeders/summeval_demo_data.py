"""
SummEval Demo Data Seeder

Creates demo data for text summarization evaluation (LLM-as-Judge).
Based on the SummEval benchmark dimensions:
- Coherence: Is the summary well-structured and logically organized?
- Fluency: Is the text grammatically correct and easy to read?
- Relevance: Does the summary capture the important information?
- Consistency: Is the summary factually consistent with the source?

Each item contains:
- Source text (original article)
- Summary to evaluate
"""

from datetime import datetime, timedelta


# Demo summarization data
# Each item has a source article and a summary to evaluate
SUMMEVAL_DEMO_DATA = [
    {
        "subject": "Breakthrough in Renewable Energy Storage",
        "source": """Scientists at MIT have announced a major breakthrough in battery technology that could revolutionize renewable energy storage. The new solid-state battery design uses a ceramic electrolyte instead of the liquid electrolytes found in conventional lithium-ion batteries.

The research team, led by Professor Jennifer Martinez, demonstrated that the new batteries can store twice as much energy as current lithium-ion cells while being significantly safer. "Liquid electrolytes are flammable and can lead to dangerous thermal runaway," explained Dr. Martinez. "Our solid-state design eliminates this risk entirely."

The breakthrough comes after five years of intensive research funded by the Department of Energy. Initial tests show the batteries can withstand over 10,000 charge cycles without significant degradation, compared to roughly 1,000 cycles for conventional batteries.

Industry experts believe this could be transformative for the renewable energy sector. Solar and wind power generation is intermittent, and efficient storage has been the missing piece for widespread adoption. "This could finally make 100% renewable grids economically viable," said energy analyst Michael Thompson.

The team estimates commercial production could begin within three to five years, pending further testing and manufacturing scale-up. Several major automotive and electronics companies have already expressed interest in licensing the technology.""",
        "summary": """MIT scientists have developed a revolutionary solid-state battery using ceramic electrolytes that stores twice the energy of current lithium-ion batteries while being much safer. After five years of DOE-funded research, the batteries showed over 10,000 charge cycles without degradation. Experts believe this breakthrough could make 100% renewable energy grids viable, with commercial production expected in 3-5 years.""",
        "quality": "high"
    },
    {
        "subject": "Global Climate Summit Reaches Historic Agreement",
        "source": """World leaders gathered in Geneva this week concluded the most ambitious climate summit in history, reaching a landmark agreement to limit global warming to 1.5 degrees Celsius above pre-industrial levels. The accord was signed by 195 nations after two weeks of intense negotiations.

Under the new framework, developed nations committed to achieving net-zero carbon emissions by 2040, while developing countries agreed to peak their emissions by 2035. A historic $500 billion annual fund was established to help poorer nations transition to clean energy.

The agreement includes binding enforcement mechanisms for the first time. Countries that fail to meet their targets will face trade penalties and restricted access to the climate fund. Independent monitoring bodies will track progress annually.

Environmental groups cautiously welcomed the deal. "This is a significant step forward, but implementation will be the real test," said Greenpeace International director Dr. Sarah Chen. Critics, however, argue the timelines are still too slow given the urgency of the climate crisis.

The summit also addressed methane emissions, with major agricultural nations agreeing to reduce livestock-related emissions by 30% by 2030. This represents the first major commitment to address agricultural contributions to climate change.""",
        "summary": """Climate summit Geneva. Countries agree limit warming. Net-zero 2040 developed nations. $500 billion fund created. Penalties for failure. Environmental groups say good but need action. Methane also addressed 30% reduction livestock.""",
        "quality": "low"
    },
    {
        "subject": "AI System Diagnoses Rare Diseases",
        "source": """A new artificial intelligence system developed by Stanford Medical School has demonstrated remarkable accuracy in diagnosing rare genetic diseases, potentially ending years of diagnostic odysseys for thousands of patients annually.

The system, named DiagnosticAI, analyzes patient symptoms, medical history, and genetic data to identify rare conditions that often take an average of seven years to diagnose. In clinical trials involving 5,000 patients, the AI correctly identified the underlying condition in 89% of cases within minutes.

Dr. Robert Kim, who led the development team, explained that the system was trained on medical records from over 2 million patients worldwide. "Rare diseases are challenging because individual doctors may only see one or two cases in their entire career. Our AI has effectively learned from millions of cases."

The technology has already been implemented in 50 hospitals across the United States, with plans for international expansion. Early adopters report significant improvements in patient outcomes, with faster diagnoses leading to earlier treatment interventions.

However, the system is designed to assist rather than replace physicians. "The AI provides recommendations that doctors then verify," clarified Dr. Kim. "The final diagnostic decision always remains with the medical professional."

Insurance companies have begun covering AI-assisted diagnostics, recognizing the potential for cost savings through earlier intervention and reduced unnecessary testing.""",
        "summary": """Stanford's DiagnosticAI system can identify rare genetic diseases in minutes with 89% accuracy, compared to the typical 7-year diagnostic journey. Trained on 2 million patient records, the AI assists doctors by analyzing symptoms, history, and genetic data. Already deployed in 50 US hospitals, the system improves outcomes through faster diagnoses while keeping physicians in control of final decisions.""",
        "quality": "high"
    },
    {
        "subject": "Ocean Plastic Cleanup Project Milestone",
        "source": """The Ocean Cleanup project announced today that it has successfully removed over 1 million kilograms of plastic waste from the Great Pacific Garbage Patch, marking a significant milestone in the fight against ocean pollution.

Founded by Dutch inventor Boyan Slat in 2013, the non-profit organization has developed innovative floating barriers that use ocean currents to passively collect plastic debris. The latest generation of their cleanup systems, called System 03, is 10 times more efficient than earlier designs.

"When we started, many said it was impossible to clean the oceans," said Slat during a press conference. "Today we're proving that with the right technology and determination, we can make a real difference."

The Great Pacific Garbage Patch, located between Hawaii and California, contains an estimated 80,000 tonnes of plastic waste spread across an area twice the size of Texas. Marine biologists have documented the devastating impact on wildlife, with sea turtles, fish, and seabirds frequently ingesting or becoming entangled in plastic debris.

The project plans to scale up operations significantly, with the goal of removing 90% of floating ocean plastic by 2040. New partnerships with recycling companies mean collected plastic is now being transformed into sustainable products, creating a circular economy model.

Environmental scientists have praised the effort while emphasizing the need to also reduce plastic production at the source. "Cleanup is essential, but prevention must be the priority," noted marine ecologist Dr. Amanda Foster.""",
        "summary": """The Ocean Cleanup has removed 1 million kg of plastic from the Great Pacific Garbage Patch using innovative floating barriers. Founded by Boyan Slat, the project's System 03 is 10 times more efficient than earlier designs. The organization aims to remove 90% of ocean plastic by 2040, partnering with recyclers to create sustainable products from collected waste.""",
        "quality": "high"
    },
    {
        "subject": "New Study on Sleep and Memory",
        "source": """Researchers at the University of California have published groundbreaking findings on the relationship between sleep and memory consolidation, revealing that specific sleep stages play distinct roles in different types of learning.

The study, involving 500 participants over three years, used advanced brain imaging to track neural activity during sleep. Results showed that deep slow-wave sleep is critical for consolidating factual knowledge, while REM sleep appears essential for procedural and emotional memories.

Dr. Patricia Wong, the study's lead author, explained: "We found that disrupting slow-wave sleep significantly impaired participants' ability to recall facts learned the previous day. But it didn't affect their memory for physical skills like typing or playing piano."

Perhaps most surprising was the discovery that a brief period of light sleep immediately after learning dramatically improved retention. "Just a 20-minute nap after studying showed a 40% improvement in recall compared to staying awake," noted Dr. Wong.

The findings have significant implications for education and workplace training. Schools that have experimented with later start times and incorporated rest periods have seen measurable improvements in student performance.

The research also sheds light on why sleep deprivation is so harmful to cognitive function. Chronic lack of sleep disrupts the brain's ability to consolidate memories, leading to cumulative learning deficits over time.""",
        "summary": """UC researchers found sleep stages affect different memory types: slow-wave sleep consolidates facts, REM sleep handles skills and emotions. Surprisingly, a 20-minute nap after learning improved recall by 40%. The 3-year study of 500 participants suggests schools should consider later starts and rest periods to boost learning.""",
        "quality": "high"
    },
    {
        "subject": "Electric Vehicle Market Growth",
        "source": """Global electric vehicle sales surged to record levels in 2024, with EVs now accounting for 25% of all new car purchases worldwide, according to a comprehensive report released by the International Energy Agency.

The rapid growth was driven by a combination of factors: expanding charging infrastructure, falling battery costs, and new government incentives. China remained the largest market, representing 60% of global EV sales, followed by Europe at 25% and North America at 10%.

Battery prices have fallen 90% since 2010, making EVs increasingly competitive with conventional vehicles. The average electric car now costs only 10% more than an equivalent gasoline model, down from a 50% premium just five years ago.

Automakers are responding to demand by accelerating their transition plans. Ford, GM, and Volkswagen have all committed to phasing out internal combustion engines by 2035. Tesla remains the market leader, but faces increasing competition from Chinese manufacturers BYD and NIO.

Challenges remain, including limited charging infrastructure in rural areas and concerns about battery raw material supply chains. However, new solid-state battery technology promises to address range anxiety with cells capable of 500-mile ranges and 10-minute charging times.

The shift to electric vehicles is expected to significantly reduce transportation emissions, which currently account for about 20% of global carbon output. Analysts predict EVs could reach 50% market share by 2030 if current trends continue.""",
        "summary": """Electric vehicle sales reached record levels with 25% global market share. Battery costs dropped 90% since 2010. China leads with 60% of sales. Major automakers plan to end combustion engines by 2035. EVs could reach 50% share by 2030, potentially cutting the 20% of emissions from transportation significantly.""",
        "quality": "high"
    },
    {
        "subject": "Quantum Computing Achieves Supremacy",
        "source": """Google's quantum computing division announced a landmark achievement this week, demonstrating that their latest quantum processor can solve certain mathematical problems millions of times faster than the world's most powerful supercomputers.

The 100-qubit Willow processor completed a complex simulation in under four minutes that would take classical computers approximately 10,000 years. This represents the clearest demonstration yet of quantum advantage for practically relevant computations.

"This is the moment we've been working toward for decades," said Dr. Hartmut Neven, head of Google Quantum AI. "We're moving from theoretical possibility to practical reality."

Quantum computers leverage the principles of quantum mechanics, using qubits that can exist in multiple states simultaneously. This allows them to explore many potential solutions to a problem at once, rather than checking each possibility sequentially like classical computers.

The implications span numerous fields. Drug discovery could be accelerated by simulating molecular interactions. Financial institutions could optimize portfolios more effectively. Cryptography will need to evolve, as quantum computers threaten to break current encryption methods.

IBM, Microsoft, and several startups are also racing to develop practical quantum computers. While Google's achievement is significant, experts caution that useful commercial applications may still be several years away.

"We're at the transistor stage of a new computing paradigm," noted MIT quantum researcher Dr. James Liu. "The full potential won't be realized for perhaps another decade."

The technology currently requires extreme cooling to near absolute zero, making it expensive and impractical for widespread deployment. Research into room-temperature quantum computing continues but faces substantial technical hurdles.""",
        "summary": """Quantum computers very fast. Google made processor. Solves problems quickly. Uses qubits not regular bits. Good for medicine and money things. IBM Microsoft also working on it. Needs to be very cold to work. Maybe useful in 10 years experts say.""",
        "quality": "low"
    },
    {
        "subject": "Urban Vertical Farming Expansion",
        "source": """Vertical farming is experiencing explosive growth in major cities worldwide, with the global market projected to reach $20 billion by 2030. These high-tech indoor farms stack growing trays in multi-story facilities, using LED lights and precisely controlled environments to grow produce year-round.

Singapore, with limited agricultural land, has emerged as a leader in the field. The city-state now produces 30% of its vegetables through vertical farms, up from just 5% five years ago. Sky Greens, the country's largest vertical farm, harvests over 1 ton of leafy greens daily using only 5% of the water required by traditional farming.

The technology offers several advantages: crops grow 20 times faster than in conventional fields, pesticides are unnecessary in the sterile environment, and transportation emissions are eliminated when farms are located within cities.

However, critics point to high energy costs as a significant drawback. Powering the LED lights and climate control systems makes vertical farming energy-intensive. Proponents counter that renewable energy and improving LED efficiency are rapidly addressing this concern.

Major investments are flowing into the sector. SoftBank recently led a $400 million funding round for US-based Plenty, while Amazon has acquired several vertical farming startups. Supermarket chains are beginning to install small farms directly in stores.

The industry primarily focuses on leafy greens and herbs currently, as these crops offer the best economics. Research into growing fruiting plants like tomatoes and strawberries is progressing, though these remain more challenging due to their longer growth cycles and pollination requirements.""",
        "summary": """Vertical farming is booming globally, projected to reach $20 billion by 2030. Singapore leads with 30% of vegetables grown in vertical farms using 95% less water. Crops grow 20x faster without pesticides in urban facilities. While energy costs remain a concern, major investors including SoftBank and Amazon are backing the technology. Currently focused on leafy greens, research continues on fruiting plants.""",
        "quality": "high"
    },
    {
        "subject": "Antibiotic Resistance Crisis",
        "source": """The World Health Organization released a sobering report this week warning that antibiotic-resistant infections now kill more people annually than HIV/AIDS and malaria combined. The report calls for urgent global action to address what officials describe as a "silent pandemic."

Approximately 5 million deaths per year are now associated with antibiotic-resistant bacteria, with the toll expected to rise dramatically without intervention. The problem is particularly acute in developing nations with limited healthcare infrastructure and fewer antibiotic options.

The crisis stems from decades of antibiotic overuse in both medicine and agriculture. Bacteria evolve rapidly, and widespread antibiotic exposure has selected for resistant strains. Common infections that were easily treatable 30 years ago can now be deadly.

"We are running out of options," warned WHO Director-General Dr. Tedros Adhanom. "If we don't act now, we risk returning to a pre-antibiotic era where minor infections could kill."

The pharmaceutical industry has largely abandoned antibiotic development due to poor financial returns. New antibiotics are used sparingly to preserve their effectiveness, limiting profitability. Government incentives are needed to restart the pipeline, experts argue.

Promising new approaches are emerging, including bacteriophage therapy using viruses that kill bacteria, and AI-designed drugs that target bacteria in novel ways. However, these remain largely experimental.

Prevention is equally critical. Better sanitation, improved hospital infection control, and reducing agricultural antibiotic use could significantly slow the spread of resistance. Some countries have already implemented strict prescribing guidelines with measurable success.""",
        "summary": """The WHO reports antibiotic-resistant infections now kill 5 million annually, more than HIV/AIDS and malaria combined. Decades of overuse in medicine and agriculture have created "superbugs." Pharmaceutical companies have abandoned antibiotic development due to low profits. New approaches like bacteriophage therapy show promise, but prevention through better sanitation and prescribing guidelines remains essential.""",
        "quality": "high"
    },
    {
        "subject": "Mars Colony Mission Update",
        "source": """SpaceX has unveiled detailed plans for the first permanent human settlement on Mars, targeting an initial crew landing by 2030. The ambitious project would establish a self-sustaining colony capable of supporting 1,000 residents within 20 years.

The plan centers on the Starship rocket system, designed to transport up to 100 passengers per flight. CEO Elon Musk outlined a strategy of sending unmanned cargo ships first to pre-position supplies and begin constructing habitats using locally-sourced materials.

"Mars is the backup drive for civilization," Musk stated at the announcement. "Becoming a multi-planetary species is essential for humanity's long-term survival."

The colony would initially depend on supplies from Earth but aims to achieve self-sufficiency within a decade. Engineers are developing systems to extract water from Martian ice, produce oxygen from the CO2-rich atmosphere, and grow food in pressurized greenhouses.

NASA has endorsed the timeline as "ambitious but potentially achievable," noting that SpaceX's progress with Starship has exceeded expectations. The agency is contributing technology and may send astronauts on early missions.

Critics raise concerns about the health risks of extended Mars missions, including radiation exposure and the psychological toll of isolation. The one-way communication delay of up to 24 minutes makes real-time Earth support impossible.

Financial estimates for the project range from $100 billion to $500 billion over 20 years. Musk has proposed ticket prices of $500,000 per passenger, with SpaceX providing loans to those who commit to working in the colony.""",
        "summary": """SpaceX plans Mars settlement by 2030, eventually housing 1,000 people. Using Starship rockets carrying 100 passengers, unmanned cargo ships will arrive first to build habitats. The colony aims for self-sufficiency within a decade through local water extraction and food production. Costs may reach $500 billion, with passenger tickets at $500,000.""",
        "quality": "high"
    },
    {
        "subject": "Gene Therapy Cures Inherited Blindness",
        "source": """In a medical breakthrough, researchers at Johns Hopkins University have successfully used gene therapy to restore vision in patients with Leber congenital amaurosis, a rare inherited condition that causes blindness from birth.

The treatment, called Luxturna, delivers a functional copy of the defective gene directly into the retina using a modified virus as a carrier. Clinical trials showed remarkable results: 93% of patients experienced significant vision improvement, with many able to navigate independently for the first time in their lives.

Eight-year-old Emma Thompson, one of the trial participants, saw her parents' faces clearly for the first time three months after treatment. "Watching her recognize us visually was the most emotional moment of our lives," said her mother, Sarah Thompson.

The therapy targets a specific mutation in the RPE65 gene, which affects about 2,000 people in the United States. While this represents a small patient population, researchers believe the approach could be adapted to treat numerous other genetic eye conditions.

Dr. Jean Bennett, who pioneered the technique, emphasized that early treatment produces better outcomes. "The retina continues to degenerate over time. Treating children before too much damage occurs gives the best chance for lasting vision."

The treatment costs $850,000 for both eyes, making it one of the most expensive medical procedures available. Insurance coverage varies, though most major insurers have agreed to cover qualified patients given the transformative results.

The success has energized the broader gene therapy field. Similar approaches are being developed for other genetic diseases, including sickle cell anemia and muscular dystrophy.""",
        "summary": """Johns Hopkins researchers cured inherited blindness using gene therapy that delivers functional genes to the retina. The treatment called Luxturna helped 93% of patients with Leber congenital amaurosis, a condition affecting 2,000 Americans. The $850,000 procedure works best in children before retinal damage progresses. This success is advancing gene therapies for other genetic diseases.""",
        "quality": "high"
    },
    {
        "subject": "Global Food Security Challenges",
        "source": """A comprehensive United Nations report warns that climate change, population growth, and resource depletion are creating unprecedented challenges for global food security. By 2050, food production must increase by 60% to feed a projected 9.7 billion people.

Changing weather patterns are already affecting agricultural yields. Extended droughts in major grain-producing regions and more frequent flooding have reduced harvests by an estimated 5% globally over the past decade. These trends are expected to accelerate.

Water scarcity presents another critical challenge. Agriculture consumes 70% of global freshwater withdrawals, but aquifers in major farming regions are being depleted faster than they can recharge. The Ogallala Aquifer, which supports a significant portion of US grain production, could be largely exhausted within 50 years.

Soil degradation compounds these problems. Intensive farming practices have depleted nutrients and organic matter in agricultural soils worldwide. The UN estimates that 40% of agricultural land is now significantly degraded.

However, the report also highlights promising solutions. Precision agriculture using satellites and sensors can optimize water and fertilizer use. Drought-resistant crop varieties developed through genetic modification show yield improvements of 20-30% in arid conditions. Vertical farming and cultured meat offer alternatives that require far less land and water.

Investment in agricultural research has declined in recent decades, a trend experts urge should be reversed. "The challenges are immense, but they are solvable with sufficient commitment and resources," concluded the report's lead author, Dr. James Hansen.""",
        "summary": """The UN warns food production must rise 60% by 2050 for 9.7 billion people amid climate challenges. Droughts and floods have cut global harvests 5%. Water scarcity threatens farming as aquifers deplete, and 40% of agricultural land is degraded. Solutions include precision agriculture, drought-resistant crops, and vertical farming, but investment in agricultural research must increase.""",
        "quality": "high"
    }
]


def seed_summeval_demo_scenario(db):
    """
    Create a SummEval-style demo scenario for summarization evaluation.

    Args:
        db: SQLAlchemy database instance
    """
    from db.models import (
        User, EvaluationItem, Message, RatingScenarios,
        ScenarioUsers, ScenarioItems, ScenarioItemDistribution,
        ScenarioRoles, FeatureFunctionType
    )

    print("\n" + "=" * 60)
    print("Seeding SummEval Demo Scenario (Summarization Evaluation)...")
    print("=" * 60)

    # Get users
    evaluator = User.query.filter_by(username='evaluator').first()
    researcher = User.query.filter_by(username='researcher').first()
    admin = User.query.filter_by(username='admin').first()

    if not evaluator or not researcher:
        print("  ERROR: Required users not found")
        return None

    # Get rating function type
    rating_type = FeatureFunctionType.query.filter_by(name='rating').first()
    if not rating_type:
        print("  ERROR: Rating function type not found")
        return None

    # Check if scenario already exists
    existing = RatingScenarios.query.filter_by(
        scenario_name='SummEval Demo - Summarization'
    ).first()

    if existing:
        print("  SummEval Demo scenario already exists")
        # Update config
        existing.config_json = _get_summeval_config()

        # Fix any missing messages from partial runs
        fixed_count = 0
        for i, data in enumerate(SUMMEVAL_DEMO_DATA):
            chat_id = 30000 + i
            item = EvaluationItem.query.filter_by(
                chat_id=chat_id,
                institut_id=1,
                function_type_id=rating_type.function_type_id
            ).first()
            if item:
                msg_count = Message.query.filter_by(item_id=item.item_id).count()
                if msg_count < 2:
                    if msg_count == 0:
                        db.session.add(Message(
                            item_id=item.item_id,
                            sender='Source Article',
                            content=data['source'],
                            timestamp=datetime.now() - timedelta(days=14-i, hours=i*2)
                        ))
                    db.session.add(Message(
                        item_id=item.item_id,
                        sender='Summary',
                        content=data['summary'],
                        timestamp=datetime.now() - timedelta(days=14-i, hours=i*2, minutes=30),
                        generated_by='LLM'
                    ))
                    fixed_count += 1

        db.session.commit()
        if fixed_count > 0:
            print(f"  Fixed {fixed_count} items with missing messages")
        print("  Updated config")
        return existing

    # Create evaluation items
    # Using chat_ids starting at 30000 to avoid conflicts
    items = []
    for i, data in enumerate(SUMMEVAL_DEMO_DATA):
        chat_id = 30000 + i

        # Check if item already exists
        existing_item = EvaluationItem.query.filter_by(
            chat_id=chat_id,
            institut_id=1,
            function_type_id=rating_type.function_type_id
        ).first()

        if existing_item:
            # Check if messages exist for this item
            msg_count = Message.query.filter_by(item_id=existing_item.item_id).count()
            if msg_count < 2:
                # Create missing messages
                if msg_count == 0:
                    source_msg = Message(
                        item_id=existing_item.item_id,
                        sender='Source Article',
                        content=data['source'],
                        timestamp=datetime.now() - timedelta(days=14-i, hours=i*2)
                    )
                    db.session.add(source_msg)
                # Add summary message
                summary_msg = Message(
                    item_id=existing_item.item_id,
                    sender='Summary',
                    content=data['summary'],
                    timestamp=datetime.now() - timedelta(days=14-i, hours=i*2, minutes=30),
                    generated_by='LLM'
                )
                db.session.add(summary_msg)
                print(f"  Added missing messages for: {data['subject'][:40]}...")
            else:
                print(f"  Item exists: {data['subject'][:40]}...")
            items.append(existing_item)
            continue

        # Create EvaluationItem
        item = EvaluationItem(
            chat_id=chat_id,
            institut_id=1,
            subject=data['subject'],
            sender='News Article',
            function_type_id=rating_type.function_type_id
        )
        db.session.add(item)
        db.session.flush()

        # Create message with source text
        source_msg = Message(
            item_id=item.item_id,
            sender='Source Article',
            content=data['source'],
            timestamp=datetime.now() - timedelta(days=14-i, hours=i*2)
        )
        db.session.add(source_msg)

        # Create message with summary to evaluate
        summary_msg = Message(
            item_id=item.item_id,
            sender='Summary',
            content=data['summary'],
            timestamp=datetime.now() - timedelta(days=14-i, hours=i*2, minutes=30),
            generated_by='LLM'
        )
        db.session.add(summary_msg)

        items.append(item)
        print(f"  Created item: {data['subject'][:40]}...")

    db.session.flush()

    # Create scenario
    scenario = RatingScenarios(
        scenario_name='SummEval Demo - Summarization',
        function_type_id=rating_type.function_type_id,
        begin=datetime.now() - timedelta(days=7),
        end=datetime.now() + timedelta(days=90),
        timestamp=datetime.now(),
        config_json=_get_summeval_config()
    )
    db.session.add(scenario)
    db.session.flush()

    # Add users to scenario
    for user, role in [
        (evaluator, ScenarioRoles.EVALUATOR),
        (researcher, ScenarioRoles.RATER)
    ]:
        scenario_user = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            role=role
        )
        db.session.add(scenario_user)

    if admin:
        admin_scenario_user = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=admin.id,
            role=ScenarioRoles.EVALUATOR
        )
        db.session.add(admin_scenario_user)

    db.session.flush()

    # Add items to scenario
    scenario_items = []
    for item in items:
        scenario_item = ScenarioItems(
            scenario_id=scenario.id,
            item_id=item.item_id
        )
        db.session.add(scenario_item)
        scenario_items.append(scenario_item)

    db.session.flush()

    # Create distributions for rater
    rater_user = ScenarioUsers.query.filter_by(
        scenario_id=scenario.id,
        role=ScenarioRoles.RATER
    ).first()

    if rater_user:
        for scenario_item in scenario_items:
            dist = ScenarioItemDistribution(
                scenario_id=scenario.id,
                scenario_user_id=rater_user.id,
                scenario_item_id=scenario_item.id
            )
            db.session.add(dist)

    db.session.commit()

    print(f"\n  Created SummEval Demo with {len(items)} items")
    print(f"  Scenario ID: {scenario.id}")
    print("=" * 60)

    return scenario


def _get_summeval_config():
    """
    Get the SummEval-style multi-dimensional config.

    This config demonstrates per-dimension scales with varied Likert scales:
    - Binary (0-1): Faithfulness
    - 4-point (0-3): Focus
    - 5-point (1-5): Informativeness, Conciseness, Clarity (global default)
    - 7-point (1-7): Coverage, Overall Quality
    """
    return {
        "evaluation": "rating",
        "type": "multi-dimensional",
        "preset": "summeval-mixed-scales",
        "enable_llm_evaluation": True,
        "llm_evaluators": [
            "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
            "mistralai/Magistral-Small-2509"
        ],
        # Global/default scale (used when dimension has no custom scale)
        "min": 1,
        "max": 5,
        "step": 1,
        "showOverallScore": True,
        "allowFeedback": True,
        "instructions": {
            "de": "Bewerten Sie die Zusammenfassung anhand des Quelltextes. Beachten Sie: Jede Dimension hat ihre eigene Bewertungsskala!",
            "en": "Evaluate the summary based on the source text. Note: Each dimension has its own rating scale!"
        },
        "dimensions": [
            # === Binary Scale (0-1) ===
            {
                "id": "faithfulness",
                "name": {"de": "Faktentreue", "en": "Faithfulness"},
                "description": {
                    "de": "Ist die Zusammenfassung faktisch korrekt und enthält NUR Aussagen, die durch den Quelltext gestützt werden?",
                    "en": "Is the summary factually accurate and contains ONLY claims supported by the source text?"
                },
                "weight": 0.15,
                "scale": {
                    "min": 0,
                    "max": 1,
                    "step": 1,
                    "labels": {
                        "0": {"de": "Nein (enthält Fehler/Halluzinationen)", "en": "No (contains errors/hallucinations)"},
                        "1": {"de": "Ja (vollständig akkurat)", "en": "Yes (fully accurate)"}
                    }
                }
            },
            # === 4-Point Scale (0-3) ===
            {
                "id": "focus",
                "name": {"de": "Fokus", "en": "Focus"},
                "description": {
                    "de": "Bleibt die Zusammenfassung beim Thema? Werden Abschweifungen vermieden?",
                    "en": "Does the summary stay on topic? Are digressions avoided?"
                },
                "weight": 0.10,
                "scale": {
                    "min": 0,
                    "max": 3,
                    "step": 1,
                    "labels": {
                        "0": {"de": "Völlig unfokussiert", "en": "Completely unfocused"},
                        "1": {"de": "Teilweise unfokussiert", "en": "Partially unfocused"},
                        "2": {"de": "Größtenteils fokussiert", "en": "Mostly focused"},
                        "3": {"de": "Vollständig fokussiert", "en": "Fully focused"}
                    }
                }
            },
            # === 5-Point Scale (1-5) - uses global default ===
            {
                "id": "informativeness",
                "name": {"de": "Informationsgehalt", "en": "Informativeness"},
                "description": {
                    "de": "Werden die wichtigsten Fakten und Kernaussagen des Quelltextes erfasst?",
                    "en": "Does the summary capture the most important facts and key points from the source?"
                },
                "weight": 0.15
                # No custom scale - uses global 1-5
            },
            {
                "id": "conciseness",
                "name": {"de": "Prägnanz", "en": "Conciseness"},
                "description": {
                    "de": "Ist die Zusammenfassung angemessen kurz und vermeidet unnötige Details?",
                    "en": "Is the summary appropriately brief and avoids unnecessary details?"
                },
                "weight": 0.15
                # No custom scale - uses global 1-5
            },
            {
                "id": "clarity",
                "name": {"de": "Klarheit", "en": "Clarity"},
                "description": {
                    "de": "Ist die Zusammenfassung klar und verständlich formuliert?",
                    "en": "Is the summary clearly and understandably written?"
                },
                "weight": 0.15
                # No custom scale - uses global 1-5
            },
            # === 7-Point Scale (1-7) ===
            {
                "id": "coverage",
                "name": {"de": "Abdeckung", "en": "Coverage"},
                "description": {
                    "de": "Wie vollständig werden alle wesentlichen Aspekte des Quelltextes abgedeckt?",
                    "en": "How comprehensively does the summary cover all essential aspects of the source?"
                },
                "weight": 0.15,
                "scale": {
                    "min": 1,
                    "max": 7,
                    "step": 1,
                    "labels": {
                        "1": {"de": "Keine Abdeckung", "en": "No coverage"},
                        "2": {"de": "Sehr lückenhaft", "en": "Very incomplete"},
                        "3": {"de": "Lückenhaft", "en": "Incomplete"},
                        "4": {"de": "Teilweise abgedeckt", "en": "Partially covered"},
                        "5": {"de": "Größtenteils abgedeckt", "en": "Mostly covered"},
                        "6": {"de": "Fast vollständig", "en": "Nearly complete"},
                        "7": {"de": "Vollständig abgedeckt", "en": "Fully covered"}
                    }
                }
            },
            {
                "id": "overall_quality",
                "name": {"de": "Gesamtqualität", "en": "Overall Quality"},
                "description": {
                    "de": "Wie würden Sie die Gesamtqualität dieser Zusammenfassung bewerten?",
                    "en": "How would you rate the overall quality of this summary?"
                },
                "weight": 0.15,
                "scale": {
                    "min": 1,
                    "max": 7,
                    "step": 1,
                    "labels": {
                        "1": {"de": "Inakzeptabel", "en": "Unacceptable"},
                        "2": {"de": "Sehr schlecht", "en": "Very poor"},
                        "3": {"de": "Schlecht", "en": "Poor"},
                        "4": {"de": "Akzeptabel", "en": "Acceptable"},
                        "5": {"de": "Gut", "en": "Good"},
                        "6": {"de": "Sehr gut", "en": "Very good"},
                        "7": {"de": "Ausgezeichnet", "en": "Excellent"}
                    }
                }
            }
        ],
        # Global labels for dimensions without custom scale (1-5)
        "labels": {
            "1": {"de": "Sehr schlecht", "en": "Very poor"},
            "2": {"de": "Schlecht", "en": "Poor"},
            "3": {"de": "Akzeptabel", "en": "Acceptable"},
            "4": {"de": "Gut", "en": "Good"},
            "5": {"de": "Ausgezeichnet", "en": "Excellent"}
        }
    }
