<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('termsPage.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <p class="intro">{{ $t('termsPage.intro') }}</p>

        <template v-for="key in sectionKeys" :key="key">
          <h3>{{ $t(`termsPage.sections.${key}.title`) }}</h3>
          <p>{{ $t(`termsPage.sections.${key}.text`) }}</p>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
// Reihenfolge der Abschnitte (entspricht der Nummerierung in den i18n-Titeln).
const sectionKeys = [
  'scope',
  'account',
  'acceptableUse',
  'content',
  'openSource',
  'availability',
  'liability',
  'termination',
  'finalProvisions',
]
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
h1, h3 {
  color: rgb(var(--v-theme-on-surface));
}
h3 {
  margin-top: 1.5rem;
}
</style>
