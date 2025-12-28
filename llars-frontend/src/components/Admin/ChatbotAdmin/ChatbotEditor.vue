<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1000"
    height="100vh"
    max-height="100vh"
    content-class="chatbot-editor-dialog"
    persistent
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="chatbot-editor-card">
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between bg-primary">
        <div class="d-flex align-center">
          <v-icon class="mr-2">{{ isEdit ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          <span>{{ isEdit ? 'Chatbot bearbeiten' : 'Neuer Chatbot' }}</span>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        />
      </v-card-title>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" bg-color="surface">
        <v-tab value="general">
          <v-icon start>mdi-information</v-icon>
          Allgemein
        </v-tab>
        <v-tab value="llm">
          <v-icon start>mdi-brain</v-icon>
          LLM-Einstellungen
        </v-tab>
        <v-tab value="rag">
          <v-icon start>mdi-magnify</v-icon>
          RAG
        </v-tab>
        <v-tab v-if="canUseAdvancedModes" value="agent">
          <v-icon start>mdi-robot-outline</v-icon>
          Agent
          <LTag variant="warning" size="sm" class="ml-2">PRO</LTag>
        </v-tab>
        <v-tab value="collections">
          <v-icon start>mdi-folder-multiple</v-icon>
          Collections
        </v-tab>
        <v-tab value="webcrawler">
          <v-icon start>mdi-spider-web</v-icon>
          Web Crawler
        </v-tab>
      </v-tabs>

      <!-- Content -->
      <v-card-text class="chatbot-editor-body">
        <v-window v-model="activeTab">
          <!-- General Tab -->
          <v-window-item value="general" eager>
            <v-form ref="formGeneral">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.name"
                    label="Technischer Name"
                    hint="Eindeutiger Bezeichner (z.B. support-bot)"
                    persistent-hint
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.display_name"
                    label="Anzeigename"
                    hint="Name wie er Benutzern angezeigt wird"
                    persistent-hint
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="formData.description"
                    label="Beschreibung"
                    hint="Kurze Beschreibung des Chatbot-Zwecks"
                    persistent-hint
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Icon Selection -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.icon"
                    label="Icon"
                    :items="iconOptions"
                    variant="outlined"
                    density="comfortable"
                  >
                    <template #selection="{ item }">
                      <v-icon class="mr-2">{{ item.value }}</v-icon>
                      {{ item.title }}
                    </template>
                    <template #item="{ props, item }">
                      <v-list-item v-bind="props">
                        <template #prepend>
                          <v-icon>{{ item.value }}</v-icon>
                        </template>
                      </v-list-item>
                    </template>
                    <template #append>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        :loading="generatingIcon"
                        :disabled="generatingIcon"
                        @click.stop="generateIcon"
                      >
                        <v-icon>mdi-auto-fix</v-icon>
                        <v-tooltip activator="parent" location="top">
                          {{ isEdit ? 'Icon vorschlagen (LLM)' : 'Zufälliges Icon' }}
                        </v-tooltip>
                      </v-btn>
                    </template>
                  </v-select>
                </v-col>

                <!-- Color Picker -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.color"
                    label="Farbe"
                    variant="outlined"
                    density="comfortable"
                  >
                    <template #prepend-inner>
                      <input
                        v-model="formData.color"
                        type="color"
                        style="width: 32px; height: 32px; border: none; cursor: pointer"
                      >
                    </template>
                    <template #append>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        :loading="generatingColor"
                        :disabled="generatingColor"
                        @click.stop="generateColor"
                      >
                        <v-icon>mdi-auto-fix</v-icon>
                        <v-tooltip activator="parent" location="top">
                          {{ isEdit ? 'Farbe vorschlagen (LLM/Brand)' : 'Zufällige Farbe' }}
                        </v-tooltip>
                      </v-btn>
                    </template>
                  </v-text-field>
                </v-col>

                <!-- Fallback Message (Welcome Message is in LLM tab) -->
                <v-col cols="12">
                  <v-textarea
                    v-model="formData.fallback_message"
                    label="Fallback-Nachricht"
                    hint="Nachricht bei Fehlern oder wenn keine Antwort möglich"
                    persistent-hint
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Status Switches -->
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="formData.is_active"
                    label="Chatbot aktiv"
                    color="success"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="formData.is_public"
                    label="Öffentlich verfügbar"
                    color="primary"
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- LLM Settings Tab -->
          <v-window-item value="llm" eager>
            <v-form ref="formLLM" class="llm-tab-form">
              <!-- Top section: Model & Prompt Templates -->
              <div class="llm-top-section">
                <v-row dense>
                  <!-- Model Selection -->
                  <v-col cols="12" md="6">
                    <v-combobox
                      v-model="formData.model_name"
                      :items="llmModelItems"
                      item-title="title"
                      item-value="value"
                      :return-object="false"
                      label="Modell"
                      variant="outlined"
                      density="compact"
                      :loading="llmModelsLoading"
                      clearable
                      hide-details
                    >
                      <template #append>
                        <v-btn
                          icon
                          variant="text"
                          size="x-small"
                          :loading="llmModelsLoading"
                          @click="syncAndLoadModels"
                        >
                          <v-icon size="18">mdi-refresh</v-icon>
                        </v-btn>
                      </template>
                    </v-combobox>
                  </v-col>

                  <!-- Temperature -->
                  <v-col cols="12" md="3">
                    <v-text-field
                      v-model.number="formData.temperature"
                      label="Temperatur"
                      type="number"
                      :min="0"
                      :max="2"
                      :step="0.1"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>

                  <!-- Max Tokens -->
                  <v-col cols="12" md="3">
                    <v-text-field
                      v-model.number="formData.max_tokens"
                      label="Max. Tokens"
                      type="number"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>

                  <!-- Prompt Templates -->
                  <v-col cols="12">
                    <div class="d-flex align-center flex-wrap ga-1">
                      <span class="text-caption text-medium-emphasis mr-2">Vorlagen:</span>
                      <v-chip
                        v-for="template in promptTemplates"
                        :key="template.name"
                        variant="outlined"
                        size="small"
                        @click="applyPromptTemplate(template)"
                      >
                        <v-icon start size="14">{{ template.icon }}</v-icon>
                        {{ template.name }}
                      </v-chip>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <!-- Bottom section: System Prompt + Welcome Message split -->
              <div class="llm-prompts-split">
                <!-- System Prompt -->
                <div class="prompt-panel">
                  <div class="prompt-panel-header">
                    <v-icon size="18" class="mr-1">mdi-code-braces</v-icon>
                    System Prompt
                    <span class="text-caption text-medium-emphasis ml-auto">
                      {{ formData.system_prompt?.length || 0 }} Zeichen
                    </span>
                  </div>
                  <div class="prompt-panel-content">
                    <textarea
                      v-model="formData.system_prompt"
                      class="prompt-textarea-full"
                      placeholder="Definieren Sie die Rolle und das Verhalten des Chatbots..."
                      @input="updateLineCount"
                    />
                  </div>
                </div>

                <!-- Welcome Message -->
                <div class="prompt-panel">
                  <div class="prompt-panel-header">
                    <v-icon size="18" class="mr-1">mdi-message-text</v-icon>
                    Willkommensnachricht
                    <span class="text-caption text-medium-emphasis ml-auto">
                      {{ formData.welcome_message?.length || 0 }} Zeichen
                    </span>
                  </div>
                  <div class="prompt-panel-content">
                    <textarea
                      v-model="formData.welcome_message"
                      class="prompt-textarea-full"
                      placeholder="Erste Nachricht beim Start eines Gesprächs..."
                    />
                  </div>
                </div>
              </div>
            </v-form>
          </v-window-item>

          <!-- RAG Settings Tab -->
          <v-window-item value="rag" eager>
            <v-form ref="formRAG">
              <v-row>
                <v-col cols="12">
                  <v-switch
                    v-model="formData.rag_enabled"
                    label="RAG aktivieren"
                    color="info"
                    hide-details
                  />
                  <div class="text-caption text-medium-emphasis mt-2">
                    Retrieval-Augmented Generation für wissensbasierte Antworten
                  </div>
                </v-col>

                <template v-if="formData.rag_enabled">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.rag_retrieval_k"
                      label="Anzahl Dokumente (k)"
                      type="number"
                      :min="1"
                      :max="20"
                      hint="Wie viele relevante Dokumente abgerufen werden"
                      persistent-hint
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.rag_min_relevance"
                      label="Minimale Relevanz"
                      type="number"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      hint="Schwellwert für Dokumenten-Relevanz (0-1)"
                      persistent-hint
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>

                  <v-col cols="12">
                    <v-switch
                      v-model="formData.rag_include_sources"
                      label="Quellen in Antwort einbeziehen"
                      color="primary"
                      :disabled="formData.prompt_settings?.rag_require_citations"
                      hide-details
                    />
                    <div class="text-caption text-medium-emphasis mt-2">
                      Zeigt Quellenangaben in den Antworten an
                      <template v-if="formData.prompt_settings?.rag_require_citations">
                        (für Zitationen erforderlich)
                      </template>
                    </div>
                  </v-col>

                  <v-col cols="12">
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon start>mdi-format-quote-close</v-icon>
                        Quellen & Antwortregeln
                      </v-card-title>
                      <v-card-text>
                        <v-switch
                          v-model="formData.prompt_settings.rag_require_citations"
                          label="Zitationen [1], [2], ... erzwingen"
                          color="primary"
                          hide-details
                          class="mb-4"
                        />

                        <v-switch
                          v-model="formData.prompt_settings.rag_use_cross_encoder"
                          label="Cross-Encoder Reranking"
                          color="primary"
                          hide-details
                          class="mb-4"
                        >
                          <template #append>
                            <LInfoTooltip
                              title="Cross-Encoder Reranking"
                              :max-width="380"
                            >
                              <p>
                                Cross-Encoder verbessern die Relevanz der abgerufenen Dokumente signifikant,
                                insbesondere bei Fragen die anders formuliert sind als die Dokument-Inhalte.
                              </p>
                              <p class="mt-2">
                                <strong>Beispiel:</strong> "Wer ist im Team?" findet Dokumente mit
                                "Max Mustermann - Geschäftsführer" korrekt, auch wenn keine wörtliche
                                Übereinstimmung vorliegt.
                              </p>
                              <p class="mt-2 text-caption">
                                Erhöht die Latenz leicht (~100-200ms), aber verbessert die Antwortqualität deutlich.
                              </p>
                            </LInfoTooltip>
                          </template>
                        </v-switch>

                        <v-text-field
                          v-model="formData.prompt_settings.rag_unknown_answer"
                          label="Antwort wenn nicht in Quellen"
                          hint="Wird bei faktischen Fragen verwendet, wenn die Antwort nicht im Kontext steht."
                          persistent-hint
                          variant="outlined"
                          density="comfortable"
                          class="mb-4"
                        />

                        <v-textarea
                          v-model="formData.prompt_settings.rag_citation_instructions"
                          label="Antwort-Instruktionen"
                          hint='Steuert wie der Chatbot antwortet. Platzhalter: {{UNKNOWN_ANSWER}}. Tipp: Smalltalk separat regeln!'
                          persistent-hint
                          rows="12"
                          variant="outlined"
                          density="comfortable"
                          class="mb-4"
                        />

                        <v-row>
                          <v-col cols="12" md="4">
                            <v-text-field
                              v-model="formData.prompt_settings.rag_context_prefix"
                              label="Kontext-Prefix"
                              hint="Überschrift vor den Quellen im Prompt"
                              persistent-hint
                              variant="outlined"
                              density="comfortable"
                            />
                          </v-col>
                          <v-col cols="12" md="8">
                            <v-textarea
                              v-model="formData.prompt_settings.rag_context_item_template"
                              label="Kontext-Eintrag Template"
                              hint="Platzhalter: {{id}}, {{title}}, {{excerpt}}, {{page_number}}, {{chunk_index}}, {{collection_name}}"
                              persistent-hint
                              rows="4"
                              variant="outlined"
                              density="comfortable"
                            />
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </template>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- Agent Mode Tab (PRO) -->
          <v-window-item v-if="canUseAdvancedModes" value="agent" eager>
            <v-form ref="formAgent">
              <v-row>
                <!-- Comprehensive Explanation Card -->
                <v-col cols="12">
                  <v-card variant="outlined" class="agent-explanation-card mb-4">
                    <v-card-title class="d-flex align-center">
                      <v-icon start color="primary">mdi-robot-outline</v-icon>
                      <span>Agent-Modi verstehen</span>
                      <v-spacer />
                      <v-btn
                        :icon="showAgentExplanation ? 'mdi-chevron-up' : 'mdi-chevron-down'"
                        variant="text"
                        size="small"
                        @click="showAgentExplanation = !showAgentExplanation"
                      />
                    </v-card-title>

                    <v-expand-transition>
                      <div v-show="showAgentExplanation">
                        <v-divider />
                        <v-card-text>
                          <!-- What are Agent Modes -->
                          <div class="mb-4">
                            <div class="text-subtitle-2 mb-2">
                              <v-icon start size="small" color="info">mdi-help-circle</v-icon>
                              Was sind Agent-Modi?
                            </div>
                            <p class="text-body-2 text-medium-emphasis">
                              Agent-Modi steuern, <strong>wie</strong> der Chatbot Fragen beantwortet. Statt einer einfachen Anfrage-Antwort
                              kann der Agent mehrere Schritte durchlaufen: nachdenken, Werkzeuge nutzen (z.B. Dokumentensuche),
                              Ergebnisse auswerten und erst dann antworten.
                            </p>
                          </div>

                          <!-- Mode Comparison -->
                          <div class="mb-4">
                            <div class="text-subtitle-2 mb-2">
                              <v-icon start size="small" color="success">mdi-compare</v-icon>
                              Ablauf-Vergleich
                            </div>
                            <div class="agent-flow-comparison">
                              <!-- Standard -->
                              <div class="flow-item">
                                <div class="flow-label">Standard</div>
                                <div class="flow-steps">
                                  <span class="flow-step step-query">Frage</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-llm">LLM</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-answer">Antwort</span>
                                </div>
                              </div>

                              <!-- ACT -->
                              <div class="flow-item">
                                <div class="flow-label">ACT</div>
                                <div class="flow-steps">
                                  <span class="flow-step step-query">Frage</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-action">ACTION</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-observation">OBSERVATION</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-answer">Antwort</span>
                                </div>
                              </div>

                              <!-- ReAct -->
                              <div class="flow-item">
                                <div class="flow-label">ReAct</div>
                                <div class="flow-steps">
                                  <span class="flow-step step-query">Frage</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-thought">THOUGHT</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-action">ACTION</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-observation">OBSERVATION</span>
                                  <span class="flow-arrow">↺</span>
                                  <span class="flow-step step-answer">Antwort</span>
                                </div>
                              </div>

                              <!-- ReflAct -->
                              <div class="flow-item">
                                <div class="flow-label">ReflAct</div>
                                <div class="flow-steps">
                                  <span class="flow-step step-query">Aufgabe</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-reflection">REFLECTION</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-action">ACTION</span>
                                  <span class="flow-arrow">→</span>
                                  <span class="flow-step step-observation">OBSERVATION</span>
                                  <span class="flow-arrow">↺</span>
                                  <span class="flow-step step-answer">Antwort</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <!-- When to use which -->
                          <div>
                            <div class="text-subtitle-2 mb-2">
                              <v-icon start size="small" color="warning">mdi-lightbulb</v-icon>
                              Empfehlungen
                            </div>
                            <v-table density="compact" class="agent-recommendations-table">
                              <thead>
                                <tr>
                                  <th>Anwendungsfall</th>
                                  <th>Empfohlener Modus</th>
                                  <th>Grund</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr>
                                  <td>Einfache FAQ, Smalltalk</td>
                                  <td><LTag variant="gray" size="sm">Standard</LTag></td>
                                  <td class="text-caption">Schnell, keine Tool-Nutzung nötig</td>
                                </tr>
                                <tr>
                                  <td>Fakten aus Dokumenten</td>
                                  <td><LTag variant="success" size="sm">ReAct</LTag></td>
                                  <td class="text-caption">Nachvollziehbarer Suchprozess</td>
                                </tr>
                                <tr>
                                  <td>Schnelle Tool-Nutzung</td>
                                  <td><LTag variant="primary" size="sm">ACT</LTag></td>
                                  <td class="text-caption">Weniger Tokens, schneller</td>
                                </tr>
                                <tr>
                                  <td>Komplexe Multi-Hop Fragen</td>
                                  <td><LTag variant="warning" size="sm">ReflAct</LTag></td>
                                  <td class="text-caption">Selbstkorrektur durch Ziel-Reflexion</td>
                                </tr>
                              </tbody>
                            </v-table>
                          </div>
                        </v-card-text>
                      </div>
                    </v-expand-transition>

                    <!-- Collapsed summary -->
                    <v-card-text v-if="!showAgentExplanation" class="pt-0">
                      <div class="text-body-2 text-medium-emphasis">
                        Agent-Modi steuern wie der Chatbot Fragen beantwortet: von einfacher Antwort (Standard)
                        bis zu mehrstufigem Reasoning mit Tool-Nutzung (ReflAct).
                        <a href="#" class="text-primary" @click.prevent="showAgentExplanation = true">Mehr erfahren...</a>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Agent Mode Selection Cards -->
                <v-col cols="12">
                  <div class="d-flex align-center mb-2">
                    <div class="text-subtitle-2">Agent-Modus wählen</div>
                  </div>
                  <div class="agent-mode-grid">
                    <v-card
                      v-for="mode in agentModes"
                      :key="mode.value"
                      :class="['agent-mode-card', { 'agent-mode-card--selected': formData.prompt_settings.agent_mode === mode.value }]"
                      variant="outlined"
                      @click="formData.prompt_settings.agent_mode = mode.value"
                    >
                      <v-card-text>
                        <!-- Header -->
                        <div class="d-flex align-center mb-2">
                          <v-icon :color="mode.color" size="28" class="mr-2">{{ mode.icon }}</v-icon>
                          <span class="text-h6 font-weight-bold">{{ mode.label }}</span>
                          <LTag v-if="mode.badge" :variant="mode.badgeColor" size="sm" class="ml-auto">
                            {{ mode.badge }}
                          </LTag>
                        </div>

                        <!-- Description -->
                        <div class="text-body-2 mb-3">{{ mode.description }}</div>

                        <!-- Details (shown on hover/selection) -->
                        <v-expand-transition>
                          <div v-if="formData.prompt_settings.agent_mode === mode.value" class="mode-details mb-3">
                            <div class="text-caption text-medium-emphasis mb-2">{{ mode.details }}</div>
                            <div class="mode-example">
                              <v-icon size="small" class="mr-1">mdi-code-tags</v-icon>
                              <code class="text-caption">{{ mode.example }}</code>
                            </div>
                          </div>
                        </v-expand-transition>

                        <!-- Tags -->
                        <div class="d-flex align-center flex-wrap ga-2">
                          <LTag variant="info" size="sm" prepend-icon="mdi-api">
                            {{ mode.calls }}
                          </LTag>
                          <LTag v-if="mode.tools" variant="success" size="sm" prepend-icon="mdi-tools">
                            Tools
                          </LTag>
                          <LTag v-if="mode.value === 'standard'" variant="gray" size="sm" prepend-icon="mdi-speedometer">
                            Schnell
                          </LTag>
                          <LTag v-if="mode.value === 'reflact'" variant="warning" size="sm" prepend-icon="mdi-brain">
                            Komplex
                          </LTag>
                        </div>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-col>

                <!-- Task Type Selection (for non-standard modes) -->
                <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
                  <div class="d-flex align-center mb-2">
                    <div class="text-subtitle-2">Task-Typ</div>
                    <LInfoTooltip title="Task-Typen" :max-width="420" class="ml-2">
                      <ul>
                        <li>Look Up: einfache Fakten-Suche mit wenigen Tool-Aufrufen.</li>
                        <li>Multi-hop: mehrschrittige Fragen, mehr Iterationen und Tokens.</li>
                      </ul>
                    </LInfoTooltip>
                  </div>
                  <div class="task-type-grid">
                    <v-card
                      v-for="task in taskTypes"
                      :key="task.value"
                      :class="['task-type-card', { 'task-type-card--selected': formData.prompt_settings.task_type === task.value }]"
                      variant="outlined"
                      @click="formData.prompt_settings.task_type = task.value"
                    >
                      <v-card-text class="pa-3">
                        <div class="d-flex align-center mb-1">
                          <v-icon color="primary" size="20" class="mr-2">{{ task.icon }}</v-icon>
                          <span class="font-weight-medium">{{ task.label }}</span>
                          <LTag v-if="task.badge" :variant="task.badgeColor" size="sm" class="ml-auto">
                            {{ task.badge }}
                          </LTag>
                        </div>
                        <div class="text-caption text-medium-emphasis">{{ task.description }}</div>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-col>

                <!-- Configuration Matrix Info -->
                <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
                  <v-alert type="success" variant="tonal" density="compact">
                    <div class="d-flex align-center">
                      <v-icon start>mdi-information</v-icon>
                      <span>
                        Aktuelle Konfiguration:
                        <strong>{{ agentModes.find(m => m.value === formData.prompt_settings.agent_mode)?.label }}</strong>
                        +
                        <strong>{{ taskTypes.find(t => t.value === formData.prompt_settings.task_type)?.label }}</strong>
                      </span>
                    </div>
                  </v-alert>
                </v-col>

                <!-- Max Iterations (for agent modes) -->
                <v-col v-if="['act', 'react', 'reflact'].includes(formData.prompt_settings.agent_mode)" cols="12" md="6">
                  <v-text-field
                    v-model.number="formData.prompt_settings.agent_max_iterations"
                    label="Max. Iterationen"
                    type="number"
                    :min="1"
                    :max="10"
                    hint="Maximale Anzahl an Agent-Zyklen"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Tools Configuration -->
                <v-col v-if="['act', 'react', 'reflact'].includes(formData.prompt_settings.agent_mode)" cols="12" md="6">
                  <v-select
                    v-model="formData.prompt_settings.tools_enabled"
                    :items="availableAgentTools"
                    label="Aktivierte Tools"
                    multiple
                    chips
                    closable-chips
                    hint="Welche Tools der Agent nutzen darf"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Web Search Configuration -->
                <v-col v-if="['act', 'react', 'reflact'].includes(formData.prompt_settings.agent_mode)" cols="12">
                  <v-card variant="outlined">
                    <v-card-title class="text-subtitle-1 d-flex align-center">
                      <v-icon start color="info">mdi-web</v-icon>
                      Web-Suche (Tavily)
                      <LTag v-if="formData.prompt_settings.web_search_enabled" variant="success" size="sm" class="ml-2">
                        Aktiv
                      </LTag>
                    </v-card-title>
                    <v-card-text>
                      <v-switch
                        v-model="formData.prompt_settings.web_search_enabled"
                        label="Web-Suche aktivieren"
                        color="info"
                        hide-details
                        class="mb-3"
                      />
                      <div v-if="formData.prompt_settings.web_search_enabled" class="mt-3">
                        <v-text-field
                          v-model.number="formData.prompt_settings.web_search_max_results"
                          label="Max. Web-Ergebnisse"
                          type="number"
                          :min="1"
                          :max="10"
                          hint="Anzahl der Web-Suchergebnisse pro Anfrage"
                          persistent-hint
                          variant="outlined"
                          density="comfortable"
                        />
                        <v-alert type="info" variant="tonal" density="compact" class="mt-3">
                          <v-icon start size="small">mdi-key</v-icon>
                          Der Tavily API-Key wird über Umgebungsvariablen konfiguriert (TAVILY_API_KEY)
                        </v-alert>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- ACT Settings -->
                <v-col v-if="formData.prompt_settings.agent_mode === 'act'" cols="12">
                  <v-expansion-panels>
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-play</v-icon>
                        ACT System-Prompt anpassen
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-textarea
                          v-model="formData.prompt_settings.act_system_prompt"
                          label="ACT System-Prompt"
                          hint="Instruktionen für den Action-only Prozess"
                          persistent-hint
                          rows="8"
                          variant="outlined"
                          density="comfortable"
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </v-col>

                <!-- ReAct Settings -->
                <v-col v-if="formData.prompt_settings.agent_mode === 'react'" cols="12">
                  <v-expansion-panels>
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-thought-bubble</v-icon>
                        ReAct System-Prompt anpassen
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-textarea
                          v-model="formData.prompt_settings.react_system_prompt"
                          label="ReAct System-Prompt"
                          hint="Instruktionen für den THOUGHT → ACTION → OBSERVATION Prozess"
                          persistent-hint
                          rows="12"
                          variant="outlined"
                          density="comfortable"
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </v-col>

                <!-- ReflAct Settings -->
                <v-col v-if="formData.prompt_settings.agent_mode === 'reflact'" cols="12">
                  <v-expansion-panels>
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-target</v-icon>
                        ReflAct System-Prompt anpassen
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-textarea
                          v-model="formData.prompt_settings.reflact_system_prompt"
                          label="ReflAct System-Prompt"
                          hint="Instruktionen für den GOAL → REFLECTION → ACTION Prozess"
                          persistent-hint
                          rows="14"
                          variant="outlined"
                          density="comfortable"
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </v-col>

                <!-- Reflection Prompt (cross-mode) -->
                <v-col v-if="formData.prompt_settings.agent_mode !== 'standard'" cols="12">
                  <v-expansion-panels>
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon start>mdi-check-decagram</v-icon>
                        Reflection Prompt anpassen
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-textarea
                          v-model="formData.prompt_settings.reflection_prompt"
                          label="Reflection Prompt"
                          hint="Instruktionen fuer die kritische Selbstpruefung der Antwort"
                          persistent-hint
                          rows="10"
                          variant="outlined"
                          density="comfortable"
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </v-col>
              </v-row>
            </v-form>
          </v-window-item>

          <!-- Collections Tab -->
          <v-window-item value="collections" eager>
            <div v-if="collections.length === 0" class="text-center pa-8">
              <v-icon size="48" color="grey-lighten-1" class="mb-2">
                mdi-folder-off
              </v-icon>
              <div class="text-medium-emphasis">
                Keine Collections verfügbar
              </div>
            </div>
            <template v-else>
              <v-list>
                <v-list-item
                  v-for="collection in collections"
                  :key="collection.id"
                >
                  <template #prepend>
                    <v-checkbox-btn
                      :model-value="isCollectionSelected(collection.id)"
                      @update:model-value="toggleCollection(collection.id)"
                    />
                  </template>
                  <v-list-item-title>{{ collection.display_name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ collection.document_count || 0 }} Dokumente
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <v-divider class="my-4" />

              <div class="d-flex align-center mb-2">
                <v-icon class="mr-2" color="primary">mdi-upload</v-icon>
                <span class="text-subtitle-1 font-weight-medium">Dokumente hinzufügen</span>
              </div>
              <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                Laden Sie PDFs, Markdown oder TXT direkt in eine zugewiesene Collection hoch.
              </v-alert>

              <v-row v-if="selectedCollectionsForUpload.length > 0">
                <v-col
                  v-for="collection in selectedCollectionsForUpload"
                  :key="collection.id"
                  cols="12"
                  md="6"
                >
                  <v-card variant="outlined">
                    <v-card-title class="d-flex align-center">
                      <v-icon class="mr-2">mdi-folder</v-icon>
                      <span class="text-truncate">{{ collection.display_name || collection.name }}</span>
                      <v-spacer />
                      <LBtn
                        size="small"
                        variant="primary"
                        prepend-icon="mdi-upload"
                        @click="openUploadDialogForCollection(collection.id)"
                      >
                        Upload
                      </LBtn>
                    </v-card-title>
                    <v-card-text class="text-caption text-medium-emphasis">
                      {{ collection.document_count || 0 }} Dokumente
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              <div v-else class="text-center pa-6 text-medium-emphasis">
                <v-icon size="48" class="mb-2">mdi-folder-plus</v-icon>
                <div>Bitte zuerst mindestens eine Collection auswählen.</div>
              </div>
            </template>
          </v-window-item>

          <!-- Web Crawler Tab -->
          <v-window-item value="webcrawler" eager>
            <v-row>
              <v-col cols="12">
                <v-alert type="info" variant="tonal" class="mb-4">
                  <template #prepend>
                    <v-icon>mdi-spider-web</v-icon>
                  </template>
                  <div class="text-subtitle-2">Website automatisch crawlen</div>
                  <div class="text-body-2">
                    Geben Sie URLs ein, die automatisch gecrawlt und als RAG-Collection für diesen Chatbot hinzugefügt werden sollen.
                  </div>
                </v-alert>
              </v-col>

              <v-col cols="12">
                <v-textarea
                  v-model="crawlerUrls"
                  label="URLs zum Crawlen"
                  placeholder="https://example.com&#10;https://docs.example.com"
                  hint="Eine URL pro Zeile. Der Crawler folgt internen Links automatisch."
                  persistent-hint
                  rows="4"
                  variant="outlined"
                />
              </v-col>

              <v-col cols="12">
                <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon start>mdi-cog</v-icon>
                      Crawler-Einstellungen
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="crawlerMaxPages"
                            label="Max. Seiten pro URL"
                            type="number"
                            min="1"
                            max="100"
                            variant="outlined"
                            density="compact"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="crawlerMaxDepth"
                            label="Max. Link-Tiefe"
                            type="number"
                            min="1"
                            max="5"
                            variant="outlined"
                            density="compact"
                          />
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-col>

              <!-- Crawl Status -->
              <v-col cols="12" v-if="crawlStatus">
                <v-alert
                  :type="crawlStatus.success ? 'success' : crawlStatus.error ? 'error' : 'info'"
                  variant="tonal"
                >
                  <div class="font-weight-bold">{{ crawlStatus.message }}</div>
                  <div v-if="crawlStatus.pages_crawled !== undefined" class="text-body-2">
                    {{ crawlStatus.pages_crawled }} Seiten gecrawlt
                    <template v-if="crawlStatus.documents_created">,
                      {{ crawlStatus.documents_created }} Dokumente erstellt
                    </template>
                  </div>
                  <!-- Progress bar -->
                  <v-progress-linear
                    v-if="crawling && crawlProgress"
                    :model-value="(crawlProgress.pages_crawled / crawlProgress.max_pages) * 100"
                    color="primary"
                    height="8"
                    rounded
                    class="mt-2"
                  >
                    <template v-slot:default>
                      {{ crawlProgress.pages_crawled }} / {{ crawlProgress.max_pages }}
                    </template>
                  </v-progress-linear>
                  <!-- Current URL being crawled -->
                  <div v-if="crawlStatus.current_url" class="text-caption text-truncate mt-1">
                    <v-icon size="small">mdi-link</v-icon>
                    {{ crawlStatus.current_url }}
                  </div>
                </v-alert>

                <!-- Live crawled pages list -->
                <v-card v-if="crawling && crawledPages.length > 0" variant="outlined" class="mt-2">
                  <v-card-title class="text-subtitle-2 py-2">
                    <v-icon start size="small">mdi-format-list-bulleted</v-icon>
                    Zuletzt gecrawlte Seiten
                  </v-card-title>
                  <v-list dense class="py-0" style="max-height: 150px; overflow-y: auto;">
                    <v-list-item
                      v-for="(url, index) in crawledPages"
                      :key="index"
                      density="compact"
                      class="text-caption"
                    >
                      <v-icon start size="x-small" color="success">mdi-check</v-icon>
                      <span class="text-truncate">{{ url }}</span>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>

              <v-col cols="12">
                <LBtn
                  variant="outlined"
                  :loading="crawling"
                  :disabled="!hasValidCrawlerUrls"
                  prepend-icon="mdi-spider-web"
                  @click="startCrawlForChatbot"
                >
                  Website crawlen und Collection erstellen
                </LBtn>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>
      </v-card-text>

      <!-- Actions -->
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="closeDialog">
          Abbrechen
        </LBtn>
        <LBtn variant="primary" @click="saveChanges">
          {{ isEdit ? 'Speichern' : 'Erstellen' }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <DocumentUploadDialog
    v-model="uploadDialogOpen"
    :collections="selectedCollectionsForUpload"
    :initial-collection-id="uploadInitialCollectionId"
    @uploaded="handleDocumentsUploaded"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import axios from 'axios';
import DocumentUploadDialog from '@/components/RAG/DocumentUploadDialog.vue';
import { usePermissions } from '@/composables/usePermissions';
import {
  useChatbotForm,
  useChatbotCrawler
} from './ChatbotEditor/composables';

// Permission check for advanced chatbot features
const { hasPermission } = usePermissions();
const canUseAdvancedModes = computed(() => hasPermission('feature:chatbots:advanced'));

// Show/hide agent explanation section
const showAgentExplanation = ref(false);

// Agent mode configuration with detailed descriptions
const agentModes = [
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

// Task type configuration
const taskTypes = [
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

// Available tools for agent modes
const availableAgentTools = [
  { title: 'RAG-Suche (Semantisch)', value: 'rag_search' },
  { title: 'Lexikalische Suche', value: 'lexical_search' },
  { title: 'Web-Suche', value: 'web_search' },
  { title: 'Antworten', value: 'respond' }
];

const props = defineProps({
  modelValue: Boolean,
  chatbot: Object,
  collections: {
    type: Array,
    default: () => []
  },
  isEdit: Boolean
});

const emit = defineEmits(['update:modelValue', 'save', 'collection-created', 'documents-uploaded']);

// Initialize composables
const {
  formData,
  activeTab,
  promptLineCount,
  iconOptions,
  promptTemplates,
  rules,
  isCollectionSelected,
  updateLineCount,
  applyPromptTemplate,
  toggleCollection,
  loadChatbot,
  prepareForSave
} = useChatbotForm();

const {
  crawlerUrls,
  crawlerMaxPages,
  crawlerMaxDepth,
  crawling,
  crawlStatus,
  crawlProgress,
  crawledPages,
  hasValidCrawlerUrls,
  startCrawl,
  resetCrawler
} = useChatbotCrawler();

const uploadDialogOpen = ref(false);
const uploadInitialCollectionId = ref(null);

const selectedCollectionsForUpload = computed(() => {
  const ids = formData.value?.collection_ids || [];
  return (props.collections || []).filter(c => ids.includes(c.id));
});

// ===== LLM Models =====
const llmModels = ref([]);
const llmModelsLoading = ref(false);

const selectedLlmModel = computed(() => {
  const modelId = formData.value?.model_name;
  if (!modelId) return null;
  return llmModels.value.find(m => m.model_id === modelId) || null;
});

const llmModelItems = computed(() => {
  const current = formData.value?.model_name;
  const items = Array.isArray(llmModels.value) ? [...llmModels.value] : [];
  const hasCurrent = current && items.some(m => m.model_id === current);

  if (current && !hasCurrent) {
    items.unshift({
      model_id: current,
      display_name: current,
      provider: 'custom',
      supports_vision: false,
      supports_reasoning: false,
      context_window: 0,
      max_output_tokens: 0
    });
  }

  return items.map(m => ({
    title: m.display_name || m.model_id,
    value: m.model_id,
    ...m
  }));
});

function formatNumber(value) {
  if (typeof value !== 'number') return value || '';
  try {
    return value.toLocaleString();
  } catch {
    return String(value);
  }
}

async function loadModels() {
  llmModelsLoading.value = true;
  try {
    const response = await axios.get('/api/llm/models?active_only=true&model_type=llm');
    if (response.data?.success) {
      llmModels.value = response.data.models || [];

      // Default selection for "create" mode only
      if (!props.isEdit) {
        const current = formData.value?.model_name;
        const def = llmModels.value.find(m => m.is_default) || llmModels.value[0];
        if (def?.model_id && (!current || current === 'gpt-4')) {
          formData.value.model_name = def.model_id;
        }
      }
    } else {
      llmModels.value = [];
    }
  } catch (error) {
    console.warn('[ChatbotEditor] Error loading LLM models:', error);
    llmModels.value = [];
  } finally {
    llmModelsLoading.value = false;
  }
}

async function syncAndLoadModels() {
  llmModelsLoading.value = true;
  try {
    await axios.post('/api/llm/models/sync');
  } catch (error) {
    console.warn('[ChatbotEditor] Model sync failed:', error);
  } finally {
    llmModelsLoading.value = false;
  }
  await loadModels();
}

// Methods
function closeDialog() {
  emit('update:modelValue', false);
  activeTab.value = 'general';
  resetCrawler();
}

function openUploadDialogForCollection(collectionId) {
  uploadInitialCollectionId.value = collectionId;
  uploadDialogOpen.value = true;
}

function handleDocumentsUploaded() {
  emit('documents-uploaded', { collection_id: uploadInitialCollectionId.value });
}

async function startCrawlForChatbot() {
  const chatbotName = formData.value.display_name || formData.value.name || 'Chatbot';

  await startCrawl(chatbotName, {
    onComplete: (data) => {
      // Auto-add the new collection to the chatbot
      if (data.collection_id && !formData.value.collection_ids.includes(data.collection_id)) {
        formData.value.collection_ids.push(data.collection_id);
      }

      // Auto-set brand color from crawled website
      if (data.brand_color && !formData.value.color) {
        formData.value.color = data.brand_color;
        console.log('[ChatbotEditor] Auto-set brand color from crawl:', data.brand_color);
      }

      // Emit event to refresh collections list in parent
      emit('collection-created', data.collection_id);
    }
  });
}

function saveChanges() {
  const dataToSave = prepareForSave(props.isEdit, props.chatbot?.id);
  emit('save', dataToSave);
}

// LLM-based generation for icon and color
const generatingIcon = ref(false);
const generatingColor = ref(false);

async function generateIcon() {
  if (!props.chatbot?.id) {
    // Fallback to random for new chatbots
    const randomIndex = Math.floor(Math.random() * iconOptions.value.length);
    formData.value.icon = iconOptions.value[randomIndex].value;
    return;
  }

  generatingIcon.value = true;
  try {
    const response = await axios.post(`/api/chatbots/${props.chatbot.id}/wizard/generate-field`, {
      field: 'icon'
    });
    if (response.data.success && response.data.value) {
      formData.value.icon = response.data.value;
    }
  } catch (error) {
    console.error('Icon generation failed:', error);
    // Fallback to random
    const randomIndex = Math.floor(Math.random() * iconOptions.value.length);
    formData.value.icon = iconOptions.value[randomIndex].value;
  } finally {
    generatingIcon.value = false;
  }
}

async function generateColor() {
  if (!props.chatbot?.id) {
    // Fallback to random for new chatbots
    formData.value.color = generateRandomColor();
    return;
  }

  generatingColor.value = true;
  try {
    const response = await axios.post(`/api/chatbots/${props.chatbot.id}/wizard/generate-field`, {
      field: 'color'
    });
    if (response.data.success && response.data.value) {
      formData.value.color = response.data.value;
    }
  } catch (error) {
    console.error('Color generation failed:', error);
    // Fallback to random
    formData.value.color = generateRandomColor();
  } finally {
    generatingColor.value = false;
  }
}

function generateRandomColor() {
  // Generate a pleasant random color (pastel-ish)
  const hue = Math.floor(Math.random() * 360);
  const saturation = 60 + Math.floor(Math.random() * 20); // 60-80%
  const lightness = 45 + Math.floor(Math.random() * 15); // 45-60%
  return hslToHex(hue, saturation, lightness);
}

function hslToHex(h, s, l) {
  s /= 100;
  l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = n => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

// Watch for chatbot changes
watch(() => props.chatbot, (newChatbot) => {
  loadChatbot(newChatbot);
}, { immediate: true });

watch(
  () => formData.value?.model_name,
  (value) => {
    if (!value || typeof value !== 'object') return;
    const normalized = value.value || value.model_id || value.id || value.name;
    if (typeof normalized === 'string' && normalized.trim()) {
      formData.value.model_name = normalized.trim();
    }
  }
);

// Load models when dialog opens
watch(() => props.modelValue, (isOpen) => {
  if (!isOpen) {
    llmModels.value = [];
    return;
  }
  loadModels();
}, { immediate: true });
</script>

<style scoped>
/* Dialog Card - fills viewport with max constraints */
.chatbot-editor-card {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  height: 100%;
}

/* Body scrolls - uses flex to fill available space */
.chatbot-editor-body {
  flex: 1;
  min-height: 0; /* Critical for flex children to scroll */
  overflow: hidden;
  padding: 0;
  display: flex;
  flex-direction: column;
}

/* Window fills body and items scroll */
.chatbot-editor-body :deep(.v-window) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.chatbot-editor-body :deep(.v-window__container) {
  height: 100%;
}

.chatbot-editor-body :deep(.v-window-item) {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
}

/* Prompt Editor */
.prompt-editor {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.line-numbers {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 8px;
  text-align: right;
  user-select: none;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.line-number {
  line-height: 1.5;
  font-size: 12px;
}

.prompt-textarea {
  flex: 1;
  border: none;
  outline: none;
  padding: 8px 12px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  min-height: 200px;
  max-height: 400px;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Agent Mode Grid */
.agent-mode-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 600px) {
  .agent-mode-grid {
    grid-template-columns: 1fr;
  }
}

.agent-mode-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.agent-mode-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.agent-mode-card--selected {
  border-color: rgb(var(--v-theme-primary)) !important;
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
}

/* Mode Details */
.mode-details {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 2px 8px 2px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.mode-example {
  display: flex;
  align-items: flex-start;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
  overflow-x: auto;
}

.mode-example code {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  word-break: break-word;
  white-space: pre-wrap;
}

/* Agent Explanation Card */
.agent-explanation-card {
  border-radius: 12px 4px 12px 4px;
}

/* Flow Comparison Visualization */
.agent-flow-comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.flow-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 2px 8px 2px;
}

.flow-label {
  min-width: 70px;
  font-weight: 600;
  font-size: 13px;
}

.flow-steps {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.flow-step {
  padding: 4px 8px;
  border-radius: 6px 2px 6px 2px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.flow-arrow {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 14px;
}

/* Flow Step Colors */
.step-query {
  background: rgba(var(--v-theme-info), 0.2);
  color: rgb(var(--v-theme-info));
}

.step-llm {
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
}

.step-answer {
  background: rgba(var(--v-theme-success), 0.2);
  color: rgb(var(--v-theme-success));
}

.step-thought {
  background: rgba(103, 58, 183, 0.2);
  color: #673ab7;
}

.step-action {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.step-observation {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.step-goal {
  background: rgba(233, 30, 99, 0.2);
  color: #e91e63;
}

.step-reflection {
  background: rgba(0, 188, 212, 0.2);
  color: #00bcd4;
}

/* Recommendations Table */
.agent-recommendations-table {
  font-size: 13px;
}

.agent-recommendations-table th {
  font-weight: 600 !important;
  background: rgba(var(--v-theme-surface-variant), 0.5) !important;
}

.agent-recommendations-table td {
  padding: 8px 12px !important;
}

/* Task Type Grid */
.task-type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (max-width: 600px) {
  .task-type-grid {
    grid-template-columns: 1fr;
  }
}

.task-type-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.task-type-card:hover {
  border-color: rgba(var(--v-theme-info), 0.5);
  background-color: rgba(var(--v-theme-info), 0.04);
}

.task-type-card--selected {
  border-color: rgb(var(--v-theme-info)) !important;
  background-color: rgba(var(--v-theme-info), 0.08) !important;
}

/* Responsive - smaller screens get fullscreen dialog */
@media (max-width: 960px) {
  .chatbot-editor-card {
    border-radius: 0;
  }
}

:deep(.chatbot-editor-dialog) {
  height: 100vh;
  max-height: 100vh;
  min-height: 100vh;
  margin: 0;
}

/* ===== LLM Tab Split Layout ===== */
/* Override default overflow for LLM tab - we handle scrolling in textareas */
.chatbot-editor-body :deep(.v-window-item:has(.llm-tab-form)) {
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

.llm-tab-form {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
  overflow: visible;
}

.llm-top-section {
  flex-shrink: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  margin-bottom: 16px;
}

.llm-prompts-split {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0; /* Critical for flex children to scroll */
  overflow: hidden;
}

.prompt-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
}

.prompt-panel-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  font-weight: 500;
  font-size: 14px;
  flex-shrink: 0;
}

.prompt-panel-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.prompt-textarea-full {
  flex: 1;
  width: 100%;
  min-height: 0;
  padding: 12px 14px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
  overflow-y: auto;
}

.prompt-textarea-full::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Responsive: Stack on smaller screens */
@media (max-width: 768px) {
  .llm-prompts-split {
    flex-direction: column;
  }

  .prompt-panel {
    flex: none;
    min-height: 200px;
  }
}
</style>
