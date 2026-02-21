<template>
  <v-container class="oncoco-info" fluid>
    <!-- Hero Section -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card class="hero-card pa-6" elevation="0">
          <v-row align="center">
            <v-col cols="12" md="8">
              <div class="d-flex align-center mb-3">
                <div class="hero-icon mr-4">
                  <LIcon size="48" color="primary">mdi-message-text-outline</LIcon>
                </div>
                <div>
                  <h1 class="text-h3 font-weight-bold">{{ $t('oncoco.info.hero.title') }}</h1>
                  <p class="text-subtitle-1 text-medium-emphasis mb-0">
                    {{ $t('oncoco.info.hero.subtitle') }}
                  </p>
                </div>
              </div>
              <p class="text-body-1 mb-4" style="max-width: 700px;">
                {{ $t('oncoco.info.hero.description') }}
              </p>
              <div class="d-flex flex-wrap ga-2">
                <v-chip color="primary" variant="flat" size="small">
                  <LIcon start size="16">mdi-tag-multiple</LIcon>
                  {{ $t('oncoco.info.hero.chips.categories') }}
                </v-chip>
                <v-chip color="success" variant="flat" size="small">
                  <LIcon start size="16">mdi-chart-line</LIcon>
                  {{ $t('oncoco.info.hero.chips.f1') }}
                </v-chip>
                <v-chip color="info" variant="flat" size="small">
                  <LIcon start size="16">mdi-translate</LIcon>
                  {{ $t('oncoco.info.hero.chips.bilingual') }}
                </v-chip>
                <v-chip color="secondary" variant="flat" size="small">
                  <LIcon start size="16">mdi-database</LIcon>
                  {{ $t('oncoco.info.hero.chips.messages') }}
                </v-chip>
                <v-chip color="purple" variant="flat" size="small">
                  <LIcon start size="16">mdi-license</LIcon>
                  {{ $t('oncoco.info.hero.chips.license') }}
                </v-chip>
              </div>
            </v-col>
            <v-col cols="12" md="4" class="text-center">
              <v-card variant="tonal" color="primary" class="pa-4">
                <div class="text-overline mb-1">{{ $t('oncoco.info.hero.performance.title') }}</div>
                <div class="text-h2 font-weight-bold mb-2">{{ $t('oncoco.info.hero.performance.value') }}</div>
                <div class="text-caption">{{ $t('oncoco.info.hero.performance.subtitle') }}</div>
                <v-divider class="my-3"></v-divider>
                <div class="text-caption text-medium-emphasis">
                  {{ $t('oncoco.info.hero.performance.note') }}
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>

    <!-- Category System Explanation -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <LIcon color="primary" class="mr-2">mdi-sitemap</LIcon>
            {{ $t('oncoco.info.hierarchy.title') }}
          </v-card-title>
          <v-card-text>
            <p class="text-body-1 mb-4">
              {{ $t('oncoco.info.hierarchy.description') }}
            </p>

            <!-- Visual Hierarchy Example -->
            <v-card variant="outlined" class="mb-4 pa-4 hierarchy-example">
              <div class="text-subtitle-2 font-weight-bold mb-3">{{ $t('oncoco.info.hierarchy.exampleTitle') }}</div>
              <div class="code-breakdown">
                <div class="code-part">
                  <div class="code-value primary">CO</div>
                  <div class="code-label">{{ $t('oncoco.info.hierarchy.parts.role.label') }}</div>
                  <div class="code-desc">{{ $t('oncoco.info.hierarchy.parts.role.description') }}</div>
                </div>
                <LIcon class="code-separator">mdi-chevron-right</LIcon>
                <div class="code-part">
                  <div class="code-value success">IF</div>
                  <div class="code-label">{{ $t('oncoco.info.hierarchy.parts.level1.label') }}</div>
                  <div class="code-desc">{{ $t('oncoco.info.hierarchy.parts.level1.description') }}</div>
                </div>
                <LIcon class="code-separator">mdi-chevron-right</LIcon>
                <div class="code-part">
                  <div class="code-value info">AC</div>
                  <div class="code-label">{{ $t('oncoco.info.hierarchy.parts.level2.label') }}</div>
                  <div class="code-desc">{{ $t('oncoco.info.hierarchy.parts.level2.description') }}</div>
                </div>
                <LIcon class="code-separator">mdi-chevron-right</LIcon>
                <div class="code-part">
                  <div class="code-value warning">RF</div>
                  <div class="code-label">{{ $t('oncoco.info.hierarchy.parts.level3.label') }}</div>
                  <div class="code-desc">{{ $t('oncoco.info.hierarchy.parts.level3.description') }}</div>
                </div>
                <LIcon class="code-separator">mdi-chevron-right</LIcon>
                <div class="code-part">
                  <div class="code-value purple">RLS-SR</div>
                  <div class="code-label">{{ $t('oncoco.info.hierarchy.parts.level45.label') }}</div>
                  <div class="code-desc">{{ $t('oncoco.info.hierarchy.parts.level45.description') }}</div>
                </div>
              </div>
              <v-divider class="my-3"></v-divider>
              <div class="text-caption text-medium-emphasis">
                <LIcon size="small" class="mr-1">mdi-information</LIcon>
                {{ $t('oncoco.info.hierarchy.fullCodeLabel') }}
                <code class="bg-grey-lighten-3 px-2 py-1 rounded">CO-IF-AC-RF-RLS-SR</code>
                {{ $t('oncoco.info.hierarchy.fullCodeDescription') }}
              </div>
            </v-card>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Two Column: Counselor & Client Overview -->
    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-card class="h-100" color="primary" variant="tonal">
          <v-card-title class="d-flex align-center">
            <v-avatar color="primary" size="36" class="mr-3">
              <LIcon>mdi-account-tie</LIcon>
            </v-avatar>
            {{ $t('oncoco.info.counselor.title') }}
          </v-card-title>
          <v-card-text>
            <div class="text-h4 font-weight-bold mb-2">38</div>
            <div class="text-body-2 mb-4">{{ $t('oncoco.info.counselor.subtitle') }}</div>

            <v-table density="compact" class="category-table">
              <thead>
                <tr>
                  <th>{{ $t('oncoco.info.counselor.table.level1') }}</th>
                  <th>{{ $t('oncoco.info.counselor.table.level2') }}</th>
                  <th class="text-right">#</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.counselor.rows.formalities') }}</td>
                  <td class="text-right">1</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.counselor.rows.moderation') }}</td>
                  <td class="text-right">1</td>
                </tr>
                <tr>
                  <td rowspan="5" class="font-weight-bold">{{ $t('oncoco.info.counselor.rows.impactFactors') }}</td>
                  <td>{{ $t('oncoco.info.counselor.rows.analysis') }}</td>
                  <td class="text-right">13</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.counselor.rows.goalSetting') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.counselor.rows.motivation') }}</td>
                  <td class="text-right">4</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.counselor.rows.resourceActivation') }}</td>
                  <td class="text-right">5</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.counselor.rows.help') }}</td>
                  <td class="text-right">8</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.counselor.rows.closing') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.counselor.rows.other') }}</td>
                  <td class="text-right">2</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="h-100" color="secondary" variant="tonal">
          <v-card-title class="d-flex align-center">
            <v-avatar color="secondary" size="36" class="mr-3">
              <LIcon>mdi-account</LIcon>
            </v-avatar>
            {{ $t('oncoco.info.client.title') }}
          </v-card-title>
          <v-card-text>
            <div class="text-h4 font-weight-bold mb-2">28</div>
            <div class="text-body-2 mb-4">{{ $t('oncoco.info.client.subtitle') }}</div>

            <v-table density="compact" class="category-table">
              <thead>
                <tr>
                  <th>{{ $t('oncoco.info.client.table.level1') }}</th>
                  <th>{{ $t('oncoco.info.client.table.level2') }}</th>
                  <th class="text-right">#</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.client.rows.formalities') }}</td>
                  <td class="text-right">4</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.client.rows.empathy') }}</td>
                  <td class="text-right">3</td>
                </tr>
                <tr>
                  <td rowspan="5" class="font-weight-bold">{{ $t('oncoco.info.client.rows.impactFactors') }}</td>
                  <td>{{ $t('oncoco.info.client.rows.analysis') }}</td>
                  <td class="text-right">8</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.client.rows.goalSetting') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.client.rows.motivation') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.client.rows.resourceActivation') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>{{ $t('oncoco.info.client.rows.help') }}</td>
                  <td class="text-right">6</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.client.rows.closing') }}</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td colspan="2">{{ $t('oncoco.info.client.rows.other') }}</td>
                  <td class="text-right">2</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Impact Factors Explanation -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <LIcon color="warning" class="mr-2">mdi-star-four-points</LIcon>
            {{ $t('oncoco.info.impactFactors.title') }}
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              {{ $t('oncoco.info.impactFactors.alert') }}
            </v-alert>

            <v-row>
              <v-col cols="12" sm="6" md="4" v-for="factor in impactFactors" :key="factor.code">
                <v-card variant="outlined" class="h-100">
                  <v-card-title class="text-subtitle-1">
                    <v-chip :color="factor.color" size="x-small" class="mr-2">{{ factor.code }}</v-chip>
                    {{ factor.name }}
                  </v-card-title>
                  <v-card-text class="text-body-2">
                    {{ factor.description }}
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Use Cases & Model Info -->
    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-card class="h-100">
          <v-card-title class="d-flex align-center">
            <LIcon color="success" class="mr-2">mdi-target</LIcon>
            {{ $t('oncoco.info.useCases.title') }}
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-chart-bar">
                <v-list-item-title>{{ $t('oncoco.info.useCases.items.quality.title') }}</v-list-item-title>
                <v-list-item-subtitle>{{ $t('oncoco.info.useCases.items.quality.subtitle') }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-school">
                <v-list-item-title>{{ $t('oncoco.info.useCases.items.training.title') }}</v-list-item-title>
                <v-list-item-subtitle>{{ $t('oncoco.info.useCases.items.training.subtitle') }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-flask">
                <v-list-item-title>{{ $t('oncoco.info.useCases.items.research.title') }}</v-list-item-title>
                <v-list-item-subtitle>{{ $t('oncoco.info.useCases.items.research.subtitle') }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-robot">
                <v-list-item-title>{{ $t('oncoco.info.useCases.items.chatbot.title') }}</v-list-item-title>
                <v-list-item-subtitle>{{ $t('oncoco.info.useCases.items.chatbot.subtitle') }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-alert">
                <v-list-item-title>{{ $t('oncoco.info.useCases.items.risk.title') }}</v-list-item-title>
                <v-list-item-subtitle>{{ $t('oncoco.info.useCases.items.risk.subtitle') }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="h-100">
          <v-card-title class="d-flex align-center">
            <LIcon color="info" class="mr-2">mdi-chip</LIcon>
            {{ $t('oncoco.info.model.title') }}
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <tbody>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.baseModel') }}</td>
                  <td>{{ $t('oncoco.info.model.baseModelValue') }}</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.accuracy') }}</td>
                  <td>~0.80</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.f1Macro1') }}</td>
                  <td>~0.78</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.f1Macro2') }}</td>
                  <td>{{ $t('oncoco.info.model.f1Macro2Value') }}</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.kappa') }}</td>
                  <td>{{ $t('oncoco.info.model.kappaValue') }}</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">{{ $t('oncoco.info.model.roleMasking') }}</td>
                  <td>{{ $t('oncoco.info.model.roleMaskingValue') }}</td>
                </tr>
              </tbody>
            </v-table>

            <v-alert type="warning" variant="tonal" density="compact" class="mt-3">
              {{ $t('oncoco.info.model.warning') }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Sample Classifications -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <LIcon color="purple" class="mr-2">mdi-text-box-search</LIcon>
            {{ $t('oncoco.info.examples.title') }}
          </v-card-title>
          <v-card-text>
            <v-table density="comfortable" class="examples-table">
              <thead>
                <tr>
                  <th style="width: 80px;">{{ $t('oncoco.info.examples.headers.role') }}</th>
                  <th style="width: 150px;">{{ $t('oncoco.info.examples.headers.code') }}</th>
                  <th>{{ $t('oncoco.info.examples.headers.text') }}</th>
                  <th style="width: 250px;">{{ $t('oncoco.info.examples.headers.path') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="example in exampleClassifications" :key="example.code">
                  <td>
                    <v-chip :color="example.role === 'CO' ? 'primary' : 'secondary'" size="small">
                      {{ example.role === 'CO' ? $t('oncoco.results.roles.counselor') : $t('oncoco.results.roles.client') }}
                    </v-chip>
                  </td>
                  <td><code class="text-caption">{{ example.code }}</code></td>
                  <td class="text-body-2 fst-italic">"{{ example.text }}"</td>
                  <td class="text-caption">{{ example.path }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Resources & Links -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card variant="tonal" color="primary">
          <v-card-title class="d-flex align-center">
            <LIcon class="mr-2">mdi-link-variant</LIcon>
            {{ $t('oncoco.info.resources.title') }}
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>{{ $t('oncoco.info.resources.paper.title') }}</v-list-subheader>
                  <v-list-item
                    href="https://anonymous.4open.science/r/OnCoCoV1-78E8"
                    target="_blank"
                    prepend-icon="mdi-file-document"
                  >
                    <v-list-item-title>{{ $t('oncoco.info.resources.paper.itemTitle') }}</v-list-item-title>
                    <v-list-item-subtitle>{{ $t('oncoco.info.resources.paper.itemSubtitle') }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>{{ $t('oncoco.info.resources.license.title') }}</v-list-subheader>
                  <v-list-item prepend-icon="mdi-license">
                    <v-list-item-title>{{ $t('oncoco.info.resources.license.itemTitle') }}</v-list-item-title>
                    <v-list-item-subtitle>{{ $t('oncoco.info.resources.license.itemSubtitle') }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>{{ $t('oncoco.info.resources.api.title') }}</v-list-subheader>
                  <v-list-item prepend-icon="mdi-api">
                    <v-list-item-title><code>/api/oncoco/info</code></v-list-item-title>
                    <v-list-item-subtitle>{{ $t('oncoco.info.resources.api.itemSubtitle') }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Expandable Label Lists -->
    <v-row>
      <v-col cols="12">
        <v-expansion-panels variant="accordion">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <LIcon color="primary" class="mr-2">mdi-account-tie</LIcon>
              <span class="font-weight-bold">{{ $t('oncoco.info.labels.counselorTitle', { count: counselorLabels.length }) }}</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact" hover>
                <thead>
                  <tr>
                    <th style="width: 180px;">{{ $t('oncoco.info.labels.headers.code') }}</th>
                    <th style="width: 250px;">{{ $t('oncoco.info.labels.headers.name') }}</th>
                    <th>{{ $t('oncoco.info.labels.headers.description') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="label in counselorLabels" :key="label.code">
                    <td><code class="text-caption">{{ label.code }}</code></td>
                    <td class="font-weight-medium">{{ label.name }}</td>
                    <td class="text-body-2">{{ label.description }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>
              <LIcon color="secondary" class="mr-2">mdi-account</LIcon>
              <span class="font-weight-bold">{{ $t('oncoco.info.labels.clientTitle', { count: clientLabels.length }) }}</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact" hover>
                <thead>
                  <tr>
                    <th style="width: 180px;">{{ $t('oncoco.info.labels.headers.code') }}</th>
                    <th style="width: 250px;">{{ $t('oncoco.info.labels.headers.name') }}</th>
                    <th>{{ $t('oncoco.info.labels.headers.description') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="label in clientLabels" :key="label.code">
                    <td><code class="text-caption">{{ label.code }}</code></td>
                    <td class="font-weight-medium">{{ label.name }}</td>
                    <td class="text-body-2">{{ label.description }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>

    <!-- Call to Action -->
    <v-row class="mt-6">
      <v-col cols="12">
        <v-alert type="info" variant="tonal" prominent>
          <template v-slot:prepend>
            <LIcon size="large">mdi-rocket-launch</LIcon>
          </template>
          <v-alert-title>{{ $t('oncoco.info.cta.title') }}</v-alert-title>
          <p class="mb-2">
            {{ $t('oncoco.info.cta.body') }}
          </p>
          <v-btn
            color="primary"
            variant="flat"
            :to="{ name: 'OnCoCoOverview' }"
            prepend-icon="mdi-play"
          >
            {{ $t('oncoco.info.cta.button') }}
          </v-btn>
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { tm } = useI18n()

const impactFactors = computed(() => tm('oncoco.info.impactFactors.items') || [])
const exampleClassifications = computed(() => tm('oncoco.info.examples.items') || [])
const counselorLabels = computed(() => tm('oncoco.info.labels.counselorItems') || [])
const clientLabels = computed(() => tm('oncoco.info.labels.clientItems') || [])
</script>

<style scoped>
.oncoco-info {
  max-width: 1400px;
  margin: 0 auto;
}

.hero-card {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.05),
    rgba(var(--v-theme-secondary), 0.05)
  );
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
}

.hero-icon {
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 16px;
  padding: 16px;
}

.hierarchy-example {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.code-breakdown {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.code-part {
  text-align: center;
  min-width: 80px;
}

.code-value {
  font-family: monospace;
  font-weight: bold;
  font-size: 1.1rem;
  padding: 4px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.code-value.primary { background: rgba(var(--v-theme-primary), 0.2); color: rgb(var(--v-theme-primary)); }
.code-value.success { background: rgba(var(--v-theme-success), 0.2); color: rgb(var(--v-theme-success)); }
.code-value.info { background: rgba(var(--v-theme-info), 0.2); color: rgb(var(--v-theme-info)); }
.code-value.warning { background: rgba(var(--v-theme-warning), 0.2); color: rgb(var(--v-theme-warning)); }
.code-value.purple { background: rgba(156, 39, 176, 0.2); color: #9c27b0; }

.code-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
  letter-spacing: 0.5px;
}

.code-desc {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  max-width: 120px;
}

.code-separator {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.category-table {
  font-size: 0.875rem;
}

.category-table th {
  font-weight: 600 !important;
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.examples-table {
  font-size: 0.875rem;
}

.examples-table td {
  vertical-align: top;
  padding-top: 12px;
  padding-bottom: 12px;
}

code {
  font-size: 0.8em;
  background: rgba(var(--v-theme-on-surface), 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

@media (max-width: 960px) {
  .code-breakdown {
    justify-content: center;
  }

  .code-separator {
    display: none;
  }

  .code-part {
    margin-bottom: 8px;
  }
}
</style>
