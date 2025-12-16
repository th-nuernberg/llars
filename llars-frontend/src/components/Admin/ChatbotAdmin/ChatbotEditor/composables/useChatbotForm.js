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
    rag_unknown_answer: 'Ich weiß es nicht',
    rag_citation_instructions: [
      'WICHTIG - Antworten mit Quellen:',
      '- Beantworte die Frage NUR mit Hilfe des Kontexts.',
      '- Zitiere jede Aussage aus dem Kontext direkt im Text als [1], [2], ... (direkt nach dem Satz).',
      '- Verwende NUR Quellennummern, die im Kontext vorkommen, und erfinde keine Quellen.',
      '- Wenn die Antwort nicht eindeutig aus dem Kontext ableitbar ist, antworte exakt mit: \"{{UNKNOWN_ANSWER}}\"'
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
      '- web_search(query): Web-Suche für aktuelle Informationen',
      '- respond(answer): Finale Antwort geben',
      '',
      'Führe die passende Aktion aus, um die Frage zu beantworten.',
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
      'Du bist ein Assistent, der strukturiert denkt und handelt.',
      '',
      'Bei jeder Anfrage folgst du diesem Prozess:',
      '1. THOUGHT: Analysiere die Frage und überlege, welche Informationen benötigt werden',
      '2. ACTION: Führe eine der verfügbaren Aktionen aus',
      '3. OBSERVATION: Analysiere das Ergebnis der Aktion',
      '4. Wiederhole bis du genug Informationen hast',
      '5. FINAL ANSWER: Gib eine fundierte Antwort mit Quellenverweisen',
      '',
      'Verfügbare Aktionen:',
      '- rag_search(query): Semantische Suche in den Dokumenten',
      '- lexical_search(query): Wörtliche Suche in den Dokumenten',
      '- respond(answer): Finale Antwort geben'
    ].join('\n'),
    react_tools_enabled: ['rag_search', 'lexical_search', 'respond'],
    reflact_system_prompt: [
      'Du bist ein zielorientierter Assistent, der vor jeder Aktion sein Ziel reflektiert.',
      '',
      'Bei jeder Anfrage folgst du diesem Prozess:',
      '1. GOAL: Definiere das übergeordnete Ziel der Anfrage',
      '2. REFLECTION: Reflektiere, wie weit du vom Ziel entfernt bist',
      '3. THOUGHT: Überlege den nächsten sinnvollen Schritt',
      '4. ACTION: Führe eine Aktion aus',
      '5. OBSERVATION: Analysiere das Ergebnis',
      '6. Wiederhole ab Schritt 2 bis das Ziel erreicht ist',
      '7. FINAL ANSWER: Gib eine fundierte Antwort mit Quellenverweisen',
      '',
      'Verfügbare Aktionen:',
      '- rag_search(query): Semantische Suche in den Dokumenten',
      '- lexical_search(query): Wörtliche Suche in den Dokumenten',
      '- respond(answer): Finale Antwort geben'
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
      formData.value = {
        ...formData.value,
        ...chatbot,
        prompt_settings: promptSettings,
        collection_ids: chatbot.collections?.map(c => c.id) || []
      };
      updateLineCount();
    } else {
      resetForm();
    }
  }

  // Prepare data for saving
  function prepareForSave(isEdit, chatbotId) {
    const dataToSave = { ...formData.value };
    if (!dataToSave.model_name) {
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
