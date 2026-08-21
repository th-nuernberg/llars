<template>
  <svg
    class="l-its-hover__svg l-its-hover--train"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Train body -->
    <g class="l-its-hover__train-body">
      <rect x="4" y="3" width="16" height="14" rx="3" />
      <!-- Windows -->
      <rect x="7" y="7" width="4" height="3" rx="0.5" />
      <rect x="13" y="7" width="4" height="3" rx="0.5" />
      <!-- Front stripe -->
      <line x1="4" y1="13" x2="20" y2="13" />
    </g>
    <!-- Wheels -->
    <g class="l-its-hover__train-wheels">
      <circle cx="8.5" cy="19" r="1.5" />
      <circle cx="15.5" cy="19" r="1.5" />
    </g>
    <!-- Rail -->
    <line class="l-its-hover__train-rail" x1="3" y1="21" x2="21" y2="21" />
  </svg>
</template>
