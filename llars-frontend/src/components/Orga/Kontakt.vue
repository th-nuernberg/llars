<template>
  <v-container class="mt-5">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <h1>{{ $t('contactPage.title') }}</h1>
        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.email.title') }}</h3>
        <p>
          <a :href="`mailto:${contactEmail}`">{{ contactEmail }}</a>
        </p>

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
          <a href="https://www.linkedin.com/company/institut-f%C3%BCr-e-beratung/about/" target="_blank" rel="noopener noreferrer">LinkedIn</a> |
          <a href="https://www.facebook.com/eberatungsinstitut/" target="_blank" rel="noopener noreferrer">Facebook</a> |
          <a href="https://www.instagram.com/e_beratungsinstitut/" target="_blank" rel="noopener noreferrer">Instagram</a> |
          <a href="https://www.youtube.com/@institutfure-beratung8798" target="_blank" rel="noopener noreferrer">YouTube</a>
        </p>

        <v-divider class="my-4"></v-divider>

        <h3>{{ $t('contactPage.sections.location.title') }}</h3>
        <!--
          Google-Maps-Einbettung nach der DSGVO-konformen "Zwei-Klick-Lösung":
          Die iframe (und damit der Verbindungsaufbau zu Google inkl.
          IP-Übertragung/Cookies) wird ERST nach expliziter Zustimmung des
          Nutzers gerendert. Vorher steht nur ein lokaler Platzhalter — es geht
          kein Request an maps.google.com raus. Die Zustimmung wird pro Browser
          gemerkt (localStorage), damit sie nicht bei jedem Besuch neu abgefragt
          wird.
        -->
        <div class="map-wrapper">
          <iframe
            v-if="mapConsent"
            :src="mapSrc"
            width="100%"
            height="600"
            frameborder="0"
            scrolling="no"
            marginheight="0"
            marginwidth="0"
            :title="$t('contactPage.sections.location.title')"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>

          <div v-else class="map-consent">
            <v-icon size="48" color="primary">mdi-map-marker-radius-outline</v-icon>
            <p class="map-consent-text">{{ $t('contactPage.sections.location.consentText') }}</p>
            <p class="map-consent-privacy">
              <router-link to="/datenschutz">{{ $t('contactPage.links.privacy') }}</router-link>
            </p>
            <v-btn color="primary" variant="flat" @click="loadMap">
              {{ $t('contactPage.sections.location.loadMap') }}
            </v-btn>
          </div>
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
import { ref } from 'vue'

// Offizielle LLARS-Kontaktadresse (identisch zu MAIL_REPLY_TO im Backend,
// app/services/email_service.py). Bewusst als Konstante statt i18n-Text, da
// es sich um eine feste Adresse handelt, die in allen Sprachen gleich ist.
const contactEmail = 'llars@e-beratungsinstitut.de'

// Google-Maps-Consent (Zwei-Klick-Lösung, siehe Template-Kommentar).
const MAP_CONSENT_KEY = 'llars-maps-consent'
const mapSrc = 'https://maps.google.com/maps?width=100%25&height=600&hl=de&q=Innere%20Cramer-Klett-Stra%C3%9Fe%204-8,%2090403%20N%C3%BCrnberg&t=&z=17&ie=UTF8&iwloc=B&output=embed'

const mapConsent = ref(readMapConsent())

function readMapConsent() {
  try {
    return localStorage.getItem(MAP_CONSENT_KEY) === 'true'
  } catch (_) {
    return false
  }
}

function loadMap() {
  mapConsent.value = true
  try {
    localStorage.setItem(MAP_CONSENT_KEY, 'true')
  } catch (_) {
    // Private-Mode / geblockter Storage: Karte lädt trotzdem für diese Session.
  }
}
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

.map-wrapper {
  width: 100%;
}

/* Platzhalter, solange keine Zustimmung vorliegt — visuell an eine Karte
 * erinnernd, aber ohne jeden externen Request. */
.map-consent {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  min-height: 320px;
  padding: 32px 24px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.25);
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.map-consent-text {
  max-width: 440px;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.map-consent-privacy {
  margin: 0;
  font-size: 0.85rem;
}
</style>
