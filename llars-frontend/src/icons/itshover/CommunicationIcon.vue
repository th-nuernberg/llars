<template>
  <svg
    class="l-its-hover__svg l-its-hover--communication"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Chat bubble -->
    <path
      class="l-its-hover__communication-bubble"
      d="M4 6h12a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H8l-3 3v-3H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"
    />
    <!-- Signal waves (voice/call indicator) -->
    <path class="l-its-hover__communication-wave l-its-hover__communication-wave--inner" d="M19 4a4 4 0 0 1 0 6" />
    <path class="l-its-hover__communication-wave l-its-hover__communication-wave--outer" d="M21 2a7 7 0 0 1 0 10" />
  </svg>
</template>

<style>
/* Communication icon - hover animation */
.l-its-hover__communication-bubble {
  transition: transform 0.25s ease;
  transform-origin: center;
}

.l-its-hover__communication-wave {
  transition: opacity 0.25s ease, transform 0.25s ease;
  transform-origin: 19px 7px;
}

.l-its-hover__communication-wave--outer {
  opacity: 0.5;
}

/* Hover: bubble shifts slightly, waves pulse */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--communication .l-its-hover__communication-bubble {
  transform: translateX(-1px);
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--communication .l-its-hover__communication-wave--inner {
  animation: llars-wave-pulse 1s ease-in-out infinite;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--communication .l-its-hover__communication-wave--outer {
  animation: llars-wave-pulse 1s ease-in-out infinite 0.2s;
}

@keyframes llars-wave-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}
</style>
