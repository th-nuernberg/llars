<template>
  <svg
    class="l-its-hover__svg l-its-hover--evaluation-assistant"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Clipboard -->
    <g class="l-its-hover__assistant-board">
      <rect x="4" y="4" width="12" height="15" rx="2" />
      <path class="l-its-hover__assistant-clip" d="M8 4V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1" />
    </g>
    <!-- Checklist items -->
    <g class="l-its-hover__assistant-list">
      <circle cx="7" cy="9" r="0.8" fill="currentColor" stroke="none" />
      <path d="M9.5 9h4" />
      <circle cx="7" cy="12" r="0.8" fill="currentColor" stroke="none" />
      <path d="M9.5 12h4" />
      <circle cx="7" cy="15" r="0.8" fill="currentColor" stroke="none" />
      <path d="M9.5 15h3" />
    </g>
    <!-- AI Magic wand - compact -->
    <g class="l-its-hover__assistant-wand">
      <path d="M18 18l3-6" />
      <path class="l-its-hover__assistant-star" d="M21 11l0.4-1l0.4 1l1 0.15l-0.7 0.7l0.2 1l-0.9-0.5l-0.9 0.5l0.2-1l-0.7-0.7z" fill="currentColor" stroke="none" />
    </g>
    <!-- AI Sparkles - smaller, thinner -->
    <g class="l-its-hover__assistant-sparkles" stroke-width="0.8">
      <path class="l-its-hover__assistant-sparkle" d="M18.5 12.5v0.5M18.25 12.75h0.5" />
      <path class="l-its-hover__assistant-sparkle l-its-hover__assistant-sparkle--two" d="M21 16.5v0.4M20.8 16.7h0.4" />
    </g>
  </svg>
</template>
