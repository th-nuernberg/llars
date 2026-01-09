<template>
  <svg
    class="l-its-hover__svg l-its-hover--chatbot"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Main chat bubble -->
    <path
      class="l-its-hover__chatbot-bubble"
      d="M3 7h14a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3H11l-4 3v-3H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"
    />
    <!-- Typing dots -->
    <g class="l-its-hover__chatbot-dots">
      <circle class="l-its-hover__chatbot-dot l-its-hover__chatbot-dot--one" cx="7" cy="13" r="1" fill="currentColor" stroke="none" />
      <circle class="l-its-hover__chatbot-dot l-its-hover__chatbot-dot--two" cx="11" cy="13" r="1" fill="currentColor" stroke="none" />
      <circle class="l-its-hover__chatbot-dot l-its-hover__chatbot-dot--three" cx="15" cy="13" r="1" fill="currentColor" stroke="none" />
    </g>
    <!-- AI Sparkles -->
    <g class="l-its-hover__chatbot-sparkles">
      <path class="l-its-hover__chatbot-sparkle l-its-hover__chatbot-sparkle--one" d="M21 2v2M20 3h2" />
      <path class="l-its-hover__chatbot-sparkle l-its-hover__chatbot-sparkle--two" d="M23 5.5v1.5M22.25 6.25h1.5" />
    </g>
  </svg>
</template>
