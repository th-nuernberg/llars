<template>
  <div v-if="visible" class="node-edit-modal">
    <!-- Stub NodeEditModal component -->
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
const props = defineProps({
  visible: Boolean,
  node: Object,
  relationships: Array,
  placeInSector: Function,
  allActors: Array
});
const emit = defineEmits(['save', 'close', 'delete']);
</script>

<style scoped>
.node-edit-modal {
  /* basic stub styles */
}
</style>