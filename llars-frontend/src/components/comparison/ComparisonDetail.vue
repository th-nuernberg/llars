<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card flat color="transparent">
          <v-card-title class="pa-0 text-h6 font-weight-bold">
            <v-icon start>mdi-chat</v-icon>
            Gegenüberstellung: Session #{{ scenarioId }}<span v-if="session">/{{
              session?.id
            }}</span>
          </v-card-title>
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
import {createSession, getSession} from '@/services/comparisonApi';
import ComparisonChat from "@/components/comparison/ComparisonChat.vue";

const route = useRoute();
const router = useRouter();

const scenarioId = ref<string | null>(null);
const session = ref<any>(null);
const loadingSession = ref<boolean>(false);

async function init() {
  scenarioId.value = route.params.id as string;
  const sessionId = (route.params.session_id as string) || null;

  if (!sessionId) {
    loadingSession.value = true;
    try {
      const payload = {scenario_id: scenarioId.value};
      const newSession = await createSession(payload);
      router.replace({
        name: 'ComparisonDetail',
        params: {id: scenarioId.value, session_id: newSession.id}
      });
    } catch (error) {
      console.error('Fehler beim Erstellen der Session', error);
    } finally {
      loadingSession.value = false;
    }
    return;
  }

  // Bestehende Session laden
  loadingSession.value = true;
  try {
    session.value = await getSession(parseInt(sessionId));
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
