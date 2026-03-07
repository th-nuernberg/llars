<template>
  <svg
    class="l-its-hover__svg l-its-hover--train-return"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Return arrow (going left) -->
    <g class="l-its-hover__train-return-arrow">
      <path d="M7 7l-4 3l4 3" />
      <line x1="3" y1="10" x2="9" y2="10" />
    </g>
    <!-- Train body (compact, right side) -->
    <g class="l-its-hover__train-return-body">
      <rect x="9" y="4" width="13" height="12" rx="2.5" />
      <!-- Windows -->
      <rect x="11.5" y="7.5" width="3.5" height="2.5" rx="0.5" />
      <rect x="16.5" y="7.5" width="3.5" height="2.5" rx="0.5" />
      <!-- Front stripe -->
      <line x1="9" y1="12.5" x2="22" y2="12.5" />
    </g>
    <!-- Wheels -->
    <g class="l-its-hover__train-return-wheels">
      <circle cx="12" cy="18" r="1.3" />
      <circle cx="18" cy="18" r="1.3" />
    </g>
    <!-- Rail -->
    <line class="l-its-hover__train-return-rail" x1="2" y1="20" x2="22" y2="20" />
  </svg>
</template>
