<template>
  <!-- "Bewertungen" — a rating star with a small sparkle. Used wherever the
       per-item vote/evaluation panel is shown (e.g. the single-data-point
       detail dialog's "Bewertungen" header). Registered as `evaluations`
       and aliased from `mdi-vote-outline`. -->
  <svg
    class="l-its-hover__svg l-its-hover--evaluations"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.35)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Rating star -->
    <path
      class="l-its-hover__evaluations-star"
      d="M11 3.4l2.18 4.42 4.88.71-3.53 3.44.83 4.86L11 14.54l-4.36 2.29.83-4.86L3.94 8.53l4.88-.71z"
    />
    <!-- Sparkle accent -->
    <path class="l-its-hover__evaluations-spark" d="M18.5 16.5v3" />
    <path class="l-its-hover__evaluations-spark" d="M17 18h3" />
  </svg>
</template>
