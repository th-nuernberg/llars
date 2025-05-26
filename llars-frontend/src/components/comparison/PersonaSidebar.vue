<template>
  <v-card class="persona-sidebar" elevation="1">
    <div class="sidebar-content">
      <template v-if="loading">
        <div class="pa-4">
          <v-skeleton-loader type="paragraph"></v-skeleton-loader>
        </div>
      </template>

      <template v-else-if="!persona">
        <div class="pa-4">
          <v-alert type="info" variant="tonal" dense>
            Bitte starten Sie eine neue Session.
          </v-alert>
        </div>
      </template>

      <template v-else>
        <div class="pa-4">
          <h2 class="font-weight-bold mb-3">{{ persona.name }}</h2>

          <div class="persona-details">
            <div class="steckbrief-section">
              <div 
                v-for="(val, key) in persona.properties?.Steckbrief"
                :key="key"
                class="steckbrief-item"
              >
                <span class="bullet">•</span>
                <span class="item-content">
                  <strong>{{ key }}:</strong> {{ val }}
                </span>
              </div>
            </div>

            <div class="section">
              <h3 class="section-title">Hauptanliegen</h3>
              <p class="section-content">{{ persona.properties?.Hauptanliegen }}</p>
            </div>

            <div v-if="persona.properties.Nebenanliegen?.length" class="section">
              <h3 class="section-title">Nebenanliegen</h3>
              <ul class="nebenanliegen-list">
                <li v-for="(n, i) in persona.properties?.Nebenanliegen" :key="i">{{ n }}</li>
              </ul>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="sidebar-footer">
      <v-divider />
      <div class="pa-3">
        <v-btn
          size="small"
          block
          variant="outlined"
          color="primary"
          prepend-icon="mdi-lightbulb"
          @click="$emit('suggestion')"
          :disabled="loading || generatingSuggestion || inputDisabled"
          :loading="generatingSuggestion"
        >
          Vorschlag generieren
        </v-btn>
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  persona?: any;
  loading: boolean;
  generatingSuggestion?: boolean;
  inputDisabled?: boolean;
}>();

defineEmits<{
  (e: 'suggestion'): void;
}>();
</script>

<style scoped>
.persona-sidebar {
  height: calc(100vh - 264px);
  display: flex;
  flex-direction: column;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.sidebar-footer {
  flex-shrink: 0;
}

.persona-details {
  margin-top: 8px;
}

.steckbrief-section {
  margin-bottom: 20px;
}

.steckbrief-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  line-height: 1.4;
}

.bullet {
  margin-right: 8px;
  margin-top: 2px;
  flex-shrink: 0;
}

.item-content {
  flex: 1;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.87);
}

.section-content {
  margin: 0;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.7);
}

.nebenanliegen-list {
  margin: 0;
  padding-left: 16px;
  line-height: 1.5;
  color: rgba(0, 0, 0, 0.7);
}

.nebenanliegen-list li {
  margin-bottom: 4px;
}

.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
