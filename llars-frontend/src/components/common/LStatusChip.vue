<template>
  <v-chip v-if="state === 'saving'" color="grey" size="x-small" variant="tonal">
    <v-progress-circular indeterminate size="12" width="2" class="mr-1" />
    Speichert...
  </v-chip>
  <v-chip v-else-if="state === 'error'" color="error" size="x-small" variant="tonal">
    <LIcon start size="x-small">mdi-alert-circle</LIcon>
    Fehler
  </v-chip>
  <v-chip v-else-if="state === 'saved'" color="success" size="x-small" variant="tonal">
    <LIcon start size="x-small">mdi-check-circle</LIcon>
    Gespeichert
  </v-chip>
</template>

<script setup>
defineProps({
  state: {
    type: String,
    default: 'idle',
    validator: (value) => ['idle', 'saving', 'saved', 'error'].includes(value)
  }
})
</script>
