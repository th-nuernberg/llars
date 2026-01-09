<template>
  <svg
    class="l-its-hover__svg l-its-hover--rag"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Database cylinders - shifted left -->
    <g class="l-its-hover__rag-db">
      <ellipse class="l-its-hover__rag-db-top" cx="9" cy="6" rx="6" ry="2" />
      <path class="l-its-hover__rag-db-section l-its-hover__rag-db-section--top" d="M3 6v4c0 1.1 2.7 2 6 2s6-0.9 6-2V6" />
      <path class="l-its-hover__rag-db-section l-its-hover__rag-db-section--middle" d="M3 10v4c0 1.1 2.7 2 6 2s6-0.9 6-2v-4" />
      <path class="l-its-hover__rag-db-section l-its-hover__rag-db-section--bottom" d="M3 14v4c0 1.1 2.7 2 6 2s6-0.9 6-2v-4" />
    </g>
    <!-- Search/Retrieval magnifier - smaller -->
    <g class="l-its-hover__rag-search">
      <circle cx="19" cy="15" r="2.2" />
      <path d="M20.8 16.8l1.5 1.5" />
    </g>
    <!-- AI Sparkle -->
    <g class="l-its-hover__rag-sparkle">
      <path class="l-its-hover__rag-sparkle-star" d="M20 4v2M19 5h2" />
    </g>
  </svg>
</template>
