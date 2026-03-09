<template>
  <svg
    class="l-its-hover__svg l-its-hover--overleaf"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Overleaf-style overlapping leaves -->
    <!-- Back leaf (slightly rotated) -->
    <path
      class="l-its-hover__overleaf-back"
      d="M12 4C8 4 5 7.5 5 12c0 3.5 2 6.5 5 7.5C11 16 12 12 14 9c1-1.5 2.5-3 4.5-3.5C17 4.5 14.5 4 12 4Z"
    />
    <!-- Front leaf -->
    <path
      class="l-its-hover__overleaf-front"
      d="M12 4c4 0 7 3.5 7 8.5 0 3-1.5 5.5-4 7C14 16 13 12.5 11 9.5 10 8 8.5 6.5 6.5 5.5 8 4.5 10 4 12 4Z"
    />
    <!-- Center vein -->
    <path class="l-its-hover__overleaf-vein" d="M12 6v13" stroke-width="1" opacity="0.4" />
  </svg>
</template>
