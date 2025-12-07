<template>
  <v-menu>
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        color="primary"
        prepend-icon="mdi-download"
      >
        Export
      </v-btn>
    </template>
    <v-list>
      <v-list-item @click="$emit('export-csv')">
        <template v-slot:prepend>
          <v-icon>mdi-file-delimited</v-icon>
        </template>
        <v-list-item-title>Als CSV</v-list-item-title>
      </v-list-item>
      <v-list-item @click="$emit('export-json')">
        <template v-slot:prepend>
          <v-icon>mdi-code-json</v-icon>
        </template>
        <v-list-item-title>Als JSON</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
defineEmits(['export-csv', 'export-json']);
</script>

<style scoped>
</style>
