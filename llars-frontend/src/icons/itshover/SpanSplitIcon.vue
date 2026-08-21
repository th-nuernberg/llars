<template>
  <!--
    LLARS "Span trennen" icon.

    Visual metaphor: one unit of text becoming two. A single bar is shown
    already parted into a left and a right half, with a dashed cut line
    standing between them — the cut is the subject, the halves are the
    result. Deliberately not a pair of scissors: the tool is not "cutting"
    in general, it is splitting ONE labelling unit into two.

    Stroke-only, 1.5 px, matching the rest of the LLARS line-icon set.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--span-split"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Left half of the span -->
    <rect x="2.5" y="8.5" width="7" height="7" rx="1.5" />
    <!-- Right half of the span -->
    <rect x="14.5" y="8.5" width="7" height="7" rx="1.5" />
    <!-- The cut between them -->
    <line x1="12" y1="5" x2="12" y2="7.5" />
    <line x1="12" y1="10.5" x2="12" y2="13.5" />
    <line x1="12" y1="16.5" x2="12" y2="19" />
  </svg>
</template>
