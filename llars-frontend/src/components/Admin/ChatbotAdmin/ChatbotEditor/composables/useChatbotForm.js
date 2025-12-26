/**
 * Chatbot Form Composable
 *
 * Handles form data, validation, and state management for chatbot editor.
 * Extracted from ChatbotEditor.vue for better maintainability.
 */

import { ref, computed, watch } from 'vue';

export function useChatbotForm() {
  const defaultPromptSettings = {
    rag_require_citations: true,
    rag_unknown_answer: 'Das kann ich dir leider nicht beantworten.',
    rag_citation_instructions: [
      'Antworte natürlich und gesprächig. Nutze die bereitgestellten Informationen als Grundlage, aber formuliere frei und menschlich. Halte das Gespräch am Laufen - stelle Rückfragen, biete Hilfe an, sei freundlich.',
      '',
      'Bei Fakten aus dem Kontext: Verweise mit [1], [2] etc. auf die Quelle.',
      'Bei Gespräch, Smalltalk oder Rückfragen: Antworte einfach natürlich.'
    ].join('\n'),
    rag_context_prefix: 'Kontext:',
    rag_context_item_template: '[{{id}}] {{title}}:\n{{excerpt}}',
    // Agent mode settings
    agent_mode: 'standard',
    task_type: 'lookup',
    agent_max_iterations: 5,
    // Web search settings
    web_search_enabled: false,
    web_search_max_results: 5,
    // Tools configuration
    tools_enabled: ['rag_search', 'lexical_search', 'respond'],
    // ACT mode prompt
    act_system_prompt: [
      'Du hast Zugriff auf folgende Tools:',
      '- rag_search(query): Semantische Suche in den Dokumenten',
      '- lexical_search(query): Wörtliche Suche in den Dokumenten',
      '- respond(answer): Finale Antwort geben',
      '',
      'Nutze web_search nur, wenn es fuer diesen Bot aktiviert ist und in der Tool-Liste angegeben wird.',
      'Nutze Suchbegriffe aus der aktuellen Nutzerfrage oder dem Verlauf.',
      'Wenn die Frage ohne Kontext unklar ist, stelle eine Rueckfrage mit respond.',
      'Schreibe keine [TOOL_CALLS]-Marker oder JSON-Toolcalls, sondern nur das ACTION-Format.',
      '',
      'Fuehre die passende Aktion aus, um die Frage zu beantworten.',
      'Format: ACTION: tool_name(parameter)'
    ].join('\n'),
    // Reflection mode prompt
    reflection_prompt: [
      'Überprüfe deine vorherige Antwort kritisch:',
      '1. Sind alle Quellenverweise [1], [2], ... korrekt und belegt?',
      '2. Wurden nur Informationen aus dem Kontext verwendet?',
      '3. Ist die Antwort vollständig und beantwortet alle Aspekte der Frage?',
      '4. Gibt es Halluzinationen oder unbelegte Behauptungen?',
      '',
      'Falls Fehler gefunden wurden, korrigiere die Antwort. Sonst bestätige die Antwort.'
    ].join('\n'),
    react_system_prompt: [
      'Du bist ein ReAct-Agent. Du denkst Schritt für Schritt und führst Aktionen aus.',
      '',
      '## Zyklus (wiederhole bis fertig):',
      '1. THOUGHT: Analysiere was du als nächstes tun musst',
      '2. ACTION: Führe GENAU EINE Aktion aus',
      '3. Warte auf OBSERVATION',
      '',
      '## Verfügbare Aktionen (NUR diese!):',
      '- rag_search("suchbegriff") - Semantische Dokumentensuche',
      '- lexical_search("suchbegriff") - Keyword-Suche',
      '- respond("antwort") - Finale Antwort (beendet Prozess)',
      '',
      '## Format (EXAKT einhalten!):',
      'THOUGHT: [deine Überlegung]',
      'ACTION: rag_search("suchbegriff")',
      '',
      'Wenn fertig:',
      'THOUGHT: [deine Überlegung]',
      'FINAL ANSWER: [vollständige Antwort mit Quellen]',
      '',
      '## Beispiel:',
      'Frage: Wer ist der CEO?',
      '',
      'THOUGHT: Ich muss nach dem CEO suchen.',
      'ACTION: rag_search("CEO Geschäftsführer")',
      '',
      '[OBSERVATION: Max Müller ist CEO seit 2020...]',
      '',
      'THOUGHT: Ich habe die Information gefunden.',
      'FINAL ANSWER: Der CEO ist Max Müller, er ist seit 2020 im Amt.[1]',
      '',
      '## WICHTIG:',
      '- IMMER erst THOUGHT, dann ACTION oder FINAL ANSWER',
      '- Aktionen GENAU so schreiben: rag_search("text")',
      '- KEINE anderen Aktionen erfinden!',
      '- Wenn keine Treffer: Query reformulieren, Komposita zerlegen (z.B. teammitglieder → team + mitglieder) und Synonyme testen.'
    ].join('\n'),
    react_tools_enabled: ['rag_search', 'lexical_search', 'respond'],
    reflact_system_prompt: [
      'Du bist ein ReflAct-Agent. Bei jedem Schritt reflektierst du deinen aktuellen Zustand RELATIV zum Aufgabenziel, dann wählst du die nächste Aktion.',
      '',
      '## ReflAct-Prinzip (basierend auf arxiv.org/abs/2505.15182):',
      '- Nicht "Was soll ich als nächstes tun?" (vorausschauend)',
      '- Sondern "Wo stehe ich relativ zum Ziel?" (zustandsbasiert)',
      '',
      '## Deine Reflection muss IMMER enthalten:',
      '1. Aktueller Zustand: Was weißt du bereits?',
      '2. Letzte Entdeckung: Was hast du gerade erfahren?',
      '3. Ziel-Relation: Wie nah bist du dem Ziel? Was fehlt noch?',
      '',
      '## Verfügbare Aktionen:',
      '- rag_search("suchbegriff") - Semantische Dokumentensuche',
      '- lexical_search("suchbegriff") - Keyword-Suche',
      '',
      '## Format (STRIKT einhalten!):',
      '',
      'REFLECTION: Aktuell weiß ich [Zustand]. Die letzte Suche ergab [Ergebnis]. Dies bringt mich [näher/nicht näher] zum Ziel [X], weil [Begründung].',
      'ACTION: rag_search("suchbegriff")',
      '',
      'Wenn das Ziel erreicht ist:',
      'REFLECTION: Ich habe alle nötigen Informationen: [Zusammenfassung]. Das Ziel ist erreicht.',
      'FINAL ANSWER: [Vollständige Antwort basierend auf den gefundenen Informationen]',
      '',
      '## Beispiel:',
      'Aufgabe: "Wer ist der Geschäftsführer von Firma X?"',
      '',
      'REFLECTION: Aktuell habe ich keine Information über Firma X. Ich muss zunächst nach Informationen über die Firma suchen.',
      'ACTION: rag_search("Firma X Geschäftsführer")',
      '',
      '[OBSERVATION: Gefunden: Max Mustermann ist Geschäftsführer...]',
      '',
      'REFLECTION: Die Suche ergab, dass Max Mustermann der Geschäftsführer von Firma X ist. Das Ziel ist erreicht.',
      'FINAL ANSWER: Der Geschäftsführer von Firma X ist Max Mustermann.',
      '',
      '## WICHTIG:',
      '- KEINE THOUGHT-Zeile - die Reflection ersetzt das Denken',
      '- Aktionen EXAKT so: rag_search("text") oder lexical_search("text")',
      '- Immer NUR EINE Aktion pro Runde',
      '- Wenn keine Treffer: Query reformulieren, Komposita zerlegen (z.B. teammitglieder → team + mitglieder) und Synonyme testen.'
    ].join('\n')
  };

  // Form data with defaults
  const formData = ref({
    name: '',
    display_name: '',
    description: '',
    icon: 'mdi-robot',
    color: '#b0ca97',
    system_prompt: '',
    model_name: '',
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 1.0,
    rag_enabled: false,
    rag_retrieval_k: 5,
    rag_min_relevance: 0.6,
    rag_include_sources: true,
    welcome_message: '',
    fallback_message: '',
    is_active: true,
    is_public: false,
    collection_ids: [],
    prompt_settings: { ...defaultPromptSettings }
  });

  const activeTab = ref('general');
  const promptLineCount = ref(10);

  // Icon options for select
  const iconOptions = [
    { title: 'Robot', value: 'mdi-robot' },
    { title: 'Account', value: 'mdi-account' },
    { title: 'Chat', value: 'mdi-chat' },
    { title: 'Help', value: 'mdi-help-circle' },
    { title: 'Information', value: 'mdi-information' },
    { title: 'Support', value: 'mdi-face-agent' },
    { title: 'Book', value: 'mdi-book-open-page-variant' },
    { title: 'Lightbulb', value: 'mdi-lightbulb' }
  ];

  // Prompt templates
  const promptTemplates = [
    {
      name: 'Support',
      icon: 'mdi-face-agent',
      prompt: 'Du bist ein freundlicher Support-Mitarbeiter. Beantworte Fragen höflich und präzise. Wenn du etwas nicht weißt, gib das ehrlich zu und biete an, weiterzuhelfen.'
    },
    {
      name: 'FAQ',
      icon: 'mdi-help-circle',
      prompt: 'Du bist ein FAQ-Bot. Beantworte häufige Fragen basierend auf den verfügbaren Dokumenten. Halte deine Antworten kurz und präzise.'
    },
    {
      name: 'Onboarding',
      icon: 'mdi-account-star',
      prompt: 'Du bist ein Onboarding-Assistent. Führe neue Benutzer freundlich durch die ersten Schritte. Erkläre Funktionen verständlich und gebe hilfreiche Tipps.'
    },
    {
      name: 'Technisch',
      icon: 'mdi-wrench',
      prompt: 'Du bist ein technischer Assistent. Beantworte Fragen präzise und sachlich. Gebe technische Details, wenn nötig, und verwende Fachbegriffe korrekt.'
    }
  ];

  // Validation rules
  const rules = {
    required: v => !!v || 'Dieses Feld ist erforderlich'
  };

  // Update line count for prompt editor
  function updateLineCount() {
    const lines = (formData.value.system_prompt || '').split('\n').length;
    promptLineCount.value = Math.max(lines, 10);
  }

  // Apply a prompt template
  function applyPromptTemplate(template) {
    formData.value.system_prompt = template.prompt;
    updateLineCount();
  }

  // Toggle collection selection
  function toggleCollection(collectionId) {
    const index = formData.value.collection_ids.indexOf(collectionId);
    if (index > -1) {
      formData.value.collection_ids.splice(index, 1);
    } else {
      formData.value.collection_ids.push(collectionId);
    }
  }

  // Check if collection is selected
  const isCollectionSelected = computed(() => {
    return (collectionId) => formData.value.collection_ids.includes(collectionId);
  });

  // Reset form to defaults
  function resetForm() {
    formData.value = {
      name: '',
      display_name: '',
      description: '',
      icon: 'mdi-robot',
      color: '#b0ca97',
      system_prompt: '',
      model_name: '',
      temperature: 0.7,
      max_tokens: 2000,
      top_p: 1.0,
      rag_enabled: false,
      rag_retrieval_k: 5,
      rag_min_relevance: 0.6,
      rag_include_sources: true,
      welcome_message: '',
      fallback_message: '',
      is_active: true,
      is_public: false,
      collection_ids: [],
      prompt_settings: { ...defaultPromptSettings }
    };
    promptLineCount.value = 10;
  }

  // Load chatbot data into form
  function loadChatbot(chatbot) {
    if (chatbot) {
      const promptSettings = chatbot.prompt_settings
        ? { ...defaultPromptSettings, ...chatbot.prompt_settings }
        : { ...defaultPromptSettings };
      const normalizedModelName = normalizeModelName(chatbot.model_name);
      formData.value = {
        ...formData.value,
        ...chatbot,
        model_name: normalizedModelName || chatbot.model_name,
        prompt_settings: promptSettings,
        collection_ids: chatbot.collections?.map(c => c.id) || []
      };
      updateLineCount();
    } else {
      resetForm();
    }
  }

  function normalizeModelName(value) {
    if (!value) return null;
    if (typeof value === 'string') {
      return value.trim() || null;
    }
    if (typeof value === 'object') {
      const raw = value.value || value.model_id || value.id || value.name;
      if (typeof raw === 'string' && raw.trim()) {
        return raw.trim();
      }
    }
    return null;
  }

  // Prepare data for saving
  function prepareForSave(isEdit, chatbotId) {
    const dataToSave = { ...formData.value };
    const normalizedModelName = normalizeModelName(dataToSave.model_name);
    if (normalizedModelName) {
      dataToSave.model_name = normalizedModelName;
    } else {
      delete dataToSave.model_name;
    }
    if (isEdit && chatbotId) {
      dataToSave.id = chatbotId;
    }
    return dataToSave;
  }

  watch(
    () => formData.value.prompt_settings?.rag_require_citations,
    (required) => {
      if (required) {
        formData.value.rag_include_sources = true;
      }
    }
  );

  return {
    // State
    formData,
    activeTab,
    promptLineCount,

    // Options
    iconOptions,
    promptTemplates,
    rules,

    // Computed
    isCollectionSelected,

    // Methods
    updateLineCount,
    applyPromptTemplate,
    toggleCollection,
    resetForm,
    loadChatbot,
    prepareForSave
  };
}
