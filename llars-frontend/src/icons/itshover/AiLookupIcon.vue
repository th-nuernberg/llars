<template>
  <svg
    class="l-its-hover__svg l-its-hover--ai-lookup"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Magnifying glass -->
    <circle cx="10.5" cy="10.5" r="6" />
    <path d="M15.5 15.5l4 4" stroke-width="2" />

    <!-- AI sparkles inside lens -->
    <g class="l-its-hover__ai-lookup-sparkles">
      <path class="l-its-hover__ai-lookup-sparkle l-its-hover__ai-lookup-sparkle--one"
        d="M9 7.5L9.5 9L11 9.5L9.5 10L9 11.5L8.5 10L7 9.5L8.5 9Z"
        fill="currentColor" stroke="none" />
      <path class="l-its-hover__ai-lookup-sparkle l-its-hover__ai-lookup-sparkle--two"
        d="M13 11L13.35 11.7L14 12L13.35 12.3L13 13L12.65 12.3L12 12L12.65 11.7Z"
        fill="currentColor" stroke="none" />
    </g>
  </svg>
</template>
