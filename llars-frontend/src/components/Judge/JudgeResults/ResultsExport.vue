<template>
  <v-menu>
    <template v-slot:activator="{ props }">
      <LBtn
        v-bind="props"
        variant="secondary"
        prepend-icon="mdi-download"
      >
        {{ $t('judge.results.export.title') }}
      </LBtn>
    </template>
    <v-list class="export-menu">
      <v-list-item @click="$emit('export-csv')" class="export-item">
        <template v-slot:prepend>
          <LIcon color="success">mdi-file-delimited</LIcon>
        </template>
        <v-list-item-title>{{ $t('judge.results.export.csv.title') }}</v-list-item-title>
        <v-list-item-subtitle>{{ $t('judge.results.export.csv.subtitle') }}</v-list-item-subtitle>
      </v-list-item>
      <v-list-item @click="$emit('export-json')" class="export-item">
        <template v-slot:prepend>
          <LIcon color="info">mdi-code-json</LIcon>
        </template>
        <v-list-item-title>{{ $t('judge.results.export.json.title') }}</v-list-item-title>
        <v-list-item-subtitle>{{ $t('judge.results.export.json.subtitle') }}</v-list-item-subtitle>
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
