<template>
  <v-container class="email-progress-dashboard" fluid>
    <v-card class="mb-4 title-card">
      <v-card-title class="text-h5">{{ scenarioName }}</v-card-title>
      <v-card-subtitle>{{ functionTypeTexts.subheader }}</v-card-subtitle>
    </v-card>

    <!-- Rater und Evaluator Panels -->
    <v-expansion-panels v-model="openPanels" multiple>
      <!-- Rater Panel -->
      <v-expansion-panel>
        <v-expansion-panel-title>
          <h3>{{ $t('adminProgress.raterTitle') }}</h3>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <!-- Legende -->
          <v-card class="mb-2 legend-card">
            <v-card-text class="py-2">
              <v-row align="center" no-gutters class="legend-row">
                <v-col cols="2" sm="1" class="username-col">
                  <strong>{{ $t('adminProgress.legend.user') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.done') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.inProgress') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.notStarted') }}</strong>
                </v-col>
                <v-col class="progress-col">
                  <strong>{{ $t('adminProgress.legend.overallProgress') }}</strong>
                </v-col>
                <v-col cols="auto" class="actions-col">
                  <strong>{{ $t('adminProgress.legend.actions') }}</strong>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card v-for="user in raterStats" :key="user.username" class="mb-2 user-card">
            <v-card-text class="py-2">
              <v-row align="center" no-gutters class="user-row">
                <v-col cols="2" sm="1" class="username-col">
                  <span class="username">{{ user.username }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.done_threads }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.progressing_threads }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.not_started_threads }}</span>
                </v-col>
                <v-col class="progress-col">
                  <div class="progress-bar-wrapper">
                    <div
                      :style="{ width: `${user.donePercentage}%` }"
                      class="progress-bar progress-bar-done"
                    >
                      <span
                        v-if="user.donePercentage > 5"
                        class="progress-label progress-label-done"
                      >
                        {{ Math.round(user.donePercentage) }}%
                      </span>
                    </div>
                    <div
                      :style="{ width: `${user.progressingPercentage}%`, left: `${user.donePercentage}%` }"
                      class="progress-bar progress-bar-progressing"
                    >
                      <span
                        v-if="user.progressingPercentage > 5"
                        class="progress-label progress-label-progressing"
                      >
                        {{ Math.round(user.progressingPercentage) }}%
                      </span>
                    </div>
                    <div
                      :style="{ width: `${user.notStartedPercentage}%`, left: `${user.donePercentage + user.progressingPercentage}%` }"
                      class="progress-bar progress-bar-not-started"
                    >
                      <span
                        v-if="user.notStartedPercentage > 5"
                        class="progress-label progress-label-not-started"
                      >
                        {{ Math.round(user.notStartedPercentage) }}%
                      </span>
                    </div>
                  </div>
                </v-col>
                <v-col cols="auto" class="actions-col" style="padding-left: 16px;">
                  <v-btn x-small color="primary" @click="showThreadDetails(user)">
                    {{ $t('adminProgress.details') }}
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>

      <!-- Evaluator Panel -->
      <v-expansion-panel>
        <v-expansion-panel-title>
          <h3>{{ $t('adminProgress.evaluatorTitle') }}</h3>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <!-- Legende für Evaluator -->
          <v-card class="mb-2 legend-card">
            <v-card-text class="py-2">
              <v-row align="center" no-gutters class="legend-row">
                <v-col cols="2" sm="1" class="username-col">
                  <strong>{{ $t('adminProgress.legend.user') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.done') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.inProgress') }}</strong>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <strong>{{ $t('adminProgress.legend.notStarted') }}</strong>
                </v-col>
                <v-col class="progress-col">
                  <strong>{{ $t('adminProgress.legend.overallProgress') }}</strong>
                </v-col>
                <v-col cols="auto" class="actions-col">
                  <strong>{{ $t('adminProgress.legend.actions') }}</strong>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card v-for="user in evaluatorStats" :key="user.username" class="mb-2 user-card">
            <v-card-text class="py-2">
              <v-row align="center" no-gutters class="user-row">
                <v-col cols="2" sm="1" class="username-col">
                  <span class="username">{{ user.username }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.done_threads }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.progressing_threads }}</span>
                </v-col>
                <v-col cols="3" sm="2" class="threads-col">
                  <span class="thread-info">{{ user.not_started_threads }}</span>
                </v-col>
                <v-col class="progress-col">
                  <div class="progress-bar-wrapper">
                    <div
                      :style="{ width: `${user.donePercentage}%` }"
                      class="progress-bar progress-bar-done"
                    >
                      <span
                        v-if="user.donePercentage > 5"
                        class="progress-label progress-label-done"
                      >
                        {{ Math.round(user.donePercentage) }}%
                      </span>
                    </div>
                    <div
                      :style="{ width: `${user.progressingPercentage}%`, left: `${user.donePercentage}%` }"
                      class="progress-bar progress-bar-progressing"
                    >
                      <span
                        v-if="user.progressingPercentage > 5"
                        class="progress-label progress-label-progressing"
                      >
                        {{ Math.round(user.progressingPercentage) }}%
                      </span>
                    </div>
                    <div
                      :style="{ width: `${user.notStartedPercentage}%`, left: `${user.donePercentage + user.progressingPercentage}%` }"
                      class="progress-bar progress-bar-not-started"
                    >
                      <span
                        v-if="user.notStartedPercentage > 5"
                        class="progress-label progress-label-not-started"
                      >
                        {{ Math.round(user.notStartedPercentage) }}%
                      </span>
                    </div>
                  </div>
                </v-col>
                <v-col cols="auto" class="actions-col" style="padding-left: 16px;">
                  <v-btn x-small color="primary" @click="showThreadDetails(user)">
                    {{ $t('adminProgress.details') }}
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Thread Details Dialog (unverändert) -->
    <v-dialog v-model="dialogVisible" max-width="700px">
      <v-card>
        <v-card-title>{{ $t('adminProgress.threadDetailsTitle', { username: selectedUser.username || '' }) }}</v-card-title>
        <v-card-text>
          <v-subheader>{{ functionTypeTexts.done }}</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.done_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ $t('adminProgress.threadDetailsMeta', { threadId: thread.thread_id, chatId: thread.chat_id, instituteId: thread.institut_id }) }}
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>

          <v-subheader>{{ functionTypeTexts.inProgress }}</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.progressing_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ $t('adminProgress.threadDetailsMeta', { threadId: thread.thread_id, chatId: thread.chat_id, instituteId: thread.institut_id }) }}
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>

          <v-subheader>{{ functionTypeTexts.notStarted }}</v-subheader>
          <v-list dense>
            <v-list-item v-for="thread in selectedUser.not_started_threads_list" :key="thread.thread_id">
              <v-list-item-content>
                <v-list-item-title class="text-subtitle-1">{{ thread.subject }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ $t('adminProgress.threadDetailsMeta', { threadId: thread.thread_id, chatId: thread.chat_id, instituteId: thread.institut_id }) }}
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogVisible = false">{{ $t('common.close') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { logI18n } from '@/utils/logI18n';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const scenario_id = route.params.id;

// Szenario-Details
const scenarioDetails = ref({
  name: "",
  func_type_id: null,
});

// Texte für die UI, abhängig vom Funktionstyp
const functionTypeTexts = computed(() => {
  if (!scenarioDetails.value.func_type_id) return {};
  const mapping = functionTypeMappings[scenarioDetails.value.func_type_id];
  if (!mapping) return {};
  return {
    subheader: t(mapping.subheader),
    done: t(mapping.done),
    inProgress: t(mapping.inProgress),
    notStarted: t(mapping.notStarted),
  };
});

const scenarioName = computed(() => scenarioDetails.value.name || t('adminProgress.unknownScenario'));

const functionTypeMappings = {
  1: {
    subheader: 'adminProgress.functionTypes.ranking.subheader',
    done: 'adminProgress.functionTypes.ranking.done',
    inProgress: 'adminProgress.functionTypes.ranking.inProgress',
    notStarted: 'adminProgress.functionTypes.ranking.notStarted',
  },
  2: {
    subheader: 'adminProgress.functionTypes.rating.subheader',
    done: 'adminProgress.functionTypes.rating.done',
    inProgress: 'adminProgress.functionTypes.rating.inProgress',
    notStarted: 'adminProgress.functionTypes.rating.notStarted',
  },
  3: {
    subheader: 'adminProgress.functionTypes.history.subheader',
    done: 'adminProgress.functionTypes.history.done',
    inProgress: 'adminProgress.functionTypes.history.inProgress',
    notStarted: 'adminProgress.functionTypes.history.notStarted',
  },
};

// Benutzerstatistiken
const raterStats = ref([]);
const evaluatorStats = ref([]);
const dialogVisible = ref(false);
const selectedUser = ref({});
const openPanels = ref([0]); // Rater Panel standardmäßig geöffnet

// Methoden
const showThreadDetails = (user) => {
  selectedUser.value = user;
  dialogVisible.value = true;
};

const calculateProgressSections = (total_threads, done_threads, progressing_threads) => {
  const donePercentage = (done_threads / total_threads) * 100 || 0;
  const progressingPercentage = (progressing_threads / total_threads) * 100 || 0;
  const notStartedPercentage = 100 - donePercentage - progressingPercentage;

  return {
    donePercentage,
    progressingPercentage,
    notStartedPercentage,
  };
};

const fetchScenarioDetails = async () => {
  try {
    const response = await axios.get(`/api/admin/scenarios/${scenario_id}`);

    scenarioDetails.value = {
      name: response.data.scenario_name || '',
      func_type_id: response.data.function_type_id || null,
    };

    if (functionTypeMappings[scenarioDetails.value.func_type_id]) {
      //statsRoute.value = functionTypeMappings[scenarioDetails.value.func_type_id].route;
      await fetchUserStats();
    } else {
      logI18n('error', 'logs.admin.stats.noMappingForFuncTypeId', scenarioDetails.value.func_type_id);
    }

  } catch (error) {
    logI18n('error', 'logs.admin.stats.scenarioDetailsLoadFailed', error);
  }
};

const fetchUserStats = async () => {
  try {
    const response = await axios.get(`/api/admin/scenario_progress_stats/${scenario_id}`);

    if (Array.isArray(response.data.rater_stats)) {
      raterStats.value = response.data.rater_stats.map(user => ({
        ...user,
        ...calculateProgressSections(user.total_threads, user.done_threads, user.progressing_threads),
      }));
    }

    const evaluatorPayload = response.data.evaluator_stats || response.data.viewer_stats || [];
    if (Array.isArray(evaluatorPayload)) {
      evaluatorStats.value = evaluatorPayload.map(user => ({
        ...user,
        ...calculateProgressSections(user.total_threads, user.done_threads, user.progressing_threads),
      }));
    }
  } catch (error) {
    logI18n('error', 'logs.admin.stats.userStatsLoadFailed', error);
  }
};

// Panel Status speichern
watch(openPanels, (newValue) => {
  localStorage.setItem("UserStatPanelState", JSON.stringify(newValue));
});

onMounted(() => {
  fetchScenarioDetails();
  const savedPanels = localStorage.getItem("UserStatPanelState");
  if (savedPanels) {
    openPanels.value = JSON.parse(savedPanels);
  }
});
</script>


<style scoped>

.admin-dashboard {
  background-color: #ffffff;
  color: #2F4F4F;
  font-family: Arial, sans-serif;
}

.title-card, .legend-card {
  background-color: #b0ca97;
}

.title-card .v-card__title {
  color: #ffffff;
  padding: 12px 16px 4px;
}

.title-card .v-card__subtitle,
.legend-card .v-card__text {
  color: #556B2F;
  padding: 0 16px 12px;
}

.user-card {
  border: 1px solid #b0ca97;
  border-radius: 4px;
  transition: box-shadow 0.3s ease-in-out;
}

.user-card:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.legend-row,
.user-row {
  display: flex;
  align-items: center;
}

.checkbox-col {
  flex: 0 0 40px;
}

.username-col {
  flex: 0 0 100px;
}

.threads-col {
  flex: 0 0 150px;
}

.progress-col {
  flex: 1;
  padding-right: 16px;
}

.actions-col {
  flex: 0 0 80px;
  text-align: right;
  padding-left: 16px;
}

.username, .thread-info {
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.thread-info {
  color: #556B2F;
}

.v-btn {
  background-color: #b0ca97 !important;
  color: #2F4F4F !important;
}

.v-btn:hover {
  background-color: #556B2F !important;
  color: #ffffff !important;
}

.v-progress-linear {
  border-radius: 4px;
}

.v-progress-linear >>> .v-progress-linear__content {
  color: #2F4F4F;
  font-weight: bold;
}

/* Fortschrittsbalken Wrapper */
.progress-bar-wrapper {
  position: relative;
  height: 20px;
  background-color: #f1efd5; /* Hintergrundfarbe der Progressbar */
  border-radius: 10px;
  overflow: hidden;
}

/* Allgemeine Balken */
.progress-bar {
  height: 100%;
  position: absolute;
}

/* Farben der Balken */
.progress-bar-done {
  background-color: #e9f5ea; /* Grün für bewertete Threads */
}

.progress-bar-progressing {
  background-color: #f7ebd9; /* Gelb für teilweise bewertete Threads */
}

.progress-bar-not-started {
  background-color: #f3f3f3; /* Rot für nicht bewertete Threads */
}

/* Prozentzahlen (Labels) */
.progress-label {
  font-size: 12px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  white-space: nowrap;
}

/* Farben der Prozentzahlen */
.progress-label-done{
  color: #4aae4d;
}

.progress-label-progressing {
  color: #ff9c12;
}

.progress-label-not-started {
  color: #a1a1a1;
}


.global-progress-card {
  background-color: #f1efd5;
}

@media (max-width: 600px) {
  .user-row {
    flex-wrap: wrap;
  }

  .username-col,
  .threads-col,
  .progress-col,
  .actions-col {
    padding-top: 4px;
    padding-bottom: 4px;
  }

  .progress-col {
    flex-basis: 100%;
    padding-right: 0;
  }

  .actions-col {
    flex-basis: 100%;
    text-align: left;
    margin-top: 8px;
  }
}
</style>
