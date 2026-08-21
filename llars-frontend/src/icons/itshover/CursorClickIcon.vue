<template>
  <svg
    class="l-its-hover__svg l-its-hover--cursor-click"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Mauszeiger -->
    <path
      class="l-its-hover__cursor-arrow"
      d="M9 9l10 4.5-4.2 1.3L13.5 19 9 9z"
    />
    <!-- Klick-Funken um die Zeigerspitze -->
    <path class="l-its-hover__cursor-spark" d="M7.5 4.5v2" />
    <path class="l-its-hover__cursor-spark" d="M4.5 7.5h2" />
    <path class="l-its-hover__cursor-spark" d="M5.2 5.2l1.4 1.4" />
  </svg>
</template>

<style>
/* Cursor-Click icon — Funken pulsieren beim Hover */
.l-its-hover__cursor-spark {
  transform-origin: 6.5px 6.5px;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.l-its-hover__svg-host:hover .l-its-hover__cursor-spark,
a:hover .l-its-hover__cursor-spark,
button:hover .l-its-hover__cursor-spark {
  opacity: 0.5;
  transform: scale(1.25);
}
</style>
