<template>
  <span class="llars-wordmark" :aria-label="ariaLabel" role="text">Llars</span>
</template>

<script setup>
/**
 * LlarsBrand - the single, reusable LLARS brand wordmark.
 *
 * Renders the product name exactly like the paper's `\textsc{Llars}`: a
 * full-height capital "L" followed by "lars" set in SMALL capitals. The
 * template feeds the span the mixed-case string "Llars" (one uppercase "L" +
 * lowercase "lars") and `font-variant-caps: small-caps` raises the lowercase
 * letters to small capitals while the leading "L" stays full height.
 *
 * Why a mixed-case string rather than "LLARS": small-caps only affects letters
 * that are lowercase in the source, so the casing here is load-bearing.
 *
 * Accessibility: assistive tech reads the `aria-label` ("LLARS"), so the
 * screen-reader experience is unchanged regardless of the visual small-caps.
 *
 * Use everywhere the product name appears as a user-visible brand wordmark
 * (app bar, footer, login/register headings, landing/docs hero, page
 * headings). Do NOT use it for the document <title>, URLs, code identifiers,
 * env keys or log strings - those stay the plain "LLARS".
 *
 * Keep the single root <span> as the FIRST node (no leading comment node) so
 * attributes bind to the element root instead of an implicit fragment.
 */
defineProps({
  ariaLabel: {
    type: String,
    default: 'LLARS'
  }
})
</script>

<style scoped>
.llars-wordmark {
  /* `font-variant` is the legacy fallback; `font-variant-caps` is the modern,
     more specific property. Declaring both maximises browser coverage. */
  font-variant: small-caps;
  font-variant-caps: small-caps;
  /* Inherit from the surrounding heading/text so the wordmark blends in. */
  font-weight: inherit;
  font-size: inherit;
  color: inherit;
  letter-spacing: inherit;
}
</style>
