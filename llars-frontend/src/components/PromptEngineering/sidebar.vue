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
import { ref, computed } from 'vue'; // computed hinzufügen
import { useRouter } from 'vue-router';

const props = defineProps({
  users: {
    type: Object,
    required: true
  },
  blocks: {
    type: Array,
    required: true
  }
});

const router = useRouter();

defineEmits(['showAddBlockDialog']);

const showPreview = ref(false);

// Neue computed property für sortierte Blöcke
const sortedBlocks = computed(() => {
  return [...props.blocks].sort((a, b) => a.position - b.position);
});

const getBlockContent = (block) => {
  if (block.content && typeof block.content.toString === 'function') {
    return block.content.toString();
  }
  return '';
};

// Füge diese Funktion im script setup-Bereich hinzu
const downloadPrompt = () => {
  // Erstelle ein Objekt aus den sortierten Blöcken
  const promptData = {};

  sortedBlocks.value.forEach(block => {
    // Hole den Inhalt des Blocks und entferne zusätzliche Leerzeichen/Zeilenumbrüche am Anfang und Ende
    const content = getBlockContent(block).trim();

    // Füge den Block zum promptData Objekt hinzu
    promptData[block.title] = content;
  });

  // Konvertiere das Objekt zu einem formatierten JSON-String
  const jsonStr = JSON.stringify(promptData, null, 2);

  // Erstelle einen Blob mit dem JSON-Inhalt
  const blob = new Blob([jsonStr], { type: 'application/json' });

  // Erstelle eine URL für den Blob
  const url = window.URL.createObjectURL(blob);

  // Erstelle ein unsichtbares <a> Element für den Download
  const a = document.createElement('a');
  a.href = url;
  a.download = 'prompt.json'; // Name der Datei, die heruntergeladen wird

  // Füge das Element zum DOM hinzu und klicke es programmatisch
  document.body.appendChild(a);
  a.click();

  // Cleanup: Entferne das Element und die URL
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};


const goToOverview = () => {
  router.push('/promptengineering');
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
  min-height: 40px; /* Einheitliche Höhe für alle Buttons */
}

.button-icon {
  font-size: 1.2em;
  line-height: 1;
  margin-right: 8px;
  display: flex;
  align-items: center;
}

.add-block-button {
  background-color: #4caf50;
}

.add-block-button:hover {
  background-color: #45a049;
}

.preview-button {
  background-color: #2196f3;
}

.preview-button:hover {
  background-color: #1976d2;
}

.download-button {
  background-color: #673ab7;
}

.download-button:hover {
  background-color: #5e35b1;
}

.back-button {
  background-color: #9e9e9e; /* leichtes Grau oder was du möchtest */
}
.back-button:hover {
  background-color: #7e7e7e;
}


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

</style>
