/**
 * ChatbotEditor Constants
 *
 * Shared constants for the ChatbotEditor component and its sub-components.
 *
 * @module ChatbotEditor/constants
 */

/**
 * Agent mode configurations with detailed descriptions for UI.
 * Each mode defines how the chatbot processes questions.
 */
export const AGENT_MODES = [
  {
    value: 'standard',
    label: 'Standard',
    icon: 'mdi-lightning-bolt',
    color: 'grey',
    description: 'Klassisches RAG: Eine Anfrage, eine Antwort. Schnellste Option ohne mehrstufiges Reasoning.',
    details: 'Der Chatbot erhält die Frage, optional RAG-Kontext, und antwortet direkt. Kein iterativer Prozess.',
    calls: '1 LLM-Call',
    example: 'Frage → [RAG-Kontext] → Antwort'
  },
  {
    value: 'act',
    label: 'ACT',
    icon: 'mdi-play',
    color: 'primary',
    description: 'Action-Only: Der Agent führt Tools aus ohne explizite Denkschritte anzuzeigen.',
    details: 'Schneller als ReAct, da keine THOUGHT-Phase. Der Agent entscheidet direkt welches Tool er nutzt.',
    calls: '1-3 LLM-Calls',
    tools: true,
    example: 'ACTION: rag_search("Begriff") → OBSERVATION → Antwort'
  },
  {
    value: 'react',
    label: 'ReAct',
    icon: 'mdi-thought-bubble',
    color: 'success',
    description: 'Reasoning + Acting: Transparenter Denkprozess mit nachvollziehbaren Schritten.',
    details: 'Der Agent denkt laut nach (THOUGHT), führt dann eine Aktion aus (ACTION) und wertet das Ergebnis aus (OBSERVATION). Dieser Zyklus wiederholt sich bis zur Antwort.',
    calls: '2-5 LLM-Calls',
    tools: true,
    badge: 'Empfohlen',
    badgeColor: 'success',
    example: 'THOUGHT: Ich muss... → ACTION: rag_search() → OBSERVATION → THOUGHT: Jetzt weiß ich... → FINAL ANSWER'
  },
  {
    value: 'reflact',
    label: 'ReflAct',
    icon: 'mdi-target',
    color: 'warning',
    description: 'Zustandsbasierte Reflexion: Bewertet bei jedem Schritt den aktuellen Zustand relativ zum Ziel.',
    details: 'Basierend auf dem ReflAct Paper (arxiv.org/abs/2505.15182). Statt "Was soll ich tun?" fragt der Agent "Wo stehe ich relativ zum Ziel?". Die Reflection ist zustandsbasiert statt vorausschauend.',
    calls: '2-6 LLM-Calls',
    tools: true,
    badge: 'Paper-basiert',
    badgeColor: 'info',
    example: 'REFLECTION: Aktuell weiß ich X, das bringt mich näher zum Ziel → ACTION → OBSERVATION → FINAL ANSWER'
  }
];

/**
 * Task type configurations for agent modes.
 * Defines complexity levels for agent operations.
 */
export const TASK_TYPES = [
  {
    value: 'lookup',
    label: 'Look Up',
    icon: 'mdi-magnify',
    description: 'Einfache Fakten-Suche: "Wer ist der CEO?" - eine Suche, eine Antwort.',
    iterations: '1-2',
    example: 'Frage → 1x Suche → Antwort'
  },
  {
    value: 'multihop',
    label: 'Multi-hop',
    icon: 'mdi-transit-connection-variant',
    description: 'Komplexe Verknüpfungen: "Welche Projekte leitet der CEO?" - mehrere Suchschritte nötig.',
    iterations: '3-5',
    badge: 'Mehr Tokens',
    badgeColor: 'warning',
    example: 'Frage → Suche CEO → Suche Projekte → Verknüpfen → Antwort'
  }
];

/**
 * Available tools for agent modes.
 */
export const AVAILABLE_AGENT_TOOLS = [
  { title: 'RAG-Suche (Semantisch)', value: 'rag_search' },
  { title: 'Lexikalische Suche', value: 'lexical_search' },
  { title: 'Web-Suche', value: 'web_search' },
  { title: 'Antworten', value: 'respond' }
];
