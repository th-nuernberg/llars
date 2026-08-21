<template>
  <v-footer height="60" app class="llars-footer">
    <v-container fluid>
      <v-row align="center" justify="space-between">
        <!-- Left Section: Links -->
        <v-col cols="12" md="6" class="text-center text-md-left">
          <template v-for="item in links" :key="item.title">
            <!-- External links (like mkdocs) -->
            <a
              v-if="item.external"
              :href="item.to"
              class="footer-link mx-2"
              target="_blank"
            >
              {{ item.title }}
            </a>
            <!-- Internal Vue routes -->
            <router-link
              v-else
              :to="item.to"
              class="footer-link mx-2"
            >
              {{ item.title }}
            </router-link>
          </template>

          <!-- Citation is a license condition for academic use -> always reachable -->
          <button type="button" class="footer-link mx-2" @click="citationOpen = true">
            {{ t('citation.link') }}
          </button>
        </v-col>

        <!-- Right Section: Copyright -->
        <v-col cols="12" md="6" class="text-center text-md-right">
          <span class="text-caption text-disabled">
            &copy; {{ (new Date()).getFullYear() }} LLars - Learning & Labeling AI Rating System
          </span>
        </v-col>
      </v-row>
    </v-container>

    <LCitationDialog v-model="citationOpen" />
  </v-footer>
</template>

<script setup>
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import LCitationDialog from '@/components/common/LCitationDialog.vue'
  import { docsUrlForLocale } from '@/utils/docsUrl'

  const { t, locale } = useI18n()

  // "Cite LLARS" dialog (see LCitationDialog docstring: citation is a license
  // condition under PolyForm Noncommercial, not just a nicety).
  const citationOpen = ref(false)

  // Doku in der aktuellen UI-Sprache (DE -> /mkdocs/, EN -> /mkdocs/en/).
  const docsUrl = computed(() => docsUrlForLocale(locale.value))

  const links = computed(() => [
    {
      title: t('footer.documentation'),
      to: docsUrl.value,
      external: true,
    },
    {
      title: t('footer.imprint'),
      to: '/Impressum',
    },
    {
      title: t('footer.privacy'),
      to: '/Datenschutz',
    },
    {
      title: t('footer.contact'),
      to: '/Kontakt',
    },
  ])
</script>

<style scoped lang="sass">
  .llars-footer
    background-color: rgba(var(--v-theme-surface), 0.95)
    border-top: 1px solid rgba(var(--v-border-color), 0.12)

  .footer-link
    color: rgba(var(--v-theme-on-background), 0.7)
    text-decoration: none
    font-size: 0.875rem
    transition: color 0.2s ease-in-out
    // Reset so the citation <button> renders identically to the <a>/<router-link> siblings
    background: none
    border: none
    padding: 0
    font-family: inherit
    cursor: pointer

    &:hover
      color: rgba(var(--v-theme-primary))
      text-decoration: underline
</style>
