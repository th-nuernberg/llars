<template>
  <!--
    Campaign / megaphone icon — used by the admin referral section
    ("Kampagnen") and by anything else mapped from ``mdi-bullhorn`` /
    ``mdi-bullhorn-variant``. Stylised megaphone with an emanating
    sound wave.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--campaign"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Megaphone body: trapezoid pointing right -->
    <path d="M4 9h4l8-4v14l-8-4H4z" />
    <!-- Hand-grip / handle dangling from the bottom -->
    <path d="M8 13v4a2 2 0 0 0 4 0v-2" />
    <!-- Sound wave -->
    <path d="M19 9.5a3 3 0 0 1 0 5" />
  </svg>
</template>
