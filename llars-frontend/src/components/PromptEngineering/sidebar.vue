<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="sidebar-content">
      <v-spacer></v-spacer>

      <!-- Online Users Liste -->
      <div class="users-list">
        <h3>Online Users:</h3>
        <div v-for="(user, id) in users" :key="id" class="user-item">
          <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
          {{ user.username }}
        </div>
      </div>

      <!-- Buttons für Aktionen -->

      <!-- Zurück-Button -->
      <button
        @click="goToOverview"
        class="action-button back-button">
        <v-icon class="button-icon">mdi-arrow-left</v-icon>
        Zur Übersicht
      </button>

      <!-- Neuen Block hinzufügen -->
      <button @click="$emit('showAddBlockDialog')" class="action-button add-block-button">
        <v-icon class="button-icon"> mdi-plus</v-icon>
        Neuer Block
      </button>

      <!-- Vorschau anzeigen -->
      <button @click="showPreview = true" class="action-button preview-button">
        <v-icon class="button-icon"> mdi-eye</v-icon>
        Vorschau anzeigen
      </button>

      <!-- Download Prompt Button -->
      <button @click="downloadPrompt" class="action-button download-button">
        <v-icon class="button-icon">mdi-download</v-icon>
        Download Prompt
      </button>
    </div>

    <!-- NEU: Bereich "Geteilt mit" -->
    <div class="shared-list" v-if="sharedWith && sharedWith.length > 0">
      <h3>Geteilt mit:</h3>
        <div
          v-for="username in sharedWith"
          :key="username"
          class="shared-user-item"
        >
          <span>{{ username }}</span>

          <!-- Button nur anzeigen, wenn man der Owner ist -->
          <button
            v-if="isOwner"
            @click="unsharePrompt(username)"
            class="unshare-button"
          >
            <v-icon>mdi-close</v-icon>
          </button>
        </div>
    </div>
    <!-- ENDE NEU -->

    <!-- Preview Modal mit Teleport -->
    <Teleport to="body">
      <div v-if="showPreview" class="preview-modal">
        <div class="preview-content">
          <div class="preview-header">
            <h3>Vorschau</h3>
            <button @click="showPreview = false" class="close-button">
              <v-icon>mdi-close</v-icon>
            </button>
          </div>
          <div class="preview-body">
            <div v-for="block in sortedBlocks" :key="block.id" class="preview-block">
              <h4>{{ block.title }}</h4>
              <p>{{ getBlockContent(block) }}</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  users: {
    type: Object,
    required: true
  },
  blocks: {
    type: Array,
    required: true
  },
  // NEU: Prompt-Id und "sharedWith" als Props
  promptId: {
    type: Number,
    required: true
  },
  sharedWith: {
    type: Array,
    required: false,
    default: () => []
  },
    isOwner: {
    type: Boolean,
    required: false,
    default: false
  }
});

const emit = defineEmits(['showAddBlockDialog', 'unshare']);

const router = useRouter();
const showPreview = ref(false);


// Computed property für sortierte Blöcke
const sortedBlocks = computed(() => {
  return [...props.blocks].sort((a, b) => a.position - b.position);
});

const getBlockContent = (block) => {
  if (block.content && typeof block.content.toString === 'function') {
    return block.content.toString();
  }
  return '';
};

const downloadPrompt = () => {
  const promptData = {};

  sortedBlocks.value.forEach(block => {
    const content = getBlockContent(block).trim();
    promptData[block.title] = content;
  });

  const jsonStr = JSON.stringify(promptData, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'prompt.json';
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

const goToOverview = () => {
  router.push('/promptengineering');
};

// NEU: Methode zum Unshare
const unsharePrompt = async (usernameToUnshare) => {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/unshare`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': api_key
        },
        body: JSON.stringify({
          unshare_with: usernameToUnshare
        })
      }
    );
    const data = await response.json();

    if (!response.ok) {
      console.error('Fehler beim Unsharen:', data.error || response.statusText);
      return;
    }

    // Wenn erfolgreich, emitte ein Event zum Parent
    emit('unshare', usernameToUnshare);

  } catch (error) {
    console.error('Fehler beim Aufruf von /unshare:', error);
  }
};
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
  height: calc(100vh - 64px);
  position: fixed;
  top: 64px;
  left: 0;
  overflow-y: auto;
  padding: 20px;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-icon {
  font-size: 1.2em;
}

.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin: 20px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.preview-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.close-button {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 8px;
  color: #666;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.close-button:hover {
  color: #e74c3c;
}

.preview-block {
  margin-bottom: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.preview-block:last-child {
  margin-bottom: 0;
}

.preview-block h4 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  color: #2c3e50;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 8px;
}

.preview-block p {
  margin: 0;
  font-size: 1rem;
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
}

.action-button {
  width: 100%;
  padding: 8px 12px;
  color: white;
  border: none;
  border-radius: 16px 4px 16px 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  min-height: 40px;
}

.button-icon {
  font-size: 1.2em;
  line-height: 1;
  margin-right: 8px;
  display: flex;
  align-items: center;
}

.back-button {
  background-color: #b0ca97;
}

.back-button:hover {
  background-color: #9bb582;
}

.add-block-button {
  background-color: #81b68b;
}

.add-block-button:hover {
  background-color: #6ca077;
}

.preview-button {
  background-color: #b0ca97;
}

.preview-button:hover {
  background-color: #9bb582;
}

.download-button {
  background-color: #92b199;
}

.download-button:hover {
  background-color: #7d9c84;
}

/* Online Users styles */
.users-list {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.users-list h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 0.9rem;
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

/* NEU: Shared-list styles */
.shared-list {
  margin-top: 20px;
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.shared-list h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
}

.shared-user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.unshare-button {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  font-size: 1rem;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.unshare-button:hover {
  color: #e74c3c;
}
</style>
