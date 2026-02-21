<template>
  <v-container class="oncoco-config">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-btn
          variant="text"
          prepend-icon="mdi-arrow-left"
          @click="router.push({ name: 'OnCoCoOverview' })"
        >
          {{ $t('oncoco.config.back') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <LIcon class="mr-2" color="primary">mdi-cog</LIcon>
            {{ $t('oncoco.config.title') }}
          </v-card-title>

          <v-card-text>
            <v-form ref="formRef" v-model="formValid">
              <!-- Analysis Name -->
              <v-text-field
                v-model="config.name"
                :label="$t('oncoco.config.form.nameLabel')"
                :placeholder="$t('oncoco.config.form.namePlaceholder')"
                :rules="[v => !!v || $t('validation.required')]"
                prepend-icon="mdi-label"
                variant="outlined"
                class="mb-4"
              ></v-text-field>

              <!-- Pillar Selection -->
              <div class="text-subtitle-1 font-weight-medium mb-2">
                <LIcon class="mr-1">mdi-database</LIcon>
                {{ $t('oncoco.config.form.pillarsTitle') }}
              </div>
              <v-row class="mb-4">
                <v-col
                  v-for="(pillar, pillarNum) in availablePillars"
                  :key="pillarNum"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-card
                    :variant="config.pillars.includes(Number(pillarNum)) ? 'tonal' : 'outlined'"
                    :color="config.pillars.includes(Number(pillarNum)) ? 'primary' : undefined"
                    class="pillar-card"
                    @click="togglePillar(Number(pillarNum))"
                  >
                    <v-card-text>
                      <div class="d-flex align-center">
                        <v-checkbox
                          :model-value="config.pillars.includes(Number(pillarNum))"
                          hide-details
                          density="compact"
                        @click.stop
                        @update:model-value="togglePillar(Number(pillarNum))"
                      ></v-checkbox>
                      <div class="ml-2">
                        <div class="font-weight-bold">{{ $t('oncoco.config.form.pillarLabel', { id: pillarNum }) }}</div>
                        <div class="text-caption">{{ pillar.name }}</div>
                      </div>
                    </div>
                    <v-divider class="my-2"></v-divider>
                    <div class="d-flex justify-space-between text-caption">
                      <span>{{ $t('oncoco.config.form.threadsLabel') }}</span>
                      <span class="font-weight-bold">{{ pillar.db_thread_count || 0 }}</span>
                    </div>
                    <div class="d-flex justify-space-between text-caption">
                      <span>{{ $t('oncoco.config.form.statusLabel') }}</span>
                      <v-chip
                        :color="pillar.db_thread_count > 0 ? 'success' : 'warning'"
                        size="x-small"
                      >
                        {{ pillar.db_thread_count > 0 ? $t('oncoco.config.form.statusReady') : $t('oncoco.config.form.statusSync') }}
                      </v-chip>
                    </div>
                  </v-card-text>
                </v-card>
                </v-col>
              </v-row>

              <!-- Advanced Options -->
              <v-expansion-panels class="mb-4">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <LIcon class="mr-2">mdi-tune</LIcon>
                    {{ $t('oncoco.config.form.advancedTitle') }}
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="config.use_level2"
                      :label="$t('oncoco.config.form.useLevel2Label')"
                      :hint="$t('oncoco.config.form.useLevel2Hint')"
                      persistent-hint
                      color="primary"
                    ></v-switch>

                    <v-slider
                      v-model="config.batch_size"
                      :label="$t('oncoco.config.form.batchSizeLabel')"
                      min="4"
                      max="64"
                      step="4"
                      thumb-label
                      :hint="$t('oncoco.config.form.batchSizeHint')"
                      persistent-hint
                      class="mt-4"
                    ></v-slider>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-form>
          </v-card-text>

          <v-card-actions class="pa-4">
            <v-btn
              variant="text"
              @click="router.push({ name: 'OnCoCoOverview' })"
            >
              {{ $t('common.cancel') }}
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-content-save"
              :disabled="!formValid || config.pillars.length === 0"
              :loading="creating"
              @click="createAnalysis"
            >
              {{ $t('oncoco.config.actions.create') }}
            </v-btn>
            <v-btn
              color="success"
              variant="flat"
              prepend-icon="mdi-play"
              :disabled="!formValid || config.pillars.length === 0"
              :loading="creating"
              @click="createAndStartAnalysis"
            >
              {{ $t('oncoco.config.actions.createAndStart') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Info Panel -->
      <v-col cols="12" md="4">
        <v-card class="mb-4">
          <v-card-title>
            <LIcon class="mr-2" color="info">mdi-information</LIcon>
            {{ $t('oncoco.config.info.title') }}
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-3">
              {{ $t('oncoco.config.info.description') }}
            </p>
            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('oncoco.config.info.categoriesTitle') }}</div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>{{ $t('oncoco.config.info.counselorLabel') }}</span>
              <span class="font-weight-bold">40</span>
            </div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>{{ $t('oncoco.config.info.clientLabel') }}</span>
              <span class="font-weight-bold">28</span>
            </div>
            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('oncoco.config.info.metricsTitle') }}</div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>{{ $t('oncoco.config.info.accuracyLabel') }}</span>
              <span class="font-weight-bold">~80%</span>
            </div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>{{ $t('oncoco.config.info.f1Label') }}</span>
              <span class="font-weight-bold">0.78</span>
            </div>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title>
            <LIcon class="mr-2" color="warning">mdi-alert</LIcon>
            {{ $t('oncoco.config.notes.title') }}
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" density="compact" class="mb-2">
              {{ $t('oncoco.config.notes.info') }}
            </v-alert>
            <v-alert type="warning" variant="tonal" density="compact">
              {{ $t('oncoco.config.notes.warning') }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

// Form State
const formRef = ref(null);
const formValid = ref(false);
const creating = ref(false);

const config = reactive({
  name: '',
  pillars: [1, 3, 5],  // Default active pillars
  use_level2: true,
  batch_size: 16
});

const availablePillars = ref({});

// Load Pillar Status
const loadPillarStatus = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/pillars`);
    availablePillars.value = response.data.pillars || {};
  } catch (error) {
    console.error('Error loading pillar status:', error);
  }
};

// Toggle Pillar Selection
const togglePillar = (pillarNum) => {
  const idx = config.pillars.indexOf(pillarNum);
  if (idx > -1) {
    config.pillars.splice(idx, 1);
  } else {
    config.pillars.push(pillarNum);
    config.pillars.sort();
  }
};

// Create Analysis
const createAnalysis = async (startImmediately = false) => {
  if (!formValid.value || config.pillars.length === 0) return;

  creating.value = true;
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses`,
      {
        name: config.name,
        pillars: config.pillars,
        use_level2: config.use_level2,
        batch_size: config.batch_size
      }
    );

    const analysisId = response.data.id;

    if (startImmediately) {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/start`,
        {},
        { headers: { 'Content-Type': 'application/json' } }
      );
    }

    router.push({ name: 'OnCoCoResults', params: { id: analysisId } });
  } catch (error) {
    console.error('Error creating analysis:', error);
  } finally {
    creating.value = false;
  }
};

const createAndStartAnalysis = () => {
  createAnalysis(true);
};

// Lifecycle
onMounted(() => {
  loadPillarStatus();
});
</script>

<style scoped>
.oncoco-config {
  max-width: 1200px;
  margin: 0 auto;
}

.pillar-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.pillar-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
