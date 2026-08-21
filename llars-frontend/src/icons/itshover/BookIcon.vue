<template>
  <!--
    LLARS book / documentation icon.

    An open book seen from above: two facing pages meeting at a spine in the
    middle, their outer edges lifting slightly the way paper does.

    The previous version was broken rather than merely plain — its second path
    drew only the TOP EDGE of the right-hand page and then stopped, so that half
    had no outer edge and no bottom, and the first path closed diagonally with
    `z` instead of forming a spine. It rendered as a lopsided half-shape with a
    stray line beside it.

    Deliberately no text lines on the pages: at the 16-20 px this is actually
    used at, they collapse into grey mush. Stroke-only, 1.5 px, matching the
    rest of the LLARS line-icon set.
  -->
  <svg
    class="l-its-hover__svg l-its-hover--book"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="var(--llars-icon-stroke, 1.5)"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- Left page: spine → outer top corner → down the outer edge → back to the spine -->
    <path d="M12 6.6C10.2 5.5 7.4 5 4 5.4v12c3.4-.4 6.2.1 8 1.2" />
    <!-- Right page, mirrored -->
    <path d="M12 6.6c1.8-1.1 4.6-1.6 8-1.2v12c-3.4-.4-6.2.1-8 1.2" />
    <!-- The spine, holding the two halves together -->
    <path d="M12 6.6v12" />
  </svg>
</template>
