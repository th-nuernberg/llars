<template>
  <div class="matrix-comparison-metrics">
    <!-- Header with Help Button -->
    <div class="d-flex align-center mb-3">
      <div class="text-h6 font-weight-bold">
        <v-icon start>mdi-chart-scatter-plot</v-icon>
        Statistische Matrix-Vergleichsmetriken
      </div>
      <v-spacer></v-spacer>
      <v-btn
        variant="outlined"
        size="small"
        prepend-icon="mdi-help-circle"
        @click="showMethodologyDialog = true"
      >
        Methodik & Quellen
      </v-btn>
    </div>

    <!-- Loading State -->
    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <!-- Error Alert -->
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <!-- Controls -->
    <v-row class="mb-4">
      <v-col cols="12" sm="4" md="3">
        <v-select
          v-model="level"
          :items="[{title: 'Level 2 (aggregiert)', value: 'level2'}, {title: 'Vollständig', value: 'full'}]"
          label="Detailstufe"
          variant="outlined"
          density="compact"
          @update:model-value="loadMetrics"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="4" md="3">
        <v-text-field
          v-model.number="smoothing"
          type="number"
          min="0"
          step="0.1"
          label="Laplace Smoothing (alpha)"
          variant="outlined"
          density="compact"
          @update:model-value="debouncedLoadMetrics"
        >
          <template v-slot:append>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small">mdi-information</v-icon>
              </template>
              <span>Additive Glättung für Nullzählungen. 0 = keine, 1 = Standard</span>
            </v-tooltip>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="3">
        <v-text-field
          v-model.number="permutations"
          type="number"
          min="100"
          max="10000"
          step="100"
          label="Permutationen"
          variant="outlined"
          density="compact"
          @update:model-value="debouncedLoadMetrics"
        >
          <template v-slot:append>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small">mdi-information</v-icon>
              </template>
              <span>Anzahl der Permutationen für Signifikanztest (mehr = genauer, aber langsamer)</span>
            </v-tooltip>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="12" md="3" class="d-flex align-center">
        <v-btn
          color="primary"
          variant="flat"
          @click="loadMetrics"
          :loading="loading"
          block
        >
          <v-icon start>mdi-refresh</v-icon>
          Berechnen
        </v-btn>
      </v-col>
    </v-row>

    <!-- Results -->
    <template v-if="metricsData && !loading">
      <!-- Pairwise Comparisons -->
      <v-row>
        <v-col
          v-for="(comparison, idx) in metricsData.pairwise_comparisons"
          :key="idx"
          cols="12"
          :md="metricsData.pairwise_comparisons.length === 1 ? 12 : 6"
        >
          <v-card variant="outlined" class="h-100">
            <v-card-title class="text-subtitle-1 py-2 d-flex align-center">
              <v-chip size="small" color="primary" class="mr-2">{{ comparison.pillar_a?.name || 'Säule A' }}</v-chip>
              <v-icon size="small">mdi-swap-horizontal</v-icon>
              <v-chip size="small" color="secondary" class="ml-2">{{ comparison.pillar_b?.name || 'Säule B' }}</v-chip>
            </v-card-title>

            <v-card-text>
              <!-- Frobenius Distance -->
              <div class="metric-row mb-3">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    Frobenius-Distanz
                    <sup class="footnote-ref" @click="showFootnote('frobenius')">[1]</sup>
                  </span>
                  <span class="font-weight-bold text-h6">{{ formatNum(comparison.metrics?.frobenius_distance) }}</span>
                </div>
                <v-progress-linear
                  :model-value="Math.min((comparison.metrics?.frobenius_distance || 0) * 100, 100)"
                  height="8"
                  rounded
                  :color="getFrobeniusColor(comparison.metrics?.frobenius_distance || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ getFrobeniusInterpretation(comparison.metrics?.frobenius_distance || 0) }}
                </div>
              </div>

              <!-- Jensen-Shannon Divergence -->
              <div class="metric-row mb-3" v-if="comparison.metrics">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    Jensen-Shannon Divergenz (Mittel)
                    <sup class="footnote-ref" @click="showFootnote('jsd')">[2]</sup>
                  </span>
                  <span class="font-weight-bold text-h6">{{ formatNum(comparison.metrics?.mean_jsd) }}</span>
                </div>
                <v-progress-linear
                  :model-value="(comparison.metrics?.mean_jsd || 0) * 100"
                  height="8"
                  rounded
                  :color="getJSDColor(comparison.metrics?.mean_jsd || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  Max: {{ formatNum(comparison.metrics?.max_jsd) }} |
                  {{ getJSDInterpretation(comparison.metrics?.mean_jsd || 0) }}
                </div>
              </div>

              <!-- Permutation Test -->
              <div class="metric-row mb-3" v-if="comparison.statistical_tests?.permutation_test">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    Permutationstest p-Wert
                    <sup class="footnote-ref" @click="showFootnote('permutation')">[3]</sup>
                  </span>
                  <v-chip
                    :color="getSignificanceColor(comparison.statistical_tests?.permutation_test?.p_value || 1)"
                    size="small"
                  >
                    p = {{ formatNum(comparison.statistical_tests?.permutation_test?.p_value) }}
                  </v-chip>
                </div>
                <div class="text-caption mt-1">
                  <v-icon
                    :color="(comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05 ? 'success' : 'warning'"
                    size="small"
                    class="mr-1"
                  >
                    {{ (comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05 ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </v-icon>
                  {{ (comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05
                    ? 'Statistisch signifikanter Unterschied (p < 0.05)'
                    : 'Kein signifikanter Unterschied nachgewiesen' }}
                </div>
              </div>

              <!-- Effect Size -->
              <div class="metric-row mb-3" v-if="comparison.effect_size">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    Effektstärke
                    <sup class="footnote-ref" @click="showFootnote('effect_size')">[4]</sup>
                  </span>
                  <div class="text-right">
                    <div class="font-weight-bold">{{ formatNum(comparison.effect_size?.normalized_frobenius) }}</div>
                    <div class="text-caption text-medium-emphasis">Norm. Frobenius</div>
                  </div>
                </div>
                <v-progress-linear
                  :model-value="Math.min((comparison.effect_size?.normalized_frobenius || 0) * 200, 100)"
                  height="8"
                  rounded
                  :color="getEffectSizeColor(comparison.effect_size?.normalized_frobenius || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ getEffectSizeInterpretation(comparison.effect_size?.normalized_frobenius || 0) }}
                </div>
              </div>

              <!-- Chi-Square Summary -->
              <div class="metric-row mb-3" v-if="comparison.statistical_tests?.chi_square">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    Chi-Quadrat Test
                    <sup class="footnote-ref" @click="showFootnote('chi_square')">[5]</sup>
                  </span>
                  <v-chip
                    :color="getChiSquareSummaryColorFromStats(comparison.statistical_tests?.chi_square)"
                    size="small"
                  >
                    {{ comparison.statistical_tests?.chi_square?.significant_rows || 0 }} / {{ comparison.statistical_tests?.chi_square?.total_rows || 0 }} signifikant
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis mt-1">
                  Zustände mit signifikant unterschiedlichen Übergangsverteilungen
                </div>
              </div>

              <v-divider class="my-3"></v-divider>

              <!-- Outlier Transitions -->
              <div class="metric-row mb-3" v-if="comparison.outlier_transitions">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-body-2 font-weight-bold">
                    <v-icon start size="small">mdi-alert-outline</v-icon>
                    Ausreißer-Transitionen
                  </span>
                  <v-chip size="x-small" color="warning" variant="tonal">
                    {{ comparison.outlier_transitions?.length || 0 }}
                  </v-chip>
                </div>
                <v-expansion-panels v-if="comparison.outlier_transitions?.length > 0" variant="accordion" density="compact">
                  <v-expansion-panel>
                    <v-expansion-panel-title class="text-caption py-1">
                      Transitionen mit Z-Score > 2 anzeigen
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-list density="compact" class="py-0">
                        <v-list-item
                          v-for="(outlier, oIdx) in comparison.outlier_transitions.slice(0, 10)"
                          :key="oIdx"
                          class="px-0"
                        >
                          <template v-slot:prepend>
                            <v-icon
                              :color="outlier.difference > 0 ? 'success' : 'error'"
                              size="small"
                            >
                              {{ outlier.difference > 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                            </v-icon>
                          </template>
                          <v-list-item-title class="text-caption">
                            {{ outlier.from_label }} -> {{ outlier.to_label }}
                          </v-list-item-title>
                          <template v-slot:append>
                            <span class="text-caption font-weight-bold">
                              z={{ formatNum(outlier.z_score, 2) }}
                            </span>
                          </template>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
                <div v-else class="text-caption text-medium-emphasis">
                  Keine Ausreißer gefunden
                </div>
              </div>

              <!-- Missing Transitions -->
              <div class="metric-row" v-if="comparison.missing_transitions">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-body-2 font-weight-bold">
                    <v-icon start size="small">mdi-help-circle-outline</v-icon>
                    Fehlende Transitionen
                  </span>
                  <div>
                    <v-chip size="x-small" color="primary" variant="tonal" class="mr-1">
                      {{ comparison.missing_transitions?.missing_in_A?.length || 0 }} nur in A
                    </v-chip>
                    <v-chip size="x-small" color="secondary" variant="tonal">
                      {{ comparison.missing_transitions?.missing_in_B?.length || 0 }} nur in B
                    </v-chip>
                  </div>
                </div>
                <v-expansion-panels v-if="(comparison.missing_transitions?.missing_in_A?.length || 0) > 0 || (comparison.missing_transitions?.missing_in_B?.length || 0) > 0" variant="accordion" density="compact">
                  <v-expansion-panel>
                    <v-expansion-panel-title class="text-caption py-1">
                      Fehlende Transitionen anzeigen
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-if="comparison.missing_transitions?.missing_in_A?.length > 0" class="mb-2">
                        <div class="text-caption font-weight-bold text-primary">Nur in {{ comparison.pillar_b?.name || 'B' }}:</div>
                        <v-chip
                          v-for="(trans, tIdx) in comparison.missing_transitions.missing_in_A.slice(0, 5)"
                          :key="'a-' + tIdx"
                          size="x-small"
                          class="ma-1"
                          variant="outlined"
                        >
                          {{ trans.from_label }} -> {{ trans.to_label }}
                        </v-chip>
                        <span v-if="comparison.missing_transitions.missing_in_A.length > 5" class="text-caption">
                          +{{ comparison.missing_transitions.missing_in_A.length - 5 }} weitere
                        </span>
                      </div>
                      <div v-if="comparison.missing_transitions?.missing_in_B?.length > 0">
                        <div class="text-caption font-weight-bold text-secondary">Nur in {{ comparison.pillar_a?.name || 'A' }}:</div>
                        <v-chip
                          v-for="(trans, tIdx) in comparison.missing_transitions.missing_in_B.slice(0, 5)"
                          :key="'b-' + tIdx"
                          size="x-small"
                          class="ma-1"
                          variant="outlined"
                        >
                          {{ trans.from_label }} -> {{ trans.to_label }}
                        </v-chip>
                        <span v-if="comparison.missing_transitions.missing_in_B.length > 5" class="text-caption">
                          +{{ comparison.missing_transitions.missing_in_B.length - 5 }} weitere
                        </span>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
                <div v-else class="text-caption text-medium-emphasis">
                  Alle Transitionen in beiden Matrizen vorhanden
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Footnotes -->
      <v-card variant="tonal" class="mt-4" color="surface-variant">
        <v-card-text class="text-caption">
          <div class="font-weight-bold mb-2">Quellen:</div>
          <div>[1] Frobenius-Norm: Golub & Van Loan (2013). Matrix Computations. Johns Hopkins University Press.</div>
          <div>[2] Jensen-Shannon Divergenz: Lin, J. (1991). Divergence measures based on the Shannon entropy. IEEE Transactions on Information Theory.</div>
          <div>[3] Permutationstest: Vautard, R. et al. (1990). Monte Carlo and parametric tests. Journal of Statistical Planning and Inference.</div>
          <div>[4] Effektstärke: Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences. Routledge.</div>
          <div>[5] Chi-Quadrat für Markov-Ketten: Anderson, T.W. & Goodman, L.A. (1957). Statistical inference about Markov chains. The Annals of Mathematical Statistics.</div>
        </v-card-text>
      </v-card>
    </template>

    <!-- Empty State -->
    <v-alert v-if="!metricsData && !loading && !error" type="info" variant="tonal">
      Klicken Sie auf "Berechnen", um statistische Metriken zu generieren.
    </v-alert>

    <!-- Methodology Dialog -->
    <v-dialog v-model="showMethodologyDialog" max-width="900" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-book-open-variant</v-icon>
          Methodik & Erklärungen
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="showMethodologyDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text>
          <v-expansion-panels variant="accordion">
            <!-- Frobenius Distance -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="primary">mdi-matrix</v-icon>
                Frobenius-Distanz
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Die Frobenius-Norm misst den Gesamtunterschied zwischen zwei Matrizen als euklidische Distanz aller Matrixelemente.</p>

                  <h4>Formel</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\|A - B\|_F = \sqrt{\sum_{i,j} (A_{ij} - B_{ij})^2}" :display-mode="true" />
                  </div>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Wenn wir die Übergangsmatrizen von <strong>Säule 1 (Rollenspiele)</strong> und <strong>Säule 3 (Anonymisierte Daten)</strong> vergleichen:</p>
                  <ul>
                    <li>Eine <strong>Frobenius-Distanz von 0.1</strong> bedeutet, dass die Beratungsmuster sehr ähnlich sind</li>
                    <li>Eine <strong>Distanz von 0.5</strong> zeigt deutliche Unterschiede in den Kommunikationsübergängen</li>
                    <li>Je größer der Wert, desto unterschiedlicher verhalten sich Berater in den verschiedenen Datenquellen</li>
                  </ul>

                  <h4>Interpretation</h4>
                  <v-chip color="success" size="small" class="mr-2">0 - 0.2: Sehr ähnlich</v-chip>
                  <v-chip color="info" size="small" class="mr-2">0.2 - 0.4: Moderat unterschiedlich</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">0.4 - 0.6: Deutlich unterschiedlich</v-chip>
                  <v-chip color="error" size="small">> 0.6: Stark unterschiedlich</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Golub, G.H. & Van Loan, C.F. (2013). Matrix Computations (4th ed.). Johns Hopkins University Press.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Jensen-Shannon Divergence -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="secondary">mdi-chart-bell-curve</v-icon>
                Jensen-Shannon Divergenz (JSD)
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Die JSD ist ein symmetrisches Maß für den Unterschied zwischen zwei Wahrscheinlichkeitsverteilungen. Sie basiert auf der Kullback-Leibler-Divergenz, ist aber symmetrisch und immer definiert.</p>

                  <h4>Formel</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\text{JSD}(P \| Q) = \frac{1}{2} \text{KL}(P \| M) + \frac{1}{2} \text{KL}(Q \| M)" :display-mode="true" />
                    <div class="formula-note">wobei <KatexFormula formula="M = \frac{1}{2}(P + Q)" /></div>
                    <KatexFormula formula="\text{KL}(P \| Q) = \sum_i P_i \cdot \log_2 \left( \frac{P_i}{Q_i} \right)" :display-mode="true" />
                  </div>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Für jede Zeile der Übergangsmatrix (jeden Ausgangszustand) berechnen wir die JSD:</p>
                  <ul>
                    <li>Wenn ein Berater nach einer <strong>"Aktiven Zuhören"-Intervention (CO-IF-AC)</strong> in Säule 1 meist zu "Fragen" übergeht, aber in Säule 3 zu "Informieren", zeigt die JSD für diese Zeile einen hohen Wert</li>
                    <li><strong>Mittlere JSD nahe 0</strong>: Die Übergangsmuster sind nahezu identisch</li>
                    <li><strong>Mittlere JSD nahe 1</strong>: Die Übergangsmuster sind völlig unterschiedlich</li>
                  </ul>

                  <h4>Interpretation</h4>
                  <v-chip color="success" size="small" class="mr-2">0 - 0.1: Sehr ähnlich</v-chip>
                  <v-chip color="info" size="small" class="mr-2">0.1 - 0.3: Moderate Unterschiede</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">0.3 - 0.5: Deutliche Unterschiede</v-chip>
                  <v-chip color="error" size="small">> 0.5: Starke Unterschiede</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Lin, J. (1991). Divergence measures based on the Shannon entropy. IEEE Transactions on Information Theory, 37(1), 145-151.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Permutation Test -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="info">mdi-shuffle-variant</v-icon>
                Permutationstest
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Ein nicht-parametrischer Signifikanztest, der die Nullhypothese prüft, dass zwei Matrizen aus derselben Verteilung stammen.</p>

                  <h4>Verfahren</h4>
                  <ol>
                    <li>Berechne die beobachtete Frobenius-Distanz zwischen den Originalmatrizen</li>
                    <li>Mische die Zähldaten beider Matrizen zufällig</li>
                    <li>Berechne die Frobenius-Distanz der gemischten Matrizen</li>
                    <li>Wiederhole Schritte 2-3 n-mal (z.B. 1000 mal)</li>
                    <li>p-Wert = Anteil der Permutationen mit Distanz >= beobachtete Distanz</li>
                  </ol>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Wir testen, ob die Unterschiede zwischen Rollenspielen (Säule 1) und echten Beratungsgesprächen (Säule 3) statistisch signifikant sind:</p>
                  <ul>
                    <li><strong>p < 0.05</strong>: Die Unterschiede sind signifikant - Rollenspiele spiegeln nicht perfekt echte Beratungen wider</li>
                    <li><strong>p >= 0.05</strong>: Kein signifikanter Unterschied nachweisbar - die Datenquellen könnten dieselben Muster zeigen</li>
                  </ul>

                  <h4>Interpretation</h4>
                  <v-chip color="success" size="small" class="mr-2">p < 0.01: Hoch signifikant</v-chip>
                  <v-chip color="info" size="small" class="mr-2">p < 0.05: Signifikant</v-chip>
                  <v-chip color="warning" size="small">p >= 0.05: Nicht signifikant</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Good, P. (2005). Permutation, Parametric and Bootstrap Tests of Hypotheses (3rd ed.). Springer.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Effect Size -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="warning">mdi-arrow-expand-horizontal</v-icon>
                Effektstärke
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Die Effektstärke gibt an, wie groß ein Unterschied praktisch ist - unabhängig von der Stichprobengröße. Ein signifikanter Unterschied kann klein sein, wenn die Stichprobe sehr groß ist.</p>

                  <h4>Normalisierte Frobenius-Distanz</h4>
                  <div class="formula-box">
                    <KatexFormula formula="d_{\text{norm}} = \frac{\|A - B\|_F}{\sqrt{n \cdot m}}" :display-mode="true" />
                    <div class="formula-note">wobei <KatexFormula formula="n, m" /> die Matrixdimensionen sind</div>
                  </div>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Selbst wenn der Permutationstest signifikant ist (p < 0.05), zeigt die Effektstärke, ob der Unterschied praktisch relevant ist:</p>
                  <ul>
                    <li><strong>Kleine Effektstärke (< 0.2)</strong>: Die Unterschiede sind statistisch, aber praktisch kaum relevant - Berater verhalten sich ähnlich</li>
                    <li><strong>Mittlere Effektstärke (0.2 - 0.5)</strong>: Erkennbare Unterschiede in den Beratungsmustern</li>
                    <li><strong>Große Effektstärke (> 0.5)</strong>: Deutlich unterschiedliche Beratungsstile zwischen den Datenquellen</li>
                  </ul>

                  <h4>Interpretation (nach Cohen)</h4>
                  <v-chip color="success" size="small" class="mr-2">< 0.2: Klein</v-chip>
                  <v-chip color="info" size="small" class="mr-2">0.2 - 0.5: Mittel</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">0.5 - 0.8: Groß</v-chip>
                  <v-chip color="error" size="small">> 0.8: Sehr groß</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Routledge.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Chi-Square Test -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="error">mdi-chart-bar</v-icon>
                Chi-Quadrat-Test für Markov-Ketten
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Der Chi-Quadrat-Test prüft für jeden Ausgangszustand, ob die Übergangswahrscheinlichkeiten signifikant unterschiedlich sind.</p>

                  <h4>Formel</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\chi^2 = \sum_j \frac{(O_j - E_j)^2}{E_j}" :display-mode="true" />
                    <div class="formula-note">wobei <KatexFormula formula="O" /> = beobachtete, <KatexFormula formula="E" /> = erwartete Häufigkeiten</div>
                  </div>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Für jeden Beratungscode (z.B. CO-IF-AC "Aktives Zuhören") testen wir separat:</p>
                  <ul>
                    <li>Wenn nach "Aktives Zuhören" in Säule 1 <strong>60% zu "Fragen"</strong> übergehen, aber in Säule 3 nur <strong>40%</strong>, zeigt der Chi-Quadrat-Test, ob dieser Unterschied signifikant ist</li>
                    <li>So finden wir <strong>genau welche Beratungstechniken</strong> sich zwischen den Datenquellen unterscheiden</li>
                  </ul>

                  <h4>Interpretation</h4>
                  <p>Der Anteil signifikanter Zustände (p < 0.05) zeigt, wie viele Beratungstechniken sich unterscheiden:</p>
                  <v-chip color="success" size="small" class="mr-2">< 20%: Wenige Unterschiede</v-chip>
                  <v-chip color="info" size="small" class="mr-2">20 - 40%: Moderate Unterschiede</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">40 - 60%: Viele Unterschiede</v-chip>
                  <v-chip color="error" size="small">> 60%: Sehr viele Unterschiede</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Anderson, T.W. & Goodman, L.A. (1957). Statistical inference about Markov chains. The Annals of Mathematical Statistics, 28(1), 89-110.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Laplace Smoothing -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start color="purple">mdi-tune</v-icon>
                Laplace-Glättung (Additive Smoothing)
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>Was ist das?</h4>
                  <p>Laplace-Glättung verhindert Probleme mit Nullzählungen in der Matrix, indem ein kleiner Wert zu allen Zellen addiert wird.</p>

                  <h4>Formel</h4>
                  <div class="formula-box">
                    <KatexFormula formula="P(y|x) = \frac{\text{count}(x,y) + \alpha}{\sum_z \text{count}(x,z) + \alpha \cdot |Z|}" :display-mode="true" />
                    <div class="formula-note">wobei <KatexFormula formula="\alpha" /> der Glättungsparameter ist</div>
                  </div>

                  <h4>OnCoCo-Beispiel</h4>
                  <p>Wenn eine bestimmte Transition (z.B. "Fragen" -> "Konfrontation") in Säule 1 <strong>nie vorkommt</strong>, aber in Säule 3 <strong>5 mal</strong>:</p>
                  <ul>
                    <li>Ohne Glättung: Division durch Null möglich, JSD = unendlich</li>
                    <li><strong>Mit alpha = 1</strong>: Jede Zelle erhält mindestens 1 Pseudozählung</li>
                    <li>Höheres alpha: Konservativere Schätzung, aber glättet echte Unterschiede</li>
                  </ul>

                  <h4>Empfohlene Werte</h4>
                  <v-chip color="info" size="small" class="mr-2">alpha = 0: Keine Glättung (nur bei vollständigen Daten)</v-chip>
                  <v-chip color="success" size="small" class="mr-2">alpha = 1: Standard (Laplace)</v-chip>
                  <v-chip color="warning" size="small">alpha > 1: Starke Glättung</v-chip>

                  <h4>Quelle</h4>
                  <p class="text-caption">Manning, C.D., Raghavan, P. & Schuetze, H. (2008). Introduction to Information Retrieval. Cambridge University Press.</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showMethodologyDialog = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Footnote Snackbar -->
    <v-snackbar v-model="showFootnoteSnackbar" :timeout="5000" location="bottom">
      {{ footnoteText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showFootnoteSnackbar = false">Schließen</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import KatexFormula from '@/components/common/KatexFormula.vue';

const props = defineProps({
  analysisId: {
    type: [Number, String],
    required: true
  }
});

// State
const loading = ref(false);
const error = ref(null);
const metricsData = ref(null);
const level = ref('level2');
const smoothing = ref(1.0);
const permutations = ref(1000);

// Dialog States
const showMethodologyDialog = ref(false);
const showFootnoteSnackbar = ref(false);
const footnoteText = ref('');

// Debounce timer
let debounceTimer = null;

// Footnote references
const footnotes = {
  frobenius: '[1] Frobenius-Norm: Golub & Van Loan (2013). Matrix Computations. Johns Hopkins University Press.',
  jsd: '[2] Jensen-Shannon Divergenz: Lin, J. (1991). Divergence measures based on the Shannon entropy. IEEE Transactions on Information Theory.',
  permutation: '[3] Permutationstest: Good, P. (2005). Permutation, Parametric and Bootstrap Tests of Hypotheses. Springer.',
  effect_size: '[4] Effektstärke: Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences. Routledge.',
  chi_square: '[5] Chi-Quadrat für Markov-Ketten: Anderson & Goodman (1957). Statistical inference about Markov chains.'
};

// Safe number formatting helper
const formatNum = (value, decimals = 4) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return Number(value).toFixed(decimals);
};

// Load Metrics
const loadMetrics = async () => {
  loading.value = true;
  error.value = null;

  try {
    const params = new URLSearchParams();
    params.append('level', level.value);
    params.append('smoothing', smoothing.value);
    params.append('n_permutations', permutations.value);

    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${props.analysisId}/matrix-comparison?${params}`
    );
    metricsData.value = response.data;
  } catch (err) {
    console.error('Error loading metrics:', err);
    error.value = err.response?.data?.error || 'Fehler beim Laden der Metriken';
  } finally {
    loading.value = false;
  }
};

// Debounced load
const debouncedLoadMetrics = () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    loadMetrics();
  }, 500);
};

// Show footnote
const showFootnote = (key) => {
  footnoteText.value = footnotes[key] || '';
  showFootnoteSnackbar.value = true;
};

// Color helpers
const getFrobeniusColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.4) return 'info';
  if (value < 0.6) return 'warning';
  return 'error';
};

const getFrobeniusInterpretation = (value) => {
  if (value < 0.2) return 'Sehr ähnliche Matrizen';
  if (value < 0.4) return 'Moderat unterschiedlich';
  if (value < 0.6) return 'Deutlich unterschiedlich';
  return 'Stark unterschiedlich';
};

const getJSDColor = (value) => {
  if (value < 0.1) return 'success';
  if (value < 0.3) return 'info';
  if (value < 0.5) return 'warning';
  return 'error';
};

const getJSDInterpretation = (value) => {
  if (value < 0.1) return 'Sehr ähnliche Verteilungen';
  if (value < 0.3) return 'Moderate Unterschiede';
  if (value < 0.5) return 'Deutliche Unterschiede';
  return 'Stark unterschiedliche Verteilungen';
};

const getSignificanceColor = (pValue) => {
  if (pValue < 0.01) return 'error';
  if (pValue < 0.05) return 'warning';
  return 'success';
};

const getEffectSizeColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.5) return 'info';
  if (value < 0.8) return 'warning';
  return 'error';
};

const getEffectSizeInterpretation = (value) => {
  if (value < 0.2) return 'Kleine Effektstärke';
  if (value < 0.5) return 'Mittlere Effektstärke';
  if (value < 0.8) return 'Große Effektstärke';
  return 'Sehr große Effektstärke';
};

const getChiSquareSignificantCount = (chiSquare) => {
  if (!chiSquare) return 0;
  return Object.values(chiSquare).filter(v => v?.p_value < 0.05).length;
};

const getChiSquareSummaryColor = (chiSquare) => {
  if (!chiSquare) return 'grey';
  const total = Object.keys(chiSquare).length;
  if (total === 0) return 'grey';
  const significant = getChiSquareSignificantCount(chiSquare);
  const ratio = significant / total;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};

// New version that takes the chi_square object from statistical_tests
const getChiSquareSummaryColorFromStats = (chiSquareStats) => {
  if (!chiSquareStats) return 'grey';
  const { significant_rows, total_rows } = chiSquareStats;
  if (!total_rows || total_rows === 0) return 'grey';
  const ratio = significant_rows / total_rows;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};

// Load on mount
onMounted(() => {
  loadMetrics();
});
</script>

<style scoped>
.matrix-comparison-metrics {
  width: 100%;
}

.metric-row {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
  padding-bottom: 8px;
}

.metric-row:last-child {
  border-bottom: none;
}

.footnote-ref {
  cursor: pointer;
  color: rgb(var(--v-theme-primary));
  font-size: 0.7em;
  vertical-align: super;
}

.footnote-ref:hover {
  text-decoration: underline;
}

.methodology-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-primary));
}

.methodology-content h4:first-child {
  margin-top: 0;
}

.methodology-content p {
  margin-bottom: 8px;
}

.methodology-content ul,
.methodology-content ol {
  margin-bottom: 12px;
  padding-left: 20px;
}

.methodology-content li {
  margin-bottom: 4px;
}

.formula-box {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 16px 20px;
  border-radius: 8px;
  margin: 12px 0;
  overflow-x: auto;
  border-left: 3px solid rgb(var(--v-theme-primary));
  text-align: center;
}

/* KaTeX specific styling */
.formula-box :deep(.katex) {
  font-size: 1.2em;
  color: rgba(var(--v-theme-on-surface), 0.95);
}

.formula-note {
  font-size: 0.9em;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-top: 8px;
  text-align: center;
}

.formula-note :deep(.katex) {
  font-size: 1em;
}
</style>
