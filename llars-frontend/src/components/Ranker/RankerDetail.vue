<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6">
        <h2>Features</h2>
        <v-expansion-panels>
          <v-expansion-panel v-for="(features, index) in groupedFeaturesByType" :key="index">
            <v-expansion-panel-header>{{ features[0].type | translateFeatureType }}</v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-list dense>
                <v-list-item v-for="feature in features" :key="feature.model_name">
                  <v-list-item-content>{{ feature.value }}</v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon @click.stop="showModelInfo(feature)">
                      <v-icon>mdi-information</v-icon>
                    </v-btn>
                  </v-list-item-action>
                </v-list-item>
              </v-list>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>

      <v-col cols="12" md="6">
        <h2>E-Mail Verlauf</h2>
        <div class="email-thread">
        <div
          v-for="message in messages"
          :key="message.message_id"
          class="email-message"
          :class="getMessageClass(message.sender)"
        >
            <div class="message-header">
              <span class="message-sender">{{ message.sender }}</span>
              <span class="message-timestamp">{{ message.timestamp }}</span>
            </div>
            <div class="message-body">
              <p>{{ message.content }}</p>
            </div>
          </div>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRoute } from 'vue-router';



const route = useRoute();
const features = ref([]);
const messages = ref([]);
const senderColors = ref({}); // Verwende ein reaktives Objekt statt einer Map

onMounted(async () => {
  try {
    const response = await axios.get(`http://localhost:8081/api/email_threads/${route.params.id}`);
    features.value = response.data.features;
    messages.value = response.data.messages;
    let lastSender = '';
    let currentColor = 'same-sender';

    messages.value.forEach(message => {
      if (message.sender !== lastSender) {
        // Wechsle die Farbe, wenn sich der Sender ändert
        currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
        lastSender = message.sender;
      }
      // Weise dem Sender die aktuelle Farbe zu
      senderColors.value[message.sender] = currentColor;
    });
  } catch (error) {
    console.error('Error fetching email threads:', error);
  }
});

function getMessageClass(sender) {
  // Hole die Farbe des Senders aus dem reaktiven Objekt
  return senderColors.value[sender];
}
</script>

<style scoped>
.email-thread {
  max-height: 600px;
  overflow-y: auto;
}

.email-message {
  padding: 16px;
  margin-bottom: 10px;
  border-radius: 10px;
}

.same-sender {
  background-color: #B2EBF2; /* Farbe für Nachrichten vom selben Sender */
}

.different-sender {
  background-color: #C8E6C9; /* Farbe für Nachrichten von verschiedenen Sendern */
}

.another-sender {
  background-color: #F0F4C3; /* Eine weitere Farbe für die Unterscheidung */
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-sender {
  font-weight: bold;
}

.message-timestamp {
  color: #666;
  font-size: 0.8rem;
}

.message-body p {
  margin: 0;
}
</style>
