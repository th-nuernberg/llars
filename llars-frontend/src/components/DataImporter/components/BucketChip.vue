<template>
  <div class="bucket-chip" :style="chipStyle">
    <span class="bucket-order">{{ bucket.order || index + 1 }}</span>
    <span class="bucket-name">{{ bucket.name }}</span>
    <button v-if="editable" class="bucket-remove" @click="$emit('remove')">
      <LIcon size="14">mdi-close</LIcon>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  bucket: {
    type: Object,
    required: true,
    validator: b => b && typeof b.name === 'string'
  },
  index: { type: Number, default: 0 },
  editable: { type: Boolean, default: false }
})

defineEmits(['remove'])

const chipStyle = computed(() => {
  const color = props.bucket.color || '#D1BC8A'
  return {
    '--bucket-color': color,
    '--bucket-bg': `${color}20`
  }
})
</script>

<style scoped>
.bucket-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bucket-bg);
  border: 1px solid var(--bucket-color);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
}

.bucket-order {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--bucket-color);
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 600;
}

.bucket-name {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.bucket-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin-left: 2px;
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.bucket-remove:hover {
  opacity: 1;
}
</style>
