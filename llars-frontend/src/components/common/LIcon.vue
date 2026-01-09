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
  name: {
    type: String,
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

const rawIcon = computed(() => props.icon ?? props.name ?? slotIcon.value)

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

.l-its-hover__chatbot-brain-wrinkle {
  opacity: 0.7;
}

.l-its-hover__file-fold,
.l-its-hover__markdown-fold,
.l-its-hover__latex-fold,
.l-its-hover__latex-doc-fold {
  transform-box: fill-box;
  /* Origin at the diagonal crease line (top-left of fold element) */
  transform-origin: 0% 0%;
  transform-style: preserve-3d;
  /* Ultra-smooth transition with custom cubic-bezier for paper-like feel */
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  /* DEFAULT STATE: Dog-ear / Eselsohr visible - fold shown as drawn */
  transform: perspective(200px) rotate3d(1, 1, 0, 0deg);
}

/* Crease lines - smooth fade transition */
.l-its-hover__file-crease,
.l-its-hover__markdown-crease,
.l-its-hover__latex-crease,
.l-its-hover__latex-doc-crease {
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  /* DEFAULT STATE: Crease line fully visible, thinner stroke */
  opacity: 1;
  stroke-width: 1;
}

.l-its-hover--refresh,
.l-its-hover--player {
  transform-origin: center;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon, .mobile-category-item:hover .v-icon) .l-its-hover__svg {
  transform: scale(var(--llars-icon-hover-scale, 1.04));
}

@keyframes llars-icon-spin {
  to {
    transform: rotate(360deg);
  }
}


@keyframes llars-oncoco-bars {
  0%,
  100% {
    transform: translateY(0.5px);
  }
  50% {
    transform: translateY(-0.5px);
  }
}


.v-icon.mdi-spin .l-its-hover__svg {
  animation: llars-icon-spin 0.9s linear infinite;
}


:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--home .l-its-hover__roof {
  transform: translateY(-2px);
  opacity: 0.7;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--home .l-its-hover__house {
  transform: scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--home .l-its-hover__door {
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

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--gear .l-its-hover__gear-rotator {
  transform: rotate(90deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--refresh {
  transform: rotate(180deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--clock .l-its-hover__clock-hands {
  transform: rotate(360deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--history .l-its-hover__history-circle {
  transform: rotate(-20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--history .l-its-hover__history-hand {
  transform: rotate(-20deg);
}

.l-its-hover__trash-lid-upper,
.l-its-hover__trash-lid-lower {
  transform-origin: center bottom;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--trash .l-its-hover__trash-lid-upper {
  transform: translateY(-3px) rotate(-20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--trash .l-its-hover__trash-lid-lower {
  transform: translateY(-2px) rotate(-12deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--eye .l-its-hover__eye-pupil {
  transform: scale(0.7);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--eye .l-its-hover__eye-shape {
  transform: scaleY(0.9);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--eye-off .l-its-hover__eye-parts {
  opacity: 0.6;
  transform: scale(0.98);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--eye-off .l-its-hover__eye-strike {
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--check .l-its-hover__check,
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--check-circle .l-its-hover__check {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--info .l-its-hover__info-dot {
  transform: scale(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--info .l-its-hover__info-line {
  transform: scaleY(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-triangle {
  transform: translateY(-2px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-line {
  transform: scaleY(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--alert .l-its-hover__alert-dot {
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

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--star .l-its-hover__star-fill {
  opacity: 1;
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--star .l-its-hover__star-outline {
  transform: rotate(5deg) scale(1.05);
}

.l-its-hover__lock-shackle {
  transform-origin: center bottom;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--lock .l-its-hover__lock-shackle {
  transform: translate(2px, -1px) rotate(20deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--users .l-its-hover__user-primary {
  transform: translateY(-2px) scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--users .l-its-hover__user-secondary {
  transform: translateX(1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-center {
  transform: translateY(-2px) scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-left {
  transform: translate(-1px, -1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--users-group .l-its-hover__user-right {
  transform: translate(1px, -1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--user-plus .l-its-hover__plus-sign {
  transform: scale(1.15);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--user-check .l-its-hover__user-check-mark {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--copy .l-its-hover__front-copy {
  transform: translate(2px, 2px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--arrow-back .l-its-hover__arrow-group,
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--arrow-left .l-its-hover__arrow-group {
  transform: translateX(-3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--arrow-right .l-its-hover__arrow-group {
  transform: translateX(3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--arrow-up .l-its-hover__arrow-group {
  transform: translateY(-3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--arrow-down .l-its-hover__arrow-group {
  transform: translateY(3px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--list .l-its-hover__list-line {
  transform: scaleX(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--list .l-its-hover__list-bullets {
  transform: scale(1.2);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chart-bar .l-its-hover__bar {
  transform: scaleY(1.08);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chart-bar .l-its-hover__bar-base {
  transform: scaleX(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--shield .l-its-hover__shield-check {
  transform: scale(1.1);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--player {
  transform: scale(0.9);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--x .l-its-hover__x-line--one {
  transform: rotate(12deg) scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--x .l-its-hover__x-line--two {
  transform: rotate(-12deg) scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar {
  animation: llars-oncoco-bars 0.9s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar--two {
  animation-delay: 0.12s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--oncoco .l-its-hover__oncoco-bar--three {
  animation-delay: 0.24s;
}

/* ========================================
   ANONYMIZE ICON - Mysterious spy animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__anonymize-hat {
  transform-origin: center bottom;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__anonymize-brim {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__anonymize-mask {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__anonymize-eye {
  transform-origin: center;
  transition: transform 0.25s ease;
}

.l-its-hover__anonymize-cloak {
  transform-origin: center top;
  transition: transform 0.3s ease;
}

/* Keyframe animations for continuous effects while hovering */
@keyframes llars-hat-tip {
  0%, 100% {
    transform: translateY(-0.5px) rotate(-2deg);
  }
  50% {
    transform: translateY(-1px) rotate(-4deg);
  }
}

@keyframes llars-eyes-look {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-1px);
  }
  75% {
    transform: translateX(1px);
  }
}

@keyframes llars-cloak-sway {
  0%, 100% {
    transform: scaleX(1);
  }
  50% {
    transform: scaleX(1.03);
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-hat {
  animation: llars-hat-tip 1.5s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-brim {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-mask {
  transform: scale(1.03);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-eye {
  animation: llars-eyes-look 2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--anonymize .l-its-hover__anonymize-cloak {
  animation: llars-cloak-sway 2s ease-in-out infinite;
}

/* ========================================
   ADMIN DASHBOARD ICON - Live dashboard animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__admin-screen {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__admin-gauge {
  transform-origin: center;
  transition: transform 0.3s ease;
}

.l-its-hover__admin-needle {
  transform-origin: 12px 13px;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__admin-dot {
  opacity: 0.6;
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.l-its-hover__admin-bars path {
  transform-origin: bottom;
  transition: transform 0.25s ease;
}

/* Keyframe animations for continuous effects while hovering */
@keyframes llars-needle-swing {
  0%, 100% {
    transform: rotate(20deg);
  }
  50% {
    transform: rotate(35deg);
  }
}

@keyframes llars-dot-pulse {
  0%, 100% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

@keyframes llars-bars-grow {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.12);
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-screen {
  transform: scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-gauge {
  transform: scale(0.92);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-needle {
  animation: llars-needle-swing 1.5s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-dot {
  animation: llars-dot-pulse 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-dot--two {
  animation-delay: 0.2s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-dot--three {
  animation-delay: 0.4s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-bars path {
  animation: llars-bars-grow 1s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--admin-dashboard .l-its-hover__admin-bars path:last-child {
  animation-delay: 0.15s;
}

/* ========================================
   CHATBOT MANAGE ICON - Chat + Settings animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__chatbot-manage-bubble {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__chatbot-manage-line {
  transform-origin: left center;
  transition: transform 0.25s ease;
}

.l-its-hover__chatbot-manage-gear {
  transform-origin: 20px 18px;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Keyframe animations */
@keyframes llars-gear-spin {
  0%, 100% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(45deg);
  }
}

@keyframes llars-line-type {
  0%, 100% {
    transform: scaleX(1);
  }
  50% {
    transform: scaleX(0.85);
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-manage-bubble {
  transform: scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-manage-line {
  animation: llars-line-type 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-manage-line:last-child {
  animation-delay: 0.2s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot-manage .l-its-hover__chatbot-manage-gear {
  animation: llars-gear-spin 1.5s ease-in-out infinite;
}

/* ========================================
   CHATBOT ICON - AI assistant animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__chatbot-bubble {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__chatbot-dot {
  transform-origin: center;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.l-its-hover__chatbot-sparkle {
  transform-origin: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  opacity: 0.6;
}

/* Keyframe animations */
@keyframes llars-chatbot-typing {
  0%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-2px);
    opacity: 1;
  }
}

@keyframes llars-sparkle-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes llars-bubble-float {
  0%, 100% {
    transform: translateY(-1px);
  }
  50% {
    transform: translateY(-2px);
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-bubble {
  animation: llars-bubble-float 2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-dot {
  animation: llars-chatbot-typing 0.8s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-dot--two {
  animation-delay: 0.15s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-dot--three {
  animation-delay: 0.3s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-sparkle {
  animation: llars-sparkle-pulse 0.6s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--chatbot .l-its-hover__chatbot-sparkle--two {
  animation-delay: 0.2s;
}

@keyframes llars-cursor-blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--prompt-engineering .l-its-hover__prompt-brace--left {
  transform: translateX(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--prompt-engineering .l-its-hover__prompt-brace--right {
  transform: translateX(1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--prompt-engineering .l-its-hover__prompt-cursor,
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--prompt-engineering .l-its-hover__prompt-cursor-top,
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--prompt-engineering .l-its-hover__prompt-cursor-bottom {
  animation: llars-cursor-blink 0.8s ease-in-out infinite;
}

@keyframes llars-latex-write {
  0%, 100% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  50% {
    stroke-dashoffset: -4;
    opacity: 0.7;
  }
}

@keyframes llars-sigma-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.85;
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-sigma {
  animation: llars-sigma-pulse 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-eq {
  stroke-dasharray: 8;
  animation: llars-latex-write 1.5s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-ai-sparkle {
  animation: llars-sparkle-pulse 0.6s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-ai-sparkle--two {
  animation-delay: 0.2s;
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover__file-fold,
:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover__markdown-fold,
:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover__latex-fold {
  /* HOVER STATE: Unfold - rotate around 45° diagonal crease line */
  transform: perspective(200px) rotate3d(1, 1, 0, -180deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon, .mobile-category-item:hover .v-icon) .l-its-hover__file-crease {
  /* HOVER STATE: Crease line fades as paper flattens */
  opacity: 0;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon, .mobile-category-item:hover .v-icon) .l-its-hover--latex-ai .l-its-hover__latex-crease {
  /* HOVER STATE: Crease line fades as paper flattens */
  opacity: 0;
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--latex-doc .l-its-hover__latex-doc-fold {
  /* HOVER STATE: Unfold - rotate around 45° diagonal crease line */
  transform: perspective(200px) rotate3d(1, 1, 0, -180deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon, .mobile-category-item:hover .v-icon) .l-its-hover--latex-doc .l-its-hover__latex-doc-crease {
  /* HOVER STATE: Crease line fades as paper flattens */
  opacity: 0;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-doc .l-its-hover__latex-doc-formula {
  transform: scale(1.05);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--latex-doc .l-its-hover__latex-doc-dx {
  transform: translateX(1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon, .mobile-category-item:hover .v-icon) .l-its-hover--markdown-collab .l-its-hover__markdown-crease {
  /* HOVER STATE: Crease line fades as paper flattens */
  opacity: 0;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--markdown-collab .l-its-hover__markdown-users {
  transform: translate(1px, -1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--markdown-collab .l-its-hover__markdown-hash {
  transform: scale(1.05);
}

/* ========================================
   RAG ICON - Database retrieval animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__rag-db {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__rag-db-section {
  transform-origin: center;
  transform-box: fill-box;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__rag-search {
  transform-origin: center;
  /* Smooth transition for both hover-in and hover-out */
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__rag-sparkle {
  transform-origin: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  opacity: 0.6;
}

/* Keyframe animations */
@keyframes llars-db-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes llars-db-middle-expand {
  0%, 100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(1.15);
  }
}


/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--rag .l-its-hover__rag-db {
  animation: llars-db-pulse 1.5s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--rag .l-its-hover__rag-db-section--middle {
  animation: llars-db-middle-expand 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--rag .l-its-hover__rag-search {
  /* Simple transform - smoothly animates back on hover-out */
  transform: translate(1px, 0.5px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--rag .l-its-hover__rag-sparkle {
  animation: llars-sparkle-pulse 0.6s ease-in-out infinite;
}

/* ========================================
   EVALUATION ICON - Clipboard check animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__evaluation-board {
  transform-origin: center;
  transition: transform 0.3s ease;
}

.l-its-hover__evaluation-check {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__evaluation-line {
  transform-origin: left center;
  transition: transform 0.25s ease;
}

.l-its-hover__evaluation-star {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Keyframe animations */
@keyframes llars-check-bounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.15);
  }
}

@keyframes llars-star-twinkle {
  0%, 100% {
    transform: scale(1) rotate(0deg);
  }
  50% {
    transform: scale(1.2) rotate(10deg);
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-board {
  transform: scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-check {
  animation: llars-check-bounce 0.8s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-check--two {
  animation-delay: 0.2s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation .l-its-hover__evaluation-star {
  animation: llars-star-twinkle 1s ease-in-out infinite;
}

/* ========================================
   EVALUATION ASSISTANT ICON - Clipboard + AI
   ======================================== */

.l-its-hover__assistant-board {
  transform-origin: center;
  transition: transform 0.3s ease;
}

.l-its-hover__assistant-wand {
  transform-origin: bottom left;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__assistant-star {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__assistant-sparkle {
  transform-origin: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  opacity: 0.5;
}

@keyframes llars-wand-magic {
  0%, 100% {
    transform: rotate(-5deg);
  }
  50% {
    transform: rotate(-12deg);
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-board {
  transform: scale(1.02);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-wand {
  animation: llars-wand-magic 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-star {
  animation: llars-star-twinkle 0.8s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-sparkle {
  animation: llars-sparkle-pulse 0.6s ease-in-out infinite;
  opacity: 1;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--evaluation-assistant .l-its-hover__assistant-sparkle--two {
  animation-delay: 0.2s;
}

.l-its-hover__scale-beam {
  transform-origin: center;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-beam {
  transform: rotate(8deg);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-pan--left {
  transform: translateY(-1px);
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--scale .l-its-hover__scale-pan--right {
  transform: translateY(1px);
}

/* ========================================
   WAND ICON - Magic wand animation
   Smooth transitions + continuous animations on hover
   ======================================== */

/* Base transitions for smooth return to original state */
.l-its-hover__wand-stick {
  transform-origin: bottom left;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__wand-tip {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__wand-sparkle {
  transform-origin: center;
  transition: transform 0.3s ease, opacity 0.3s ease;
  opacity: 0.5;
}

/* Keyframe animations */
@keyframes llars-wand-wave {
  0%, 100% {
    transform: rotate(-3deg);
  }
  50% {
    transform: rotate(-8deg);
  }
}

@keyframes llars-star-glow {
  0%, 100% {
    transform: scale(1.1);
    opacity: 1;
  }
  50% {
    transform: scale(1.25);
    opacity: 0.85;
  }
}

/* Hover state - initial transform + continuous animation */
:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--wand .l-its-hover__wand-stick {
  animation: llars-wand-wave 1.2s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--wand .l-its-hover__wand-tip {
  animation: llars-star-glow 0.8s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--wand .l-its-hover__wand-sparkle {
  animation: llars-sparkle-pulse 0.5s ease-in-out infinite;
  opacity: 1;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--wand .l-its-hover__wand-sparkle--two {
  animation-delay: 0.15s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--wand .l-its-hover__wand-sparkle--three {
  animation-delay: 0.3s;
}

/* Flask Icon */
@keyframes llars-flask-bubble {
  0% {
    transform: translateY(0);
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateY(-4px);
    opacity: 0;
  }
}

@keyframes llars-flask-simmer {
  0%, 100% {
    transform: scaleX(1);
  }
  50% {
    transform: scaleX(1.02);
  }
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--flask .l-its-hover__flask-body {
  animation: llars-flask-simmer 0.8s ease-in-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--flask .l-its-hover__flask-bubble {
  animation: llars-flask-bubble 1.2s ease-out infinite;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--flask .l-its-hover__flask-bubble--two {
  animation-delay: 0.3s;
}

:is(.v-icon:hover, .feature-card:hover .v-icon, .category-item:hover .v-icon) .l-its-hover--flask .l-its-hover__flask-bubble--three {
  animation-delay: 0.6s;
}

/* ========================================
   SUN ICON - Light Mode
   Smooth interruptible transitions (no keyframes for main effects)
   ======================================== */
.l-its-hover__sun-center {
  transform-origin: center;
  /* Smooth transition that can reverse mid-animation */
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__sun-rays {
  transform-origin: center;
  /* Smooth transition that can reverse mid-animation */
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Universal hover selector - works in menus, cards, buttons, etc. */
:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--sun .l-its-hover__sun-center {
  /* Simple scale transform - smooth and interruptible */
  transform: scale(1.15);
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--sun .l-its-hover__sun-rays {
  transform: rotate(45deg);
}

/* ========================================
   MOON ICON - Dark Mode
   Smooth interruptible transitions
   ======================================== */
.l-its-hover__moon-crescent {
  transform-origin: center;
  /* Smooth transition that can reverse mid-animation */
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__moon-star {
  transform-origin: center;
  /* Smooth transition for stars */
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
  opacity: 0.6;
}

/* Universal hover selector */
:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--moon .l-its-hover__moon-crescent {
  transform: rotate(-10deg) scale(1.05);
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--moon .l-its-hover__moon-star {
  /* Stars brighten and scale - smooth and interruptible */
  transform: scale(1.25);
  opacity: 1;
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--moon .l-its-hover__moon-star--two {
  /* Slightly different scale for variety */
  transform: scale(1.35);
  transition-delay: 0.05s;
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--moon .l-its-hover__moon-star--three {
  transform: scale(1.2);
  transition-delay: 0.1s;
}

/* ========================================
   SYSTEM THEME ICON - Auto/System
   Smooth interruptible transitions
   ======================================== */
.l-its-hover__system-monitor {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.l-its-hover__system-sun {
  transform-origin: center;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}

.l-its-hover__system-moon {
  transform-origin: center;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}

.l-its-hover__system-divider {
  transition: opacity 0.3s ease;
}

.l-its-hover__system-content {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Universal hover selector */
:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--system-theme .l-its-hover__system-monitor {
  transform: scale(1.05);
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--system-theme .l-its-hover__system-sun {
  /* Sun scales up on hover - smooth and interruptible */
  transform: scale(1.2);
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--system-theme .l-its-hover__system-moon {
  /* Moon scales up on hover - smooth and interruptible */
  transform: scale(1.15);
}

:is(
  .v-icon:hover,
  .feature-card:hover .v-icon,
  .category-item:hover .v-icon,
  .mobile-category-item:hover .v-icon,
  .theme-option:hover .v-icon,
  .theme-toggle-btn:hover .v-icon,
  button:hover .v-icon,
  [role="button"]:hover .v-icon
) .l-its-hover--system-theme .l-its-hover__system-divider {
  opacity: 0.3;
}
</style>
