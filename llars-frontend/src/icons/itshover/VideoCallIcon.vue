<template>
  <svg
    class="l-its-hover__svg l-its-hover--video-call"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Camera body -->
    <rect
      class="l-its-hover__video-call-body"
      x="2" y="6" width="13" height="12" rx="2"
    />
    <!-- Lens/record dot -->
    <circle
      class="l-its-hover__video-call-lens"
      cx="8.5" cy="12" r="1.5"
      fill="currentColor"
      stroke="none"
    />
    <!-- Viewfinder triangle -->
    <path
      class="l-its-hover__video-call-viewfinder"
      d="M17 9l4-2v10l-4-2z"
    />
  </svg>
</template>

<style>
/* Video Call icon - hover animation */
.l-its-hover__video-call-body,
.l-its-hover__video-call-viewfinder {
  transition: transform 0.25s ease;
}

.l-its-hover__video-call-lens {
  transform-origin: 8.5px 12px;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.l-its-hover__video-call-viewfinder {
  transform-origin: 17px 12px;
}

/* Hover: lens pulses (recording), viewfinder extends */
:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--video-call .l-its-hover__video-call-lens {
  animation: llars-record-pulse 1s ease-in-out infinite;
}

:is(.v-icon:hover, .v-btn:hover .v-icon, .feature-card:hover .v-icon) .l-its-hover--video-call .l-its-hover__video-call-viewfinder {
  transform: scaleX(1.1);
}

@keyframes llars-record-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.6; }
}
</style>
