<template>
  <svg
    class="l-its-hover__svg l-its-hover--view-list"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Row 1: card-like row with asymmetric radius -->
    <rect x="3" y="3" width="18" height="5" rx="1.5" ry="0.5" />
    <!-- Row 2 -->
    <rect x="3" y="10" width="18" height="5" rx="1.5" ry="0.5" />
    <!-- Row 3 -->
    <rect x="3" y="17" width="18" height="5" rx="1.5" ry="0.5" />
    <!-- Content lines inside rows -->
    <line x1="5.5" y1="5.5" x2="10" y2="5.5" stroke-width="1" opacity="0.5" />
    <line x1="5.5" y1="12.5" x2="10" y2="12.5" stroke-width="1" opacity="0.5" />
    <line x1="5.5" y1="19.5" x2="10" y2="19.5" stroke-width="1" opacity="0.5" />
    <!-- Right-aligned detail dots -->
    <circle cx="18" cy="5.5" r="0.7" fill="currentColor" stroke="none" opacity="0.4" />
    <circle cx="18" cy="12.5" r="0.7" fill="currentColor" stroke="none" opacity="0.4" />
    <circle cx="18" cy="19.5" r="0.7" fill="currentColor" stroke="none" opacity="0.4" />
  </svg>
</template>
