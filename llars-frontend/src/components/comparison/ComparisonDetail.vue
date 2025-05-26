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

          <v-dialog v-model="infoDialog" max-width="600">
            <v-card>
              <v-card-title class="text-h5 bg-primary text-white pa-4">
                <v-icon start class="mr-2">mdi-information</v-icon>
                Informationen zur Gegenüberstellung
              </v-card-title>
              <v-card-text class="pa-6">
                <div class="text-body-1 mb-4">
                  <v-icon color="primary" class="mr-2">mdi-robot</v-icon>
                  <strong>Was ist der Gegenüberstellungsmodus?</strong>
                </div>
                <p class="mb-4">
                  In diesem Modus chatten Sie mit zwei verschiedenen KI-Modellen. Beide Modelle erhalten die selbe Eingabe und wir möchten mit Ihrer Hilfe herausfinden, welches der Modelle besser ist und besser den Klienten simuliert.
                </p>

                <div class="text-body-1 mb-4">
                  <v-icon color="primary" class="mr-2">mdi-account-details</v-icon>
                  <strong>Persona-Informationen</strong>
                </div>
                <p class="mb-4">
                  Einige Details zum jeweiligen Klienten sind links in der Seitenleiste angegeben.
                </p>

                <div class="text-body-1 mb-4">
                  <v-icon color="primary" class="mr-2">mdi-star</v-icon>
                  <strong>Bewertung und Interaktion</strong>
                </div>
                <p class="mb-4">
                  Nachdem die KI-Modelle etwas geschrieben haben, sollen Sie bewerten, welches der beiden besser ist (oder gleich gut). Anschließend können Sie eine Antwort formulieren, auf welche die Modelle wieder antworten etc.
                </p>

                <div class="text-body-1 mb-4">
                  <v-icon color="primary" class="mr-2">mdi-infinity</v-icon>
                  <strong>Keine Limits</strong>
                </div>
                <p class="mb-0">
                  Es gibt hier kein Limit - Sie können so viel schreiben wie sie möchten. Falls Sie eine andere Persona ausprobieren möchten, wechseln Sie einfach zur nächsten Session über die untere Leiste oder die Übersichtsseite.
                </p>
              </v-card-text>
              <v-card-actions class="pa-4">
                <v-spacer />
                <v-btn
                  color="primary"
                  variant="elevated"
                  @click="infoDialog = false"
                >
                  Verstanden
                </v-btn>
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
          :generating-suggestion="generatingSuggestion"
          :input-disabled="!canSendMessage"
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
              @suggestion-state-change="onSuggestionStateChange"
            />
          </template>
        </v-card>
      </v-col>
    </v-row>

    <ComparisonFooterBar
      v-if="session && allSessions.length > 0"
      :current-session-id="session.id"
      :all-sessions="allSessions"
      :rated-messages="getRatedMessagesCount()"
      :total-messages="getTotalMessagesCount()"
    />
  </v-container>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import PersonaSidebar from '@/components/comparison/PersonaSidebar.vue';
import {getSession, listSessionsForUser} from '@/services/comparisonApi';
import ComparisonChat from "@/components/comparison/ComparisonChat.vue";
import ComparisonFooterBar from "@/components/comparison/ComparisonFooterBar.vue";

const route = useRoute();
const router = useRouter();

const sessionId = ref<string | null>(null);
const session = ref<any>(null);
const allSessions = ref<Array<any>>([]);
const loadingSession = ref<boolean>(false);
const infoDialog = ref(false);
const chatComponent = ref<any>(null);
const generatingSuggestion = ref(false);

async function init() {
  sessionId.value = route.params.session_id as string;
  try {
    allSessions.value = await listSessionsForUser();
  } catch (error) {
    console.error('Fehler beim Laden aller Sessions', error);
  }

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
  if (chatComponent.value && chatComponent.value.generateSuggestion) {
    chatComponent.value.generateSuggestion();
  }
}

function onSuggestionStateChange(generating: boolean) {
  generatingSuggestion.value = generating;
}

const canSendMessage = computed(() => {
  if (!session.value?.messages) return true;
  
  const messages = session.value.messages;
  const lastMessage = messages[messages.length - 1];
  
  return !lastMessage ||
    lastMessage.type === 'user' ||
    (lastMessage.type === 'bot_pair' && lastMessage.selected);
});

function getRatedMessagesCount(): number {
  if (!session.value?.messages) return 0;
  return session.value.messages.filter((msg: any) => msg.type === 'bot_pair' && msg.selected).length;
}

function getTotalMessagesCount(): number {
  if (!session.value?.messages) return 0;
  return session.value.messages.filter((msg: any) => msg.type === 'bot_pair').length;
}

onMounted(init);
</script>

<style scoped>
.chat-card {
  height: calc(100vh - 240px);
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
