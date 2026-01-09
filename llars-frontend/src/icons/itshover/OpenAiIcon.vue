<template>
  <svg
    class="l-its-hover__svg l-its-hover--openai"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- OpenAI-inspired hexagonal/neural pattern -->
    <path class="l-its-hover__openai-outer" d="M12 2L4 6.5v11L12 22l8-4.5v-11L12 2z" />
    <path class="l-its-hover__openai-inner" d="M12 6l-5 3v6l5 3l5-3V9l-5-3z" />
    <circle class="l-its-hover__openai-core" cx="12" cy="12" r="2" fill="currentColor" stroke="none" />
    <!-- Connection lines -->
    <g class="l-its-hover__openai-connections">
      <line x1="12" y1="6" x2="12" y2="2" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="7" y1="9" x2="4" y2="6.5" />
      <line x1="17" y1="9" x2="20" y2="6.5" />
    </g>
  </svg>
</template>
