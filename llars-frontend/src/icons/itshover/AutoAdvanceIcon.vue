<template>
  <!--
    LLARS auto-advance icon.

    Visual metaphor: a small "tap" ring on the left, a forward arrow in
    the middle, and a "skip-to-next" bar on the right — i.e. *click and
    jump straight to the next item*. Stroke-only, 1.5 px, matching the
    rest of the LLARS line-icon set so it sits cleanly next to
    ViewSplitIcon and the layout-toggle group.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--auto-advance"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Tap ring (the "click") -->
    <circle cx="5.5" cy="12" r="2.4" />
    <!-- Tap centre dot -->
    <circle cx="5.5" cy="12" r="0.7" fill="currentColor" stroke="none" />

    <!-- Forward arrow shaft -->
    <path d="M10 12 H17" />
    <!-- Arrow head -->
    <path d="M14.6 9.6 L17 12 L14.6 14.4" />

    <!-- Skip-to-next bar -->
    <line x1="20" y1="8.5" x2="20" y2="15.5" />
  </svg>
</template>
