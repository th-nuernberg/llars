<!--
  ChatbotEditor - Web Crawler Tab

  Web crawler configuration for automatic website scraping.
-->
<template>
  <v-row>
    <v-col cols="12">
      <v-alert type="info" variant="tonal" class="mb-4">
        <template #prepend>
          <LIcon>mdi-spider-web</LIcon>
        </template>
        <div class="text-subtitle-2">Website automatisch crawlen</div>
        <div class="text-body-2">
          Geben Sie URLs ein, die automatisch gecrawlt und als RAG-Collection für diesen Chatbot hinzugefügt werden sollen.
        </div>
      </v-alert>
    </v-col>

    <v-col cols="12">
      <v-textarea
        v-model="localUrls"
        label="URLs zum Crawlen"
        placeholder="https://example.com&#10;https://docs.example.com"
        hint="Eine URL pro Zeile. Der Crawler folgt internen Links automatisch."
        persistent-hint
        rows="4"
        variant="outlined"
        @update:model-value="$emit('update:crawlerUrls', $event)"
      />
    </v-col>

    <v-col cols="12">
      <v-expansion-panels>
        <v-expansion-panel>
          <v-expansion-panel-title>
            <LIcon start>mdi-cog</LIcon>
            Crawler-Einstellungen
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  :model-value="crawlerMaxPages"
                  label="Max. Seiten pro URL"
                  type="number"
                  min="1"
                  max="100"
                  variant="outlined"
                  density="compact"
                  @update:model-value="$emit('update:crawlerMaxPages', Number($event))"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  :model-value="crawlerMaxDepth"
                  label="Max. Link-Tiefe"
                  type="number"
                  min="1"
                  max="5"
                  variant="outlined"
                  density="compact"
                  @update:model-value="$emit('update:crawlerMaxDepth', Number($event))"
                />
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-col>

    <!-- Crawl Status -->
    <v-col v-if="crawlStatus" cols="12">
      <v-alert
        :type="crawlStatus.success ? 'success' : crawlStatus.error ? 'error' : 'info'"
        variant="tonal"
      >
        <div class="font-weight-bold">{{ crawlStatus.message }}</div>
        <div v-if="crawlStatus.pages_crawled !== undefined" class="text-body-2">
          {{ crawlStatus.pages_crawled }} Seiten gecrawlt
          <template v-if="crawlStatus.documents_created">,
            {{ crawlStatus.documents_created }} Dokumente erstellt
          </template>
        </div>
        <!-- Progress bar -->
        <v-progress-linear
          v-if="crawling && crawlProgress"
          :model-value="(crawlProgress.pages_crawled / crawlProgress.max_pages) * 100"
          color="primary"
          height="8"
          rounded
          class="mt-2"
        >
          <template v-slot:default>
            {{ crawlProgress.pages_crawled }} / {{ crawlProgress.max_pages }}
          </template>
        </v-progress-linear>
        <!-- Current URL being crawled -->
        <div v-if="crawlStatus.current_url" class="text-caption text-truncate mt-1">
          <LIcon size="small">mdi-link</LIcon>
          {{ crawlStatus.current_url }}
        </div>
      </v-alert>

      <!-- Live crawled pages list -->
      <v-card v-if="crawling && crawledPages.length > 0" variant="outlined" class="mt-2">
        <v-card-title class="text-subtitle-2 py-2">
          <LIcon start size="small">mdi-format-list-bulleted</LIcon>
          Zuletzt gecrawlte Seiten
        </v-card-title>
        <v-list dense class="py-0" style="max-height: 150px; overflow-y: auto;">
          <v-list-item
            v-for="(url, index) in crawledPages"
            :key="index"
            density="compact"
            class="text-caption"
          >
            <LIcon start size="x-small" color="success">mdi-check</LIcon>
            <span class="text-truncate">{{ url }}</span>
          </v-list-item>
        </v-list>
      </v-card>
    </v-col>

    <v-col cols="12">
      <LBtn
        variant="outlined"
        :loading="crawling"
        :disabled="!hasValidCrawlerUrls"
        prepend-icon="mdi-spider-web"
        @click="$emit('start-crawl')"
      >
        Website crawlen und Collection erstellen
      </LBtn>
    </v-col>
  </v-row>
</template>

<script setup>
/**
 * @component CrawlerTab
 * @description Web crawler configuration for automatic website scraping.
 */
import { ref, watch } from 'vue';

const props = defineProps({
  /** URLs to crawl (newline separated) */
  crawlerUrls: {
    type: String,
    default: ''
  },
  /** Maximum pages per URL */
  crawlerMaxPages: {
    type: Number,
    default: 10
  },
  /** Maximum link depth */
  crawlerMaxDepth: {
    type: Number,
    default: 3
  },
  /** Crawling in progress */
  crawling: {
    type: Boolean,
    default: false
  },
  /** Current crawl status */
  crawlStatus: {
    type: Object,
    default: null
  },
  /** Crawl progress data */
  crawlProgress: {
    type: Object,
    default: null
  },
  /** List of crawled page URLs */
  crawledPages: {
    type: Array,
    default: () => []
  },
  /** Whether valid URLs are entered */
  hasValidCrawlerUrls: {
    type: Boolean,
    default: false
  }
});

defineEmits([
  'update:crawlerUrls',
  'update:crawlerMaxPages',
  'update:crawlerMaxDepth',
  'start-crawl'
]);

// Local copy for v-model
const localUrls = ref(props.crawlerUrls);

watch(() => props.crawlerUrls, (val) => {
  localUrls.value = val;
});
</script>
