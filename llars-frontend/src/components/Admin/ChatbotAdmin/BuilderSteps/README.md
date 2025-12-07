# Chatbot Builder Steps

This directory contains the step components for the multi-step Chatbot Builder Wizard.

## Architecture

The wizard has been refactored from a monolithic 1147-line component into modular step components:

```
ChatbotBuilderWizard.vue (584 lines) - Container
├── StepCrawlerConfig.vue - Step 1: URL & Crawler Configuration
├── StepCollectionSetup.vue - Steps 2 & 3: Crawling & Embedding Progress
├── StepChatbotConfig.vue - Step 4: Chatbot Configuration
└── StepReview.vue - Step 5: Review & Completion
```

## Components

### StepCrawlerConfig.vue
**Purpose:** URL input and crawler configuration
- URL validation
- Advanced crawler settings (max pages, max depth)
- Error display

**Props:**
- `url` (String) - The website URL to crawl
- `config` (Object) - Crawler configuration (maxPages, maxDepth)
- `errorMessage` (String) - Error message to display

**Events:**
- `update:url` - URL changed
- `update:config` - Configuration changed
- `start` - Start wizard/crawling

### StepCollectionSetup.vue
**Purpose:** Combined crawling and embedding progress display
- Real-time crawling progress with page list
- Embedding progress tracking
- Option to skip to configuration while processing
- Stats display (documents, chunks, elapsed time)

**Props:**
- `buildStatus` (String) - Current build status (crawling/embedding)
- `crawlProgress` (Object) - Crawling progress data
- `embeddingProgress` (Number) - Embedding progress percentage
- `collectionInfo` (Object) - Collection metadata
- `errorMessage` (String) - Error message to display

**Events:**
- `skip-to-config` - Skip to configuration step
- `pause` - Pause the build process

### StepChatbotConfig.vue
**Purpose:** Chatbot configuration with AI-powered field generation
- Name, display name configuration
- System prompt and welcome message
- Icon and color customization
- AI field generation

**Props:**
- `config` (Object) - Chatbot configuration data
- `buildStatus` (String) - Current build status
- `crawlProgress` (Object) - Crawl progress (for background banner)
- `embeddingProgress` (Number) - Embedding progress (for background banner)
- `generatingFields` (Object) - Field generation loading states
- `canGenerate` (Boolean) - Whether AI generation is available

**Events:**
- `update:config` - Configuration changed
- `generate-field` - Generate field with AI (field name)

### StepReview.vue
**Purpose:** Final review and completion screen
- Success confirmation
- Chatbot preview card
- Collection statistics
- Test and close actions

**Props:**
- `config` (Object) - Final chatbot configuration
- `url` (String) - Source URL
- `collectionInfo` (Object) - Collection metadata

**Events:**
- `test` - Test the chatbot
- `close` - Close the wizard

## Composables

### useBuilderState.js
**Purpose:** Centralized state management for the wizard

**Exports:**
- State refs: `currentStep`, `loading`, `chatbotId`, `buildStatus`, `wizardData`, etc.
- Computed: `isProcessing`, `crawlProgressPercent`
- Navigation: `canNavigateToStep()`, `navigateToStep()`
- Updates: `updateCrawlProgress()`, `updateEmbeddingProgress()`, etc.
- Reset: `resetWizard()`, `resetErrors()`

### useBuilderValidation.js
**Purpose:** Validation rules and helper functions

**Exports:**
- `rules` - Vuetify validation rules (required, url)
- `formatDuration()` - Format seconds to human-readable duration
- `extractPageTitle()` - Extract title from URL
- `validateUrl()` - Validate URL format
- `validateConfig()` - Validate chatbot configuration

## Usage Example

```vue
<script setup>
import { useBuilderState } from '@/composables/useBuilderState'
import StepCrawlerConfig from './BuilderSteps/StepCrawlerConfig.vue'

const {
  wizardData,
  crawlerConfig,
  errors,
  startWizard
} = useBuilderState()
</script>

<template>
  <StepCrawlerConfig
    v-model:url="wizardData.url"
    v-model:config="crawlerConfig"
    :error-message="errors.url"
    @start="startWizard"
  />
</template>
```

## State Flow

1. **Step 1 (URL Config):** User enters URL → Validates → Creates wizard chatbot
2. **Step 2 (Crawling):** Backend crawls pages → Socket.IO updates → Progress display
3. **Step 3 (Embedding):** Backend creates embeddings → Socket.IO updates → Progress display
4. **Step 4 (Configuration):** User configures chatbot → Optional AI generation
5. **Step 5 (Review):** Final review → Test or close

## Socket.IO Events

The wizard subscribes to these events:

**Crawler:**
- `crawler:progress` - Overall crawling progress
- `crawler:page_crawled` - Individual page crawled
- `crawler:complete` - Crawling finished
- `crawler:error` - Crawling error

**RAG/Embedding:**
- `rag:collection_progress` - Embedding progress
- `rag:collection_completed` - Embedding finished
- `rag:collection_error` - Embedding error

## Benefits of Refactoring

1. **Reduced Complexity:** Main component reduced from 1147 to 584 lines (49% reduction)
2. **Reusability:** Step components can be tested and used independently
3. **Maintainability:** Each step has clear responsibilities
4. **State Management:** Centralized state in composable
5. **Testability:** Smaller components are easier to unit test
6. **Code Organization:** Related functionality grouped together

## File Structure

```
ChatbotAdmin/
├── ChatbotBuilderWizard.vue (584 lines)
├── BuilderSteps/
│   ├── README.md (this file)
│   ├── StepCrawlerConfig.vue
│   ├── StepCollectionSetup.vue
│   ├── StepChatbotConfig.vue
│   └── StepReview.vue
└── composables/
    ├── useBuilderState.js
    └── useBuilderValidation.js
```
