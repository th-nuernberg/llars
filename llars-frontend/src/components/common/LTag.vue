<template>
  <span
    :class="tagClasses"
    @click="handleClick"
  >
    <LIcon v-if="prependIcon" :icon="prependIcon" :size="iconSize" />
    <slot></slot>
    <LIcon
      v-if="closable"
      icon="mdi-close"
      :size="iconSize"
      class="close-icon"
      @click.stop="$emit('close')"
    />
    <LIcon v-else-if="appendIcon" :icon="appendIcon" :size="iconSize" />
  </span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'danger', 'gray'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'small', 'md', 'default', 'lg', 'large'].includes(v)
  },
  prependIcon: {
    type: String,
    default: null
  },
  appendIcon: {
    type: String,
    default: null
  },
  closable: {
    type: Boolean,
    default: false
  },
  clickable: {
    type: Boolean,
    default: false
  }
});

defineEmits(['click', 'close']);

// Normalize size to internal format
const normalizedSize = computed(() => {
  const sizeMap = {
    small: 'sm',
    default: 'md',
    large: 'lg'
  };
  return sizeMap[props.size] || props.size;
});

const tagClasses = computed(() => {
  const classes = ['llars-tag', `llars-tag--${props.variant}`];

  if (normalizedSize.value !== 'md') {
    classes.push(`llars-tag--${normalizedSize.value}`);
  }

  if (props.clickable) {
    classes.push('llars-tag--clickable');
  }

  return classes;
});

const iconSize = computed(() => {
  const sizes = {
    sm: 12,
    md: 14,
    lg: 16
  };
  return sizes[normalizedSize.value] || 14;
});

const handleClick = (e) => {
  if (props.clickable) {
    // Click handled by parent
  }
};
</script>

<style scoped>
/* Clickable state */
.llars-tag--clickable {
  cursor: pointer;
}

.llars-tag--clickable:hover {
  filter: brightness(0.95);
  transform: translateY(-1px);
}

/* Close icon */
.close-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
  margin-left: 2px;
}

.close-icon:hover {
  opacity: 1;
}
</style>
