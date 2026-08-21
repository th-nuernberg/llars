<template>
  <!--
    Welcome / greeting icon — a waving hand with motion arcs. Used for the
    "Willkommen" mail template (admin Mail-Center) and anywhere a friendly
    greeting is needed. itshover style: 24×24, currentColor stroke, animates
    on hover (hand tilts, arcs pulse). Registered as 'welcome' + alias
    mdi-hand-wave / llars:welcome.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--welcome"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <g class="l-its-hover__welcome-hand">
      <!-- four fingers (staggered, middle longest) -->
      <path d="M6.6 12.2V8.2a1 1 0 0 1 2 0v3.2" />
      <path d="M8.6 11.4V6.2a1 1 0 0 1 2 0v5" />
      <path d="M10.6 11V5.6a1 1 0 0 1 2 0V11" />
      <path d="M12.6 11.4V7.4a1 1 0 0 1 2 0v4" />
      <!-- thumb sweeping down + palm/wrist into the forearm -->
      <path d="M6.6 12.2 5.2 10.6a1.1 1.1 0 0 0-1.8 1.2l2.3 4.1A5.5 5.5 0 0 0 10.4 22h1.2a5 5 0 0 0 5-5v-4.6" />
    </g>
    <!-- waving motion arcs (upper right) -->
    <path class="l-its-hover__welcome-wave l-its-hover__welcome-wave--inner" d="M17.6 4.8A2.6 2.6 0 0 1 20.2 7.4" />
    <path class="l-its-hover__welcome-wave l-its-hover__welcome-wave--outer" d="M17.6 2.6A4.8 4.8 0 0 1 22.4 7.4" />
  </svg>
</template>

<style>
/* Welcome icon — hover animation: the hand gives a little wave, arcs pulse. */
.l-its-hover__welcome-hand {
  transition: transform 0.25s ease;
  transform-origin: 10px 18px;
}

.l-its-hover__welcome-wave {
  transition: opacity 0.25s ease, transform 0.25s ease;
  transform-origin: 17px 7px;
}

.l-its-hover__welcome-wave--outer {
  opacity: 0.4;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .template-card:hover .v-icon) .l-its-hover--welcome .l-its-hover__welcome-hand {
  animation: llars-welcome-wave 0.9s ease-in-out infinite;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .template-card:hover .v-icon) .l-its-hover--welcome .l-its-hover__welcome-wave--inner {
  animation: llars-welcome-pulse 0.9s ease-in-out infinite;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon, .template-card:hover .v-icon) .l-its-hover--welcome .l-its-hover__welcome-wave--outer {
  animation: llars-welcome-pulse 0.9s ease-in-out infinite 0.15s;
}

@keyframes llars-welcome-wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-12deg); }
  75% { transform: rotate(12deg); }
}

@keyframes llars-welcome-pulse {
  0%, 100% { opacity: 0.35; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.06); }
}
</style>
