<template>
  <v-menu>
    <template v-slot:activator="{ props }">
      <LBtn
        v-bind="props"
        variant="secondary"
        prepend-icon="mdi-download"
      >
        Export
      </LBtn>
    </template>
    <v-list class="export-menu">
      <v-list-item @click="$emit('export-csv')" class="export-item">
        <template v-slot:prepend>
          <v-icon color="success">mdi-file-delimited</v-icon>
        </template>
        <v-list-item-title>Als CSV exportieren</v-list-item-title>
        <v-list-item-subtitle>Tabellenformat für Excel</v-list-item-subtitle>
      </v-list-item>
      <v-list-item @click="$emit('export-json')" class="export-item">
        <template v-slot:prepend>
          <v-icon color="info">mdi-code-json</v-icon>
        </template>
        <v-list-item-title>Als JSON exportieren</v-list-item-title>
        <v-list-item-subtitle>Strukturierte Daten</v-list-item-subtitle>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
defineEmits(['export-csv', 'export-json']);
</script>

<style scoped>
.export-menu {
  border-radius: var(--llars-radius-sm);
  overflow: hidden;
}

.export-item {
  transition: background-color 0.2s ease;
}

.export-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}
</style>
