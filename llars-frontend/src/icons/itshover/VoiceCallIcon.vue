<template>
  <svg
    class="l-its-hover__svg l-its-hover--voice-call"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Phone handset -->
    <path
      class="l-its-hover__voice-call-handset"
      d="M5 4h4l2 5l-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1 -2 2A16 16 0 0 1 2 5a2 2 0 0 1 2 -2z"
    />
    <!-- Signal waves -->
    <path class="l-its-hover__voice-call-wave l-its-hover__voice-call-wave--inner" d="M15 5a3 3 0 0 1 0 4" />
    <path class="l-its-hover__voice-call-wave l-its-hover__voice-call-wave--outer" d="M18 2a8 8 0 0 1 0 10" />
  </svg>
</template>

<style>
/* Voice Call icon - hover animation */
.l-its-hover__voice-call-handset {
  transform-origin: 12px 12px;
  transition: transform 0.25s ease;
}

.l-its-hover__voice-call-wave {
  transform-origin: 15px 7px;
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.l-its-hover__voice-call-wave--outer {
  opacity: 0.4;
}

/* Hover: handset jiggles, waves pulse */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--voice-call .l-its-hover__voice-call-handset {
  animation: llars-phone-ring 0.4s ease-in-out 2;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--voice-call .l-its-hover__voice-call-wave--inner {
  animation: llars-call-wave-pulse 1s ease-in-out infinite;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--voice-call .l-its-hover__voice-call-wave--outer {
  animation: llars-call-wave-pulse 1s ease-in-out infinite 0.2s;
}

@keyframes llars-phone-ring {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(8deg); }
  75% { transform: rotate(-8deg); }
}

@keyframes llars-call-wave-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}
</style>
