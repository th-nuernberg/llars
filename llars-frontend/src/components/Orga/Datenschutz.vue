<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('privacyPolicy.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <p class="intro">{{ $t('privacyPolicy.intro') }}</p>

        <!-- 1. Verantwortlicher -->
        <h3>{{ $t('privacyPolicy.sections.controller.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.controller.intro') }}</p>
        <p v-html="$t('privacyPolicy.sections.controller.contact')"></p>
        <p>{{ $t('privacyPolicy.sections.controller.dpo') }}</p>

        <!-- 2. Datenerhebung -->
        <h3>{{ $t('privacyPolicy.sections.dataCollection.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.dataCollection.paragraph1') }}</p>
        <p>{{ $t('privacyPolicy.sections.dataCollection.paragraph2') }}</p>

        <!-- 3. Server-Logfiles -->
        <h3>{{ $t('privacyPolicy.sections.serverLogs.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.serverLogs.text') }}</p>
        <p class="legal-basis">{{ $t('privacyPolicy.sections.serverLogs.legalBasis') }}</p>

        <!-- 4. Cookies -->
        <h3>{{ $t('privacyPolicy.sections.cookies.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.cookies.text') }}</p>
        <p>{{ $t('privacyPolicy.sections.cookies.optional') }}</p>

        <!-- 5. Matomo -->
        <h3>{{ $t('privacyPolicy.sections.analytics.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.analytics.text') }}</p>
        <p>{{ $t('privacyPolicy.sections.analytics.consent') }}</p>
        <p class="legal-basis">{{ $t('privacyPolicy.sections.analytics.legalBasis') }}</p>

        <!-- 6. Google Maps -->
        <h3>{{ $t('privacyPolicy.sections.maps.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.maps.text') }}</p>
        <p>{{ $t('privacyPolicy.sections.maps.consent') }}</p>
        <p class="legal-basis">{{ $t('privacyPolicy.sections.maps.legalBasis') }}</p>

        <!-- 7. Konto & Authentifizierung -->
        <h3>{{ $t('privacyPolicy.sections.account.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.account.text') }}</p>
        <p class="legal-basis">{{ $t('privacyPolicy.sections.account.legalBasis') }}</p>

        <!-- 8. E-Mail-Versand -->
        <h3>{{ $t('privacyPolicy.sections.email.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.email.text') }}</p>
        <p class="legal-basis">{{ $t('privacyPolicy.sections.email.legalBasis') }}</p>

        <!-- 9. Empfänger -->
        <h3>{{ $t('privacyPolicy.sections.recipients.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.recipients.paragraph1') }}</p>
        <p>{{ $t('privacyPolicy.sections.recipients.paragraph2') }}</p>

        <!-- 10. Speicherdauer -->
        <h3>{{ $t('privacyPolicy.sections.retention.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.retention.text') }}</p>

        <!-- 11. Schutz -->
        <h3>{{ $t('privacyPolicy.sections.protection.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.protection.paragraph1') }}</p>

        <!-- 12. Rechte -->
        <h3>{{ $t('privacyPolicy.sections.rights.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.rights.paragraph1') }}</p>
        <p>{{ $t('privacyPolicy.sections.rights.complaint') }}</p>
        <p>{{ $t('privacyPolicy.sections.rights.contact') }}</p>

        <!-- 13. Änderungen -->
        <h3>{{ $t('privacyPolicy.sections.changes.title') }}</h3>
        <p>{{ $t('privacyPolicy.sections.changes.paragraph1') }}</p>

        <v-divider class="my-4"></v-divider>
        <i18n-t keypath="privacyPolicy.thNuremberg" tag="p">
          <a href="https://www.th-nuernberg.de/datenschutz/" target="_blank" rel="noopener noreferrer">{{ $t('privacyPolicy.links.thNuremberg') }}</a>
        </i18n-t>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
</script>

<style scoped>
.mt-5 {
  margin-top: 5rem;
}
.intro {
  font-size: 1.02rem;
}
p {
  margin-bottom: 1rem;
  line-height: 1.6;
}
/* Rechtsgrundlagen-Zeilen dezent absetzen (Meta-Information) */
.legal-basis {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  margin-top: -0.5rem;
}
h1, h3 {
  color: rgb(var(--v-theme-on-surface));
}
h3 {
  margin-top: 1.5rem;
}
a {
  color: rgb(var(--v-theme-info));
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
