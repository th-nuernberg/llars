<template>
  <v-icon v-bind="iconAttrs" :icon="resolvedIcon" />
</template>

<script setup>
import { computed, useAttrs, useSlots } from 'vue'
import { resolveIconComponent } from '@/icons/itshover'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  icon: {
    type: [String, Object, Function, Array],
    default: undefined
  },
  size: {
    type: [String, Number],
    default: undefined
  },
  color: {
    type: String,
    default: undefined
  }
})

const attrs = useAttrs()
const slots = useSlots()

const slotIcon = computed(() => {
  const nodes = slots.default?.() || []
  for (const node of nodes) {
    if (typeof node.children === 'string') {
      const text = node.children.trim()
      if (text) return text
    }
  }
  return undefined
})

const rawIcon = computed(() => props.icon ?? slotIcon.value)

const parsedIcon = computed(() => {
  if (typeof rawIcon.value !== 'string') {
    return { name: rawIcon.value, spin: false }
  }
  const parts = rawIcon.value.split(/\s+/).filter(Boolean)
  const spin = parts.includes('mdi-spin')
  const name = parts.find((part) => part !== 'mdi-spin') || parts[0]
  return { name, spin }
})

const resolvedIcon = computed(() => {
  if (typeof parsedIcon.value.name === 'string') {
    return resolveIconComponent(parsedIcon.value.name)
  }
  return parsedIcon.value.name
})

const iconAttrs = computed(() => {
  const { icon: _icon, color: _color, size: _size, class: className, ...rest } = attrs
  return {
    ...rest,
    icon: resolvedIcon.value,
    color: props.color ?? _color,
    size: props.size ?? _size,
    class: [className, parsedIcon.value.spin ? 'mdi-spin' : null]
  }
})
</script>

<style>
.l-its-hover__svg {
  width: 1em;
  height: 1em;
  display: block;
  transition: transform 0.25s ease;
}

.l-its-hover__svg [class^='l-its-hover__'] {
  transform-box: fill-box;
  transform-origin: center;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.l-its-hover__file-fold,
.l-its-hover__markdown-fold,
.l-its-hover__latex-fold {
  transform-origin: 0% 100%;
}

.l-its-hover--refresh,
.l-its-hover--player {
  transform-origin: center;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover__svg {
  transform: scale(var(--llars-icon-hover-scale, 1.04));
}

@keyframes llars-icon-spin {
  to {
    transform: rotate(360deg);
  }
}

.l-its-hover__latex-spark {
  transform-origin: center;
}

@keyframes llars-oncoco-bars {
  0%,
  100% {
    transform: translateY(1px);
  }
  50% {
    transform: translateY(-1.5px);
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark {
  animation: llars-sparkle 1s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark path {
  animation: llars-sparkle-flicker 1s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark path:nth-child(2) {
  animation-delay: 0.12s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark path:nth-child(3) {
  animation-delay: 0.24s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark path:nth-child(4) {
  animation-delay: 0.36s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-spark path:nth-child(5) {
  animation-delay: 0.48s;
}

.v-icon.mdi-spin .l-its-hover__svg {
  animation: llars-icon-spin 0.9s linear infinite;
}

@keyframes llars-sparkle {
  0% {
    transform: scale(0.95);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.08);
    opacity: 1;
  }
  100% {
    transform: scale(0.95);
    opacity: 0.7;
  }
}

@keyframes llars-sparkle-flicker {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--home .l-its-hover__roof {
  transform: translateY(-2px);
  opacity: 0.7;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--home .l-its-hover__house {
  transform: scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--home .l-its-hover__door {
  transform-origin: center bottom;
  transform: scaleY(1.12);
}

.l-its-hover__gear-rotator,
.l-its-hover--refresh,
.l-its-hover__clock-hands,
.l-its-hover__history-circle,
.l-its-hover__history-hand {
  transition: transform 0.35s ease;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--gear .l-its-hover__gear-rotator {
  transform: rotate(90deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--refresh {
  transform: rotate(180deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--clock .l-its-hover__clock-hands {
  transform: rotate(360deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--history .l-its-hover__history-circle {
  transform: rotate(-20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--history .l-its-hover__history-hand {
  transform: rotate(-20deg);
}

.l-its-hover__trash-lid-upper,
.l-its-hover__trash-lid-lower {
  transform-origin: center bottom;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--trash .l-its-hover__trash-lid-upper {
  transform: translateY(-3px) rotate(-20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--trash .l-its-hover__trash-lid-lower {
  transform: translateY(-2px) rotate(-12deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--eye .l-its-hover__eye-pupil {
  transform: scale(0.7);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--eye .l-its-hover__eye-shape {
  transform: scaleY(0.9);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--eye-off .l-its-hover__eye-parts {
  opacity: 0.6;
  transform: scale(0.98);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--eye-off .l-its-hover__eye-strike {
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--check .l-its-hover__check,
:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--check-circle .l-its-hover__check {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--info .l-its-hover__info-dot {
  transform: scale(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--info .l-its-hover__info-line {
  transform: scaleY(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-triangle {
  transform: translateY(-2px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-line {
  transform: scaleY(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-dot {
  transform: scale(1.2);
  opacity: 0.7;
}

.l-its-hover__star-fill {
  transform-origin: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.l-its-hover__star-outline {
  transform-origin: center;
  transition: transform 0.3s ease;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--star .l-its-hover__star-fill {
  opacity: 1;
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--star .l-its-hover__star-outline {
  transform: rotate(5deg) scale(1.05);
}

.l-its-hover__lock-shackle {
  transform-origin: center bottom;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--lock .l-its-hover__lock-shackle {
  transform: translate(2px, -1px) rotate(20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--users .l-its-hover__user-primary {
  transform: translateY(-2px) scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--users .l-its-hover__user-secondary {
  transform: translateX(1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-center {
  transform: translateY(-2px) scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-left {
  transform: translate(-1px, -1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-right {
  transform: translate(1px, -1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--user-plus .l-its-hover__plus-sign {
  transform: scale(1.15);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--user-check .l-its-hover__user-check-mark {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--copy .l-its-hover__front-copy {
  transform: translate(2px, 2px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--arrow-back .l-its-hover__arrow-group,
:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--arrow-left .l-its-hover__arrow-group {
  transform: translateX(-3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--arrow-right .l-its-hover__arrow-group {
  transform: translateX(3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--arrow-up .l-its-hover__arrow-group {
  transform: translateY(-3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--arrow-down .l-its-hover__arrow-group {
  transform: translateY(3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--list .l-its-hover__list-line {
  transform: scaleX(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--list .l-its-hover__list-bullets {
  transform: scale(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--chart-bar .l-its-hover__bar {
  transform: scaleY(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--chart-bar .l-its-hover__bar-base {
  transform: scaleX(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--shield .l-its-hover__shield-check {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--player {
  transform: scale(0.9);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--x .l-its-hover__x-line--one {
  transform: rotate(12deg) scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--x .l-its-hover__x-line--two {
  transform: rotate(-12deg) scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar {
  animation: llars-oncoco-bars 0.9s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar--two {
  animation-delay: 0.12s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar--three {
  animation-delay: 0.24s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-hat {
  transform: translateY(-1px) rotate(-4deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-mask {
  transform: scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-badge {
  transform: translateY(-1px) scale(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-bar {
  transform: scaleY(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-bar--two {
  transform: scaleY(1.35);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-gear {
  transform: rotate(90deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-antenna {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-sigma {
  transform: translateX(1px) scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-eq {
  transform: scaleX(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover__file-fold,
:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover__markdown-fold,
:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover__latex-fold {
  transform: rotate(-20deg) translate(2px, -2px) scale(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--markdown-collab .l-its-hover__markdown-link {
  transform: translateX(1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--markdown-collab .l-its-hover__markdown-hash {
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-check {
  transform: scale(1.15);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-clip {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-wand {
  transform: rotate(12deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-db-top {
  transform: translateY(-1px);
}

.l-its-hover__scale-beam {
  transform-origin: center;
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-beam {
  transform: rotate(8deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-pan--left {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-pan--right {
  transform: translateY(1px);
}
</style>
