<template>
  <svg
    class="l-its-hover__svg l-its-hover--batch-generation"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Stacked documents (batch) -->
    <rect class="l-its-hover__batch-doc l-its-hover__batch-doc--back" x="6" y="2" width="12" height="14" rx="1.5" />
    <rect class="l-its-hover__batch-doc l-its-hover__batch-doc--front" x="4" y="5" width="12" height="14" rx="1.5" />

    <!-- Text lines in front document -->
    <line class="l-its-hover__batch-line" x1="6.5" y1="9" x2="11" y2="9" />
    <line class="l-its-hover__batch-line" x1="6.5" y1="12" x2="13.5" y2="12" />
    <line class="l-its-hover__batch-line" x1="6.5" y1="15" x2="10" y2="15" />

    <!-- Sparkle/generation indicator -->
    <path class="l-its-hover__batch-spark" d="M19 14l1.5 2.5L23 18l-2.5 1.5L19 22l-1.5-2.5L15 18l2.5-1.5z" />
    <circle class="l-its-hover__batch-spark-dot" cx="21" cy="11" r="0.8" fill="currentColor" />
  </svg>
</template>
