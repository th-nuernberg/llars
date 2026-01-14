<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('imprintPage.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <p>
          {{ $t('imprintPage.intro') }}
        </p>

        <h3>{{ $t('imprintPage.sections.address.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.address.project') }}<br>
          {{ $t('imprintPage.sections.address.university') }}<br>
          {{ $t('imprintPage.sections.address.street') }}<br>
          {{ $t('imprintPage.sections.address.city') }}<br>
          {{ $t('imprintPage.sections.address.phone') }}<br>
          {{ $t('imprintPage.sections.address.fax') }}<br>
          {{ $t('imprintPage.sections.address.email') }}<br>
          {{ $t('imprintPage.sections.address.websiteLabel') }}
          <a href="https://www.e-beratungsinstitut.de" target="_blank">{{ $t('imprintPage.links.eConsulting') }}</a>
        </p>

        <h3>{{ $t('imprintPage.sections.contactPerson.title') }}</h3>
        <p>{{ $t('imprintPage.sections.contactPerson.text') }}</p>

        <h3>{{ $t('imprintPage.sections.supervisoryAuthority.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.supervisoryAuthority.name') }}<br>
          {{ $t('imprintPage.sections.supervisoryAuthority.street') }}<br>
          {{ $t('imprintPage.sections.supervisoryAuthority.city') }}<br>
          {{ $t('imprintPage.sections.supervisoryAuthority.websiteLabel') }}
          <a href="https://www.stmwk.bayern.de" target="_blank">{{ $t('imprintPage.links.stmwk') }}</a>
        </p>

        <h3>{{ $t('imprintPage.sections.vatId.title') }}</h3>
        <p>{{ $t('imprintPage.sections.vatId.text') }}</p>

        <h3>{{ $t('imprintPage.sections.terms.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.terms.text') }}
        </p>

        <h3>{{ $t('imprintPage.sections.disclaimer.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.disclaimer.text') }}
        </p>

        <h3>{{ $t('imprintPage.sections.links.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.links.text') }}
        </p>

        <h3>{{ $t('imprintPage.sections.copyright.title') }}</h3>
        <p>
          {{ $t('imprintPage.sections.copyright.text') }}
        </p>

        <h3>{{ $t('imprintPage.sections.jurisdiction.title') }}</h3>
        <p>{{ $t('imprintPage.sections.jurisdiction.text') }}</p>
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
