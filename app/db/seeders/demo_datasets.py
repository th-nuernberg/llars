"""
Demo Datasets for LLARS Development Mode

Contains realistic sample data for all scenario types:
- Rating: Text quality evaluation samples
- Ranking: Features to sort into quality buckets
- Mail Rating: Counseling conversation threads
- Authenticity: Real vs Fake news detection (German)
- Comparison: Sentiment comparison pairs (German)
- Labeling: German news articles from 10kGNAD

Sources:
- 10kGNAD: https://github.com/tblock/10kGNAD (CC BY-NC-SA 4.0)
- German Sentiment: https://github.com/oliverguhr/german-sentiment
- Authenticity: Crafted examples based on common patterns
"""

from datetime import datetime, timedelta
import random


# =============================================================================
# RATING SCENARIO SAMPLES
# =============================================================================
# Counseling responses to be rated on quality (1-5 scale)

RATING_SAMPLES = [
    {
        "subject": "Beratungsanfrage: Stress im Studium",
        "messages": [
            {"sender": "Klient", "content": "Hallo, ich bin total gestresst wegen meines Studiums. Die Prüfungen stehen an und ich schaffe es nicht mehr, alles zu lernen. Ich schlafe schlecht und habe ständig Kopfschmerzen."},
            {"sender": "Berater", "content": "Vielen Dank für Ihre offene Nachricht. Prüfungsstress ist eine sehr häufige Erfahrung und Ihre Symptome zeigen, dass Ihr Körper Ihnen deutliche Signale sendet. Lassen Sie uns gemeinsam schauen, wie Sie die verbleibende Zeit effektiver nutzen können. Welche Prüfungen stehen als erstes an und wie haben Sie Ihr Lernen bisher organisiert?"},
        ],
        "features": {
            "Situation Summary": "Student/in im Prüfungsstress mit psychosomatischen Symptomen (Schlafprobleme, Kopfschmerzen). Überforderung durch Lernpensum erkennbar.",
            "Client Needs": "Stressmanagement-Strategien, Lernorganisation, evtl. Entspannungstechniken zur Symptomlinderung.",
            "Recommended Actions": "1) Prioritätenliste der Prüfungen erstellen, 2) Pomodoro-Technik vorstellen, 3) Entspannungsübungen empfehlen.",
            "Risk Assessment": "Mittleres Risiko bei anhaltender Belastung. Auf Burnout-Anzeichen achten."
        }
    },
    {
        "subject": "Hilfe bei Entscheidungsfindung",
        "messages": [
            {"sender": "Klient", "content": "Ich stehe vor einer schweren Entscheidung: Soll ich meinen sicheren Job aufgeben und mein eigenes Unternehmen gründen? Meine Familie ist dagegen, aber ich habe diesen Traum schon so lange."},
            {"sender": "Berater", "content": "Das ist eine bedeutsame Entscheidung, die Sie da beschäftigt. Solche beruflichen Weichenstellungen verdienen eine gründliche Reflexion. Darf ich fragen: Was genau zieht Sie zur Selbständigkeit? Und welche konkreten Bedenken hat Ihre Familie geäußert?"},
        ],
        "features": {
            "Situation Summary": "Klient erwägt Jobwechsel zur Selbständigkeit. Konflikt zwischen persönlichem Traum und familiären Erwartungen.",
            "Client Needs": "Strukturierte Entscheidungshilfe, Abwägung von Risiken und Chancen, Umgang mit familiärem Druck.",
            "Recommended Actions": "1) Pro-Contra-Liste erstellen, 2) Finanzielle Absicherung prüfen, 3) Kompromissmöglichkeiten explorieren.",
            "Risk Assessment": "Finanzielles Risiko bei unvorbereiteter Gründung. Familienkonflikt möglich."
        }
    },
    {
        "subject": "Beziehungsprobleme nach Umzug",
        "messages": [
            {"sender": "Klient", "content": "Mein Partner und ich sind vor drei Monaten zusammengezogen. Seitdem streiten wir fast täglich wegen Kleinigkeiten. Ich frage mich, ob wir einen Fehler gemacht haben."},
            {"sender": "Berater", "content": "Das Zusammenziehen ist ein großer Schritt, der viele Paare vor Herausforderungen stellt. Konflikte in dieser Übergangsphase sind nicht ungewöhnlich. Können Sie mir ein typisches Streitthema nennen? Das hilft mir zu verstehen, wo genau die Reibungspunkte liegen."},
        ],
        "features": {
            "Situation Summary": "Paar in Anpassungsphase nach Zusammenzug. Konflikte um Haushalt und unterschiedliche Bedürfnisse.",
            "Client Needs": "Kommunikationsstrategien, Aushandlung von Kompromissen, Normalitätseinordnung der Situation.",
            "Recommended Actions": "1) Haushaltsplan gemeinsam erstellen, 2) Bedürfnisse klar kommunizieren lernen, 3) Qualitätszeit definieren.",
            "Risk Assessment": "Geringes Risiko bei konstruktiver Bearbeitung. Typische Anpassungsphase."
        }
    },
    {
        "subject": "Erschöpfung durch Pflege der Eltern",
        "messages": [
            {"sender": "Klient", "content": "Ich pflege seit zwei Jahren meine demenzkranke Mutter neben meinem Vollzeitjob. Ich bin am Ende meiner Kräfte. Meine Geschwister helfen kaum. Ich weiß nicht mehr weiter."},
            {"sender": "Berater", "content": "Was Sie leisten, ist enorm und Ihre Erschöpfung ist absolut nachvollziehbar. Pflegende Angehörige geraten oft selbst an ihre Grenzen. Bevor wir nach Lösungen schauen: Wie sieht ein typischer Tag bei Ihnen aus? Und haben Sie bereits professionelle Unterstützungsangebote in Anspruch genommen?"},
        ],
        "features": {
            "Situation Summary": "Pflegende/r Angehörige/r mit Erschöpfungssyndrom. Doppelbelastung durch Job und Pflege.",
            "Client Needs": "Entlastung, Informationen über Pflegeangebote, Strategien für Familiengespräch, Selbstfürsorge.",
            "Recommended Actions": "1) Pflegeberatung aufsuchen, 2) Verhinderungspflege nutzen, 3) Familienkonferenz anregen.",
            "Risk Assessment": "Hohes Risiko für Burnout. Dringende Entlastung notwendig."
        }
    },
    {
        "subject": "Soziale Ängste im Beruf",
        "messages": [
            {"sender": "Klient", "content": "Ich habe Angst vor Präsentationen und Meetings. Mein Herz rast, ich bekomme feuchte Hände und manchmal verliere ich den Faden. Das behindert meine Karriere massiv."},
            {"sender": "Berater", "content": "Soziale Ängste im beruflichen Kontext sind verbreiteter als viele denken. Die körperlichen Symptome, die Sie beschreiben, sind typische Stressreaktionen. Wie lange begleiten Sie diese Ängste schon und gab es einen auslösenden Moment?"},
        ],
        "features": {
            "Situation Summary": "Klient mit sozialer Angst im beruflichen Setting. Körperliche Angstsymptome beeinträchtigen Karriereentwicklung.",
            "Client Needs": "Angstbewältigungsstrategien, Expositionsübungen, ggf. Therapieempfehlung.",
            "Recommended Actions": "1) Atemtechniken erlernen, 2) Schrittweise Exposition planen, 3) Kognitive Umstrukturierung.",
            "Risk Assessment": "Mittleres Risiko. Bei starker Beeinträchtigung Therapie empfehlen."
        }
    },
    {
        "subject": "Mobbing am Arbeitsplatz",
        "messages": [
            {"sender": "Klient", "content": "Ich werde von meinen Kollegen systematisch ausgegrenzt. Sie lästern hinter meinem Rücken und schließen mich von wichtigen Informationen aus. Mein Chef ignoriert das Problem."},
            {"sender": "Berater", "content": "Das klingt nach einer sehr belastenden Situation. Mobbing am Arbeitsplatz ist ein ernstes Problem, das nicht ignoriert werden sollte. Seit wann beobachten Sie dieses Verhalten und haben Sie konkrete Vorfälle dokumentiert?"},
        ],
        "features": {
            "Situation Summary": "Mobbing-Situation am Arbeitsplatz mit Ausgrenzung und mangelnder Unterstützung durch Vorgesetzte.",
            "Client Needs": "Dokumentationshilfe, rechtliche Information, emotionale Unterstützung, Handlungsoptionen.",
            "Recommended Actions": "1) Mobbingtagebuch führen, 2) Betriebsrat/HR einschalten, 3) Rechtliche Beratung empfehlen.",
            "Risk Assessment": "Hohes Risiko für psychische Gesundheit. Zeitnahe Intervention wichtig."
        }
    },
    {
        "subject": "Trauer nach Verlust des Haustieres",
        "messages": [
            {"sender": "Klient", "content": "Mein Hund ist letzte Woche gestorben. Er war 14 Jahre bei mir und ich vermisse ihn so sehr. Meine Freunde verstehen nicht, warum ich so traurig bin. 'Es war doch nur ein Hund', sagen sie."},
            {"sender": "Berater", "content": "Der Verlust eines Tieres, das Sie 14 Jahre begleitet hat, ist ein echter Verlust, der Trauer verdient. Die Bindung zu einem Haustier kann sehr tief sein. Dass andere das nicht verstehen, macht es noch schwerer. Möchten Sie mir von Ihrem Hund erzählen?"},
        ],
        "features": {
            "Situation Summary": "Trauer nach Verlust eines langjährigen Haustieres. Fehlende soziale Anerkennung der Trauer.",
            "Client Needs": "Validierung der Trauer, Raum zum Erzählen, Trauerbegleitung.",
            "Recommended Actions": "1) Trauer anerkennen und begleiten, 2) Abschiedsrituale anregen, 3) Eventuell Selbsthilfegruppe.",
            "Risk Assessment": "Geringes Risiko. Normale Trauerreaktion, die Begleitung verdient."
        }
    },
    {
        "subject": "Überforderung als neue Führungskraft",
        "messages": [
            {"sender": "Klient", "content": "Ich wurde vor drei Monaten zur Teamleiterin befördert. Seitdem habe ich das Gefühl, ständig zu versagen. Manche Teammitglieder akzeptieren mich nicht als Chefin und ich weiß nicht, wie ich durchgreifen soll."},
            {"sender": "Berater", "content": "Der Übergang in eine Führungsposition ist eine der herausforderndsten Phasen im Berufsleben. Dass Sie Unsicherheiten empfinden, ist völlig normal. Erzählen Sie mir mehr: Welche konkreten Situationen bereiten Ihnen am meisten Schwierigkeiten?"},
        ],
        "features": {
            "Situation Summary": "Neue Führungskraft mit Autoritätsproblemen und Selbstzweifeln. Schwierige Teamdynamik.",
            "Client Needs": "Führungscoaching, Autoritätsaufbau, Konfliktmanagement, Selbstvertrauen stärken.",
            "Recommended Actions": "1) Führungsgrundsätze definieren, 2) Einzelgespräche mit kritischen Mitarbeitern, 3) Coaching empfehlen.",
            "Risk Assessment": "Mittleres Risiko. Ohne Unterstützung könnte Situation eskalieren."
        }
    },
]


# =============================================================================
# RANKING SCENARIO SAMPLES - SummEval Dataset
# Source: https://huggingface.co/datasets/mteb/summeval
# Task: Rank multiple summaries of the same news article by quality
# Each summary has human ratings for relevance (1-5 scale)
# =============================================================================

RANKING_SAMPLES = [
    {
        "subject": "Summary Ranking: Sterling Court Case",
        "source_text": """(CNN)Donald Sterling's racist remarks cost him an NBA team last year. But now it's his former female companion who has lost big. A Los Angeles judge has ordered V. Stiviano to pay back more than $2.6 million in gifts after Sterling's wife sued her. In the lawsuit, Rochelle "Shelly" Sterling accused Stiviano of targeting extremely wealthy older men. She claimed Donald Sterling used the couple's money to buy Stiviano a Ferrari, two Bentleys and a Range Rover, and that he helped her get a $1.8 million duplex. Stiviano countered that there was nothing wrong with Donald Sterling giving her gifts and that she never took advantage of the former Los Angeles Clippers owner. Shelly Sterling was thrilled with the court decision Tuesday, her lawyer told CNN affiliate KABC. "This is a victory for the Sterling family in recovering the $2,630,000 that Donald lavished on a conniving mistress," attorney Pierce O'Donnell said.""",
        "summaries": [
            {"id": "A", "content": "Donald Sterling's racist remarks cost him an NBA team last year. But now it's his former female companion who has lost big. A Los Angeles judge has ordered V. Stiviano to pay back more than $2.6 million in gifts after Sterling's wife sued her.", "human_scores": {"relevance": 3.0, "avg": 3.0}},
            {"id": "B", "content": "A Los Angeles judge has ordered V. Stiviano to pay back more than $2.6 million in gifts after Sterling's wife sued her. In the lawsuit, Rochelle 'Shelly' Sterling accused Stiviano of targeting extremely wealthy older men. She claimed Donald Sterling used the couple's money to buy Stiviano a Ferrari, two Bentleys and a Range Rover.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "C", "content": "(CNN) Donald Sterling's racist remarks cost him an NBA team last year. But now it's his former female companion who has lost big. A Los Angeles judge has ordered V. Stiviano to pay back more than $2.6 million in gifts after Sterling's wife sued her. In the lawsuit, Rochelle 'Shelly' Sterling accused Stiviano of targeting extremely wealthy older men.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "D", "content": "Donald Sterling's racist remarks cost him an NBA team last year. In the lawsuit, Rochelle 'Shelly' Sterling used the couple's money to buy Stiviano a Ferrari, wealthy older men. Shelly Sterling's gifts from Donald Sterling was $2.6 million in gifts.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "E", "content": "Donald Sterling, NBA team last year. Sterling's wife sued for $2.6 million in gifts. Sterling says he is the former female companion who has lost the. Sterling has ordered V. Stiviano to pay back $2.6m in gifts after his wife sued.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Gray Whale Migration Record",
        "source_text": """(CNN)A North Pacific gray whale has earned a spot in the record books after completing the longest migration of a mammal ever recorded. The whale, named Varvara, swam nearly 14,000 miles (22,500 kilometers), according to a release from Oregon State University, whose scientists helped conduct the whale-tracking study. Varvara, which is Russian for "Barbara," left her primary feeding ground off Russia's Sakhalin Island to cross the Pacific Ocean and down the West Coast of the United States to Baja, Mexico. Varvara's journey surpassed a record listed on the Guinness Worlds Records website. It said the previous record was set by a humpback whale that swam a mere 10,190-mile round trip.""",
        "summaries": [
            {"id": "A", "content": "North Pacific gray whale has earned a spot in the record books. The whale, named Varvara, swam nearly 14,000 miles (22,500 kilometers). Varvara, which is Russian for 'Barbara,' left her primary feeding ground off Russia.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "B", "content": "The whale, named Varvara, swam nearly 14,000 miles (22,500 kilometers). It said the previous record was set by a humpback whale that swam a mere 10,190-mile round trip between the 'warm breeding waters of the Arctic and Antarctic regions'.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "C", "content": "A North Pacific gray whale swam nearly 14,000 miles from Oregon State University. Varvara's journey surpassed a record listed on the Guinness Worlds Records. The whale is Russian for 'Barbara,' which is set by a humpback whale.", "human_scores": {"relevance": 2.0, "avg": 2.0}},
            {"id": "D", "content": "A North Pacific gray whale has earned a spot in the record books after completing the longest migration of a mammal ever recorded. The whale, named Varvara, swam nearly 14,000 miles (22,500 kilometers), according to a release from Oregon State University. Varvara's journey surpassed a record listed on the Guinness Worlds Records website.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "E", "content": "(CNN) A North Pacific gray whale has earned a spot in the record books after completing the longest migration of a mammal ever recorded. The whale, named Varvara, swam nearly 14,000 miles (22,500 kilometers), according to a release from Oregon State University, whose scientists helped conduct the whale-tracking study.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: US-Russia Air Incident",
        "source_text": """(CNN)After a Russian fighter jet intercepted a U.S. reconnaissance plane in an "unsafe and unprofessional manner" earlier this week, the United States is complaining to Moscow about the incident. On Tuesday, a U.S. RC-135U was flying over the Baltic Sea when it was intercepted by a Russian SU-27 Flanker. The Pentagon said the incident occurred in international airspace north of Poland. The U.S. crew believed the Russian pilot's actions were "unsafe and unprofessional due to the aggressive maneuvers it performed in close proximity to their aircraft and its high rate of speed," Pentagon spokesman Mark Wright said.""",
        "summaries": [
            {"id": "A", "content": "Russian fighter jet intercepted a U.S. reconnaissance plane in an 'unsafe and unprofessional manner' earlier this week, the United States is complaining to Moscow about the incident. The Pentagon said the incident occurred in international airspace north of Poland. Russian state news agency Sputnik reported the U.S. plane was flying toward the Russian border with its transponder switched off.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "B", "content": "A U.S. RC-135U was flying over the Baltic Sea when it was intercepted by a Russian Flanker. The Pentagon said the incident occurred in international airspace north of Poland. The U.S. crew believed the Russian pilot's actions were 'unsafe and unprofessional,' Pentagon says.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "C", "content": "The United States is complaining to Moscow about the incident. U.S. RC-135U was flying over Baltic Sea when it was intercepted by Russian SU-27 Flanker. U.S. command says the transponder was off was false.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "D", "content": "The incident occurred in international airspace north of Poland. The U.S. crew believed the Russian pilot's actions were 'unsafe and unprofessional due to the aggressive maneuvers it performed in close proximity to their aircraft and its high rate of speed'.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "E", "content": "(CNN) After a Russian fighter jet intercepted a U.S. reconnaissance plane in an 'unsafe and unprofessional manner' earlier this week, the United States is complaining to Moscow about the incident. On Tuesday, a U.S. RC-135U was flying over the Baltic Sea when it was intercepted by a Russian SU-27 Flanker. The Pentagon said the incident occurred in international airspace north of Poland.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Tour Bus Fire",
        "source_text": """(CNN)Lady Antebellum singer Hillary Scott's tour bus caught fire on a Texas freeway Thursday morning, but everyone on board was safely evacuated. Michael Barnett captured dramatic video of the fire, on Interstate 30 just northeast of Dallas. Smoke and flames poured from the rear of the bus as traffic slowed to a crawl. Hillary Scott, co-lead singer for the band, posted a photo of the charred bus on Instagram and noted that she, her husband, the tour manager and the driver were all evacuated safely. "Thanking God for our safety," she wrote. The tour manager told CNN affiliate KTVT that the bus stopped after a rear tire blew out.""",
        "summaries": [
            {"id": "A", "content": "Lady Antebellum singer Hillary Scott's tour bus catches fire on a Texas freeway. Everyone on board was evacuated safely, Scott posts on Instagram.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "B", "content": "Hillary Scott's tour bus caught fire on a Texas freeway Thursday morning. Smoke and flames poured from the rear of the bus as traffic slowed to a crawl and Barnett slowly approached in his vehicle. Barnett said he didn't realize at the time that the bus belonged to the country band.", "human_scores": {"relevance": 3.0, "avg": 3.0}},
            {"id": "C", "content": "Lady Antebellum's tour bus caught fire on a Texas freeway Thursday morning. Michael Barnett captured dramatic video of fire on Interstate 30. He decided to stop filming because he didn't know what to expect. Hillary Scott, co-lead singer, posted a photo of the charred bus on Instagram.", "human_scores": {"relevance": 3.0, "avg": 3.0}},
            {"id": "D", "content": "Michael Barnett captured the fire on Interstate 30 just northeast of Dallas. The Antebellum singer Hillary Scott, co-lead singer for the band. The band's two other members, Charles Kelley and Dave Haywood were not traveling on the bus. The bus is set to perform at the 50th Academy of Country Music Awards.", "human_scores": {"relevance": 2.0, "avg": 2.0}},
            {"id": "E", "content": "Hillary Scott's tour bus caught fire on a Texas freeway Thursday morning. Michael Barnett captured dramatic video of the fire, on Interstate 30 just northeast of Dallas. Barnett decided to stop filming because he didn't know what to expect.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Siberian Wildfires Sunset",
        "source_text": """(CNN)A fiery sunset greeted people in Washington Sunday. The deep reddish color caught Seattle native Tim Durkan's eye. He photographed aerial shots of the sunset warming the city's skyline. The stunning sunsets were the result of raging wildfires in parts of Siberia. The fires were started in southeastern Siberia by farmers burning grass in their fields. But on April 14, the flames quickly grew out of control because of strong winds. The lingering smoke from the widespread fires were picked up by atmospheric winds, carrying the smoke from Siberia across the Pacific Ocean to the Pacific Northwest.""",
        "summaries": [
            {"id": "A", "content": "(CNN) A fiery sunset greeted people in Washington Sunday. The deep reddish color caught Seattle native Tim Durkan's eye. He photographed a handful of aerial shots of the sunset warming the city's skyline and shared them on CNN iReport.", "human_scores": {"relevance": 2.33, "avg": 2.33}},
            {"id": "B", "content": "A fiery sunset greeted people in Washington Sunday.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "C", "content": "Raging wildfires in parts of Siberia are causing stunning sunsets in the Pacific Northwest. Lingering smoke from the fires is being carried across the Pacific Ocean by atmospheric winds. Parts of Oregon, Washington and British Columbia are seeing the results of the smoke, wind and solar light combination.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "D", "content": "Stunning sunsets were the result of raging wildfires in parts of Siberia. Fires were started in southeastern Siberia by farmers burning grass in their fields. But on April 14, it is believed that the flames quickly grew out of control.", "human_scores": {"relevance": 3.33, "avg": 3.33}},
            {"id": "E", "content": "The deep reddish color caught Seattle native Tim Durkan's eye. The stunning sunsets were the result of raging wildfires in parts of Siberia. The fires were started in southeastern Siberia by farmers burning grass in their fields.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Mediterranean Migrant Crisis",
        "source_text": """Rome (CNN)Italy is coping with a rising wave of desperate migrants from Africa and Middle East hoping to make it to Europe. From Friday to Monday, a total of 8,480 migrants were rescued, according to the Italian coast guard, which said it received on Monday alone SOS calls from 20 boats in distress. On Tuesday, a spokesman with Save the Children told CNN the group fears 400 migrants could be missing, citing testimony from survivors who said their ship carrying 550 people capsized in the Mediterranean Sea about 80 miles off the Libyan coast.""",
        "summaries": [
            {"id": "A", "content": "Italy is coping with a rising wave of desperate migrants from Africa and Middle East. From Friday to Monday, a total of 8,480 migrants were rescued, according to the Italian coast guard, which said it received on Monday alone SOS calls from 20 boats in distress. The Italian coast guard fears 400 migrants could be missing.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "B", "content": "Italy is coping with a rising wave of desperate migrants from Africa and Middle East hoping to make it to Europe. From Friday to Monday, a total of 8,480 migrants were rescued, according to the Italian coast guard. On Tuesday, a spokesman with Save the Children told CNN the group fears 400 migrants could be missing.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "C", "content": "A total of 8,480 migrants were rescued. The group fears 400 migrants could be missing. The Italian coast guard has not yet found evidence. Italy registered more than 10,000 migrants in the first three months of 2015.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "D", "content": "A Save the Children spokesman says a ship carrying 550 people capsized off the Libyan coast. The Italian coast guard says it cannot confirm such an incident. There has been a recent upsurge in migrant boats crossing the Mediterranean. Italy registered more than 10,000 migrants arriving in first three months of 2015.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "E", "content": "A total of 8,480 migrants were rescued at sea during the first weekend of April. The Italian coast guard says 400 migrants are missing in the Mediterranean Sea. The 400 migrants have died while crossing the Libyan coast. The coast guard official says 20 boats are missing.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: SpaceX Rocket Landing",
        "source_text": """(CNN)SpaceX on Tuesday launched a two-stage Falcon 9 rocket carrying an uncrewed cargo spacecraft called Dragon on a flight from Cape Canaveral, Florida, to the International Space Station. That was the easy part. In a difficult bid to land a rocket stage on a floating barge for the first time, the private space exploration company was unsuccessful. SpaceX founder Elon Musk tweeted: "Ascent successful. Dragon enroute to Space Station. Rocket landed on droneship, but too hard for survival." He later clarified that the rocket landed, but tipped over.""",
        "summaries": [
            {"id": "A", "content": "(CNN) SpaceX on Tuesday launched a two-stage Falcon 9 rocket carrying an uncrewed cargo spacecraft called Dragon on a flight from Cape Canaveral, Florida, to the International Space Station. That was the easy part. Dragon enroute to Space Station.", "human_scores": {"relevance": 2.33, "avg": 2.33}},
            {"id": "B", "content": "Two-stage Falcon 9 rocket carrying an uncrewed cargo spacecraft called Dragon on a flight from Cape Canaveral, Florida, to the International Space Station. SpaceX has said it will keep trying and, after it masters landing at sea, hopes to someday land rockets on the ground.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "C", "content": "SpaceX launched a two-stage Falcon 9 rocket carrying an uncrewed cargo spacecraft called Dragon on a flight from Cape Canaveral, Florida, to the International Space Station. That was the easy part. In a difficult bid to land a rocket stage on a floating barge for the first time. Musk wants to cut costs.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "D", "content": "(CNN) SpaceX on Tuesday launched a two-stage Falcon 9 rocket carrying an uncrewed cargo spacecraft called Dragon on a flight from Cape Canaveral, Florida, to the International Space Station. That was the easy part. In a difficult bid to land a rocket stage on a floating barge for the first time, the private space exploration company was unsuccessful.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "E", "content": "SpaceX founder Elon Musk tweeted: 'Ascent successful. Rocket landed on droneship, but too hard for survival'. SpaceX has said it will keep trying and, after it hit at an angle and exploded.", "human_scores": {"relevance": 2.0, "avg": 2.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Cruise Ship Deaths",
        "source_text": """(CNN)Two passengers found dead on a cruise ship in Puerto Rico appear to have died in a murder-suicide, the cruise line said. Holland America Line said two guests were found dead inside their stateroom on the ms Ryndam at 11:30 a.m. Thursday. "The cabin was immediately secured, and the authorities were notified, including the FBI," Holland America said. The ship left Tampa, Florida, on March 29 on a 14-day Southern Caribbean cruise. It's currently in San Juan, Puerto Rico.""",
        "summaries": [
            {"id": "A", "content": "Holland left Tampa, Florida, on March 29. Two passengers found dead inside their stateroom on the ship. It's in San Juan, Puerto Rico.", "human_scores": {"relevance": 3.33, "avg": 3.33}},
            {"id": "B", "content": "Holland America Line says two guests were found dead inside their stateroom. The ship left Tampa, Florida, on March 29 on a 14-day Southern Caribbean cruise. Puerto Rico Port Authority spokesman says cleaning staff discovered the deceased passengers.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "C", "content": "(CNN) Two passengers found dead on a cruise ship in Puerto Rico appear to have died in a murder-suicide, the cruise line said. Holland America Line said two guests were found dead inside their stateroom on the ms Ryndam at 11:30 a.m. Thursday. 'The cabin was immediately secured, and the authorities were notified, including the FBI,' Holland America said.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "D", "content": "(CNN) Two passengers found dead on a cruise ship in Puerto Rico appear to have died in a murder-suicide, the cruise line said. Holland America Line said two guests were found dead inside their stateroom on the ms Ryndam at 11:30 a.m. Thursday. The ship left Tampa, Florida, on March 29 on a 14-day Southern Caribbean cruise.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "E", "content": "Two passengers found dead on a cruise ship in Puerto Rico appear to have died in a murder-suicide. The ship left Tampa, Florida, on a 14-day Southern Caribbean cruise.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: ISIS Releases Yazidis",
        "source_text": """(CNN)ISIS on Wednesday released more than 200 Yazidis, a minority group whose members were killed, captured and displaced when the Islamist terror organization overtook their towns in northern Iraq last summer, officials said. Most of those released were women and children; the rest were ill or elderly, said Rassol Omar, a commander in the Peshmerga force that defends northern Iraq's semi-autonomous Kurdish region. Omar didn't say what led to the release, other than asserting that Arab tribal leaders helped to coordinate it.""",
        "summaries": [
            {"id": "A", "content": "NEW: ISIS released more than 200 Yazidis, a minority group group says. The Islamist terror group has been killed in recent summer. The ISIS released scores of other Yazidis, mainly children and the elderly. The Peshmerga commander says the freed Yazidis are released.", "human_scores": {"relevance": 2.0, "avg": 2.0}},
            {"id": "B", "content": "ISIS on Wednesday released more than 200 Yazidis, a minority group whose members were killed, captured and displaced when the Islamist terror organization overtook their towns in northern Iraq last summer. Most of those released were women and children; the rest were ill or elderly, said Rassol Omar, a commander in the Peshmerga force.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "C", "content": "Yazidis are of Kurdish descent, and their religion is considered a pre-Islamic sect that draws from Christianity, Judaism and Zoroastrianism. ISIS' conquest of the town of Sinjar, in particular, provoked a major humanitarian crisis.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "D", "content": "Most of those released were women and children; the rest were ill or elderly, officials say. Freed Yazidis, a minority group, captured and displaced in northern Iraq last summer. Arab tribal leaders did not say what led to release.", "human_scores": {"relevance": 3.33, "avg": 3.33}},
            {"id": "E", "content": "(CNN) ISIS on Wednesday released more than 200 Yazidis, a minority group whose members were killed, captured and displaced when the Islamist terror organization overtook their towns in northern Iraq last summer, officials said. Most of those released were women and children; the rest were ill or elderly. Omar didn't say what led to the release, other than asserting that Arab tribal leaders helped to coordinate it.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Iran Border Guards Killed",
        "source_text": """(CNN)Eight Iranian border guards have been killed in clashes with militants near the border with Pakistan, Iranian state media reported. Three of the militants were killed by Iranian forces in the fighting Monday in the southeastern town of Negur. A militant group called Jaish al Adal claimed responsibility for the attack, according to Iranian state media. The Pakistani government condemned Monday's attack, calling it an "act of terrorism." "The concerned security agencies of Pakistan are actively investigating this incident," the government said.""",
        "summaries": [
            {"id": "A", "content": "Three of the militants were killed by Iranian forces near the border with Pakistan, Iranian state media reports. Jaish al Adal says it aims to thwart Iranian influence in Pakistan. The Sunni Muslim group has targeted Shiites.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "B", "content": "Eight Iranian border guards killed in clashes with militants near the border with Pakistan, Iranian state media reports. A militant group called Jaish al Adal claimed responsibility for the attack.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "C", "content": "(CNN) Eight Iranian border guards have been killed in clashes with militants near the border with Pakistan, Iranian state media reported. Three of the militants were killed by Iranian forces in the fighting Monday in the southeastern town of Negur. A militant group called Jaish al Adal claimed responsibility for the attack.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "D", "content": "The Iranian border guards were killed by militants in the eastern province of Baluchistan. Iran is a major ally of Pakistan in the region.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "E", "content": "Three of the militants were killed by Iranian forces in the fighting Monday in the southeastern town of Negur. Iranian officials have reportedly asked Pakistani authorities to catch the surviving assailants. Jaish al Adal has also claimed responsibility for the attack.", "human_scores": {"relevance": 3.0, "avg": 3.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Japan UFO Discussion",
        "source_text": """(CNN)The classic video game "Space Invaders" was developed in Japan back in the late 1970's -- and now their real-life counterparts are the topic of an earnest political discussion in Japan's corridors of power. Luckily, Japanese can sleep soundly in their beds tonight as the government's top military official earnestly revealed that the country's Air Self Defense Force (ASDF) had never encountered an extraterrestrial unidentified flying object. Responding to a query from flamboyant former wrestler-turned-lawmaker Antonio Inoki, Defense Minister Gen Nakatani told the Diet, Japan's parliament, that his jets had, to date, never come across any UFOs from outer space.""",
        "summaries": [
            {"id": "A", "content": "'Space Invaders' was developed in Japan back in the late 1970's -- and now their real-life counterparts are the topic of an earnest political discussion in Japan's corridors of power. Luckily, Japanese can sleep soundly in their beds tonight as the government's top military official earnestly. Inoki has appeared in the U.S.-based WWE.", "human_scores": {"relevance": 1.33, "avg": 1.33}},
            {"id": "B", "content": "Japan's military has never seen an alien, and apparently never will.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "C", "content": "Japan's top military official reveals that the country's Air Self Defense Force has never encountered an extraterrestrial unidentified flying object. Defense Minister Gen Nakatani told the Diet that his jets had, to date, never come across any UFOs from outer space.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "D", "content": "(CNN) The classic video game 'Space Invaders' was developed in Japan back in the late 1970's -- and now their real-life counterparts are the topic of an earnest political discussion in Japan's corridors of power. Luckily, Japanese can sleep soundly in their beds tonight as the government's top military official earnestly revealed that the country's Air Self Defense Force (ASDF) had never encountered an extraterrestrial unidentified flying object.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "E", "content": "'Space Invaders' was developed in Japan back in 1970. Japanese can sleep soundly in their beds tonight as government's top military official. He also fought Muhammad Ali in 1976. Inoki has appeared in the U.S.-based WWE.", "human_scores": {"relevance": 1.0, "avg": 1.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Boston Marathon Bombing Sentencing",
        "source_text": """(CNN)The parents of the youngest victim of the Boston Marathon bombings are making an emotional, passionate plea to take the death penalty off the table for the man convicted in the case. Last week, Dzhokhar Tsarnaev was found guilty on all 30 charges he faced related to the bombings at the 2013 race and the dramatic violence that dragged out for days afterward. The sentencing phase begins Tuesday, a day after this year's edition of the landmark race. It is expected to last four weeks. In a front-page opinion piece in The Boston Globe, Bill and Denise Richard wrote about the toll taken on their family after the death of their 8-year-old son, Martin.""",
        "summaries": [
            {"id": "A", "content": "Dzhokhar Tsarnaev was found guilty on all 30 charges he faced related to the bombings at the 2013 race and the dramatic violence that dragged out for days afterward. The sentencing phase begins Tuesday, a day after this year's edition of the landmark race.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "B", "content": "(CNN) The parents of the youngest victim of the Boston Marathon bombings are making an emotional, passionate plea to take the death penalty off the table for the man convicted in the case. Last week, Dzhokhar Tsarnaev was found guilty on all 30 charges he faced related to the bombings at the 2013 race and the dramatic violence that dragged out for days afterward.", "human_scores": {"relevance": 4.67, "avg": 4.67}},
            {"id": "C", "content": "(CNN) The parents of the youngest victim of the Boston Marathon bombings are making an emotional, passionate plea to take the death penalty off the table for the man convicted in the case. Last week, Dzhokhar Tsarnaev was found guilty on all 30 charges he faced related to the bombings. The sentencing phase begins Tuesday, a day after this year's edition of the landmark race.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "D", "content": "Dzhokhar Tsarnaev was found guilty on all 30 charges in the 2013 race. It is expected to last four weeks, a day after the race. The 13th Juror: Now it is real.", "human_scores": {"relevance": 1.67, "avg": 1.67}},
            {"id": "E", "content": "The sentencing phase begins Tuesday, a day after this year's edition of the landmark race. It is expected to last four weeks. Bill and Denise Richard wrote about the toll taken on their family after the death of their 8-year-old son, Martin.", "human_scores": {"relevance": 2.0, "avg": 2.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Roots TV Remake",
        "source_text": """(CNN)One of the biggest TV events of all time is being reimagined for new audiences. "Roots," the epic miniseries about an African-American slave and his descendants, had a staggering audience of over 100 million viewers back in 1977. Now A&E networks are remaking the miniseries, to air in 2016. LeVar Burton, who portrayed Kinte in the original, will co-executive produce the new miniseries. A press release describes the new version as "original" and "contemporary" and will draw more from Alex Haley's classic novel.""",
        "summaries": [
            {"id": "A", "content": "'Roots,' the epic miniseries about an African-American slave and his descendants, had a staggering audience of over 100 million viewers back in 1977. A&E networks are remaking the miniseries, to air in 2016. LeVar Burton, who portrayed Kinte in the original, will co-executive produce the new miniseries.", "human_scores": {"relevance": 5.0, "avg": 5.0}},
            {"id": "B", "content": "A&E Networks will simulcast the original 'Roots' in 2016. The original 'Roots' premiered in 1977 and ran for four seasons. The miniseries followed Kunta Kinte, a free black man in Virginia, as he was sold into slavery.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "C", "content": "A&E, Lifetime and History are remaking the miniseries, to air in 2016. 'Roots,' LeVar Burton, will co-executive produce the new miniseries. Alex Haley's 'contemporary' novel is 'original' novel.", "human_scores": {"relevance": 2.33, "avg": 2.33}},
            {"id": "D", "content": "'Roots,' the epic miniseries about an African-American slave and his descendants, had a staggering audience of over 100 million viewers back in 1977. Now A&E networks are remaking the miniseries, to air in 2016.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "E", "content": "A&E networks are remaking the series, to air in 2016. The three networks will broadcast a remake of the saga of Kunta Kinte. The 'Roots' is the epic episode of the African-American slave and his descendants.", "human_scores": {"relevance": 3.33, "avg": 3.33}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Brisbane Car Crash",
        "source_text": """Ten people, including four children, have been involved in a multi-vehicle crash in Brisbane's west. Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon. A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter. They've been taken to the Princess Alexandra Hospital in Brisbane. Shortly after, a 27-year-old woman with arm injuries and a six-year-old girl suffering from abdominal pain were also being flown out. Six others have been taken to Ipswich Hospital with minor injuries.""",
        "summaries": [
            {"id": "A", "content": "Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon. A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter. Six others - including an infant and two young girls - have been taken to Ipswich Hospital with minor injuries.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "B", "content": "Ten people, including four children, have been involved in a multi-vehicle crash in Brisbane's west. Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon. A 40-year-old man with chest and shoulder injuries and a five-year-old boy with chest pain were the first patients flown out by rescue helicopter.", "human_scores": {"relevance": 5.0, "avg": 5.0}},
            {"id": "C", "content": "Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale. A 40-year-old man with chest and shoulder injuries and a five-year-old girl suffering from abdominal pain were also being flown out. A man has also suffered hand lacerations and two females escaped injuries.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
            {"id": "D", "content": "One person was trapped inside their car. The helicopter landed at the scene and airlifted a number of patients to hospital.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "E", "content": "Ten people, including four children, have been involved in a multi-vehicle crash in Brisbane's west. Three vehicles collided on the Brisbane Valley Highway, 2km south of Fernvale, on Wednesday afternoon. A 27-year-old woman with arm injuries and a six-year-old girl suffering from abdominal pain were also being flown out by rescue helicopter.", "human_scores": {"relevance": 4.0, "avg": 4.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
    {
        "subject": "Summary Ranking: Serena Williams Fed Cup",
        "source_text": """Twice French Open champion Serena Williams said her struggle to beat Sara Errani in the Fed Cup on Sunday had been a real 'eye-opener' as the claycourt season gets into full swing. World No 1 Williams eventually prevailed 4-6 7-6(3) 6-3 against the dogged Italian to take her career record over her to 8-0 but the American was not impressed. The US were beaten 3-2 as Williams and Alison Riske were thrashed 6-0 6-3 in the doubles rubber by Errani and Flavia Pennetta, meaning they were relegated to World Group II.""",
        "summaries": [
            {"id": "A", "content": "Serena Williams won 6-3 6-3 against Sara Errani to become the first woman to win four majors. Williams was happy with her performance in the Fed Cup, but she was not impressed by the way Errani had played. Errani and Pennetta were beaten 6-0 6-3 by Williams and Alison Riske in the doubles rubber.", "human_scores": {"relevance": 2.67, "avg": 2.67}},
            {"id": "B", "content": "French Open champion Serena Williams says her struggle to beat Sara Errani. Serena Williams beat Italian Sara Errani in the Fed Cup play-off. Williams eventually prevailed 4-6 7-6(3) 6-3 against Italian. Williams and Alison Riske were relegated to World Group II. Williams won her 19th singles grand slam at the Australian Open.", "human_scores": {"relevance": 3.67, "avg": 3.67}},
            {"id": "C", "content": "Serena Williams beat Sara Errani 4-6 7-6(3) in the Fed Cup. The claycourt season gets into full swing. World No 1 Williams defeated Sara Errani in the semi-finals.", "human_scores": {"relevance": 3.0, "avg": 3.0}},
            {"id": "D", "content": "Twice French Open champion Serena Williams said her struggle to beat Sara Errani in the Fed Cup on Sunday had been a real 'eye-opener' as the claycourt season gets into full swing. World No 1 Williams eventually prevailed 4-6 7-6(3) 6-3 against the dogged Italian. The US were beaten 3-2 as Williams and Alison Riske were thrashed 6-0 6-3 in the doubles rubber by Errani and Flavia Pennetta, meaning they were relegated to World Group II.", "human_scores": {"relevance": 4.33, "avg": 4.33}},
            {"id": "E", "content": "Twice French Open champion Serena Williams said her struggle to beat Sara Errani in the Fed Cup on Sunday had been a real 'eye-opener' as the claycourt season gets into full swing. World No 1 Williams eventually prevailed 4-6 7-6(3) 6-3 against the dogged Italian to take her career record over her to 8-0 but the American was not impressed. The US were beaten 3-2 as Williams and Alison Riske were thrashed 6-0 6-3 in the doubles rubber by Errani and Flavia Pennetta, meaning they were relegated to World Group II.", "human_scores": {"relevance": 5.0, "avg": 5.0}},
        ],
        "task": "Rank these summaries by quality (coherence, relevance, fluency)"
    },
]


# =============================================================================
# MAIL RATING SCENARIO SAMPLES (Counseling Conversations)
# =============================================================================

MAIL_RATING_SAMPLES = [
    {
        "subject": "Beratungsverlauf: Berufliche Neuorientierung",
        "messages": [
            {"sender": "Klient", "content": "Hallo, ich bin 38 Jahre alt und arbeite seit 15 Jahren in der Buchhaltung. Ich fühle mich total ausgebrannt und frage mich, ob ich den falschen Beruf gewählt habe."},
            {"sender": "Berater", "content": "Vielen Dank für Ihre Offenheit. Nach 15 Jahren ist es absolut legitim, innezuhalten und zu reflektieren. Können Sie mir beschreiben, was genau Sie an Ihrer Arbeit erschöpft?"},
            {"sender": "Klient", "content": "Es ist so monoton. Jeden Tag die gleichen Zahlen, die gleichen Prozesse. Ich wollte eigentlich etwas Kreatives machen, aber meine Eltern haben mir davon abgeraten."},
            {"sender": "Berater", "content": "Das ist ein wichtiger Punkt - Sie haben Ihren ursprünglichen Wunsch zurückgestellt. Was wäre denn 'etwas Kreatives' für Sie gewesen? Und: Gibt es Möglichkeiten, kreative Elemente in Ihren Alltag zu integrieren?"},
            {"sender": "Klient", "content": "Ich habe früher viel gezeichnet und fotografiert. Das mache ich immer noch in meiner Freizeit. Aber davon leben? Das scheint mir unrealistisch."},
            {"sender": "Berater", "content": "Lassen Sie uns das genauer anschauen. 'Unrealistisch' ist oft ein Glaubenssatz aus der Vergangenheit. Es gibt heute viele Wege, kreative Fähigkeiten beruflich einzusetzen - von UX-Design bis Content Creation. Wären Sie offen für eine Kompetenzanalyse?"},
        ]
    },
    {
        "subject": "Beratungsverlauf: Familienkonflikt",
        "messages": [
            {"sender": "Klient", "content": "Ich brauche dringend Hilfe. Meine erwachsene Tochter (28) spricht seit drei Monaten nicht mehr mit mir. Ich weiß nicht einmal, was ich falsch gemacht habe."},
            {"sender": "Berater", "content": "Das klingt nach einer sehr schmerzhaften Situation. Der plötzliche Kontaktabbruch eines Kindes ist für Eltern besonders belastend. Gab es ein bestimmtes Ereignis vor drei Monaten?"},
            {"sender": "Klient", "content": "Nicht direkt. Bei ihrer Geburtstagsfeier war ich kritisch gegenüber ihrem neuen Freund. Ich fand ihn... naja, nicht gut genug für sie. Aber so etwas habe ich schon öfter gesagt."},
            {"sender": "Berater", "content": "Ich höre, dass Sie sich Sorgen um Ihre Tochter machen. Gleichzeitig klingt 'schon öfter' so, als gäbe es ein Muster. Wie reagiert Ihre Tochter normalerweise auf Ihre Kritik?"},
            {"sender": "Klient", "content": "Sie wird immer sehr still und zieht sich zurück. Aber sie ist doch mein Kind! Ich will nur ihr Bestes."},
            {"sender": "Berater", "content": "Ihre Fürsorge ist spürbar. Manchmal kann gut gemeinte Kritik aber als Ablehnung wahrgenommen werden - besonders wenn sie wiederholt kommt. Wie würde es sich für Sie anfühlen, den ersten Schritt zu machen und Ihre Tochter um ein Gespräch zu bitten - ohne ihre Partnerschaft zu thematisieren?"},
        ]
    },
    {
        "subject": "Beratungsverlauf: Gesundheitsangst",
        "messages": [
            {"sender": "Klient", "content": "Ich habe ständig Angst, schwer krank zu sein. Bei jedem kleinen Symptom denke ich sofort an Krebs oder andere schlimme Krankheiten. Mein Arzt sagt, ich sei gesund, aber ich kann ihm nicht glauben."},
            {"sender": "Berater", "content": "Krankheitsängste können sehr belastend sein und das tägliche Leben stark beeinträchtigen. Wie oft denken Sie am Tag an mögliche Krankheiten?"},
            {"sender": "Klient", "content": "Fast ständig. Ich google auch viel nach Symptomen, was es nur schlimmer macht. Ich weiß, dass ich damit aufhören sollte, aber ich kann nicht."},
            {"sender": "Berater", "content": "Das Googeln von Symptomen ist ein häufiges Verhalten bei Gesundheitsangst - es gibt kurzfristig Erleichterung, verstärkt aber langfristig die Angst. Haben Sie schon einmal von einer kognitiven Verhaltenstherapie gehört?"},
        ]
    },
    {
        "subject": "Beratungsverlauf: Einsamkeit im Alter",
        "messages": [
            {"sender": "Klient", "content": "Ich bin 72 und seit dem Tod meines Mannes vor zwei Jahren sehr einsam. Meine Kinder leben weit weg und haben ihre eigenen Familien. Manche Tage spreche ich mit niemandem."},
            {"sender": "Berater", "content": "Der Verlust Ihres Mannes und die Einsamkeit danach sind eine große Belastung. Zwei Jahre sind noch nicht lang für so einen Verlust. Wie verbringen Sie Ihre Tage derzeit?"},
            {"sender": "Klient", "content": "Ich lese viel, schaue fern, kümmere mich um meinen kleinen Garten. Aber das Reden mit Menschen fehlt mir. Früher hatten wir viele Freunde, aber die meisten sind auch schon gestorben oder können nicht mehr."},
            {"sender": "Berater", "content": "Der soziale Kreis wird im Alter leider oft kleiner. Aber es gibt Möglichkeiten, neue Kontakte zu knüpfen. Haben Sie schon einmal über eine Seniorengruppe oder einen Verein nachgedacht? In Ihrer Stadt gibt es bestimmt auch ehrenamtliche Besuchsdienste."},
        ]
    },
]


# =============================================================================
# AUTHENTICITY SAMPLES - Real vs Fake News Detection (German)
# =============================================================================

AUTHENTICITY_SAMPLES = [
    {
        "subject": "Wissenschaftliche Studie zu Klimawandel",
        "messages": [
            {"sender": "Nachricht", "content": """Eine neue Studie der Universität Hamburg, veröffentlicht im Journal "Nature Climate Change", zeigt einen Anstieg der globalen Durchschnittstemperatur um 0.8°C seit 1900. Die Forscher analysierten Daten von 4.500 Messstationen weltweit über einen Zeitraum von 120 Jahren. Professor Dr. Maria Schmidt, Leiterin der Studie, betont: "Die Ergebnisse sind konsistent mit früheren IPCC-Berichten." Die vollständige Studie ist unter DOI 10.1038/s41558-024-01234-5 einsehbar."""},
        ],
        "is_fake": False,
        "indicators": ["Quellenangabe", "DOI", "Peer-Review Journal", "Messbare Daten"]
    },
    {
        "subject": "SCHOCK: Geheime Regierungspläne enthüllt!!!",
        "messages": [
            {"sender": "Nachricht", "content": """EXKLUSIV!!! Insider berichten von GEHEIMEN Plänen der Regierung, die SIE nicht erfahren sollen! Ein anonymer Whistleblower hat uns brisante Dokumente zugespielt, die ALLES verändern werden! Teilen Sie diesen Artikel SOFORT, bevor er GELÖSCHT wird! Die Mainstream-Medien SCHWEIGEN zu diesem Skandal! WACHT ENDLICH AUF!!!"""},
        ],
        "is_fake": True,
        "indicators": ["Clickbait", "Anonyme Quellen", "Verschwörungsnarrative", "Emotionale Sprache"]
    },
    {
        "subject": "Bundestagsbeschluss zur Rentenreform",
        "messages": [
            {"sender": "Nachricht", "content": """Der Bundestag hat am gestrigen Donnerstag mit 412 zu 237 Stimmen das Rentenreformgesetz verabschiedet. Das Gesetz sieht eine schrittweise Anhebung des Renteneintrittsalters auf 67 Jahre bis 2031 vor. Bundesarbeitsminister Thomas Müller (SPD) erklärte in der Pressekonferenz: "Mit dieser Reform sichern wir die Renten für kommende Generationen." Die Opposition kritisierte den Beschluss als sozial unausgewogen."""},
        ],
        "is_fake": False,
        "indicators": ["Konkrete Zahlen", "Namentliche Quellen", "Sachlicher Ton", "Beide Seiten"]
    },
    {
        "subject": "Ärzte WARNEN: Dieses Lebensmittel TÖTET Sie langsam!",
        "messages": [
            {"sender": "Nachricht", "content": """Führende Mediziner schlagen Alarm! Ein alltägliches Lebensmittel, das in JEDEM Haushalt zu finden ist, verursacht KREBS und andere tödliche Krankheiten! Die Pharma-Industrie VERHEIMLICHT diese Information seit Jahren! Klicken Sie HIER um zu erfahren, welches Lebensmittel Sie SOFORT aus Ihrem Kühlschrank verbannen müssen!"""},
        ],
        "is_fake": True,
        "indicators": ["Gesundheitspanikmache", "Verschwörung", "Clickbait", "Keine konkreten Quellen"]
    },
    {
        "subject": "Wirtschaftswachstum im dritten Quartal",
        "messages": [
            {"sender": "Nachricht", "content": """Das Statistische Bundesamt meldet für das dritte Quartal 2024 ein Wirtschaftswachstum von 0.3 Prozent gegenüber dem Vorquartal. Im Jahresvergleich stieg das Bruttoinlandsprodukt um 1.2 Prozent. Haupttreiber waren der private Konsum (+0.5%) und die Bauinvestitionen (+1.1%). Die Exporte gingen hingegen um 0.8 Prozent zurück. Das ifo-Institut bestätigte diese Entwicklung in seiner aktuellen Konjunkturprognose."""},
        ],
        "is_fake": False,
        "indicators": ["Offizielle Statistik", "Prozentangaben", "Mehrere Quellen", "Differenzierte Analyse"]
    },
    {
        "subject": "Impfungen verursachen Autismus - Neue Beweise!",
        "messages": [
            {"sender": "Nachricht", "content": """Eine Facebook-Gruppe mit über 50.000 Mitgliedern hat "erschreckende Beweise" gesammelt, dass Impfungen direkt zu Autismus führen. "Mein Kind war völlig normal, bis es geimpft wurde", berichtet eine betroffene Mutter. Die Schulmedizin WEIGERT sich, diese Zusammenhänge anzuerkennen. Informieren Sie sich SELBST und schützen Sie Ihre Kinder vor der Impf-Mafia!"""},
        ],
        "is_fake": True,
        "indicators": ["Wissenschaftlich widerlegt", "Anekdotische Evidenz", "Verschwörung", "Anti-Wissenschaft"]
    },
    {
        "subject": "EZB erhöht Leitzins um 0.25 Prozentpunkte",
        "messages": [
            {"sender": "Nachricht", "content": """Die Europäische Zentralbank (EZB) hat heute den Leitzins um 0.25 Prozentpunkte auf 4.5 Prozent angehoben. EZB-Präsidentin Christine Lagarde begründete den Schritt mit der anhaltend hohen Inflation im Euroraum. "Wir werden die Geldpolitik so lange straffen, bis die Inflation nachhaltig auf unser Ziel von zwei Prozent sinkt", sagte Lagarde in Frankfurt. Ökonomen erwarten weitere Zinsschritte in den kommenden Monaten."""},
        ],
        "is_fake": False,
        "indicators": ["Offizielle Institution", "Zitate", "Sachlicher Ton", "Kontext"]
    },
    {
        "subject": "5G-Masten verbreiten Corona!!!",
        "messages": [
            {"sender": "Nachricht", "content": """Die WAHRHEIT wird UNTERDRÜCKT: 5G-Strahlung AKTIVIERT das Coronavirus! Bemerken Sie, dass die höchsten Corona-Zahlen GENAU dort sind, wo 5G-Masten stehen? Das ist KEIN Zufall! Die Mobilfunkindustrie und die Regierung arbeiten zusammen, um uns krank zu machen! Schützen Sie sich: Unterschreiben Sie unsere Petition gegen 5G und teilen Sie diesen Post mit ALLEN!"""},
        ],
        "is_fake": True,
        "indicators": ["Falsche Kausalität", "Verschwörungstheorie", "Panikmache", "Keine Evidenz"]
    },
]


# =============================================================================
# COMPARISON SAMPLES - Counseling Response Comparison
# For comparing LLM-generated counseling responses
# =============================================================================

COMPARISON_SAMPLES = [
    {
        "persona": {"name": "Studentin mit Prüfungsstress", "concern": "Überwältigt von Prüfungen und Deadlines"},
        "counselor_message": "Ich bin total gestresst wegen meiner Prüfungen. Ich schlafe kaum noch und habe Angst zu versagen.",
        "llm1_response": "Das klingt sehr belastend. Prüfungsstress kann sich wirklich auf alle Lebensbereiche auswirken. Wie lange haben Sie schon Schlafprobleme? Und gibt es bestimmte Prüfungen, die Ihnen besonders Sorgen machen?",
        "llm2_response": "Sie sollten früher mit dem Lernen anfangen und einen Zeitplan erstellen. Hier sind einige Tipps: 1) Lernen Sie jeden Tag zur gleichen Zeit. 2) Machen Sie Pausen. 3) Schlafen Sie genug."
    },
    {
        "persona": {"name": "Berufstätiger mit Burnout-Symptomen", "concern": "Erschöpfung und Motivationsverlust im Job"},
        "counselor_message": "Ich fühle mich total ausgebrannt. Jeden Morgen kostet es mich enorme Überwindung, zur Arbeit zu gehen.",
        "llm1_response": "Das klingt nach einer sehr belastenden Situation. Erschöpfung und der Verlust von Motivation sind wichtige Warnsignale. Seit wann erleben Sie diese Gefühle? Und gab es einen bestimmten Auslöser?",
        "llm2_response": "Burnout ist ein ernstes Problem. Sie sollten mit Ihrem Arzt sprechen und vielleicht eine Krankschreibung in Betracht ziehen. Hier sind die typischen Symptome von Burnout: emotionale Erschöpfung, Depersonalisierung, reduzierte Leistungsfähigkeit."
    },
    {
        "persona": {"name": "Elternteil mit Erziehungsfragen", "concern": "Konflikte mit jugendlichem Kind"},
        "counselor_message": "Mein Sohn (15) redet kaum noch mit mir. Wenn ich etwas sage, verdreht er nur die Augen.",
        "llm1_response": "Das ist eine Erfahrung, die viele Eltern von Jugendlichen teilen. Es kann sehr verletzend sein, wenn die Kommunikation so schwierig wird. Wie war Ihre Beziehung zu Ihrem Sohn, bevor diese Phase begann?",
        "llm2_response": "Das ist typisches Verhalten für Jugendliche in der Pubertät. Sie müssen klare Grenzen setzen und konsequent sein. Versuchen Sie, gemeinsame Aktivitäten zu planen und zeigen Sie Interesse an seinen Hobbys."
    },
    {
        "persona": {"name": "Trauernde Person", "concern": "Umgang mit dem Verlust eines Angehörigen"},
        "counselor_message": "Meine Mutter ist vor drei Monaten gestorben. Ich funktioniere im Alltag, aber innerlich fühle ich mich leer.",
        "llm1_response": "Mein aufrichtiges Beileid für Ihren Verlust. Drei Monate sind noch sehr frisch. Dass Sie im Alltag funktionieren und gleichzeitig diese innere Leere spüren, ist eine ganz normale Reaktion. Wie zeigt sich diese Leere für Sie?",
        "llm2_response": "Trauer verläuft in Phasen: Verleugnung, Wut, Verhandeln, Depression und Akzeptanz. Es klingt, als wären Sie in der Depressionsphase. Das ist normal und wird vorbeigehen. Haben Sie überlegt, einer Trauergruppe beizutreten?"
    },
    {
        "persona": {"name": "Person mit Beziehungsproblemen", "concern": "Kommunikationsschwierigkeiten in der Partnerschaft"},
        "counselor_message": "Mein Partner und ich streiten ständig über Kleinigkeiten. Ich habe das Gefühl, wir reden aneinander vorbei.",
        "llm1_response": "Häufige Konflikte über vermeintliche Kleinigkeiten deuten oft auf tieferliegende Bedürfnisse hin, die nicht erfüllt werden. Können Sie mir ein Beispiel für einen typischen Streit nennen?",
        "llm2_response": "Kommunikationsprobleme sind häufig in Beziehungen. Versuchen Sie die 'Ich-Botschaften'-Technik: Sagen Sie 'Ich fühle mich...', statt 'Du machst immer...'. Planen Sie auch regelmäßige Gesprächstermine ein, um wichtige Themen zu besprechen."
    },
    {
        "persona": {"name": "Arbeitnehmer mit Konflikten", "concern": "Schwieriger Umgang mit Vorgesetzten"},
        "counselor_message": "Mein Chef kritisiert mich ständig vor dem ganzen Team. Ich traue mich kaum noch, etwas zu sagen.",
        "llm1_response": "Das klingt nach einer sehr unangenehmen und belastenden Arbeitssituation. Öffentliche Kritik kann sehr demütigend sein. Wie lange geht das schon so? Und wie reagieren Ihre Kollegen darauf?",
        "llm2_response": "Das ist inakzeptables Verhalten Ihres Vorgesetzten. Sie sollten das dokumentieren und sich an die Personalabteilung wenden. Falls das nicht hilft, können Sie den Betriebsrat einschalten oder rechtliche Schritte prüfen."
    },
    {
        "persona": {"name": "Entscheidungssuchende", "concern": "Unsicherheit bei wichtiger Lebensentscheidung"},
        "counselor_message": "Ich weiß nicht, ob ich den Job in einer anderen Stadt annehmen soll. Meine Familie ist hier, aber beruflich wäre es eine große Chance.",
        "llm1_response": "Das ist eine Entscheidung mit vielen Dimensionen. Solche Abwägungen zwischen beruflichen Chancen und persönlichen Bindungen sind nie einfach. Was würde sich für Sie am schwersten anfühlen - die Chance nicht zu nutzen oder von Ihrer Familie getrennt zu sein?",
        "llm2_response": "Erstellen Sie eine Pro-Contra-Liste. Auf der einen Seite: Gehalt, Karrierechancen, neue Erfahrungen. Auf der anderen: Familie, bestehende Freundschaften, Sicherheit. Was überwiegt quantitativ? Alternativ könnten Sie auch über eine Fernbeziehung oder regelmäßige Besuche nachdenken."
    },
    {
        "persona": {"name": "Selbstzweifelnde Person", "concern": "Geringes Selbstwertgefühl und Unsicherheit"},
        "counselor_message": "Ich habe immer das Gefühl, nicht gut genug zu sein. Egal was ich erreiche, ich denke, es war nur Glück.",
        "llm1_response": "Was Sie beschreiben, klingt nach einem sehr belastenden inneren Erleben. Dieses Gefühl, Erfolge nicht wirklich sich selbst zuschreiben zu können, ist verbreiteter als viele denken. Können Sie mir erzählen, wann Sie zum ersten Mal so über sich gedacht haben?",
        "llm2_response": "Das klingt nach dem Hochstapler-Syndrom. Das ist ein bekanntes psychologisches Phänomen. Versuchen Sie, Ihre Erfolge in einem Tagebuch festzuhalten und objektiv zu betrachten. Auch positive Affirmationen können helfen, Ihr Selbstbild zu verbessern."
    },
]


# =============================================================================
# WIZARD COMPARISON SAMPLES (For Wizard-created Comparison Scenarios)
# =============================================================================

WIZARD_COMPARISON_SAMPLES = [
    {
        "subject": "Beratungsqualität: Empathie-Vergleich",
        "option_a": {
            "content": "Das klingt wirklich schwierig. Ich kann verstehen, dass Sie sich überfordert fühlen. Lassen Sie uns gemeinsam schauen, welche Schritte Sie als nächstes gehen können.",
            "quality": "empathisch",
            "model": "LLM-A"
        },
        "option_b": {
            "content": "Sie sollten folgende Schritte unternehmen: 1. Prioritäten setzen, 2. Zeitmanagement verbessern, 3. Delegieren lernen. Das sollte Ihr Problem lösen.",
            "quality": "sachlich",
            "model": "LLM-B"
        },
        "task": "Welche Beratungsantwort ist hilfreicher für den Klienten?",
    },
    {
        "subject": "Krisenintervention: Reaktions-Vergleich",
        "option_a": {
            "content": "Ich höre, dass Sie gerade eine sehr schwere Zeit durchmachen. Es ist mutig von Ihnen, sich Hilfe zu suchen. Können Sie mir mehr darüber erzählen, wie Sie sich gerade fühlen?",
            "quality": "unterstützend",
            "model": "LLM-A"
        },
        "option_b": {
            "content": "Wenn Sie sich in einer Krise befinden, wenden Sie sich bitte an die Telefonseelsorge (0800-1110111). Das ist ein kostenloses Angebot, das rund um die Uhr erreichbar ist.",
            "quality": "informativ",
            "model": "LLM-B"
        },
        "task": "Welche Antwort ist in einer Krisensituation angemessener?",
    },
    {
        "subject": "Karriereberatung: Strategien-Vergleich",
        "option_a": {
            "content": "Ein Jobwechsel ist ein großer Schritt. Was genau erhofft Sie sich von einer Veränderung? Manchmal hilft es, zuerst die eigenen Werte und Prioritäten zu klären.",
            "quality": "explorativ",
            "model": "LLM-A"
        },
        "option_b": {
            "content": "Hier sind die aktuellen Trends auf dem Arbeitsmarkt: KI-Berufe, Nachhaltigkeit, Healthcare. Ich empfehle, sich in einem dieser Bereiche weiterzubilden.",
            "quality": "direktiv",
            "model": "LLM-B"
        },
        "task": "Welcher Beratungsansatz ist für eine Karriereentscheidung sinnvoller?",
    },
    {
        "subject": "Konfliktlösung: Mediations-Vergleich",
        "option_a": {
            "content": "Konflikte am Arbeitsplatz sind belastend. Bevor wir Lösungen suchen: Können Sie mir beschreiben, wie die Situation aus Ihrer Sicht entstanden ist?",
            "quality": "prozessorientiert",
            "model": "LLM-A"
        },
        "option_b": {
            "content": "In Konfliktsituationen empfehle ich das Harvard-Konzept: Trennen Sie die Person vom Problem, konzentrieren Sie sich auf Interessen statt Positionen, entwickeln Sie Win-Win-Lösungen.",
            "quality": "methodisch",
            "model": "LLM-B"
        },
        "task": "Welche Herangehensweise an den Arbeitsplatzkonflikt ist hilfreicher?",
    },
    {
        "subject": "Trauerbegleitung: Ansatz-Vergleich",
        "option_a": {
            "content": "Der Verlust eines nahestehenden Menschen ist einer der schmerzhaftesten Erfahrungen. Es gibt keinen 'richtigen' Weg zu trauern. Wie geht es Ihnen heute?",
            "quality": "validierend",
            "model": "LLM-A"
        },
        "option_b": {
            "content": "Trauer verläuft typischerweise in fünf Phasen nach Kübler-Ross: Verleugnung, Wut, Verhandeln, Depression, Akzeptanz. In welcher Phase befinden Sie sich?",
            "quality": "analytisch",
            "model": "LLM-B"
        },
        "task": "Welcher Ansatz ist für eine trauernde Person hilfreicher?",
    },
]


# =============================================================================
# LABELING SAMPLES - German News Articles from 10kGNAD
# Source: https://github.com/tblock/10kGNAD (CC BY-NC-SA 4.0)
# =============================================================================

LABELING_SAMPLES = [
    {
        "subject": "Nachricht: Bayern-Niederlage in der Champions League",
        "text": "Bayern München hat in seinem 13. Pflichtspiel der Saison die erste Niederlage kassiert. Das Team von Trainer Pep Guardiola musste sich am Dienstagabend in seinem dritten Gruppenspiel beim FC Arsenal mit 0:2 (0:0) geschlagen geben. Den Londonern gelang damit nach zwei Niederlagen zum Auftakt das dringend notwendige Erfolgserlebnis.",
        "expected_label": "Sport",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Neue Intendantin für Theater Forum Schwechat",
        "text": "Manuela Seidl wird neue Intendantin des Theater Forum Schwechat. Der Stadtrat habe am Montagabend grünes Licht für die Neubesetzung der künstlerischen Leitung gegeben. Eine eigens einberufene Jury hat unter 20 Bewerbern eine klare Empfehlung zugunsten von Seidl abgegeben.",
        "expected_label": "Kultur",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Lenovo plant Retro-Thinkpad",
        "text": "In einem Blogeintrag fragt Lenovo-Designchef David Hill, wie es denn mit dem Interesse nach einer Art Retro-Thinkpad aussieht, also einem Laptop mit aktuellen Innereien aber klassischem Design. Die Reaktionen der Community können derzeit getrost unter dem Begriff begeistert zusammengefasst werden.",
        "expected_label": "Web/Technologie",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Uber beschwert sich bei EU-Kommission",
        "text": "Nach einer Beschwerde des US-Fahrdienstanbieters Uber nimmt die EU-Kommission das französische Taxirecht unter die Lupe. Die Wettbewerbshüter bereiteten sich derzeit darauf vor, ein Verfahren gegen Frankreich zu eröffnen. Uber sieht sich durch ein französisches Gesetz benachteiligt.",
        "expected_label": "Wirtschaft",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: FPÖ-Erfolg bei Landtagswahlen",
        "text": "Die SPÖ tut sich schwer, junge männliche Arbeitnehmer zu erreichen – und genau in diesen Bereich stoßen die Freiheitlichen vor. Frühere Wähler der Großparteien haben am Sonntag Wahlabstinenz geübt. Die Wählerstromanalysen zeigen beachtliche Abflüsse an die Nichtwähler.",
        "expected_label": "Inland",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Brexit-Referendum in Großbritannien",
        "text": "Zehn Wochen vor dem Referendum in Großbritannien haben EU-Anhänger und Brexit-Befürworter ihre offiziellen Kampagnen gestartet. Laut Umfragen steht der Ausgang auf Messers Schneide. Premier David Cameron hatte den Briten das Referendum versprochen.",
        "expected_label": "International",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Flüchtlingsunglück in der Ägäis",
        "text": "Bei einem Flüchtlingsunglück in der türkischen Ägäis sind vier Menschen ums Leben gekommen, unter ihnen drei Kinder. Drei Boote seien bei schlechtem Wetter auf dem Weg zur griechischen Insel Lesbos gekentert. Mehr als 100 Flüchtlinge wurden gerettet.",
        "expected_label": "Panorama",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Fischleiter-System gewinnt Staatspreis",
        "text": "Um Fischleitern energetisch nachhaltig zu konstruieren, hat der gelernte Maschinenschlosser Walter Albrecht eine Drehrohr-Doppel-Wasserkraftschnecke entwickelt. Seine Erfindung wurde mit dem Staatspreis für Umwelt- und Energietechnologie prämiert.",
        "expected_label": "Wissenschaft",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: ORF präsentiert neues Frühstücksfernsehen",
        "text": "Eva Pölzl und Lukas Schweighofer werden als Hauptmoderatoren des neuen Frühstücksfernsehens 'Guten Morgen Österreich' engagiert. Das neue Format wird ab 29. März alternierend von Pölzl und Schweighofer präsentiert, teilte der ORF mit.",
        "expected_label": "Medien/Etat",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Marcel Hirscher nur knapp geschlagen",
        "text": "Nur drei Hundertstelsekunden haben Marcel Hirscher zu einem perfekten Sonntag am Ganslernhang gefehlt. Der Salzburger musste sich auf pickelharter Eispiste nur Henrik Kristoffersen geschlagen geben. Der ÖSV blieb damit bei den 76. Hahnenkammrennen ohne Sieg.",
        "expected_label": "Sport",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Juli Zeh veröffentlicht neuen Roman",
        "text": "Mit ihrem neuen Roman 'Unterleuten' schafft die deutsche Schriftstellerin ein Bild gestriger und heutiger Zustände. Ein solcher Ort in Brandenburg, 100 Kilometer von Berlin entfernt, verleiht diesem groß angelegten Zeitroman Mikrokosmos sowie Titel.",
        "expected_label": "Kultur",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: IT-Netzwerk des Bundestags kompromittiert",
        "text": "Die Erneuerung des IT-Netzwerks des Deutschen Bundestags nach dem schweren Hackerangriff wird mindestens ein Jahr dauern. Unter anderem müsse die gesamte Software des Bundestags ausgetauscht werden. Diese Aufgabe soll T-Systems übernehmen.",
        "expected_label": "Web/Technologie",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: TTIP-Verhandlungen gehen weiter",
        "text": "Die Verhandlungen zu dem umstrittenen Abkommen werden fortgesetzt. In Wien stellte sich die EU-Handelskommissarin den Kritikern. Vor allem in Österreich und Deutschland gebe es die hitzige Debatte zu TTIP wie in keinem EU-Land sonst.",
        "expected_label": "Wirtschaft",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Neuwahlen in Spanien angesetzt",
        "text": "Erstmals seit Spaniens Rückkehr zur Demokratie in den 1970er Jahren stehen in dem Land vorgezogene Neuwahlen an. Nach dem endgültigen Scheitern einer Regierungsbildung setzte König Felipe VI. den erneuten Urnengang für den 26. Juni an.",
        "expected_label": "International",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Costa Concordia Kapitän legt Berufung ein",
        "text": "Drei Tage nach der Staatsanwaltschaft haben jetzt auch die Anwälte des ehemaligen Kapitäns des havarierten Kreuzfahrtschiffs Costa Concordia, Francesco Schettino, Berufung gegen die Verurteilung eingereicht. Schettino war zu 16 Jahren verurteilt worden.",
        "expected_label": "Panorama",
        "source": "10kGNAD"
    },
    {
        "subject": "Nachricht: Bronzezeitliches Grab bei Stuttgart 21 entdeckt",
        "text": "Die im Juli in einer Baugrube für das Bahnprojekt Stuttgart 21 entdeckten Gebeine konnten mittlerweile zugeordnet werden: Sie stammen von einer Frau aus der Bronzezeit. Sie sei etwa 17 bis 19 Jahre alt und knapp über 1,60 Meter groß gewesen.",
        "expected_label": "Wissenschaft",
        "source": "10kGNAD"
    },
]


def get_demo_data_for_scenario_type(scenario_type: str, count: int = 20) -> list:
    """
    Get demo data for a specific scenario type.

    Args:
        scenario_type: One of 'rating', 'ranking', 'mail_rating', 'authenticity', 'comparison', 'labeling'
        count: Number of samples to return (will cycle if more than available)

    Returns:
        List of sample data dictionaries
    """
    data_map = {
        'rating': RATING_SAMPLES,
        'ranking': RANKING_SAMPLES,
        'mail_rating': MAIL_RATING_SAMPLES,
        'authenticity': AUTHENTICITY_SAMPLES,
        'comparison': COMPARISON_SAMPLES,
        'wizard_comparison': WIZARD_COMPARISON_SAMPLES,
        'labeling': LABELING_SAMPLES,
    }

    samples = data_map.get(scenario_type, [])
    if not samples:
        return []

    # If we need more samples than available, cycle through them
    result = []
    for i in range(count):
        sample = samples[i % len(samples)].copy()
        # Add unique identifier to cycled samples
        if i >= len(samples):
            sample['_cycle_index'] = i // len(samples)
        result.append(sample)

    return result
