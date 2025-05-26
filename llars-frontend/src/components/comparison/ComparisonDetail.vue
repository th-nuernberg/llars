<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card flat color="transparent">
          <v-card-title class="pa-0 text-h6 font-weight-bold">
            <v-icon start>mdi-chat</v-icon>
            Gegenüberstellung: {{ session?.persona_name || 'Laden...' }}
            <v-icon
              class="ml-1 mb-3 text-orange"
              size="20"
              @click="infoDialog = true"
              title="Mehr Informationen"
            >mdi-information</v-icon>
          </v-card-title>

          <v-dialog v-model="infoDialog" max-width="400">
            <v-card>
              <v-card-title class="text-h6">Informationen zur Gegenüberstellung</v-card-title>
              <v-card-text>
                In diesem Modus chatten Sie mit zwei verschiedenen KI-Modellen. Beide Modelle erhalten die selbe Eingabe und wir möchten mit Ihrer Hilfe herausfinden, welches der Modelle besser ist und besser den Klienten simuliert.
                Einige Details zum jeweiligen Klienten sind links in der Seitenleiste angegeben.
                <br />
                <br />
                Nachdem die KI-Modelle etwas geschrieben haben, sollen Sie bewerten, welches der beiden besser ist (oder gleich gut). Anschließend können Sie eine Antwort formulieren, auf welche die Modelle wieder antworten etc.
                <br />
                <br />
                Es gibt hier kein Limit - Sie können so viel schreiben wie sie möchten. Falls Sie eine andere Persona ausprobieren möchten, starten Sie einfach das Szenario von vorne (zurück auf die Startseite -> Gegenüberstellung -> Szenario wählen).
                Die Persona wird Ihnen zufällig zugewiesen.
              </v-card-text>
              <v-card-actions>
                <v-spacer />
                <v-btn text @click="infoDialog = false">Schließen</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-2" no-gutters>
      <v-col cols="12" md="3" class="pr-md-4 mb-4 mb-md-0">
        <PersonaSidebar
          :persona="session?.persona_json"
          :loading="loadingSession"
          @suggestion="onSuggestion"
        />
      </v-col>

      <v-col cols="12" md="9">
        <v-card flat color="transparent" class="chat-card">
          <template v-if="loadingSession">
            <v-skeleton-loader type="paragraph"/>
          </template>
          <template v-else>
            <ComparisonChat
              ref="chatComponent"
              :session-id="session?.id"
              :persona="session?.persona_json"
              @message-update="onMessageUpdate"
            />
          </template>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import PersonaSidebar from '@/components/comparison/PersonaSidebar.vue';
import {getSession} from '@/services/comparisonApi';
import ComparisonChat from "@/components/comparison/ComparisonChat.vue";

const route = useRoute();
const router = useRouter();

const sessionId = ref<string | null>(null);
const session = ref<any>(null);
const loadingSession = ref<boolean>(false);
const infoDialog = ref(false);

async function init() {
  sessionId.value = route.params.session_id as string;

  // Bestehende Session laden
  loadingSession.value = true;
  try {
    session.value = await getSession(parseInt(sessionId.value));
    console.log(session.value)
  } catch (error) {
    console.error('Fehler beim Laden der Session', error);
  } finally {
    loadingSession.value = false;
  }
}

function onMessageUpdate() {
  // Reload session data when messages are updated
  if (session.value) {
    getSession(session.value.id).then(updatedSession => {
      session.value = updatedSession;
    }).catch(error => {
      console.error('Fehler beim Aktualisieren der Session', error);
    });
  }
}

function onSuggestion() {
  // TODO: Vorschlags-Logik implementieren
  console.log('Vorschlag generieren');
}

onMounted(init);
</script>

<style scoped>
.chat-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.chat-card .v-card-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
