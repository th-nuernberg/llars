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
# RANKING SCENARIO SAMPLES
# =============================================================================
# Features to be ranked/sorted into quality buckets

RANKING_SAMPLES = [
    {
        "subject": "Analyse: Stressbewältigung",
        "feature_text": "Der Klient zeigt deutliche Anzeichen von chronischem Stress mit Schlafstörungen und Konzentrationsproblemen. Die Arbeitsbelastung übersteigt die verfügbaren Ressourcen erheblich. Empfehlung: Priorisierung der Aufgaben und Einführung von Pausen.",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Beziehungskonflikt",
        "feature_text": "Kommunikationsprobleme zwischen den Partnern. Beide Seiten fühlen sich unverstanden. Fehlende gemeinsame Zeit verschärft die Situation. Klärungsgespräch unter professioneller Anleitung empfohlen.",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Karriereberatung",
        "feature_text": "Der Klient ist unzufrieden. Es sollte etwas geändert werden. Vielleicht ein neuer Job?",
        "expected_bucket": "Schlecht"
    },
    {
        "subject": "Analyse: Angststörung",
        "feature_text": "Typische Symptome einer generalisierten Angststörung erkennbar. Körperliche Manifestationen (Herzrasen, Schwitzen) treten situationsübergreifend auf. Therapeutische Intervention dringend angeraten.",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Eltern-Kind-Konflikt",
        "feature_text": "Generationenkonflikt, wie er häufig vorkommt. Die Eltern verstehen die Jugend nicht, die Jugend die Eltern nicht. Normal.",
        "expected_bucket": "Mittel"
    },
    {
        "subject": "Analyse: Trauerbegleitung",
        "feature_text": "Der Klient befindet sich in der Phase der Verhandlung nach dem Kübler-Ross-Modell. Die Trauer verläuft normal, bedarf aber kontinuierlicher Begleitung. Keine pathologischen Anzeichen erkennbar.",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Burnout-Prävention",
        "feature_text": "Erste Burnout-Warnzeichen. Erschöpfung, Zynismus, verminderte Leistungsfähigkeit. 12-Punkte-Plan zur Intervention: 1) Arbeitszeit reduzieren...",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Suchtproblematik",
        "feature_text": "Problem erkannt. Trinkt zu viel. Sollte aufhören.",
        "expected_bucket": "Schlecht"
    },
    {
        "subject": "Analyse: Mobbing",
        "feature_text": "Systematisches Mobbing am Arbeitsplatz identifiziert. Täter-Opfer-Dynamik klar erkennbar. Dokumentation der Vorfälle empfohlen. Rechtliche Schritte sollten erwogen werden. Psychische Belastung hoch.",
        "expected_bucket": "Gut"
    },
    {
        "subject": "Analyse: Identitätskrise",
        "feature_text": "Klient in Orientierungsphase. Typisch für dieses Alter. Wird sich schon finden.",
        "expected_bucket": "Mittel"
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
