<template>
  <v-dialog
    :model-value="modelValue"
    max-width="680"
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="l-citation-card">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-format-quote-close</v-icon>
        {{ $t('citation.title') }}
      </v-card-title>

      <v-card-text>
        <p class="text-body-2 mb-3">{{ $t('citation.ask') }}</p>

        <!-- Human-readable reference above the raw BibTeX -->
        <p class="text-body-2 font-weight-medium mb-3">
          {{ PAPER_REFERENCE }}
          <a
            :href="PAPER_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="citation-link"
          >arXiv:2605.10593</a>
        </p>

        <pre class="citation-bibtex">{{ BIBTEX }}</pre>

        <div class="d-flex align-center flex-wrap mt-3" style="gap: 8px;">
          <LBtn
            variant="primary"
            size="small"
            :prepend-icon="copied ? 'mdi-check' : 'mdi-content-copy'"
            @click="copyBibtex"
          >
            {{ copied ? $t('citation.copied') : $t('citation.copy') }}
          </LBtn>
          <span v-if="copyFailed" class="text-caption text-error">
            {{ $t('citation.copyFailed') }}
          </span>
        </div>

        <p class="text-caption text-medium-emphasis mt-4 mb-0">
          {{ $t('citation.licenseNote') }}
          <a
            :href="LICENSE_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="citation-link"
          >{{ $t('citation.licenseLink') }}</a>
        </p>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="$emit('update:modelValue', false)">
          {{ $t('citation.close') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * LCitationDialog - "Cite LLARS" dialog.
 *
 * Shown from both footers (AppFooter for the authenticated app, LandingFooter
 * for the public landing page). Since LLARS moved to the PolyForm Noncommercial
 * License 1.0.0, citing the LLARS paper is a *condition* of the license grant
 * for academic use — so the citation must be reachable from anywhere in the app,
 * not just from the README.
 *
 * The BibTeX entry is a code literal rather than an i18n string on purpose:
 * it is language-independent verbatim content, and putting it in the locale
 * files would risk translators reformatting or breaking the LaTeX escaping
 * (note the `\&` in the title). Only the surrounding prose is translated.
 *
 * Keep in sync with the root CITATION.cff / README.md when the paper reference
 * is updated (the arXiv preprint will be replaced by the IJCAI-ECAI 2026
 * proceedings version once published).
 */
import { ref, watch } from 'vue'

import LBtn from '@/components/common/LBtn.vue'

const props = defineProps({
  /** v-model: dialog open state */
  modelValue: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])

const PAPER_URL = 'https://arxiv.org/abs/2605.10593'
const LICENSE_URL = 'https://github.com/th-nuernberg/llars/blob/main/LICENSE'

const PAPER_REFERENCE =
  'Steigerwald, P., Stieler, M., Burghardt, J., Rudolph, E., & Albrecht, J. (2026). ' +
  'LLARS: Enabling Domain Expert & Developer Collaboration for LLM Prompting, ' +
  'Generation and Evaluation.'

const BIBTEX = `@article{steigerwald2026llars,
  title   = {LLARS: Enabling Domain Expert \\& Developer Collaboration for LLM Prompting, Generation and Evaluation},
  author  = {Steigerwald, Philipp and Stieler, Mara and Burghardt, Jennifer and Rudolph, Eric and Albrecht, Jens},
  journal = {arXiv preprint arXiv:2605.10593},
  year    = {2026},
  url     = {https://arxiv.org/abs/2605.10593}
}`

// Transient button feedback: swaps the label/icon for ~2s after a copy.
const copied = ref(false)
const copyFailed = ref(false)
let resetTimer = null

async function copyBibtex() {
  copyFailed.value = false
  try {
    await navigator.clipboard.writeText(BIBTEX)
    copied.value = true
    if (resetTimer) clearTimeout(resetTimer)
    resetTimer = setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    // Clipboard API is unavailable over plain http on some browsers — the
    // BibTeX stays selectable in the <pre> box, so this is a soft failure.
    copyFailed.value = true
  }
}

// Reset the transient state whenever the dialog is re-opened.
watch(() => props.modelValue, (open) => {
  if (!open) return
  copied.value = false
  copyFailed.value = false
})
</script>

<style scoped>
.l-citation-card {
  /* LLARS signature asymmetric border-radius */
  border-radius: 16px 4px 16px 4px;
}

.citation-bibtex {
  font-family: 'Roboto Mono', 'SFMono-Regular', Menlo, Consolas, monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  white-space: pre;
  overflow-x: auto;
  padding: 12px 14px;
  margin: 0;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 12px 3px 12px 3px;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.citation-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.citation-link:hover {
  text-decoration: underline;
}
</style>
