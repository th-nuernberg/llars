<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>Kontakt</h1>
        <v-divider class="my-4"></v-divider>

        <h3>E-Mail</h3>
        <p>E-Mail: info [at] e-beratungsinstitut . de</p>

        <h3>Telefon</h3>
        <p>Telefon: +49 911 5880-2580</p>
        <p>
          Bitte hinterlassen Sie gerne eine Nachricht auf unseren Anrufbeantwortern, wir rufen gerne zurück.
        </p>
        <p>Telefax: +49 911 5880-602580</p>

        <h3>Postadresse</h3>
        <p>
          Institut für E-Beratung<br>
          Technische Hochschule Nürnberg<br>
          Keßlerplatz 12<br>
          90489 Nürnberg
        </p>

        <h3>Besucheradresse</h3>
        <p>
          LLARS Projekt, Technische Hochschule Nürnberg<br>
          Innere Cramer-Klett-Straße 4-8<br>
          90403 Nürnberg<br>
          Räume SCU 118, 119, 120a, 120b, 121, SC 004, 005, 009, 010
        </p>

        <v-divider class="my-4"></v-divider>

        <h3>Soziale Medien</h3>
        <p>
          <a href="https://www.linkedin.com/company/institut-f%C3%BCr-e-beratung/about/" target="_blank">LinkedIn</a> |
          <a href="https://www.facebook.com/eberatungsinstitut/" target="_blank">Facebook</a> |
          <a href="https://www.instagram.com/e_beratungsinstitut/" target="_blank">Instagram</a> |
          <a href="https://www.youtube.com/@institutfure-beratung8798" target="_blank">YouTube</a>
        </p>

        <v-divider class="my-4"></v-divider>

        <h3>Standort</h3>
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

        <h3>Datenschutz Hinweis</h3>
        <p>
          Weitere Informationen finden Sie in unserer <router-link to="/datenschutz">Datenschutzerklärung</router-link>.
        </p>
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
  color: #333;
}
a {
  color: #1976D2;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
