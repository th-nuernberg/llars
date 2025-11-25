"""
OnCoCo Label Definitions and Hierarchy

Based on the OnCoCo 1.0 paper category system:
- 40 Counselor (CO) categories
- 28 Client (CL) categories

Hierarchical structure with up to 5 levels.
"""

# Full label definitions with display names and descriptions
ONCOCO_LABELS = {
    # ============================================================================
    # COUNSELOR LABELS (CO)
    # ============================================================================

    # Formalities at Beginning
    "CO-FA-*-*-*-*": {
        "display_name": "Formalities at Beginning",
        "display_name_de": "Formalitäten zu Beginn",
        "level2": "CO-FA",
        "category": "formalities",
        "role": "counselor"
    },

    # Moderation
    "CO-Mod-*-*-*-*": {
        "display_name": "Moderation",
        "display_name_de": "Moderation",
        "level2": "CO-Mod",
        "category": "moderation",
        "role": "counselor"
    },

    # Impact Factors - Analysis and Clarification - Reflection (Fact)
    "CO-IF-AC-RF-RPD-*": {
        "display_name": "Request Personal Data",
        "display_name_de": "Frage nach persönlichen Daten",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RPA-*": {
        "display_name": "Request Previous Attempts",
        "display_name_de": "Frage nach bisherigen Lösungsversuchen",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-SRx-*": {
        "display_name": "Simple Reflection",
        "display_name_de": "Einfache Spiegelung",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RLS-SR": {
        "display_name": "Request Living Situation - Social",
        "display_name_de": "Frage Lebenssituation - Soziales",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RLS-PS": {
        "display_name": "Request Living Situation - Professional",
        "display_name_de": "Frage Lebenssituation - Beruf",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RLS-ES": {
        "display_name": "Request Living Situation - Economic",
        "display_name_de": "Frage Lebenssituation - Finanzen",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RLS-H": {
        "display_name": "Request Living Situation - Health",
        "display_name_de": "Frage Lebenssituation - Gesundheit",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RLS-L": {
        "display_name": "Request Living Situation - Leisure",
        "display_name_de": "Frage Lebenssituation - Freizeit",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RC-*": {
        "display_name": "Request for Concerns",
        "display_name_de": "Frage nach Anliegen",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RTP-*": {
        "display_name": "Targeted, Precise Request",
        "display_name_de": "Gezielte, präzise Nachfrage",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RF-RCD-*": {
        "display_name": "Request Change/Development",
        "display_name_de": "Frage nach Veränderung",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Impact Factors - Analysis - Reflection (Emotion)
    "CO-IF-AC-RE-RCR-*": {
        "display_name": "Complex Reflection",
        "display_name_de": "Komplexe Spiegelung",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AC-RE-RES-*": {
        "display_name": "Request Emotional State",
        "display_name_de": "Frage nach Gefühlszustand",
        "level2": "CO-IF-AC",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Impact Factors - Analysis - Objectives
    "CO-IF-AO-*-ROW-*": {
        "display_name": "Request Objectives/Wishes",
        "display_name_de": "Frage nach Zielen/Wünschen",
        "level2": "CO-IF-AO",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-AO-*-ICO-*": {
        "display_name": "Definition Counseling Objectives",
        "display_name_de": "Definition der Beratungsziele",
        "level2": "CO-IF-AO",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Impact Factors - Creating Motivation
    "CO-IF-Mot-*-RFC-*": {
        "display_name": "Eliciting Change-Talk (MI)",
        "display_name_de": "Change-Talk evozieren (MI)",
        "level2": "CO-IF-Mot",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-Mot-*-IAC-*": {
        "display_name": "Articulation Ability to Change",
        "display_name_de": "Wahrgenommene Veränderungsfähigkeit",
        "level2": "CO-IF-Mot",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-Mot-*-ITA-*": {
        "display_name": "Thanks and Appreciation",
        "display_name_de": "Dank und Wertschätzung",
        "level2": "CO-IF-Mot",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-Mot-*-IEM-*": {
        "display_name": "Encouragement, Motivation",
        "display_name_de": "Ermutigung, Motivation",
        "level2": "CO-IF-Mot",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-Mot-*-RS-*": {
        "display_name": "Question Support Resources",
        "display_name_de": "Frage nach Unterstützungsressourcen",
        "level2": "CO-IF-Mot",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Impact Factors - Resource Activation
    "CO-IF-RA-*-RP-*": {
        "display_name": "Request Problem Statement",
        "display_name_de": "Anfrage zur Problemdarstellung",
        "level2": "CO-IF-RA",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-RA-*-RAP-*": {
        "display_name": "Suggestion Professional Level",
        "display_name_de": "Vorschlag professionelle Ebene",
        "level2": "CO-IF-RA",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-RA-*-N-RAFa": {
        "display_name": "Suggestion Family Level",
        "display_name_de": "Vorschlag Familienebene",
        "level2": "CO-IF-RA",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-RA-*-N-RAFr": {
        "display_name": "Suggestion Friendship Level",
        "display_name_de": "Vorschlag Freundesebene",
        "level2": "CO-IF-RA",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Impact Factors - Help, Problem Solving
    "CO-IF-HP-*-ITFE-*": {
        "display_name": "Technical/Factual Explanations",
        "display_name_de": "Fachliche Erklärungen",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-IPFR-*": {
        "display_name": "Professional Recommendation",
        "display_name_de": "Professionelle Empfehlung",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-IF-*": {
        "display_name": "Future Forecast",
        "display_name_de": "Zukunftsprognose",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-IW-*": {
        "display_name": "Warning",
        "display_name_de": "Warnung",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-ICO-*": {
        "display_name": "Calming",
        "display_name_de": "Beruhigung",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-PP-IA": {
        "display_name": "Advice",
        "display_name_de": "Ratschlag",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-IEA": {
        "display_name": "Evaluation, Interpretation",
        "display_name_de": "Bewertung, Interpretation",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },
    "CO-IF-HP-*-PP-IW": {
        "display_name": "Wish",
        "display_name_de": "Wunsch",
        "level2": "CO-IF-HP",
        "category": "impact_factors",
        "role": "counselor"
    },

    # Formalities Conclusion
    "CO-FC-*-*-F-*": {
        "display_name": "Farewell",
        "display_name_de": "Verabschiedung",
        "level2": "CO-FC",
        "category": "formalities",
        "role": "counselor"
    },
    "CO-FC-*-*-OPR-*": {
        "display_name": "Offer Professional Resources",
        "display_name_de": "Angebot professioneller Ressourcen",
        "level2": "CO-FC",
        "category": "formalities",
        "role": "counselor"
    },

    # Other
    "CO-O-*-*-O-*": {
        "display_name": "Other Statements",
        "display_name_de": "Andere Aussagen",
        "level2": "CO-O",
        "category": "other",
        "role": "counselor"
    },
    "CO-O-*-*-UCO-*": {
        "display_name": "Inappropriate Remark",
        "display_name_de": "Unangemessene Bemerkung",
        "level2": "CO-O",
        "category": "other",
        "role": "counselor"
    },
    "CO-O-*-*-PI-*": {
        "display_name": "Personal Information",
        "display_name_de": "Persönliche Information",
        "level2": "CO-O",
        "category": "other",
        "role": "counselor"
    },
    "CO-O-*-*-ST-*": {
        "display_name": "Small Talk",
        "display_name_de": "Small Talk",
        "level2": "CO-O",
        "category": "other",
        "role": "counselor"
    },

    # ============================================================================
    # CLIENT LABELS (CL)
    # ============================================================================

    # Formalities Beginning
    "CL-FB-*-*-*-*": {
        "display_name": "Formalities at Beginning",
        "display_name_de": "Formalitäten zu Beginn",
        "level2": "CL-FB",
        "category": "formalities",
        "role": "client"
    },

    # Empathy
    "CL-E-*-*-PT-*": {
        "display_name": "Empathy Third Parties",
        "display_name_de": "Empathie für Dritte",
        "level2": "CL-E",
        "category": "empathy",
        "role": "client"
    },
    "CL-E-*-*-ECC-*": {
        "display_name": "Compassion for Others",
        "display_name_de": "Mitgefühl für andere",
        "level2": "CL-E",
        "category": "empathy",
        "role": "client"
    },
    "CL-E-*-*-ECP-*": {
        "display_name": "Concern for Another Person",
        "display_name_de": "Sorge um andere Person",
        "level2": "CL-E",
        "category": "empathy",
        "role": "client"
    },

    # Impact Factors - Analysis Clarification Problems
    "CL-IF-ACP-*-PS-*": {
        "display_name": "Problem Statement",
        "display_name_de": "Problemdarstellung",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-PD-*": {
        "display_name": "Problem Definition",
        "display_name_de": "Problemdefinition",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-DPD-*": {
        "display_name": "Disclosure Personal Data",
        "display_name_de": "Offenlegung persönlicher Daten",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-FPA-*": {
        "display_name": "Feedback Previous Attempts",
        "display_name_de": "Feedback zu bisherigen Versuchen",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-OE-*": {
        "display_name": "Own Emotional Expression",
        "display_name_de": "Eigener Gefühlsausdruck",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-Cons-*": {
        "display_name": "Consent",
        "display_name_de": "Zustimmung",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-Rej-*": {
        "display_name": "Rejection",
        "display_name_de": "Ablehnung",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-ACP-*-Req-*": {
        "display_name": "General Request",
        "display_name_de": "Allgemeine Anfrage",
        "level2": "CL-IF-ACP",
        "category": "impact_factors",
        "role": "client"
    },

    # Impact Factors - Analysis Objectives
    "CL-IF-AO-*-Obj-*": {
        "display_name": "Objective Assignment",
        "display_name_de": "Ziel des Auftrags",
        "level2": "CL-IF-AO",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-AO-*-Ext-*": {
        "display_name": "Extension Assignment",
        "display_name_de": "Erweiterung des Auftrags",
        "level2": "CL-IF-AO",
        "category": "impact_factors",
        "role": "client"
    },

    # Impact Factors - Creating Motivation
    "CL-IF-Mot-*-FC-*": {
        "display_name": "Eliciting Change-Talk",
        "display_name_de": "Change-Talk",
        "level2": "CL-IF-Mot",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-Mot-*-RC-*": {
        "display_name": "Articulation Reasons for Change",
        "display_name_de": "Gründe für Veränderung",
        "level2": "CL-IF-Mot",
        "category": "impact_factors",
        "role": "client"
    },

    # Impact Factors - Resource Activation
    "CL-IF-RA-*-RF-*": {
        "display_name": "Considering Friends/Family",
        "display_name_de": "Ressourcen Freunde/Familie",
        "level2": "CL-IF-RA",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-RA-*-RP-*": {
        "display_name": "Considering Professional Level",
        "display_name_de": "Ressourcen professionelle Ebene",
        "level2": "CL-IF-RA",
        "category": "impact_factors",
        "role": "client"
    },

    # Impact Factors - Help Coping Problems
    "CL-IF-HP-*-PosF-*": {
        "display_name": "General Positive Feedback",
        "display_name_de": "Allgemeines positives Feedback",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-HP-*-PosFR-*": {
        "display_name": "Positive Feedback Recommendations",
        "display_name_de": "Positives Feedback zu Empfehlungen",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-HP-*-NegFR-*": {
        "display_name": "Negative Feedback Recommendations",
        "display_name_de": "Negatives Feedback zu Empfehlungen",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-HP-*-RepRA-*": {
        "display_name": "Report Implementation",
        "display_name_de": "Bericht zur Umsetzung",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-HP-*-Succ-*": {
        "display_name": "Final Success",
        "display_name_de": "Finaler Erfolg",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },
    "CL-IF-HP-*-Fail-*": {
        "display_name": "Final Failure",
        "display_name_de": "Finales Scheitern",
        "level2": "CL-IF-HP",
        "category": "impact_factors",
        "role": "client"
    },

    # Formalities Conclusion
    "CL-FC-*-*-F-*": {
        "display_name": "Farewell",
        "display_name_de": "Verabschiedung",
        "level2": "CL-FC",
        "category": "formalities",
        "role": "client"
    },
    "CL-FC-*-*-UPR-*": {
        "display_name": "Further Use Professional Resources",
        "display_name_de": "Weitere Nutzung prof. Ressourcen",
        "level2": "CL-FC",
        "category": "formalities",
        "role": "client"
    },

    # Other
    "CL-O-*-*-O-*": {
        "display_name": "Other Statements",
        "display_name_de": "Andere Aussagen",
        "level2": "CL-O",
        "category": "other",
        "role": "client"
    },
    "CL-O-*-*-UCO-*": {
        "display_name": "Inappropriate Remark",
        "display_name_de": "Unangemessene Bemerkung",
        "level2": "CL-O",
        "category": "other",
        "role": "client"
    },
}

# Level 2 hierarchy for aggregated views
LABEL_HIERARCHY = {
    # Counselor
    "CO-FA": {"display_name": "Formalities Beginning", "display_name_de": "Formalitäten Beginn", "role": "counselor"},
    "CO-Mod": {"display_name": "Moderation", "display_name_de": "Moderation", "role": "counselor"},
    "CO-IF-AC": {"display_name": "Analysis & Clarification", "display_name_de": "Analyse & Klärung", "role": "counselor"},
    "CO-IF-AO": {"display_name": "Analysis Objectives", "display_name_de": "Analyse Ziele", "role": "counselor"},
    "CO-IF-Mot": {"display_name": "Creating Motivation", "display_name_de": "Motivation schaffen", "role": "counselor"},
    "CO-IF-RA": {"display_name": "Resource Activation", "display_name_de": "Ressourcenaktivierung", "role": "counselor"},
    "CO-IF-HP": {"display_name": "Help, Problem Solving", "display_name_de": "Hilfe, Problemlösung", "role": "counselor"},
    "CO-FC": {"display_name": "Formalities Conclusion", "display_name_de": "Formalitäten Abschluss", "role": "counselor"},
    "CO-O": {"display_name": "Other", "display_name_de": "Sonstiges", "role": "counselor"},

    # Client
    "CL-FB": {"display_name": "Formalities Beginning", "display_name_de": "Formalitäten Beginn", "role": "client"},
    "CL-E": {"display_name": "Empathy", "display_name_de": "Empathie", "role": "client"},
    "CL-IF-ACP": {"display_name": "Analysis & Clarification", "display_name_de": "Analyse & Klärung", "role": "client"},
    "CL-IF-AO": {"display_name": "Analysis Objectives", "display_name_de": "Analyse Ziele", "role": "client"},
    "CL-IF-Mot": {"display_name": "Creating Motivation", "display_name_de": "Motivation", "role": "client"},
    "CL-IF-RA": {"display_name": "Resource Activation", "display_name_de": "Ressourcenaktivierung", "role": "client"},
    "CL-IF-HP": {"display_name": "Help Coping", "display_name_de": "Problembewältigung", "role": "client"},
    "CL-FC": {"display_name": "Formalities Conclusion", "display_name_de": "Formalitäten Abschluss", "role": "client"},
    "CL-O": {"display_name": "Other", "display_name_de": "Sonstiges", "role": "client"},
}


def get_label_level2(label: str) -> str:
    """Extract level 2 category from full label."""
    if label in ONCOCO_LABELS:
        return ONCOCO_LABELS[label].get("level2", label[:6])

    # Fallback: extract first two components
    parts = label.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return label


def get_label_display_name(label: str, language: str = "de") -> str:
    """Get human-readable display name for a label."""
    if label in ONCOCO_LABELS:
        key = "display_name_de" if language == "de" else "display_name"
        return ONCOCO_LABELS[label].get(key, label)

    if label in LABEL_HIERARCHY:
        key = "display_name_de" if language == "de" else "display_name"
        return LABEL_HIERARCHY[label].get(key, label)

    return label


def get_label_role(label: str) -> str:
    """Get role (counselor/client) for a label."""
    if label.startswith("CO-"):
        return "counselor"
    if label.startswith("CL-"):
        return "client"
    if label in ONCOCO_LABELS:
        return ONCOCO_LABELS[label].get("role", "unknown")
    return "unknown"


def get_label_category(label: str) -> str:
    """Get category for a label."""
    if label in ONCOCO_LABELS:
        return ONCOCO_LABELS[label].get("category", "other")
    return "other"
