<template>
  <v-card class="pa-4" elevation="1">
    <template v-if="loading">
      <v-skeleton-loader type="paragraph"></v-skeleton-loader>
    </template>

    <template v-else-if="!persona">
      <v-alert type="info" variant="tonal" dense>
        Bitte starten Sie eine neue Session.
      </v-alert>
    </template>

    <template v-else>
      <h2 class="font-weight-bold">{{ persona.name }}</h2>

      <div>
        <v-list density="compact" class="pl-0">
          <v-list-item
            v-for="(val, key) in persona.properties?.Steckbrief"
            :key="key"
            class="px-0"
            style="margin-bottom: -10px;"
          >
            <template v-slot:prepend>
              <span class="mr-2">•</span>
            </template>
            <v-list-item-title>
              <strong>{{ key }}:</strong> {{ val }}
            </v-list-item-title>
          </v-list-item>
        </v-list>

        <h3 class="mt-4 mb-1">Hauptanliegen</h3>
        <p>{{ persona.properties?.Hauptanliegen }}</p>

        <template v-if="persona.properties.Nebenanliegen?.length">
          <h3 class="mt-4 mb-1">Nebenanliegen</h3>
          <ul class="pl-4">
            <li v-for="(n, i) in persona.properties?.Nebenanliegen" :key="i">{{ n }}</li>
          </ul>
        </template>
      </div>
    </template>

    <!-- Action-Buttons -->
    <v-divider class="my-4" />

    <v-btn
      class="mt-2"
      block
      variant="outlined"
      color="primary"
      prepend-icon="mdi-lightbulb"
      @click="$emit('suggestion')"
      :disabled="loading"
    >
      Vorschlag generieren
      <v-progress-circular
        indeterminate
        size="16"
        width="2"
        class="ml-2"
        v-if="loading"
      />
    </v-btn>
  </v-card>
</template>

<script setup lang="ts">
defineProps<{
  persona?: any;
  loading: boolean;
}>();

defineEmits<{
  (e: 'suggestion'): void;
}>();
</script>
