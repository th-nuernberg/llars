<!--
  ChatbotEditor - RAG Settings Tab

  RAG configuration including document retrieval, reranking, and citation settings.
-->
<template>
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
              <LIcon start>mdi-format-quote-close</LIcon>
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
                v-model="formData.rag_use_cross_encoder"
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
                      Erhöht die Latenz leicht (~100-350ms je nach Modell), aber verbessert die Antwortqualität deutlich.
                    </p>
                  </LInfoTooltip>
                </template>
              </v-switch>

              <!-- Reranker Model Selection -->
              <v-select
                v-if="formData.rag_use_cross_encoder"
                v-model="formData.rag_reranker_model"
                :items="rerankerModelItems"
                item-title="title"
                item-value="value"
                label="Reranker-Modell"
                hint="Welches Cross-Encoder-Modell für das Reranking verwendet wird"
                persistent-hint
                variant="outlined"
                density="comfortable"
                clearable
                :loading="rerankerModelsLoading"
                class="mb-4"
              >
                <template #item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template #subtitle>
                      {{ item.raw.description }}
                    </template>
                    <template #append>
                      <div class="d-flex align-center ga-1">
                        <LTag v-if="item.raw.params" variant="gray" size="sm">
                          {{ item.raw.params }}M
                        </LTag>
                        <LTag v-if="item.raw.is_default" variant="primary" size="sm">
                          Standard
                        </LTag>
                      </div>
                    </template>
                  </v-list-item>
                </template>
                <template #selection="{ item }">
                  <div class="d-flex align-center">
                    <span>{{ item.title }}</span>
                    <LTag v-if="item.raw.params" variant="gray" size="sm" class="ml-2">
                      {{ item.raw.params }}M
                    </LTag>
                    <LTag v-if="item.raw.is_default" variant="primary" size="sm" class="ml-1">
                      Standard
                    </LTag>
                  </div>
                </template>
              </v-select>

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
</template>

<script setup>
/**
 * @component RagSettingsTab
 * @description RAG (Retrieval-Augmented Generation) configuration tab.
 */

defineProps({
  /** Form data object */
  formData: {
    type: Object,
    required: true
  },
  /** Available reranker models */
  rerankerModelItems: {
    type: Array,
    default: () => []
  },
  /** Reranker models loading state */
  rerankerModelsLoading: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}
</style>
