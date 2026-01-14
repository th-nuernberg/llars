<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('contactPage.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.email.title') }}</h3>
        <p>{{ $t('contactPage.sections.email.address') }}</p>

        <h3>{{ $t('contactPage.sections.phone.title') }}</h3>
        <p>{{ $t('contactPage.sections.phone.number') }}</p>
        <p>
          {{ $t('contactPage.sections.phone.voicemail') }}
        </p>
        <p>{{ $t('contactPage.sections.phone.fax') }}</p>

        <h3>{{ $t('contactPage.sections.postal.title') }}</h3>
        <p v-html="$t('contactPage.sections.postal.address')"></p>

        <h3>{{ $t('contactPage.sections.visitor.title') }}</h3>
        <p v-html="$t('contactPage.sections.visitor.address')"></p>

        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.social.title') }}</h3>
        <p>
          <a href="https://www.linkedin.com/company/institut-f%C3%BCr-e-beratung/about/" target="_blank">LinkedIn</a> |
          <a href="https://www.facebook.com/eberatungsinstitut/" target="_blank">Facebook</a> |
          <a href="https://www.instagram.com/e_beratungsinstitut/" target="_blank">Instagram</a> |
          <a href="https://www.youtube.com/@institutfure-beratung8798" target="_blank">YouTube</a>
        </p>

        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.location.title') }}</h3>
        <div style="width: 100%">
          <iframe
            width="100%"
            height="600"
            frameborder="0"
            scrolling="no"
            marginheight="0"
            marginwidth="0"
            src="https://maps.google.com/maps?width=100%25&amp;height=600&amp;hl=en&amp;q=Innere%20Cramer-Klett-Stra%C3%9Fe%204-8,%2090403%20N%C3%BCrnberg+(My%20Business%20Name)&amp;t=&amp;z=17&amp;ie=UTF8&amp;iwloc=B&amp;output=embed"
          >
          </iframe>
        </div>

        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.privacy.title') }}</h3>
        <i18n-t keypath="contactPage.sections.privacy.text" tag="p">
          <router-link to="/datenschutz">{{ $t('contactPage.links.privacy') }}</router-link>
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
