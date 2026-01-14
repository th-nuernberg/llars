<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('privacyPolicy.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('privacyPolicy.sections.controller.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.controller.intro') }}
        </p>
        <p v-html="$t('privacyPolicy.sections.controller.contact')"></p>

        <h3>{{ $t('privacyPolicy.sections.dataCollection.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.dataCollection.paragraph1') }}
        </p>
        <p>
          {{ $t('privacyPolicy.sections.dataCollection.paragraph2') }}
        </p>

        <h3>{{ $t('privacyPolicy.sections.recipients.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.recipients.paragraph1') }}
        </p>
        <p>
          {{ $t('privacyPolicy.sections.recipients.paragraph2') }}
        </p>

        <h3>{{ $t('privacyPolicy.sections.protection.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.protection.paragraph1') }}
        </p>

        <h3>{{ $t('privacyPolicy.sections.rights.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.rights.paragraph1') }}
        </p>

        <h3>{{ $t('privacyPolicy.sections.changes.title') }}</h3>
        <p>
          {{ $t('privacyPolicy.sections.changes.paragraph1') }}
        </p>

        <i18n-t keypath="privacyPolicy.sections.thNuremberg" tag="p">
          <a href="https://www.th-nuernberg.de/datenschutz/" target="_blank">{{ $t('privacyPolicy.links.thNuremberg') }}</a>
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
p {
  margin-bottom: 1rem;
  line-height: 1.6;
}
h1, h3 {
  color: rgb(var(--v-theme-on-surface));
}
a {
  color: rgb(var(--v-theme-info));
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
