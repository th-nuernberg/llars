<!--
  ChatbotEditor - Main Dialog Component

  Comprehensive chatbot configuration dialog with multiple tabs:
  - General: Basic settings (name, icon, color, status)
  - LLM: Model selection, prompts
  - RAG: Retrieval-Augmented Generation settings
  - Agent: Advanced agent modes (ACT, ReAct, ReflAct)
  - Collections: RAG collection assignment
  - Web Crawler: Automatic website scraping

  @component ChatbotEditor
  @example
  <ChatbotEditor
    v-model="dialogOpen"
    :chatbot="selectedChatbot"
    :collections="availableCollections"
    :is-edit="true"
    @save="handleSave"
  />
-->
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
          <LIcon class="mr-2">{{ isEdit ? 'mdi-pencil' : 'mdi-plus' }}</LIcon>
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
          <LIcon start>mdi-information</LIcon>
          Allgemein
        </v-tab>
        <v-tab value="llm">
          <LIcon start>mdi-brain</LIcon>
          LLM-Einstellungen
        </v-tab>
        <v-tab value="rag">
          <LIcon start>mdi-magnify</LIcon>
          RAG
        </v-tab>
        <v-tab v-if="canUseAdvancedModes" value="agent">
          <LIcon start>mdi-robot-outline</LIcon>
          Agent
          <LTag variant="warning" size="sm" class="ml-2">PRO</LTag>
        </v-tab>
        <v-tab value="collections">
          <LIcon start>mdi-folder-multiple</LIcon>
          Collections
        </v-tab>
        <v-tab value="webcrawler">
          <LIcon start>mdi-spider-web</LIcon>
          Web Crawler
        </v-tab>
      </v-tabs>

      <!-- Content -->
      <v-card-text class="chatbot-editor-body">
        <v-window v-model="activeTab">
          <!-- General Tab -->
          <v-window-item value="general" eager>
            <GeneralTab
              :form-data="formData"
              :icon-options="iconOptions"
              :rules="rules"
              :is-edit="isEdit"
              :generating-icon="generatingIcon"
              :generating-color="generatingColor"
              @generate-icon="generateIcon"
              @generate-color="generateColor"
            />
          </v-window-item>

          <!-- LLM Settings Tab -->
          <v-window-item value="llm" eager>
            <LlmSettingsTab
              :form-data="formData"
              :prompt-templates="promptTemplates"
              @apply-template="applyPromptTemplate"
              @update-line-count="updateLineCount"
            />
          </v-window-item>

          <!-- RAG Settings Tab -->
          <v-window-item value="rag" eager>
            <RagSettingsTab
              :form-data="formData"
              :reranker-model-items="rerankerModelItems"
              :reranker-models-loading="rerankerModelsLoading"
            />
          </v-window-item>

          <!-- Agent Mode Tab (PRO) -->
          <v-window-item v-if="canUseAdvancedModes" value="agent" eager>
            <AgentModeTab :form-data="formData" />
          </v-window-item>

          <!-- Collections Tab -->
          <v-window-item value="collections" eager>
            <CollectionsTab
              :collections="collections"
              :selected-collections="selectedCollectionsForUpload"
              :is-collection-selected="isCollectionSelected"
              @toggle-collection="toggleCollection"
              @open-upload="openUploadDialogForCollection"
            />
          </v-window-item>

          <!-- Web Crawler Tab -->
          <v-window-item value="webcrawler" eager>
            <CrawlerTab
              :crawler-urls="crawlerUrls"
              :crawler-max-pages="crawlerMaxPages"
              :crawler-max-depth="crawlerMaxDepth"
              :crawling="crawling"
              :crawl-status="crawlStatus"
              :crawl-progress="crawlProgress"
              :crawled-pages="crawledPages"
              :has-valid-crawler-urls="hasValidCrawlerUrls"
              @update:crawler-urls="crawlerUrls = $event"
              @update:crawler-max-pages="crawlerMaxPages = $event"
              @update:crawler-max-depth="crawlerMaxDepth = $event"
              @start-crawl="startCrawlForChatbot"
            />
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
/**
 * @component ChatbotEditor
 * @description Main chatbot configuration dialog with tabbed interface.
 */
import { computed, ref, watch } from 'vue';
import axios from 'axios';
import DocumentUploadDialog from '@/components/RAG/DocumentUploadDialog.vue';
import { usePermissions } from '@/composables/usePermissions';
import {
  useChatbotForm,
  useChatbotCrawler
} from './ChatbotEditor/composables';
import {
  GeneralTab,
  LlmSettingsTab,
  RagSettingsTab,
  AgentModeTab,
  CollectionsTab,
  CrawlerTab
} from './ChatbotEditor/tabs';

// ===== Props & Emits =====
const props = defineProps({
  /** Dialog visibility (v-model) */
  modelValue: Boolean,
  /** Chatbot object to edit (null for new) */
  chatbot: Object,
  /** Available RAG collections */
  collections: {
    type: Array,
    default: () => []
  },
  /** Whether editing an existing chatbot */
  isEdit: Boolean
});

const emit = defineEmits([
  'update:modelValue',
  'save',
  'collection-created',
  'documents-uploaded'
]);

// ===== Composables =====
const { hasPermission } = usePermissions();
const canUseAdvancedModes = computed(() => hasPermission('feature:chatbots:advanced'));

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

// ===== Local State =====
const uploadDialogOpen = ref(false);
const uploadInitialCollectionId = ref(null);
const generatingIcon = ref(false);
const generatingColor = ref(false);

// ===== Reranker Models =====
const rerankerModels = ref([]);
const rerankerModelsLoading = ref(false);

const rerankerModelItems = computed(() => {
  const items = Array.isArray(rerankerModels.value) ? [...rerankerModels.value] : [];

  const defaultModel = items.find(m => m.is_default);
  const defaultLabel = defaultModel ? `System-Standard (${defaultModel.display_name})` : 'System-Standard';
  const defaultParams = defaultModel?.max_output_tokens || null;

  return [
    {
      title: defaultLabel,
      value: null,
      description: 'Verwendet das systemweite Standard-Reranker-Modell',
      is_default: true,
      params: defaultParams
    },
    ...items.map(m => ({
      title: m.display_name || m.model_id,
      value: m.model_id,
      description: m.description || '',
      is_default: false,
      params: m.max_output_tokens || null
    }))
  ];
});

async function loadRerankerModels() {
  rerankerModelsLoading.value = true;
  try {
    const response = await axios.get('/api/llm/models?active_only=true&model_type=reranker');
    if (response.data?.success) {
      rerankerModels.value = response.data.models || [];
    } else {
      rerankerModels.value = [];
    }
  } catch (error) {
    console.warn('[ChatbotEditor] Error loading reranker models:', error);
    rerankerModels.value = [];
  } finally {
    rerankerModelsLoading.value = false;
  }
}

// ===== Collections =====
const selectedCollectionsForUpload = computed(() => {
  const ids = formData.value?.collection_ids || [];
  return (props.collections || []).filter(c => ids.includes(c.id));
});

function openUploadDialogForCollection(collectionId) {
  uploadInitialCollectionId.value = collectionId;
  uploadDialogOpen.value = true;
}

function handleDocumentsUploaded() {
  emit('documents-uploaded', { collection_id: uploadInitialCollectionId.value });
}

// ===== Dialog Actions =====
function closeDialog() {
  emit('update:modelValue', false);
  activeTab.value = 'general';
  resetCrawler();
}

function saveChanges() {
  const dataToSave = prepareForSave(props.isEdit, props.chatbot?.id);
  emit('save', dataToSave);
}

// ===== Crawler =====
async function startCrawlForChatbot() {
  const chatbotName = formData.value.display_name || formData.value.name || 'Chatbot';

  await startCrawl(chatbotName, {
    onComplete: (data) => {
      if (data.collection_id && !formData.value.collection_ids.includes(data.collection_id)) {
        formData.value.collection_ids.push(data.collection_id);
      }

      emit('collection-created', data.collection_id);
    }
  });
}

// ===== Icon & Color Generation =====
async function generateIcon() {
  if (!props.chatbot?.id) {
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
    const randomIndex = Math.floor(Math.random() * iconOptions.value.length);
    formData.value.icon = iconOptions.value[randomIndex].value;
  } finally {
    generatingIcon.value = false;
  }
}

async function generateColor() {
  if (!props.chatbot?.id) {
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
    formData.value.color = generateRandomColor();
  } finally {
    generatingColor.value = false;
  }
}

function generateRandomColor() {
  const hue = Math.floor(Math.random() * 360);
  const saturation = 60 + Math.floor(Math.random() * 20);
  const lightness = 45 + Math.floor(Math.random() * 15);
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

// ===== Watchers =====
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

watch(() => props.modelValue, (isOpen) => {
  if (!isOpen) {
    rerankerModels.value = [];
    return;
  }
  loadRerankerModels();
}, { immediate: true });
</script>

<style scoped>
@import './ChatbotEditor/styles/ChatbotEditor.css';
</style>
