<template>
  <svg
    class="l-its-hover__svg l-its-hover--train-outbound"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Train body (compact, left side) -->
    <g class="l-its-hover__train-outbound-body">
      <rect x="2" y="4" width="13" height="12" rx="2.5" />
      <!-- Windows -->
      <rect x="4.5" y="7.5" width="3.5" height="2.5" rx="0.5" />
      <rect x="9.5" y="7.5" width="3.5" height="2.5" rx="0.5" />
      <!-- Front stripe -->
      <line x1="2" y1="12.5" x2="15" y2="12.5" />
    </g>
    <!-- Departure arrow (going right) -->
    <g class="l-its-hover__train-outbound-arrow">
      <path d="M17 7l4 3l-4 3" />
      <line x1="15" y1="10" x2="21" y2="10" />
    </g>
    <!-- Wheels -->
    <g class="l-its-hover__train-outbound-wheels">
      <circle cx="6" cy="18" r="1.3" />
      <circle cx="12" cy="18" r="1.3" />
    </g>
    <!-- Rail -->
    <line class="l-its-hover__train-outbound-rail" x1="2" y1="20" x2="22" y2="20" />
  </svg>
</template>
