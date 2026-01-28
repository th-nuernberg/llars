<template>
  <v-card class="scenario-wizard">
    <!-- Header -->
    <v-card-title class="wizard-header">
      <LIcon color="primary" class="mr-3" size="28">mdi-robot-outline</LIcon>
      <span>{{ $t('scenarioManager.wizard.title') }}</span>
      <v-spacer />
      <v-btn icon variant="text" @click="$emit('close')">
        <LIcon>mdi-close</LIcon>
      </v-btn>
    </v-card-title>

    <!-- AI-Native Badge -->
    <div class="ai-badge">
      <LIcon size="16" color="primary">mdi-sparkles</LIcon>
      <span>{{ $t('scenarioManager.wizard.aiPowered') }}</span>
    </div>

    <!-- Stepper -->
    <div class="wizard-stepper">
      <div
        v-for="(step, index) in steps"
        :key="step.key"
        class="step"
        :class="{
          active: currentStep === index,
          completed: currentStep > index,
          clickable: currentStep > index
        }"
        @click="currentStep > index && goToStep(index)"
      >
        <div class="step-indicator">
          <LIcon v-if="currentStep > index" size="18">mdi-check</LIcon>
          <LIcon v-else-if="step.icon" size="18">{{ step.icon }}</LIcon>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <span class="step-label">{{ step.label }}</span>
      </div>
    </div>

    <v-divider />

    <!-- Step Content -->
    <v-card-text class="wizard-content">
      <!-- Step 1: Data Upload & AI Analysis -->
      <div v-if="currentStep === 0" class="step-content">
        <div class="step-title-row">
          <h3 class="step-title">{{ $t('scenarioManager.wizard.step1.title') }}</h3>
          <LInfoTooltip
            :title="$t('scenarioManager.wizard.step1.dataFormatTooltipTitle')"
            :aria-label="$t('scenarioManager.wizard.step1.dataFormatTooltipTitle')"
            location="bottom"
            max-width="520"
          >
            <div>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipIntro') }}</div>
            <ul>
              <li>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipItem1') }}</li>
              <li>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipItem2') }}</li>
              <li>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipItem3') }}</li>
              <li>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipItem4') }}</li>
              <li>{{ $t('scenarioManager.wizard.step1.dataFormatTooltipItem5') }}</li>
            </ul>
            <div class="mt-3"><strong>{{ $t('scenarioManager.wizard.step1.idealDataTitle') }}</strong></div>
            <div class="format-examples">
              <div class="format-example">
                <span class="format-label">{{ $t('scenarioManager.wizard.step1.idealDataSingleLabel') }}:</span>
                <code>{{ codeExamples.single }}</code>
              </div>
              <div class="format-example">
                <span class="format-label">{{ $t('scenarioManager.wizard.step1.idealDataRankingLabel') }}:</span>
                <code>{{ codeExamples.ranking }}</code>
                <div class="format-hint">{{ $t('scenarioManager.wizard.step1.idealDataRankingHint') }}</div>
              </div>
              <div class="format-example">
                <span class="format-label">{{ $t('scenarioManager.wizard.step1.idealDataComparisonLabel') }}:</span>
                <code>{{ codeExamples.comparison }}</code>
              </div>
            </div>
          </LInfoTooltip>
        </div>
        <p class="step-description">{{ $t('scenarioManager.wizard.step1.description') }}</p>

        <!-- File Upload Area -->
        <div
          class="upload-zone"
          :class="{ 'drag-over': isDragging, 'has-files': uploadedFiles.length > 0 }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleFileDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".json,.csv,.xlsx,.xls"
            multiple
            hidden
            @change="handleFileSelect"
          />

          <template v-if="uploadedFiles.length === 0">
            <LIcon size="48" color="primary" class="upload-icon">mdi-cloud-upload-outline</LIcon>
            <p class="upload-text">{{ $t('scenarioManager.wizard.step1.dropFiles') }}</p>
            <p class="upload-hint">{{ $t('scenarioManager.wizard.step1.supportedFormats') }}</p>
            <p class="upload-hint-multi">
              <LIcon size="14" class="mr-1">mdi-information-outline</LIcon>
              {{ $t('scenarioManager.wizard.step1.multiFileHint') }}
            </p>
          </template>

          <template v-else>
            <div class="files-list" @click.stop>
              <div class="files-header">
                <span class="files-count">
                  <LIcon size="18" class="mr-1">mdi-file-multiple</LIcon>
                  {{ uploadedFiles.length }} {{ $t('scenarioManager.wizard.step1.filesSelected') }}
                </span>
                <v-btn size="small" variant="text" color="primary" @click.stop="triggerFileInput">
                  <LIcon start size="16">mdi-plus</LIcon>
                  {{ $t('scenarioManager.wizard.step1.addMore') }}
                </v-btn>
              </div>
              <div class="files-scroll">
                <div
                  v-for="(file, index) in uploadedFiles"
                  :key="file.name + index"
                  class="file-item"
                >
                  <LIcon size="24" :color="getFileColor(file.name)">
                    {{ getFileIcon(file.name) }}
                  </LIcon>
                  <div class="file-details">
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                  <v-btn icon size="small" variant="text" @click.stop="removeFile(index)">
                    <LIcon size="16">mdi-close</LIcon>
                  </v-btn>
                </div>
              </div>
              <div class="files-footer">
                <span class="total-size">
                  {{ $t('scenarioManager.wizard.step1.totalSize') }}: {{ formatFileSize(totalFileSize) }}
                </span>
                <v-btn size="small" variant="text" color="error" @click.stop="clearAllFiles">
                  <LIcon start size="16">mdi-delete-outline</LIcon>
                  {{ $t('scenarioManager.wizard.step1.clearAll') }}
                </v-btn>
              </div>
            </div>
          </template>
        </div>

        <!-- AI Analysis Section -->
        <div v-if="uploadedFiles.length > 0" class="ai-analysis-section">
          <div class="analysis-header">
            <LIcon color="primary" class="mr-2">mdi-robot</LIcon>
            <span>{{ $t('scenarioManager.wizard.step1.aiAnalysis') }}</span>
          </div>

          <!-- Start Analysis Button (before analysis) -->
          <LBtn
            v-if="!analyzing && !analysisResult && !streamingPhase"
            variant="primary"
            @click="analyzeData"
          >
            <LIcon start>mdi-magnify-scan</LIcon>
            {{ $t('scenarioManager.wizard.step1.startAnalysis') }}
          </LBtn>

          <!-- Streaming Analysis Panel (during and after analysis) -->
          <StreamingAnalysisPanel
            v-if="analyzing || analysisResult || streamingPhase"
            ref="analysisPanel"
            :analyzed-data="analyzedData"
            :data-summary="dataSummaryForPanel"
            :data-quality="analysisResult?.dataQuality"
            :show-chat="streamingPhase === 'done' && analysisResult?.aiPowered"
            @update:config="handleAnalysisPanelConfigUpdate"
            @regenerate="reanalyzeData"
          />
        </div>
      </div>

      <!-- Step 2: Task Definition -->
      <div v-if="currentStep === 1" class="step-content">
        <h3 class="step-title">{{ $t('scenarioManager.wizard.step2.title') }}</h3>
        <p class="step-description">{{ $t('scenarioManager.wizard.step2.description') }}</p>

        <!-- AI Suggestion Banner -->
        <v-alert
          v-if="analysisResult?.suggestedType"
          type="info"
          variant="tonal"
          class="mb-4"
        >
          <template v-slot:prepend>
            <LIcon>mdi-robot</LIcon>
          </template>
          {{ $t('scenarioManager.wizard.step2.aiSuggests', { type: getSuggestedTypeName(analysisResult.suggestedType) }) }}
        </v-alert>

        <!-- Evaluation Type Selection - General Types -->
        <div class="type-category">
          <h4 class="type-category-title">
            <LIcon color="primary" size="20" class="mr-2">mdi-view-grid</LIcon>
            {{ $t('scenarioManager.wizard.step2.generalTypes') }}
          </h4>
          <p class="type-category-description">
            {{ $t('scenarioManager.wizard.step2.generalTypesDescription') }}
          </p>
          <div class="type-grid">
            <div
              v-for="type in evaluationTypesGrouped.general"
              :key="type.id"
              class="type-card"
              :class="{
                selected: formData.evalType === type.id,
                suggested: analysisResult?.suggestedType === type.id
              }"
              @click="selectEvalType(type.id)"
            >
              <div class="type-icon" :style="{ backgroundColor: type.color + '20' }">
                <LIcon :color="type.color" size="32">{{ type.icon }}</LIcon>
              </div>
              <h4 class="type-name">{{ type.name }}</h4>
              <p class="type-description">{{ type.description }}</p>
              <div class="type-check" v-if="formData.evalType === type.id">
                <LIcon color="primary">mdi-check-circle</LIcon>
              </div>
              <LTag v-if="analysisResult?.suggestedType === type.id" variant="warning" size="small" class="suggested-tag">
                {{ $t('scenarioManager.wizard.step2.recommended') }}
              </LTag>
            </div>
          </div>
        </div>

        <!-- Evaluation Type Selection - LLARS Domain Types -->
        <div class="type-category type-category--llars mt-6">
          <h4 class="type-category-title">
            <LIcon color="accent" size="20" class="mr-2">mdi-school</LIcon>
            {{ $t('scenarioManager.wizard.step2.llarsTypes') }}
            <LTag variant="info" size="x-small" class="ml-2">LLARS</LTag>
          </h4>
          <p class="type-category-description">
            {{ $t('scenarioManager.wizard.step2.llarsTypesDescription') }}
          </p>
          <div class="type-grid">
            <div
              v-for="type in evaluationTypesGrouped.llars"
              :key="type.id"
              class="type-card type-card--llars"
              :class="{
                selected: formData.evalType === type.id,
                suggested: analysisResult?.suggestedType === type.id
              }"
              @click="selectEvalType(type.id)"
            >
              <div class="type-icon" :style="{ backgroundColor: type.color + '20' }">
                <LIcon :color="type.color" size="32">{{ type.icon }}</LIcon>
              </div>
              <h4 class="type-name">{{ type.name }}</h4>
              <p class="type-description">{{ type.description }}</p>
              <div v-if="type.baseType" class="type-base-hint">
                <LIcon size="12" class="mr-1">mdi-arrow-right</LIcon>
                {{ $t('scenarioManager.wizard.step2.basedOn') }} {{ getBaseTypeName(type.baseType) }}
              </div>
              <div class="type-check" v-if="formData.evalType === type.id">
                <LIcon color="accent">mdi-check-circle</LIcon>
              </div>
              <LTag v-if="analysisResult?.suggestedType === type.id" variant="warning" size="small" class="suggested-tag">
                {{ $t('scenarioManager.wizard.step2.recommended') }}
              </LTag>
            </div>
          </div>
        </div>

        <!-- Basic Info Form -->
        <div class="basic-info-form mt-6">
          <h4 class="subsection-title">{{ $t('scenarioManager.wizard.step2.basicInfo') }}</h4>
          <v-form ref="infoForm" v-model="infoFormValid">
            <v-text-field
              v-model="formData.scenario_name"
              :label="$t('scenarioManager.wizard.step2.name')"
              :rules="[rules.required, rules.minLength(3)]"
              variant="outlined"
              class="mb-3"
            >
              <template #append-inner>
                <LAIFieldButton
                  field-key="scenario.settings.name"
                  :context="{
                    scenario_type: formData.evalType,
                    existing_description: formData.description,
                    existing_name: formData.scenario_name
                  }"
                  icon-only
                  size="small"
                  @generated="formData.scenario_name = $event"
                />
              </template>
            </v-text-field>

            <v-textarea
              v-model="formData.description"
              :label="$t('scenarioManager.wizard.step2.descriptionField')"
              :hint="$t('scenarioManager.wizard.step2.descriptionHint')"
              variant="outlined"
              rows="2"
            >
              <template #append-inner>
                <LAIFieldButton
                  field-key="scenario.settings.description"
                  :context="{
                    scenario_type: formData.evalType,
                    scenario_name: formData.scenario_name,
                    existing_description: formData.description
                  }"
                  icon-only
                  size="small"
                  @generated="formData.description = $event"
                />
              </template>
            </v-textarea>
          </v-form>
        </div>
      </div>

      <!-- Step 3: Configuration -->
      <div v-if="currentStep === 2" class="step-content">
        <h3 class="step-title">{{ $t('scenarioManager.wizard.step3.title') }}</h3>
        <p class="step-description">{{ $t('scenarioManager.wizard.step3.description') }}</p>

        <!-- Evaluation Config Editor -->
        <EvaluationConfigEditor
          v-if="formData.evalType"
          :eval-type="formData.evalType"
          v-model="formData.evalConfig"
          :show-presets="true"
          :show-preview="true"
        />

        <v-divider class="my-6" />

        <!-- Distribution Settings -->
        <div class="distribution-settings">
          <h4 class="subsection-title">{{ $t('scenarioManager.wizard.step3.distributionSettings') }}</h4>

          <div class="config-section">
            <LRadioGroup
              v-model="formData.config.distribution_mode"
              :label="$t('scenarioManager.wizard.step3.distribution')"
              :options="distributionOptions"
              row
            />
          </div>

          <div class="config-section">
            <LRadioGroup
              v-model="formData.config.order_mode"
              :label="$t('scenarioManager.wizard.step3.order')"
              :options="orderOptions"
              row
            />
          </div>

          <div class="config-section">
            <LSwitch
              v-model="formData.config.enable_llm_evaluation"
              :label="$t('scenarioManager.wizard.step3.enableLLM')"
            />
          </div>
        </div>
      </div>

      <!-- Step 4: Team (Users & AI) -->
      <div v-if="currentStep === 3" class="step-content">
        <h3 class="step-title">{{ $t('scenarioManager.wizard.step4.teamTitle') }}</h3>
        <p class="step-description">{{ $t('scenarioManager.wizard.step4.teamDescription') }}</p>

        <!-- AI Native Banner -->
        <v-alert type="info" variant="tonal" class="mb-4">
          <template v-slot:prepend>
            <LIcon>mdi-robot</LIcon>
          </template>
          {{ $t('scenarioManager.wizard.step4.aiNativeHint') }}
        </v-alert>

        <v-row>
          <!-- Human Evaluators -->
          <v-col cols="12" md="6">
            <div class="team-section">
              <div class="team-section-header">
                <LIcon color="primary" class="mr-2">mdi-account-group</LIcon>
                <span class="font-weight-bold">{{ $t('scenarioManager.wizard.step4.humanEvaluators') }}</span>
                <v-chip size="small" class="ml-2">{{ selectedUsers.length }}</v-chip>
              </div>

              <v-select
                v-model="inviteRole"
                :items="roleOptions"
                :label="$t('scenarioManager.wizard.step4.defaultRole')"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <div v-if="loadingUsers" class="d-flex justify-center py-4">
                <v-progress-circular indeterminate size="24" />
              </div>

              <div v-else class="user-list">
                <div
                  v-for="user in availableUsers"
                  :key="user.id"
                  class="user-item"
                  :class="{ selected: isUserSelected(user) }"
                  @click="toggleUser(user)"
                >
                  <LAvatar :user="user" size="sm" class="mr-2" />
                  <div class="user-info">
                    <span class="user-name">{{ user.display_name || user.username }}</span>
                    <span class="user-email">{{ user.email }}</span>
                  </div>
                  <LIcon v-if="isUserSelected(user)" color="primary">mdi-check-circle</LIcon>
                </div>
                <p v-if="availableUsers.length === 0" class="text-caption text-medium-emphasis pa-4 text-center">
                  {{ $t('scenarioManager.wizard.step4.noUsersAvailable') }}
                </p>
              </div>
            </div>
          </v-col>

          <!-- AI Evaluators (LLMs) -->
          <v-col cols="12" md="6">
            <div class="team-section team-section--ai">
              <div class="team-section-header">
                <LIcon color="accent" class="mr-2">mdi-robot-outline</LIcon>
                <span class="font-weight-bold">{{ $t('scenarioManager.wizard.step4.aiEvaluators') }}</span>
                <v-chip size="small" color="accent" class="ml-2">{{ selectedLLMs.length }}</v-chip>
              </div>

              <v-alert v-if="selectedLLMs.length > 0" type="success" variant="tonal" density="compact" class="mb-3">
                <LIcon size="16" class="mr-1">mdi-lightning-bolt</LIcon>
                {{ $t('scenarioManager.wizard.step4.aiAutoStart') }}
              </v-alert>

              <div v-if="loadingLLMs && loadingUserProviders" class="d-flex justify-center py-4">
                <v-progress-circular indeterminate size="24" />
              </div>

              <div v-else class="llm-list">
                <!-- System LLMs Section -->
                <div v-if="availableLLMs.length > 0" class="llm-category">
                  <div class="llm-category-header">
                    <LIcon size="16" color="primary">mdi-server</LIcon>
                    <span>{{ $t('scenarioManager.wizard.step4.systemModels') }}</span>
                    <v-chip size="x-small" variant="outlined" class="ml-auto">{{ availableLLMs.length }}</v-chip>
                  </div>
                  <div
                    v-for="llm in availableLLMs"
                    :key="'system-' + llm.id"
                    class="llm-item"
                    :class="{ selected: isLLMSelected(llm) }"
                    @click="toggleLLM(llm)"
                  >
                    <div class="llm-icon">
                      <LIcon size="24" color="accent">mdi-chip</LIcon>
                    </div>
                    <div class="llm-info">
                      <span class="llm-name">{{ llm.display_name || llm.model_id }}</span>
                      <span class="llm-provider">{{ llm.provider || 'System' }}</span>
                    </div>
                    <LIcon v-if="isLLMSelected(llm)" color="accent">mdi-check-circle</LIcon>
                  </div>
                </div>

                <!-- User Providers Section -->
                <div v-if="userProviders.length > 0" class="llm-category mt-3">
                  <div class="llm-category-header">
                    <LIcon size="16" color="secondary">mdi-account-key</LIcon>
                    <span>{{ $t('scenarioManager.wizard.step4.myProviders') }}</span>
                    <v-chip size="x-small" variant="outlined" class="ml-auto">{{ userProviders.length }}</v-chip>
                  </div>
                  <div
                    v-for="provider in userProviders"
                    :key="'provider-' + provider.id"
                    class="llm-item llm-item--user"
                    :class="{ selected: isProviderSelected(provider) }"
                    @click="toggleProvider(provider)"
                  >
                    <div class="llm-icon">
                      <LIcon size="24" :color="getProviderIconColor(provider)">{{ getProviderIcon(provider) }}</LIcon>
                    </div>
                    <div class="llm-info">
                      <span class="llm-name">{{ provider.name }}</span>
                      <span class="llm-provider">
                        {{ getProviderTypeLabel(provider.provider_type) }}
                        <span v-if="provider.source !== 'own'" class="llm-shared-badge">
                          <LIcon size="12">mdi-share-variant</LIcon>
                          {{ provider.shared_by }}
                        </span>
                      </span>
                    </div>
                    <LIcon v-if="isProviderSelected(provider)" color="secondary">mdi-check-circle</LIcon>
                  </div>
                </div>

                <!-- Empty State -->
                <p v-if="availableLLMs.length === 0 && userProviders.length === 0" class="text-caption text-medium-emphasis pa-4 text-center">
                  {{ $t('scenarioManager.wizard.step4.noLLMsAvailable') }}
                  <br />
                  <router-link to="/settings" class="text-primary">
                    {{ $t('scenarioManager.wizard.step4.addProviderHint') }}
                  </router-link>
                </p>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- Selected Summary -->
        <div v-if="selectedUsers.length > 0 || selectedLLMs.length > 0 || selectedProviders.length > 0" class="selected-summary mt-4">
          <h5 class="text-subtitle-2 mb-2">{{ $t('scenarioManager.wizard.step4.selectedSummary') }}</h5>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="user in selectedUsers"
              :key="'user-' + user.id"
              closable
              size="small"
              @click:close="toggleUser(user)"
            >
              <LIcon size="16" class="mr-1">mdi-account</LIcon>
              {{ user.display_name || user.username }}
            </v-chip>
            <v-chip
              v-for="llm in selectedLLMs"
              :key="'llm-' + llm.id"
              closable
              size="small"
              color="accent"
              @click:close="toggleLLM(llm)"
            >
              <LIcon size="16" class="mr-1">mdi-robot</LIcon>
              {{ llm.display_name || llm.model_id }}
            </v-chip>
            <v-chip
              v-for="provider in selectedProviders"
              :key="'provider-' + provider.id"
              closable
              size="small"
              color="secondary"
              @click:close="toggleProvider(provider)"
            >
              <LIcon size="16" class="mr-1">{{ getProviderIcon(provider) }}</LIcon>
              {{ provider.name }}
            </v-chip>
          </div>
        </div>
      </div>

      <!-- Step 5: Summary & Create -->
      <div v-if="currentStep === 4" class="step-content">
        <h3 class="step-title">{{ $t('scenarioManager.wizard.step5.title') }}</h3>
        <p class="step-description">{{ $t('scenarioManager.wizard.step5.description') }}</p>

        <div class="summary-card">
          <div class="summary-section">
            <h5 class="summary-section-title">
              <LIcon class="mr-2" color="primary">mdi-information-outline</LIcon>
              {{ $t('scenarioManager.wizard.step5.basicInfo') }}
            </h5>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.name') }}</span>
              <span class="summary-value">{{ formData.scenario_name }}</span>
            </div>
            <div class="summary-row" v-if="formData.description">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.descriptionLabel') }}</span>
              <span class="summary-value">{{ formData.description }}</span>
            </div>
          </div>

          <v-divider class="my-3" />

          <div class="summary-section">
            <h5 class="summary-section-title">
              <LIcon class="mr-2" color="primary">mdi-clipboard-check-outline</LIcon>
              {{ $t('scenarioManager.wizard.step5.evaluationType') }}
            </h5>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.type') }}</span>
              <LTag :variant="selectedTypeInfo?.variant || 'gray'">
                <LIcon size="16" class="mr-1">{{ selectedTypeInfo?.icon }}</LIcon>
                {{ selectedTypeInfo?.name }}
              </LTag>
            </div>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.preset') }}</span>
              <span class="summary-value">{{ formData.evalConfig?.presetId || 'custom' }}</span>
            </div>
          </div>

          <v-divider class="my-3" />

          <div class="summary-section">
            <h5 class="summary-section-title">
              <LIcon class="mr-2" color="primary">mdi-database-outline</LIcon>
              {{ $t('scenarioManager.wizard.step5.data') }}
            </h5>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.files') }}</span>
              <span class="summary-value">
                {{ uploadedFiles.length > 0 ? `${uploadedFiles.length} ${$t('scenarioManager.wizard.step1.filesSelected')}` : '-' }}
              </span>
            </div>
            <div class="summary-row" v-if="analysisResult">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.items') }}</span>
              <span class="summary-value">{{ analysisResult.itemCount }}</span>
            </div>
          </div>

          <v-divider class="my-3" />

          <!-- Team Section -->
          <div class="summary-section">
            <h5 class="summary-section-title">
              <LIcon class="mr-2" color="primary">mdi-account-group</LIcon>
              {{ $t('scenarioManager.wizard.step5.team') }}
            </h5>

            <!-- Human Evaluators -->
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.humanEvaluators') }}</span>
              <span class="summary-value">
                <span v-if="selectedUsers.length === 0" class="text-medium-emphasis">-</span>
                <div v-else class="d-flex flex-wrap gap-1">
                  <v-chip
                    v-for="user in selectedUsers"
                    :key="user.id"
                    size="small"
                    variant="tonal"
                  >
                    <LIcon size="14" class="mr-1">mdi-account</LIcon>
                    {{ user.display_name || user.username }}
                  </v-chip>
                </div>
              </span>
            </div>

            <!-- AI Evaluators -->
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.aiEvaluators') }}</span>
              <span class="summary-value">
                <span v-if="selectedLLMs.length === 0" class="text-medium-emphasis">-</span>
                <div v-else class="d-flex flex-wrap gap-1">
                  <v-chip
                    v-for="llm in selectedLLMs"
                    :key="llm.id"
                    size="small"
                    variant="tonal"
                    color="accent"
                  >
                    <LIcon size="14" class="mr-1">mdi-robot</LIcon>
                    {{ llm.display_name || llm.model_id }}
                  </v-chip>
                </div>
              </span>
            </div>

            <!-- User Providers -->
            <div v-if="selectedProviders.length > 0" class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.userProviders') }}</span>
              <span class="summary-value">
                <div class="d-flex flex-wrap gap-1">
                  <v-chip
                    v-for="provider in selectedProviders"
                    :key="provider.id"
                    size="small"
                    variant="tonal"
                    color="secondary"
                  >
                    <LIcon size="14" class="mr-1">{{ getProviderIcon(provider) }}</LIcon>
                    {{ provider.name }}
                  </v-chip>
                </div>
              </span>
            </div>

            <!-- AI Auto-start Info -->
            <v-alert
              v-if="selectedLLMs.length > 0 || selectedProviders.length > 0"
              type="info"
              variant="tonal"
              density="compact"
              class="mt-3"
            >
              <LIcon size="16" class="mr-1">mdi-lightning-bolt</LIcon>
              {{ $t('scenarioManager.wizard.step5.aiAutoStartInfo') }}
            </v-alert>
          </div>

          <v-divider class="my-3" />

          <div class="summary-section">
            <h5 class="summary-section-title">
              <LIcon class="mr-2" color="primary">mdi-cog-outline</LIcon>
              {{ $t('scenarioManager.wizard.step5.settings') }}
            </h5>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.distribution') }}</span>
              <span class="summary-value">{{ $t(`scenarioManager.wizard.step3.distribution${capitalize(formData.config.distribution_mode)}`) }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">{{ $t('scenarioManager.wizard.step5.llmEnabled') }}</span>
              <LIcon :color="formData.config.enable_llm_evaluation ? 'success' : 'grey'">
                {{ formData.config.enable_llm_evaluation ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </LIcon>
            </div>
          </div>
        </div>

        <v-alert type="info" variant="tonal" class="mt-4">
          <template v-slot:prepend>
            <LIcon>mdi-information</LIcon>
          </template>
          {{ $t('scenarioManager.wizard.step5.nextSteps') }}
        </v-alert>
      </div>
    </v-card-text>

    <v-divider />

    <!-- Actions -->
    <v-card-actions class="wizard-actions">
      <LBtn variant="text" @click="$emit('close')">
        {{ $t('common.cancel') }}
      </LBtn>
      <v-spacer />
      <LBtn
        v-if="currentStep > 0"
        variant="secondary"
        @click="currentStep--"
      >
        <LIcon start>mdi-chevron-left</LIcon>
        {{ $t('common.back') }}
      </LBtn>
      <LBtn
        v-if="currentStep < steps.length - 1"
        variant="primary"
        :disabled="!canProceed"
        @click="nextStep"
      >
        {{ $t('common.next') }}
        <LIcon end>mdi-chevron-right</LIcon>
      </LBtn>
      <LBtn
        v-else
        variant="primary"
        :loading="creating"
        @click="createScenario"
      >
        <LIcon start>mdi-check</LIcon>
        {{ $t('scenarioManager.wizard.create') }}
      </LBtn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
/**
 * Scenario Wizard Component
 *
 * AI-powered wizard for creating evaluation scenarios.
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Dieses Komponente erstellt Szenarien, deren Daten im einheitlichen
 * EvaluationData Schema-Format gespeichert werden:
 *
 * - Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
 * - Frontend: src/schemas/evaluationSchemas.js (Validation)
 * - Presets: src/views/ScenarioManager/config/evaluationPresets.js
 *
 * WICHTIG:
 * - Hochgeladene Daten werden in Items mit technischen IDs konvertiert
 * - Item.id = "item_1", "item_2" etc. (NIEMALS LLM-Namen!)
 * - Item.label = UI-Anzeigename (generisch)
 * - Item.source = Herkunft (human/llm/unknown)
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useScenarioManager } from '../composables/useScenarioManager'
import importService from '@/services/importService'
import EvaluationConfigEditor from './EvaluationConfigEditor.vue'
import { StreamingAnalysisPanel } from '@/components/ScenarioWizard/AIAnalysis'
import {
  EVAL_TYPES,
  ID_TYPE_MAP,
  TYPE_INFO,
  getDefaultConfig,
  getTypesByCategory,
  isLlarsDomainType,
  getBaseType
} from '../config/evaluationPresets'

const props = defineProps({
  /**
   * Optional generation job ID to load data from.
   * When provided, the wizard will pre-load outputs from this batch generation job.
   */
  generationJobId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['close', 'created'])

const { t, locale } = useI18n()
const { createNewScenario, inviteUsers } = useScenarioManager()
const auth = useAuth()

// JSON code examples (raw strings to avoid vue-i18n placeholder parsing)
const codeExamples = computed(() => ({
  single: '[{"id":"1","text":"...","label":"positive"}]',
  conversation: '{"id":"1","messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}',
  comparison: '{"id":"1","text_a":"...","text_b":"..."}',
  ranking: locale.value === 'de'
    ? '{"source_text":"Originaltext...","items":[{"id":"A","content":"Item 1..."},{"id":"B","content":"Item 2..."}]}'
    : '{"source_text":"Original text...","items":[{"id":"A","content":"Item 1..."},{"id":"B","content":"Item 2..."}]}'
}))

// Refs
const fileInput = ref(null)
const infoForm = ref(null)
const infoFormValid = ref(false)
const analysisPanel = ref(null) // StreamingAnalysisPanel ref

// Stepper state
const currentStep = ref(0)
const creating = ref(false)

// File upload state
const uploadedFiles = ref([])
const isDragging = ref(false)
const analyzing = ref(false)
const analysisResult = ref(null)
const analyzedData = ref([]) // Merged data from all files
const aiSuggestions = ref(null) // AI-generated suggestions

// Streaming AI state
const aiThinking = ref(false)
const streamedJsonContent = ref('') // Raw JSON being streamed from LLM
const streamingPhase = ref(null) // 'parsing' | 'thinking' | 'streaming' | 'done'

// Team/User state
const availableUsers = ref([])
const selectedUsers = ref([])
const loadingUsers = ref(false)
const inviteRole = ref('EVALUATOR')

// LLM state - System models (admin-configured)
const availableLLMs = ref([])
const selectedLLMs = ref([])
const loadingLLMs = ref(false)

// User Provider state - User's own and shared providers
const userProviders = ref([])
const selectedProviders = ref([])
const loadingUserProviders = ref(false)

// Steps definition
const steps = computed(() => [
  { key: 'data', label: t('scenarioManager.wizard.steps.data'), icon: 'mdi-database-import-outline' },
  { key: 'task', label: t('scenarioManager.wizard.steps.task'), icon: 'mdi-clipboard-list-outline' },
  { key: 'config', label: t('scenarioManager.wizard.steps.config'), icon: 'mdi-tune' },
  { key: 'team', label: t('scenarioManager.wizard.steps.team'), icon: 'mdi-account-group' },
  { key: 'summary', label: t('scenarioManager.wizard.steps.summary'), icon: 'mdi-check-all' }
])

// Evaluation types - grouped by category
const evaluationTypesGrouped = computed(() => {
  const categories = getTypesByCategory()

  return {
    general: categories.general.map(typeId => ({
      id: typeId,
      name: TYPE_INFO[typeId]?.name[locale.value] || TYPE_INFO[typeId]?.name.de || typeId,
      description: TYPE_INFO[typeId]?.description[locale.value] || TYPE_INFO[typeId]?.description.de || '',
      icon: TYPE_INFO[typeId]?.icon,
      color: TYPE_INFO[typeId]?.color,
      variant: getTypeVariant(typeId),
      category: 'general'
    })),
    llars: categories.llars.map(typeId => ({
      id: typeId,
      name: TYPE_INFO[typeId]?.name[locale.value] || TYPE_INFO[typeId]?.name.de || typeId,
      description: TYPE_INFO[typeId]?.description[locale.value] || TYPE_INFO[typeId]?.description.de || '',
      icon: TYPE_INFO[typeId]?.icon,
      color: TYPE_INFO[typeId]?.color,
      variant: getTypeVariant(typeId),
      category: 'llars',
      baseType: TYPE_INFO[typeId]?.baseType
    }))
  }
})

// All evaluation types as flat list (for compatibility)
const evaluationTypes = computed(() => [
  ...evaluationTypesGrouped.value.general,
  ...evaluationTypesGrouped.value.llars
])

// Get variant for type (used for tags)
function getTypeVariant(typeId) {
  const variants = {
    [EVAL_TYPES.RATING]: 'warning',
    [EVAL_TYPES.RANKING]: 'success',
    [EVAL_TYPES.LABELING]: 'danger',
    [EVAL_TYPES.COMPARISON]: 'primary',
    [EVAL_TYPES.MAIL_RATING]: 'info',
    [EVAL_TYPES.AUTHENTICITY]: 'success'
  }
  return variants[typeId] || 'gray'
}

// Get base type name for display
function getBaseTypeName(baseTypeId) {
  const info = TYPE_INFO[baseTypeId]
  if (!info) return baseTypeId
  return info.name[locale.value] || info.name.de || baseTypeId
}

// Form data
const formData = ref({
  evalType: null,
  scenario_name: '',
  description: '',
  evalConfig: null,
  config: {
    distribution_mode: 'all',
    order_mode: 'random',
    enable_llm_evaluation: true
  }
})

// Validation rules
const rules = {
  required: v => !!v || t('validation.required'),
  minLength: (len) => v => (v && v.length >= len) || t('validation.minLength', { length: len })
}

// Computed
const selectedTypeInfo = computed(() => {
  return evaluationTypes.value.find(t => t.id === formData.value.evalType)
})

// Radio options for distribution settings
const distributionOptions = computed(() => [
  { value: 'all', label: t('scenarioManager.wizard.step3.distributionAll') },
  { value: 'random', label: t('scenarioManager.wizard.step3.distributionRandom') },
  { value: 'sequential', label: t('scenarioManager.wizard.step3.distributionSequential') }
])

const orderOptions = computed(() => [
  { value: 'fixed', label: t('scenarioManager.wizard.step3.orderFixed') },
  { value: 'random', label: t('scenarioManager.wizard.step3.orderRandom') }
])

// Computed for total file size
const totalFileSize = computed(() => {
  return uploadedFiles.value.reduce((sum, file) => sum + file.size, 0)
})

// Data summary for StreamingAnalysisPanel
const dataSummaryForPanel = computed(() => {
  const result = analysisResult.value
  return {
    itemCount: result?.itemCount || 0,
    fieldsCount: result?.fieldsCount || 0,
    fileCount: uploadedFiles.value.length,
    fields: result?.fields?.map(f => ({
      name: f,
      type: 'string',
      completeness: 1
    })) || []
  }
})

const canProceed = computed(() => {
  if (currentStep.value === 0) {
    // Step 1: Need files and analysis
    return uploadedFiles.value.length > 0 && analysisResult.value !== null
  }
  if (currentStep.value === 1) {
    // Step 2: Need type and name
    return formData.value.evalType !== null &&
           formData.value.scenario_name &&
           formData.value.scenario_name.length >= 3
  }
  if (currentStep.value === 2) {
    // Step 3: Need config
    return formData.value.evalConfig !== null
  }
  if (currentStep.value === 3) {
    // Step 4: Team - need at least one evaluator (human or LLM)
    return selectedUsers.value.length > 0 || selectedLLMs.value.length > 0
  }
  return true
})

// Role options for user invitations
const roleOptions = [
  { value: 'EVALUATOR', title: 'Evaluator' },
  { value: 'RATER', title: 'Rater' }
]

// Methods
function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

function goToStep(index) {
  if (index < currentStep.value) {
    currentStep.value = index
  }
}

function nextStep() {
  if (currentStep.value === 1 && infoForm.value) {
    infoForm.value.validate()
    if (!infoFormValid.value) return
  }
  currentStep.value++
}

// File handling
function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files || [])
  processFiles(files)
  // Reset input so same files can be selected again
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function handleFileDrop(event) {
  isDragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  processFiles(files)
}

function processFiles(files) {
  const validTypes = ['.json', '.csv', '.xlsx', '.xls']
  const validFiles = files.filter(file => {
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    return validTypes.includes(ext)
  })

  if (validFiles.length === 0) {
    console.error('No valid files selected')
    return
  }

  // Add to existing files, avoiding duplicates by name
  const existingNames = new Set(uploadedFiles.value.map(f => f.name))
  const newFiles = validFiles.filter(f => !existingNames.has(f.name))

  uploadedFiles.value = [...uploadedFiles.value, ...newFiles]
  analysisResult.value = null
  analyzedData.value = []
}

function removeFile(index) {
  uploadedFiles.value.splice(index, 1)
  if (uploadedFiles.value.length === 0) {
    analysisResult.value = null
    analyzedData.value = []
  }
}

function clearAllFiles() {
  uploadedFiles.value = []
  analysisResult.value = null
  analyzedData.value = []
}

// Fetch available users for invitation
async function fetchAvailableUsers() {
  loadingUsers.value = true
  try {
    const response = await axios.get('/api/admin/available_users_for_scenario')
    availableUsers.value = response.data.users || response.data || []
  } catch (error) {
    console.error('Failed to fetch users:', error)
    availableUsers.value = []
  } finally {
    loadingUsers.value = false
  }
}

// Fetch available LLM models for evaluation (chat models only, not embedding models)
async function fetchAvailableLLMs() {
  loadingLLMs.value = true
  try {
    // Filter by model_type=llm to exclude embedding/reranker models
    const response = await axios.get('/api/llm/models/available', {
      params: { model_type: 'llm' }
    })
    availableLLMs.value = (response.data.models || []).filter(m => m.is_active)
  } catch (error) {
    console.error('Failed to fetch LLM models:', error)
    availableLLMs.value = []
  } finally {
    loadingLLMs.value = false
  }
}

// Fetch user's own and shared LLM providers
async function fetchUserProviders() {
  loadingUserProviders.value = true
  try {
    const response = await axios.get('/api/user/providers/available')
    userProviders.value = (response.data.providers || []).filter(p => p.is_active)
  } catch (error) {
    console.error('Failed to fetch user providers:', error)
    userProviders.value = []
  } finally {
    loadingUserProviders.value = false
  }
}

// Toggle user selection
function toggleUser(user) {
  const index = selectedUsers.value.findIndex(u => u.id === user.id)
  if (index >= 0) {
    selectedUsers.value.splice(index, 1)
  } else {
    selectedUsers.value.push({ ...user, role: inviteRole.value })
  }
}

// Toggle LLM selection
function toggleLLM(llm) {
  const index = selectedLLMs.value.findIndex(l => l.id === llm.id)
  if (index >= 0) {
    selectedLLMs.value.splice(index, 1)
  } else {
    selectedLLMs.value.push(llm)
  }
}

// Check if user is selected
function isUserSelected(user) {
  return selectedUsers.value.some(u => u.id === user.id)
}

// Check if LLM is selected
function isLLMSelected(llm) {
  return selectedLLMs.value.some(l => l.id === llm.id)
}

// Toggle user provider selection
function toggleProvider(provider) {
  const index = selectedProviders.value.findIndex(p => p.id === provider.id)
  if (index >= 0) {
    selectedProviders.value.splice(index, 1)
  } else {
    selectedProviders.value.push(provider)
  }
}

// Check if user provider is selected
function isProviderSelected(provider) {
  return selectedProviders.value.some(p => p.id === provider.id)
}

// Get provider icon based on type
function getProviderIcon(provider) {
  const icons = {
    openai: 'mdi-creation',
    anthropic: 'mdi-head-snowflake',
    gemini: 'mdi-google',
    azure: 'mdi-microsoft-azure',
    ollama: 'mdi-llama',
    litellm: 'mdi-api',
    custom: 'mdi-cog'
  }
  return icons[provider.provider_type] || 'mdi-api'
}

// Get provider icon color based on type
function getProviderIconColor(provider) {
  const colors = {
    openai: '#10a37f',
    anthropic: '#d4a574',
    gemini: '#4285f4',
    azure: '#0078d4',
    ollama: '#ffffff',
    litellm: '#ffc107',
    custom: '#9e9e9e'
  }
  return colors[provider.provider_type] || 'secondary'
}

// Get human-readable provider type label
function getProviderTypeLabel(providerType) {
  const labels = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gemini: 'Google Gemini',
    azure: 'Azure OpenAI',
    ollama: 'Ollama',
    litellm: 'LiteLLM',
    custom: 'Custom'
  }
  return labels[providerType] || providerType
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  switch (ext) {
    case 'json': return 'mdi-code-json'
    case 'csv': return 'mdi-file-delimited'
    case 'xlsx':
    case 'xls': return 'mdi-file-excel'
    default: return 'mdi-file'
  }
}

function getFileColor(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  switch (ext) {
    case 'json': return '#f5a623'
    case 'csv': return '#4caf50'
    case 'xlsx':
    case 'xls': return '#217346'
    default: return 'grey'
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// AI Analysis with Streaming
async function analyzeData() {
  if (uploadedFiles.value.length === 0) return

  analyzing.value = true
  aiSuggestions.value = null
  aiThinking.value = false
  streamedJsonContent.value = ''
  streamingPhase.value = 'parsing'
  const allData = []
  const fileResults = []
  let totalErrors = 0

  try {
    // Step 1: Parse all files locally
    for (const file of uploadedFiles.value) {
      try {
        const text = await readFileContent(file)
        let data = []

        const ext = file.name.split('.').pop().toLowerCase()
        if (ext === 'json') {
          data = JSON.parse(text)
          if (!Array.isArray(data)) {
            data = data.data || data.items || data.results || [data]
          }
        } else if (ext === 'csv') {
          data = parseCSV(text)
        }

        if (Array.isArray(data)) {
          allData.push(...data)
          fileResults.push({ name: file.name, count: data.length, success: true })
        } else {
          allData.push(data)
          fileResults.push({ name: file.name, count: 1, success: true })
        }
      } catch (fileError) {
        console.error(`Error processing ${file.name}:`, fileError)
        fileResults.push({ name: file.name, count: 0, success: false, error: fileError.message })
        totalErrors++
      }
    }

    // Store merged data for later use
    analyzedData.value = allData

    // Step 2: Call streaming AI analysis endpoint
    try {
      streamingPhase.value = 'thinking'
      aiThinking.value = true

      // Get auth token for fetch (axios interceptors don't apply to fetch)
      const token = auth.getToken()
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch('/api/ai-assist/analyze-scenario-data/stream', {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          data: allData,
          filename: uploadedFiles.value[0]?.name || 'data',
          file_count: uploadedFiles.value.length
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let tokensUsed = 0
      let currentEventType = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
            continue
          }
          if (line.startsWith('data: ')) {
            const eventData = line.slice(6)
            try {
              const parsed = JSON.parse(eventData)

              // Handle events based on tracked event type
              switch (currentEventType) {
                case 'data_summary':
                  analysisResult.value = {
                    itemCount: parsed.item_count,
                    fieldsCount: parsed.fields?.length || 0,
                    fields: parsed.fields || [],
                    sampleData: parsed.sample_items || [],
                    fileResults,
                    filesProcessed: uploadedFiles.value.length,
                    filesSuccessful: uploadedFiles.value.length - totalErrors,
                    errors: totalErrors,
                    aiPowered: true,
                    streaming: true
                  }
                  break

                case 'thinking':
                  streamingPhase.value = 'thinking'
                  break

                case 'chunk':
                  streamingPhase.value = 'streaming'
                  aiThinking.value = false
                  streamedJsonContent.value += parsed.content || ''
                  // Forward to panel for live parsing
                  if (analysisPanel.value?.processChunk) {
                    analysisPanel.value.processChunk(parsed.content || '')
                  }
                  break

                case 'suggestions': {
                  aiSuggestions.value = parsed

                  // Update analysis result with suggestions
                  // Support both old (eval_type) and new (evaluation_type) field names
                  if (analysisResult.value) {
                    analysisResult.value.suggestedType = parsed.evaluation_type || parsed.eval_type || EVAL_TYPES.RATING
                    analysisResult.value.suggestedTypeConfidence = parsed.confidence || parsed.eval_type_confidence
                    analysisResult.value.suggestedTypeReasoning = parsed.reasoning || parsed.eval_type_reasoning
                  }

                  // Auto-apply AI suggestions
                  const evalType = parsed.evaluation_type || parsed.eval_type
                  if (evalType) {
                    formData.value.evalType = evalType
                  }
                  const scenarioName = parsed.name || parsed.scenario_name
                  if (scenarioName) {
                    formData.value.scenario_name = scenarioName
                  }
                  const scenarioDescription = parsed.description || parsed.scenario_description
                  if (scenarioDescription) {
                    formData.value.description = scenarioDescription
                  }

                  // Forward to panel for final parsing
                  if (analysisPanel.value?.processSuggestions) {
                    analysisPanel.value.processSuggestions(parsed)
                  }
                  break
                }

                case 'data_quality':
                  if (analysisResult.value) {
                    analysisResult.value.dataQuality = parsed
                  }
                  // Forward to panel
                  if (analysisPanel.value?.processDataQuality) {
                    analysisPanel.value.processDataQuality(parsed)
                  }
                  break

                case 'done':
                  tokensUsed = parsed.tokens_used || 0
                  if (analysisResult.value) {
                    analysisResult.value.tokensUsed = tokensUsed
                    analysisResult.value.streaming = false
                  }
                  streamingPhase.value = 'done'
                  // Finalize panel
                  if (analysisPanel.value?.finalize) {
                    analysisPanel.value.finalize()
                  }
                  break

                case 'error':
                  console.warn('Streaming AI error:', parsed.error)
                  if (analysisPanel.value?.setError) {
                    analysisPanel.value.setError(parsed.error)
                  }
                  throw new Error(parsed.error)
              }

              currentEventType = null // Reset after processing data
            } catch (parseError) {
              // Ignore parse errors for incomplete JSON
              if (parseError.message && !parseError.message.includes('Unexpected')) {
                throw parseError
              }
            }
          }
        }
      }

      // Success - streaming complete
      return

    } catch (apiError) {
      console.warn('Streaming AI analysis failed, falling back to local analysis:', apiError)
      aiThinking.value = false
      streamingPhase.value = null
    }

    // Step 3: Fallback to local heuristic analysis
    performLocalAnalysis(allData, fileResults, totalErrors)

  } catch (error) {
    console.error('Analysis error:', error)
    analysisResult.value = {
      itemCount: 0,
      fieldsCount: 0,
      fields: [],
      suggestedType: EVAL_TYPES.RATING,
      error: error.message,
      fileResults,
      filesProcessed: uploadedFiles.value.length,
      filesSuccessful: 0,
      errors: uploadedFiles.value.length,
      aiPowered: false
    }
  } finally {
    analyzing.value = false
    aiThinking.value = false
  }
}

// Local heuristic analysis (fallback when AI is unavailable)
function performLocalAnalysis(allData, fileResults, totalErrors) {
  const itemCount = allData.length
  const sampleItem = allData[0]
  const fields = sampleItem ? Object.keys(sampleItem) : []

  // Simple heuristic type suggestion based on field names
  let suggestedType = EVAL_TYPES.RATING
  if (fields.some(f => f.toLowerCase().includes('label') || f.toLowerCase().includes('category') || f.toLowerCase().includes('class'))) {
    suggestedType = EVAL_TYPES.LABELING
  } else if (fields.some(f => f.toLowerCase().includes('compare') || f.toLowerCase().includes('versus') || f.toLowerCase().includes('chosen'))) {
    suggestedType = EVAL_TYPES.COMPARISON
  } else if (fields.some(f => f.toLowerCase().includes('rank') || f.toLowerCase().includes('order') || f.toLowerCase().includes('bucket'))) {
    suggestedType = EVAL_TYPES.RANKING
  }
  // Default is RATING (including for message/email data which uses rating with custom dimensions)

  analysisResult.value = {
    itemCount,
    fieldsCount: fields.length,
    fields,
    suggestedType,
    sampleData: allData.slice(0, 3),
    fileResults,
    filesProcessed: uploadedFiles.value.length,
    filesSuccessful: uploadedFiles.value.length - totalErrors,
    errors: totalErrors,
    aiPowered: false
  }

  // Auto-select suggested type
  formData.value.evalType = suggestedType
}

// Handle config updates from StreamingAnalysisPanel
function handleAnalysisPanelConfigUpdate(config) {
  console.log('Config update from AI chat:', config)

  if (config.evalType) {
    formData.value.evalType = config.evalType
  }
  if (config.scenarioName) {
    formData.value.scenario_name = config.scenarioName
  }
  if (config.scenarioDescription) {
    formData.value.description = config.scenarioDescription
  }

  // Ensure evalConfig is initialized before applying detailed config updates
  const hasConfigUpdates = config.labels || config.scales || config.buckets ||
    config.categories || config.criteria || config.min !== undefined ||
    config.max !== undefined || config.step !== undefined

  if (hasConfigUpdates) {
    // Initialize evalConfig if not present
    if (!formData.value.evalConfig) {
      const evalType = config.evalType || formData.value.evalType || EVAL_TYPES.RATING
      formData.value.evalConfig = {
        presetId: 'custom',
        config: getDefaultConfig(evalType) || {}
      }
    }
    if (!formData.value.evalConfig.config) {
      formData.value.evalConfig.config = {}
    }

    // Apply config updates
    if (config.labels) {
      // For authenticity/labeling types, labels map to categories
      const evalType = formData.value.evalType
      const defaultColors = ['#98d4bb', '#e8a087', '#88c4c8', '#D1BC8A', '#b0ca97']

      if (evalType === EVAL_TYPES.AUTHENTICITY || evalType === EVAL_TYPES.LABELING) {
        // Convert labels to categories format
        const categories = config.labels.map((label, idx) => ({
          id: label.name?.toLowerCase().replace(/\s+/g, '-') || `label-${idx}`,
          name: { de: label.name, en: label.name },
          description: label.description ? { de: label.description, en: label.description } : undefined,
          color: label.color || defaultColors[idx % defaultColors.length]
        }))
        formData.value.evalConfig.config.categories = categories
        console.log('Applied labels as categories:', categories)
      } else {
        formData.value.evalConfig.config.labels = config.labels
        console.log('Applied labels:', config.labels)
      }
      formData.value.evalConfig.presetId = 'custom'
    }
    if (config.scales) {
      formData.value.evalConfig.config.scales = config.scales
      formData.value.evalConfig.presetId = 'custom'
      console.log('Applied scales:', config.scales)
    }
    if (config.buckets) {
      formData.value.evalConfig.config.buckets = config.buckets
      formData.value.evalConfig.presetId = 'custom'
      console.log('Applied buckets:', config.buckets)
    }
    if (config.categories) {
      formData.value.evalConfig.config.categories = config.categories
      formData.value.evalConfig.presetId = 'custom'
      console.log('Applied categories:', config.categories)
    }
    if (config.criteria) {
      formData.value.evalConfig.config.criteria = config.criteria
      formData.value.evalConfig.presetId = 'custom'
      console.log('Applied criteria:', config.criteria)
    }
    // Handle rating config (min, max, step)
    if (config.min !== undefined) {
      formData.value.evalConfig.config.min = config.min
      formData.value.evalConfig.presetId = 'custom'
    }
    if (config.max !== undefined) {
      formData.value.evalConfig.config.max = config.max
      formData.value.evalConfig.presetId = 'custom'
    }
    if (config.step !== undefined) {
      formData.value.evalConfig.config.step = config.step
      formData.value.evalConfig.presetId = 'custom'
    }
  }
}

// Re-analyze data (triggered by regenerate button in panel)
function reanalyzeData() {
  // Reset analysis state
  analysisResult.value = null
  aiSuggestions.value = null
  streamingPhase.value = null
  streamedJsonContent.value = ''

  // Reset panel state
  if (analysisPanel.value) {
    analysisPanel.value.reset()
  }

  // Start new analysis
  analyzeData()
}

function readFileContent(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = (e) => reject(e)
    reader.readAsText(file)
  })
}

function parseCSV(text) {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []

  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
  const data = []

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''))
    const obj = {}
    headers.forEach((h, idx) => {
      obj[h] = values[idx] || ''
    })
    data.push(obj)
  }

  return data
}

function formatSample(item) {
  const maxLength = 100
  const str = JSON.stringify(item, null, 2)
  if (str.length > maxLength) {
    return str.substring(0, maxLength) + '...'
  }
  return str
}

function getSuggestedTypeName(typeId) {
  const info = TYPE_INFO[typeId]
  if (!info) return typeId
  return info.name[locale.value] || info.name.de || typeId
}

function selectEvalType(typeId) {
  formData.value.evalType = typeId
  // Initialize default config for the type
  formData.value.evalConfig = {
    presetId: null,
    config: getDefaultConfig(typeId)
  }
}

// Map eval type string to backend task_type string
function getTaskType(evalType) {
  const taskTypeMapping = {
    [EVAL_TYPES.RANKING]: 'ranking',
    [EVAL_TYPES.RATING]: 'rating',
    [EVAL_TYPES.MAIL_RATING]: 'mail_rating',
    [EVAL_TYPES.COMPARISON]: 'comparison',
    [EVAL_TYPES.AUTHENTICITY]: 'authenticity',
    [EVAL_TYPES.LABELING]: 'labeling'
  }
  return taskTypeMapping[evalType] || 'mail_rating'
}

// Create scenario
async function createScenario() {
  creating.value = true
  try {
    // Map eval type to function_type_id for backend compatibility
    const functionTypeId = ID_TYPE_MAP[formData.value.evalType] || 2

    const llmEvaluators = formData.value.config.enable_llm_evaluation
      ? selectedLLMs.value.map(l => l.model_id).filter(Boolean)
      : []

    const scenarioPayload = {
      scenario_name: formData.value.scenario_name,
      function_type_id: functionTypeId,
      description: formData.value.description,
      config_json: {
        ...formData.value.config,
        eval_type: formData.value.evalType,
        eval_config: formData.value.evalConfig,
        llm_evaluators: llmEvaluators
      }
    }

    if (!llmEvaluators.length) {
      delete scenarioPayload.config_json.llm_evaluators
    }

    const scenario = await createNewScenario(scenarioPayload)

    // Invite selected human users
    if (selectedUsers.value.length > 0 && scenario?.id) {
      // Group users by role
      const evaluators = selectedUsers.value.filter(u => u.role === 'EVALUATOR').map(u => u.id)
      const raters = selectedUsers.value.filter(u => u.role === 'RATER').map(u => u.id)

      if (evaluators.length > 0) {
        await inviteUsers(scenario.id, evaluators, 'EVALUATOR')
      }
      if (raters.length > 0) {
        await inviteUsers(scenario.id, raters, 'RATER')
      }
    }

    // Import file data into the scenario
    if (analyzedData.value.length > 0 && scenario?.id) {
      try {
        const taskType = getTaskType(formData.value.evalType)

        // Get AI-suggested field mapping if available
        const fieldMapping = aiSuggestions.value?.field_mapping || null

        const importResult = await importService.importFromData(
          analyzedData.value,
          scenario.id,
          taskType,
          formData.value.scenario_name,
          fieldMapping
        )
        console.log('Data import result:', importResult)

        if (importResult.warnings?.length > 0) {
          console.warn('Import warnings:', importResult.warnings)
        }
      } catch (importError) {
        console.error('Failed to import data:', importError)
        // Continue anyway - scenario was created, just data import failed
      }
    }

    emit('created', scenario)
  } catch (error) {
    console.error('Failed to create scenario:', error)
  } finally {
    creating.value = false
  }
}

// Watch eval type changes to update config
watch(() => formData.value.evalType, (newType) => {
  if (newType && !formData.value.evalConfig) {
    formData.value.evalConfig = {
      presetId: null,
      config: getDefaultConfig(newType)
    }
  }
})

// Load data from generation job if provided
const loadingFromGeneration = ref(false)
const generationJobName = ref('')

async function loadFromGenerationJob() {
  if (!props.generationJobId) return

  loadingFromGeneration.value = true
  try {
    // Fetch all completed outputs from the generation job
    const response = await axios.get(`/api/generation/jobs/${props.generationJobId}/outputs`, {
      params: { status: 'completed', per_page: 1000 }
    })

    const outputs = response.data.items || []
    if (outputs.length === 0) {
      console.warn('No completed outputs found in generation job')
      return
    }

    // Fetch job info for the name
    const jobResponse = await axios.get(`/api/generation/jobs/${props.generationJobId}`)
    generationJobName.value = jobResponse.data.job?.name || `Generation Job #${props.generationJobId}`

    // Transform outputs into items for the wizard
    // Combine original input data with generated response as a complete conversation
    const items = outputs.map((output) => {
      const promptVars = output.prompt_variables || {}
      const generatedContent = output.generated_content || ''

      // Build the combined content structure
      let messages = []
      let text = ''

      // Check if there are original messages (conversation history)
      if (promptVars.messages && Array.isArray(promptVars.messages)) {
        // Copy original messages
        messages = [...promptVars.messages]
        // Add the generated response as a new assistant message
        messages.push({
          role: 'assistant',
          content: generatedContent
        })
        // For text field, create a summary
        text = messages.map(m => `${m.role}: ${m.content}`).join('\n\n')
      } else if (promptVars.input) {
        // Single input text - create a Q&A pair
        messages = [
          { role: 'user', content: promptVars.input },
          { role: 'assistant', content: generatedContent }
        ]
        text = `User: ${promptVars.input}\n\nAssistant: ${generatedContent}`
      } else {
        // No original input, just the generated content
        text = generatedContent
      }

      return {
        id: output.id.toString(),
        text: text,
        content: generatedContent,
        messages: messages.length > 0 ? messages : undefined,
        subject: promptVars.subject || undefined,
        // Include metadata for context
        _source: 'generation',
        _model: output.llm_model_name,
        _prompt_variant: output.prompt_variant_name,
        _source_item_id: output.source_item_id,
        _original_input: promptVars.input || null
      }
    })

    // Set the data
    analyzedData.value = items

    // Create a virtual "file" entry to show in the UI
    uploadedFiles.value = [{
      name: `${generationJobName.value}.json`,
      size: JSON.stringify(items).length,
      _isVirtual: true,
      _generationJobId: props.generationJobId
    }]

    // Pre-fill scenario name based on job name
    formData.value.scenario_name = generationJobName.value

    // Auto-advance to step 1 (task type selection) since we have data
    // The user can still go back to see the data if needed
    currentStep.value = 1

  } catch (error) {
    console.error('Failed to load generation job data:', error)
  } finally {
    loadingFromGeneration.value = false
  }
}

// Fetch data on mount
onMounted(() => {
  fetchAvailableUsers()
  fetchAvailableLLMs()
  fetchUserProviders()

  // If generation job ID is provided, load data from it
  if (props.generationJobId) {
    loadFromGenerationJob()
  }
})
</script>

<style scoped>
.scenario-wizard {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.wizard-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  font-size: 1.25rem;
  font-weight: 600;
}

/* AI Badge */
.ai-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 16px;
  background: linear-gradient(90deg, rgba(176, 202, 151, 0.1), rgba(136, 196, 200, 0.1));
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Stepper */
.wizard-stepper {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 16px 24px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: all 0.2s;
}

.step.clickable {
  cursor: pointer;
}

.step.clickable:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.step.active {
  background-color: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.step.completed {
  color: rgb(var(--v-theme-primary));
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  font-size: 0.75rem;
  font-weight: 600;
}

.step.active .step-indicator,
.step.completed .step-indicator {
  background-color: rgb(var(--v-theme-primary));
  color: white;
}

.step-label {
  font-weight: 500;
}

/* Content */
.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px !important;
}

.step-content {
  max-width: 800px;
  margin: 0 auto;
}

.step-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-on-surface));
}

.step-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-description {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 24px;
}

/* Format Examples in Tooltip */
.format-examples {
  margin-top: 8px;
}

.format-example {
  margin-bottom: 8px;
}

.format-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 2px;
}

.format-example code {
  display: block;
  font-size: 0.7rem;
  background: rgba(0, 0, 0, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
  white-space: pre-wrap;
}

.format-hint {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
  font-style: italic;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: rgb(var(--v-theme-on-surface));
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.upload-zone.has-files {
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  padding: 16px;
  cursor: default;
}

.upload-icon {
  margin-bottom: 12px;
}

.upload-text {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 4px;
  color: rgb(var(--v-theme-on-surface));
}

.upload-hint {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

.upload-hint-multi {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: rgb(var(--v-theme-primary));
  margin-top: 12px;
}

/* Files List */
.files-list {
  width: 100%;
  text-align: left;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.files-count {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.files-scroll {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background-color: rgba(var(--v-theme-surface), 1);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  transition: all 0.15s;
}

.file-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

.file-details {
  flex: 1;
  text-align: left;
  min-width: 0;
}

.file-name {
  display: block;
  font-weight: 500;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.files-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.total-size {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* File breakdown in analysis */
.file-breakdown {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-result-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  font-size: 0.8rem;
  border-radius: 4px;
}

.file-result-item.error {
  background-color: rgba(var(--v-theme-error), 0.08);
}

.file-result-name {
  flex: 1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-result-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.files-processed {
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

/* AI Analysis */
.ai-analysis-section {
  margin-top: 20px;
  padding: 16px;
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.analysis-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  margin-bottom: 12px;
  color: rgb(var(--v-theme-primary));
}

.analyzing-state {
  display: flex;
  align-items: center;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.analyzing-content {
  display: flex;
  flex-direction: column;
}

/* Streaming Preview */
.streaming-preview {
  margin-top: 12px;
  padding: 12px;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.streaming-header {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
  margin-bottom: 8px;
}

.streaming-content {
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 0.7rem;
  line-height: 1.4;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  padding: 8px;
  background-color: rgba(var(--v-theme-surface), 0.5);
  border-radius: 4px;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.streaming-content .cursor {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.result-item.suggested {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: rgba(var(--v-theme-warning), 0.1);
  border-radius: 8px;
}

.sample-preview {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.sample-preview h5 {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.sample-cards {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.sample-card {
  flex-shrink: 0;
  padding: 8px 12px;
  background-color: rgba(var(--v-theme-surface), 1);
  border-radius: 6px;
  font-size: 0.75rem;
}

.sample-card pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: monospace;
}

/* Type Category */
.type-category {
  margin-bottom: 24px;
}

.type-category-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: rgb(var(--v-theme-on-surface));
}

.type-category-description {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 16px;
}

.type-category--llars {
  padding: 16px;
  background: linear-gradient(135deg, rgba(136, 196, 200, 0.05), rgba(152, 212, 187, 0.05));
  border: 1px solid rgba(136, 196, 200, 0.2);
  border-radius: 12px;
}

/* Type Grid */
.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.type-card {
  position: relative;
  padding: 20px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background-color: rgba(var(--v-theme-primary), 0.02);
}

.type-card.selected {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.type-card.suggested {
  border-color: rgba(var(--v-theme-warning), 0.5);
}

.type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.type-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: rgb(var(--v-theme-on-surface));
}

.type-description {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.4;
  margin: 0;
}

.type-check {
  position: absolute;
  top: 12px;
  right: 12px;
}

.suggested-tag {
  position: absolute;
  top: -8px;
  left: 12px;
}

/* LLARS-specific type cards */
.type-card--llars {
  border-color: rgba(136, 196, 200, 0.3);
}

.type-card--llars:hover {
  border-color: rgba(136, 196, 200, 0.5);
  background-color: rgba(136, 196, 200, 0.05);
}

.type-card--llars.selected {
  border-color: rgb(var(--v-theme-accent));
  background-color: rgba(var(--v-theme-accent), 0.08);
}

.type-base-hint {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.1);
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Config Section */
.config-section {
  margin-bottom: 20px;
}

.config-label {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-on-surface));
}

/* Summary */
.summary-card {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px;
  padding: 20px;
}

.summary-section {
  margin-bottom: 4px;
}

.summary-section-title {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 12px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.summary-label {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.summary-value {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

/* Actions */
.wizard-actions {
  padding: 16px 24px;
}

/* Team Step Styles */
.team-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.team-section--ai {
  background-color: rgba(var(--v-theme-accent), 0.03);
  border-color: rgba(var(--v-theme-accent), 0.15);
}

.team-section-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* User List */
.user-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background-color: rgba(var(--v-theme-surface), 1);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.user-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.user-item.selected {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-color: rgb(var(--v-theme-primary));
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* LLM List */
.llm-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.llm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background-color: rgba(var(--v-theme-surface), 1);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.llm-item:hover {
  background-color: rgba(var(--v-theme-accent), 0.05);
  border-color: rgba(var(--v-theme-accent), 0.2);
}

.llm-item.selected {
  background-color: rgba(var(--v-theme-accent), 0.1);
  border-color: rgb(var(--v-theme-accent));
}

.llm-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: rgba(var(--v-theme-accent), 0.1);
  border-radius: 8px;
}

.llm-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.llm-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.llm-provider {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* LLM Category Sections */
.llm-category {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  padding: 8px;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
}

.llm-category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  margin-bottom: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* User Provider Items */
.llm-item--user .llm-icon {
  background-color: rgba(var(--v-theme-secondary), 0.1);
}

.llm-item--user:hover {
  background-color: rgba(var(--v-theme-secondary), 0.05);
  border-color: rgba(var(--v-theme-secondary), 0.2);
}

.llm-item--user.selected {
  background-color: rgba(var(--v-theme-secondary), 0.1);
  border-color: rgb(var(--v-theme-secondary));
}

/* Shared Badge */
.llm-shared-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-left: 6px;
  padding: 1px 6px;
  background-color: rgba(var(--v-theme-info), 0.1);
  border-radius: 10px;
  font-size: 0.65rem;
  color: rgb(var(--v-theme-info));
}

/* Selected Summary */
.selected-summary {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 12px 16px;
}

/* AI Analysis Styles */
.ai-powered-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: linear-gradient(90deg, rgba(176, 202, 151, 0.15), rgba(136, 196, 200, 0.15));
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.ai-reasoning {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  margin-top: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  font-style: italic;
}

.ai-suggestions-panel {
  background-color: rgba(var(--v-theme-primary), 0.03);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 12px;
  padding: 16px;
}

.ai-suggestions-title {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgb(var(--v-theme-primary));
}

.suggestion-field {
  margin-bottom: 12px;
}

.suggestion-field:last-child {
  margin-bottom: 0;
}

.suggestion-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 4px;
}
</style>
