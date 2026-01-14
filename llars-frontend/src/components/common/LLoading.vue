<template>
  <div class="l-loading" :class="sizeClasses" role="status" :aria-live="label ? 'polite' : 'off'">
    <div class="l-loading__scene" aria-hidden="true">
      <div class="l-loading__sheet l-loading__sheet--back"></div>
      <div class="l-loading__sheet l-loading__sheet--front">
        <span class="l-loading__line l-loading__line--1" />
        <span class="l-loading__line l-loading__line--2" />
        <span class="l-loading__line l-loading__line--3" />
        <span class="l-loading__line l-loading__line--4" />
        <span class="l-loading__progress"></span>
      </div>
    </div>
    <div v-if="label" class="l-loading__label">{{ label }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  label: {
    type: String,
    default: ''
  }
})

const sizeClasses = computed(() => ({
  'l-loading--sm': props.size === 'sm',
  'l-loading--lg': props.size === 'lg'
}))
</script>

<style scoped>
.l-loading {
  --l-loading-scale: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.l-loading--sm {
  --l-loading-scale: 0.85;
}

.l-loading--lg {
  --l-loading-scale: 1.15;
}

.l-loading__scene {
  position: relative;
  width: calc(140px * var(--l-loading-scale));
  height: calc(96px * var(--l-loading-scale));
}

.l-loading__sheet {
  position: absolute;
  inset: 0;
  border-radius: 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  background: rgba(var(--v-theme-surface), 0.9);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.l-loading__sheet--back {
  transform: translate(calc(10px * var(--l-loading-scale)), calc(10px * var(--l-loading-scale)));
  opacity: 0.5;
}

.l-loading__sheet--front {
  overflow: hidden;
  animation: llars-loading-float 2.2s ease-in-out infinite;
}

.l-loading__sheet--front::after {
  content: '';
  position: absolute;
  top: 0;
  left: -60%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(136, 196, 200, 0.25), transparent);
  animation: llars-loading-sweep 1.6s ease-in-out infinite;
}

.l-loading__line {
  position: absolute;
  left: calc(16px * var(--l-loading-scale));
  height: calc(6px * var(--l-loading-scale));
  border-radius: 999px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  transform-origin: left;
  animation: llars-loading-line 1.4s ease-in-out infinite;
}

.l-loading__line--1 {
  top: calc(18px * var(--l-loading-scale));
  width: 68%;
}

.l-loading__line--2 {
  top: calc(34px * var(--l-loading-scale));
  width: 82%;
  animation-delay: 0.15s;
}

.l-loading__line--3 {
  top: calc(50px * var(--l-loading-scale));
  width: 54%;
  animation-delay: 0.3s;
}

.l-loading__line--4 {
  top: calc(66px * var(--l-loading-scale));
  width: 74%;
  animation-delay: 0.45s;
}

.l-loading__progress {
  position: absolute;
  left: calc(16px * var(--l-loading-scale));
  right: calc(16px * var(--l-loading-scale));
  bottom: calc(14px * var(--l-loading-scale));
  height: calc(6px * var(--l-loading-scale));
  border-radius: 999px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  overflow: hidden;
}

.l-loading__progress::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 40%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--llars-primary), var(--llars-accent));
  animation: llars-loading-progress 1.4s ease-in-out infinite;
}

.l-loading__label {
  font-size: 0.85rem;
  opacity: 0.75;
}

@keyframes llars-loading-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

@keyframes llars-loading-sweep {
  0% {
    transform: translateX(-20%);
    opacity: 0;
  }
  40% {
    opacity: 0.4;
  }
  100% {
    transform: translateX(200%);
    opacity: 0;
  }
}

@keyframes llars-loading-line {
  0%,
  100% {
    transform: scaleX(0.65);
    opacity: 0.5;
  }
  50% {
    transform: scaleX(1);
    opacity: 0.9;
  }
}

@keyframes llars-loading-progress {
  0%,
  100% {
    transform: translateX(-10%);
  }
  50% {
    transform: translateX(150%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .l-loading__sheet--front,
  .l-loading__sheet--front::after,
  .l-loading__line,
  .l-loading__progress::after {
    animation: none;
  }
}
</style>
