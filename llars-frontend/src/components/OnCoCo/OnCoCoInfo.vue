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
                  <v-icon size="48" color="primary">mdi-message-text-outline</v-icon>
                </div>
                <div>
                  <h1 class="text-h3 font-weight-bold">OnCoCo 1.0</h1>
                  <p class="text-subtitle-1 text-medium-emphasis mb-0">
                    Online Counseling Conversations Dataset
                  </p>
                </div>
              </div>
              <p class="text-body-1 mb-4" style="max-width: 700px;">
                Ein fein-granulares Kategorie- und Klassifikationssystem für die automatisierte
                Inhaltsanalyse von psychosozialer Online-Beratung. Entwickelt an der TH Nürnberg
                nach Methoden qualitativer Sozialforschung.
              </p>
              <div class="d-flex flex-wrap ga-2">
                <v-chip color="primary" variant="flat" size="small">
                  <v-icon start size="16">mdi-tag-multiple</v-icon>
                  66 Kategorien
                </v-chip>
                <v-chip color="success" variant="flat" size="small">
                  <v-icon start size="16">mdi-chart-line</v-icon>
                  F1 Macro: 0.78
                </v-chip>
                <v-chip color="info" variant="flat" size="small">
                  <v-icon start size="16">mdi-translate</v-icon>
                  Bilingual DE/EN
                </v-chip>
                <v-chip color="secondary" variant="flat" size="small">
                  <v-icon start size="16">mdi-database</v-icon>
                  2.778 Nachrichten
                </v-chip>
                <v-chip color="purple" variant="flat" size="small">
                  <v-icon start size="16">mdi-license</v-icon>
                  CC BY-SA 4.0
                </v-chip>
              </div>
            </v-col>
            <v-col cols="12" md="4" class="text-center">
              <v-card variant="tonal" color="primary" class="pa-4">
                <div class="text-overline mb-1">Modell-Performance</div>
                <div class="text-h2 font-weight-bold mb-2">~0.88</div>
                <div class="text-caption">Cohen's Kappa vs. Menschen</div>
                <v-divider class="my-3"></v-divider>
                <div class="text-caption text-medium-emphasis">
                  XLM-RoBERTa-Large erreicht menschliche Zuverlässigkeit
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
            <v-icon color="primary" class="mr-2">mdi-sitemap</v-icon>
            Das hierarchische Kategoriensystem
          </v-card-title>
          <v-card-text>
            <p class="text-body-1 mb-4">
              OnCoCo verwendet ein <strong>5-stufiges hierarchisches System</strong> zur Klassifikation
              von Aussagen in Online-Beratungsgesprächen. Jede Kategorie hat einen eindeutigen Code,
              der den Pfad durch die Hierarchie beschreibt.
            </p>

            <!-- Visual Hierarchy Example -->
            <v-card variant="outlined" class="mb-4 pa-4 hierarchy-example">
              <div class="text-subtitle-2 font-weight-bold mb-3">Beispiel: Label-Code aufgeschlüsselt</div>
              <div class="code-breakdown">
                <div class="code-part">
                  <div class="code-value primary">CO</div>
                  <div class="code-label">Rolle</div>
                  <div class="code-desc">Counselor (Berater)</div>
                </div>
                <v-icon class="code-separator">mdi-chevron-right</v-icon>
                <div class="code-part">
                  <div class="code-value success">IF</div>
                  <div class="code-label">Level 1</div>
                  <div class="code-desc">Impact Factors</div>
                </div>
                <v-icon class="code-separator">mdi-chevron-right</v-icon>
                <div class="code-part">
                  <div class="code-value info">AC</div>
                  <div class="code-label">Level 2</div>
                  <div class="code-desc">Analysis & Clarification</div>
                </div>
                <v-icon class="code-separator">mdi-chevron-right</v-icon>
                <div class="code-part">
                  <div class="code-value warning">RF</div>
                  <div class="code-label">Level 3</div>
                  <div class="code-desc">Reflection (Fact)</div>
                </div>
                <v-icon class="code-separator">mdi-chevron-right</v-icon>
                <div class="code-part">
                  <div class="code-value purple">RLS-SR</div>
                  <div class="code-label">Level 4-5</div>
                  <div class="code-desc">Request Living Situation - Social Relationships</div>
                </div>
              </div>
              <v-divider class="my-3"></v-divider>
              <div class="text-caption text-medium-emphasis">
                <v-icon size="small" class="mr-1">mdi-information</v-icon>
                Vollständiger Code: <code class="bg-grey-lighten-3 px-2 py-1 rounded">CO-IF-AC-RF-RLS-SR</code>
                – „Frage nach sozialen Beziehungen/Lebenssituation"
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
              <v-icon>mdi-account-tie</v-icon>
            </v-avatar>
            Berater-Kategorien (CO-)
          </v-card-title>
          <v-card-text>
            <div class="text-h4 font-weight-bold mb-2">38</div>
            <div class="text-body-2 mb-4">Kategorien für Berater-Aussagen</div>

            <v-table density="compact" class="category-table">
              <thead>
                <tr>
                  <th>Level 1</th>
                  <th>Level 2</th>
                  <th class="text-right">#</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="2">Formalitäten zu Beginn</td>
                  <td class="text-right">1</td>
                </tr>
                <tr>
                  <td colspan="2">Moderation</td>
                  <td class="text-right">1</td>
                </tr>
                <tr>
                  <td rowspan="5" class="font-weight-bold">Impact Factors</td>
                  <td>Analyse & Problemklärung</td>
                  <td class="text-right">13</td>
                </tr>
                <tr>
                  <td>Zielvereinbarung</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>Motivation erzeugen</td>
                  <td class="text-right">4</td>
                </tr>
                <tr>
                  <td>Ressourcenaktivierung</td>
                  <td class="text-right">5</td>
                </tr>
                <tr>
                  <td>Hilfe & Problemlösung</td>
                  <td class="text-right">8</td>
                </tr>
                <tr>
                  <td colspan="2">Abschluss & Verabschiedung</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td colspan="2">Sonstige Aussagen</td>
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
              <v-icon>mdi-account</v-icon>
            </v-avatar>
            Klienten-Kategorien (CL-)
          </v-card-title>
          <v-card-text>
            <div class="text-h4 font-weight-bold mb-2">28</div>
            <div class="text-body-2 mb-4">Kategorien für Klienten-Aussagen</div>

            <v-table density="compact" class="category-table">
              <thead>
                <tr>
                  <th>Level 1</th>
                  <th>Level 2</th>
                  <th class="text-right">#</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="2">Formalitäten zu Beginn</td>
                  <td class="text-right">4</td>
                </tr>
                <tr>
                  <td colspan="2">Empathie</td>
                  <td class="text-right">3</td>
                </tr>
                <tr>
                  <td rowspan="5" class="font-weight-bold">Impact Factors</td>
                  <td>Analyse & Problemklärung</td>
                  <td class="text-right">8</td>
                </tr>
                <tr>
                  <td>Zielvereinbarung</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>Motivation</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>Ressourcenaktivierung</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td>Hilfe & Problembewältigung</td>
                  <td class="text-right">6</td>
                </tr>
                <tr>
                  <td colspan="2">Abschluss</td>
                  <td class="text-right">2</td>
                </tr>
                <tr>
                  <td colspan="2">Sonstige Aussagen</td>
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
            <v-icon color="warning" class="mr-2">mdi-star-four-points</v-icon>
            Impact Factors – Das Herzstück
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              <strong>Impact Factors</strong> sind die wirksamkeitsrelevanten Kategorien nach Grawe (2000).
              Sie bilden den Schwerpunkt der Analyse, da sie die Qualität und Methodik der Beratung abbilden.
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
            <v-icon color="success" class="mr-2">mdi-target</v-icon>
            Anwendungsfelder
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-chart-bar">
                <v-list-item-title>Qualitätsmonitoring</v-list-item-title>
                <v-list-item-subtitle>Übergänge & Impact-Faktoren sichtbar machen</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-school">
                <v-list-item-title>Training & Supervision</v-list-item-title>
                <v-list-item-subtitle>Muster in Gesprächen aufdecken, Feedback geben</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-flask">
                <v-list-item-title>Forschung</v-list-item-title>
                <v-list-item-subtitle>Skalierbare Inhaltsanalyse für psychosoziale Beratung</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-robot">
                <v-list-item-title>Chatbot-Evaluation</v-list-item-title>
                <v-list-item-subtitle>Vergleich Mensch vs. KI in feingranulären Klassen</v-list-item-subtitle>
              </v-list-item>
              <v-list-item prepend-icon="mdi-alert">
                <v-list-item-title>Risikoerkennung</v-list-item-title>
                <v-list-item-subtitle>Automatische Erkennung kritischer Situationen</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="h-100">
          <v-card-title class="d-flex align-center">
            <v-icon color="info" class="mr-2">mdi-chip</v-icon>
            Modell & Technik
          </v-card-title>
          <v-card-text>
            <v-table density="compact">
              <tbody>
                <tr>
                  <td class="font-weight-bold">Basis-Modell</td>
                  <td>XLM-RoBERTa-Large (561M Parameter)</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">Accuracy @1</td>
                  <td>~0.80</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">F1 Macro @1</td>
                  <td>~0.78</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">F1 Macro @2</td>
                  <td>~0.87 (bei Berücksichtigung Top-2)</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">Cohen's Kappa</td>
                  <td>~0.88 (vergleichbar mit Menschen)</td>
                </tr>
                <tr>
                  <td class="font-weight-bold">Rollen-Maskierung</td>
                  <td>Output-Logits werden nach Rolle gefiltert</td>
                </tr>
              </tbody>
            </v-table>

            <v-alert type="warning" variant="tonal" density="compact" class="mt-3">
              <strong>Zero-Shot versagt:</strong> GPT-4o erreicht nur F1 ~0.29 – Fine-Tuning ist notwendig!
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
            <v-icon color="purple" class="mr-2">mdi-text-box-search</v-icon>
            Beispiel-Klassifikationen
          </v-card-title>
          <v-card-text>
            <v-table density="comfortable" class="examples-table">
              <thead>
                <tr>
                  <th style="width: 80px;">Rolle</th>
                  <th style="width: 150px;">Code</th>
                  <th>Text</th>
                  <th style="width: 250px;">Kategorie-Pfad</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="example in exampleClassifications" :key="example.code">
                  <td>
                    <v-chip :color="example.role === 'CO' ? 'primary' : 'secondary'" size="small">
                      {{ example.role === 'CO' ? 'Berater' : 'Klient' }}
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
            <v-icon class="mr-2">mdi-link-variant</v-icon>
            Ressourcen & Referenzen
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>Paper & Datensatz</v-list-subheader>
                  <v-list-item
                    href="https://anonymous.4open.science/r/OnCoCoV1-78E8"
                    target="_blank"
                    prepend-icon="mdi-file-document"
                  >
                    <v-list-item-title>LREC 2026 Paper</v-list-item-title>
                    <v-list-item-subtitle>OnCoCo 1.0 Publikation</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>Lizenz</v-list-subheader>
                  <v-list-item prepend-icon="mdi-license">
                    <v-list-item-title>CC BY-SA 4.0</v-list-item-title>
                    <v-list-item-subtitle>Nutzung für Forschung & Bildung</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col cols="12" md="4">
                <v-list density="compact" bg-color="transparent">
                  <v-list-subheader>API in dieser Instanz</v-list-subheader>
                  <v-list-item prepend-icon="mdi-api">
                    <v-list-item-title><code>/api/oncoco/info</code></v-list-item-title>
                    <v-list-item-subtitle>Modell-Status & Label-Infos</v-list-item-subtitle>
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
              <v-icon color="primary" class="mr-2">mdi-account-tie</v-icon>
              <span class="font-weight-bold">Alle Berater-Labels ({{ counselorLabels.length }})</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact" hover>
                <thead>
                  <tr>
                    <th style="width: 180px;">Code</th>
                    <th style="width: 250px;">Name</th>
                    <th>Beschreibung</th>
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
              <v-icon color="secondary" class="mr-2">mdi-account</v-icon>
              <span class="font-weight-bold">Alle Klienten-Labels ({{ clientLabels.length }})</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact" hover>
                <thead>
                  <tr>
                    <th style="width: 180px;">Code</th>
                    <th style="width: 250px;">Name</th>
                    <th>Beschreibung</th>
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
            <v-icon size="large">mdi-rocket-launch</v-icon>
          </template>
          <v-alert-title>Bereit für die Analyse?</v-alert-title>
          <p class="mb-2">
            Starte auf der Übersichtsseite eine neue Analyse, um Transition-Matrizen,
            Säulen-Statistiken und Satz-Labels live zu verfolgen.
          </p>
          <v-btn
            color="primary"
            variant="flat"
            :to="{ name: 'OnCoCoOverview' }"
            prepend-icon="mdi-play"
          >
            Zur Analyse-Übersicht
          </v-btn>
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
const impactFactors = [
  {
    code: 'AC',
    name: 'Analyse & Problemklärung',
    description: 'Erfassung und Verständnis des Problems durch Fragen, Spiegelungen und Reflexionen.',
    color: 'info'
  },
  {
    code: 'AO',
    name: 'Zielvereinbarung',
    description: 'Definition und Abstimmung von Beratungszielen und Erwartungen.',
    color: 'success'
  },
  {
    code: 'Mot',
    name: 'Motivation erzeugen',
    description: 'Förderung von Veränderungsbereitschaft, Change-Talk (MI), Wertschätzung.',
    color: 'warning'
  },
  {
    code: 'RA',
    name: 'Ressourcenaktivierung',
    description: 'Aktivierung vorhandener Unterstützung aus Familie, Freunden oder professionellen Stellen.',
    color: 'purple'
  },
  {
    code: 'HP',
    name: 'Hilfe & Problemlösung',
    description: 'Konkrete Empfehlungen, Erklärungen, Warnungen und Ratschläge.',
    color: 'error'
  }
];

const exampleClassifications = [
  {
    role: 'CO',
    code: 'CO-IF-AC-RF-RLS-L',
    text: 'Um Sie besser beraten zu können, wäre es hilfreich zu wissen, welche Hobbys oder Interessen Sie haben.',
    path: 'Impact Factors → Analyse → Reflexion → Lebenssituation → Freizeit'
  },
  {
    role: 'CO',
    code: 'CO-IF-AC-RF-RTP-*',
    text: 'Können Sie das Gefühl, das Sie danach haben, noch etwas genauer beschreiben?',
    path: 'Impact Factors → Analyse → Reflexion → Gezielte Nachfrage'
  },
  {
    role: 'CO',
    code: 'CO-IF-HP-*-ITFE-*',
    text: 'Es ist völlig normal, dass junge Menschen in der Pubertät anfangen, sexuelle Wünsche und Fantasien zu entwickeln.',
    path: 'Impact Factors → Hilfe → Fachliche Erklärung'
  },
  {
    role: 'CL',
    code: 'CL-E-*-*-ECP-*',
    text: 'Es geht eigentlich mehr um meinen Bruder als um mich.',
    path: 'Empathie → Sorge um andere Person'
  },
  {
    role: 'CL',
    code: 'CL-IF-ACP-*-FPA-*',
    text: 'Ich habe versucht, meine Entzugssymptome mit Medikamenten zu lindern, aber es fühlt sich wie ein ständiger Kampf an.',
    path: 'Impact Factors → Analyse → Feedback zu bisherigen Versuchen'
  }
];

const counselorLabels = [
  { code: 'CO-FA-*-*-*-*', name: 'Formalitäten zu Beginn', description: 'Begrüßt und eröffnet das Gespräch.' },
  { code: 'CO-Mod-*-*-*-*', name: 'Moderation', description: 'Steuert Ablauf, fasst zusammen, setzt Übergänge.' },
  { code: 'CO-IF-AC-RF-RPD-*', name: 'Frage nach persönlichen Daten', description: 'Erfragt Basisinfos wie Alter, Kontakt oder Rahmenbedingungen.' },
  { code: 'CO-IF-AC-RF-RPA-*', name: 'Frage nach bisherigen Lösungsversuchen', description: 'Prüft, was bereits ausprobiert wurde.' },
  { code: 'CO-IF-AC-RF-SRx-*', name: 'Einfache Spiegelung', description: 'Spiegelt Kernaussagen kurz wider, um Verständnis zu zeigen.' },
  { code: 'CO-IF-AC-RF-RLS-SR', name: 'Frage Lebenssituation – Soziales', description: 'Erkundigt sich nach sozialem Umfeld und Beziehungen.' },
  { code: 'CO-IF-AC-RF-RLS-PS', name: 'Frage Lebenssituation – Beruf', description: 'Fragt nach Arbeit, Ausbildung oder beruflicher Lage.' },
  { code: 'CO-IF-AC-RF-RLS-ES', name: 'Frage Lebenssituation – Finanzen', description: 'Klärt finanzielle Situation und Belastungen.' },
  { code: 'CO-IF-AC-RF-RLS-H', name: 'Frage Lebenssituation – Gesundheit', description: 'Fragt nach körperlichem oder mentalem Gesundheitszustand.' },
  { code: 'CO-IF-AC-RF-RLS-L', name: 'Frage Lebenssituation – Freizeit', description: 'Erkundigt Hobbys und Ausgleichsaktivitäten.' },
  { code: 'CO-IF-AC-RF-RC-*', name: 'Frage nach Anliegen', description: 'Lässt das zentrale Anliegen präzisieren.' },
  { code: 'CO-IF-AC-RF-RTP-*', name: 'Gezielte, präzise Nachfrage', description: 'Stellt fokussierte Rückfragen, um Details zu klären.' },
  { code: 'CO-IF-AC-RF-RCD-*', name: 'Frage nach Veränderung', description: 'Erfragt gewünschte Änderungen oder Zielrichtung.' },
  { code: 'CO-IF-AC-RE-RCR-*', name: 'Komplexe Spiegelung', description: 'Spiegelt und ordnet komplexe Inhalte verdichtend.' },
  { code: 'CO-IF-AC-RE-RES-*', name: 'Frage nach Gefühlszustand', description: 'Erkundigt Emotionen und Stimmung.' },
  { code: 'CO-IF-AO-*-ROW-*', name: 'Frage nach Zielen/Wünschen', description: 'Klärt Ziele, Wünsche oder Erwartungen.' },
  { code: 'CO-IF-AO-*-ICO-*', name: 'Definition der Beratungsziele', description: 'Formuliert gemeinsame Ziele und Rahmen.' },
  { code: 'CO-IF-Mot-*-RFC-*', name: 'Change-Talk evozieren (MI)', description: 'Lenkt auf Veränderungsgründe und intrinsische Motivation.' },
  { code: 'CO-IF-Mot-*-IAC-*', name: 'Wahrgenommene Veränderungsfähigkeit', description: 'Spiegelt oder fördert Zutrauen in die eigene Fähigkeit.' },
  { code: 'CO-IF-Mot-*-ITA-*', name: 'Dank und Wertschätzung', description: 'Gibt positives Feedback und Anerkennung.' },
  { code: 'CO-IF-Mot-*-IEM-*', name: 'Ermutigung, Motivation', description: 'Unterstützt aktiv und bestärkt.' },
  { code: 'CO-IF-Mot-*-RS-*', name: 'Frage nach Unterstützungsressourcen', description: 'Erfragt verfügbare Personen oder Hilfen im Umfeld.' },
  { code: 'CO-IF-RA-*-RP-*', name: 'Anfrage zur Problemdarstellung', description: 'Fordert zur klaren Problembeschreibung auf.' },
  { code: 'CO-IF-RA-*-RAP-*', name: 'Vorschlag professionelle Ebene', description: 'Empfiehlt professionelle Angebote oder Stellen.' },
  { code: 'CO-IF-RA-*-N-RAFa', name: 'Vorschlag Familienebene', description: 'Regt an, Familie als Ressource einzubeziehen.' },
  { code: 'CO-IF-RA-*-N-RAFr', name: 'Vorschlag Freundesebene', description: 'Schlägt Unterstützung durch Freunde vor.' },
  { code: 'CO-IF-HP-*-ITFE-*', name: 'Fachliche Erklärungen', description: 'Gibt sachliche oder technische Infos.' },
  { code: 'CO-IF-HP-*-IPFR-*', name: 'Professionelle Empfehlung', description: 'Spricht konkrete Fach-Empfehlung aus.' },
  { code: 'CO-IF-HP-*-IF-*', name: 'Zukunftsprognose', description: 'Schätzt mögliche Entwicklung oder Verlauf.' },
  { code: 'CO-IF-HP-*-IW-*', name: 'Warnung', description: 'Weist auf Risiken oder Gefahren hin.' },
  { code: 'CO-IF-HP-*-ICO-*', name: 'Beruhigung', description: 'Wirkt deeskalierend und nimmt Druck.' },
  { code: 'CO-IF-HP-*-PP-IA', name: 'Ratschlag', description: 'Gibt direkte Handlungsanweisung.' },
  { code: 'CO-IF-HP-*-IEA', name: 'Bewertung, Interpretation', description: 'Ordnet Gesagtes ein und interpretiert.' },
  { code: 'CO-IF-HP-*-PP-IW', name: 'Wunsch', description: 'Formuliert eigenen Wunsch an die Klientin/den Klienten.' },
  { code: 'CO-FC-*-*-F-*', name: 'Verabschiedung', description: 'Schließt das Gespräch ab.' },
  { code: 'CO-FC-*-*-OPR-*', name: 'Angebot professioneller Ressourcen', description: 'Bietet weitere Stellen oder Materialien an.' },
  { code: 'CO-O-*-*-O-*', name: 'Andere Aussagen', description: 'Sonstiges, nicht in andere Kategorien passend.' },
  { code: 'CO-O-*-*-UCO-*', name: 'Unangemessene Bemerkung', description: 'Grenzüberschreitende oder unpassende Aussage.' }
];

const clientLabels = [
  { code: 'CL-FB-*-*-*-*', name: 'Formalitäten zu Beginn', description: 'Begrüßt und eröffnet das Gespräch.' },
  { code: 'CL-E-*-*-PT-*', name: 'Empathie für Dritte', description: 'Zeigt Mitgefühl für andere beteiligte Personen.' },
  { code: 'CL-E-*-*-ECC-*', name: 'Mitgefühl für andere', description: 'Bringt Mitgefühl allgemein zum Ausdruck.' },
  { code: 'CL-E-*-*-ECP-*', name: 'Sorge um andere Person', description: 'Sorge oder Anteilnahme für jemanden im Umfeld.' },
  { code: 'CL-IF-ACP-*-PS-*', name: 'Problemdarstellung', description: 'Schildert die Situation oder das Anliegen.' },
  { code: 'CL-IF-ACP-*-PD-*', name: 'Problemdefinition', description: 'Formuliert das Problem präziser oder analytisch.' },
  { code: 'CL-IF-ACP-*-DPD-*', name: 'Offenlegung persönlicher Daten', description: 'Teilt private Daten oder Hintergründe.' },
  { code: 'CL-IF-ACP-*-FPA-*', name: 'Feedback zu bisherigen Versuchen', description: 'Berichtet über bereits getestete Schritte.' },
  { code: 'CL-IF-ACP-*-OE-*', name: 'Eigener Gefühlsausdruck', description: 'Teilt eigene Emotionen offen mit.' },
  { code: 'CL-IF-ACP-*-Cons-*', name: 'Zustimmung', description: 'Stimmt Vorschlägen oder Fragen zu.' },
  { code: 'CL-IF-ACP-*-Rej-*', name: 'Ablehnung', description: 'Lehnt Vorschläge oder Annahmen ab.' },
  { code: 'CL-IF-ACP-*-Req-*', name: 'Allgemeine Anfrage', description: 'Fragt allgemein nach Hilfe oder Information.' },
  { code: 'CL-IF-AO-*-Obj-*', name: 'Ziel des Auftrags', description: 'Benennt das gewünschte Ziel oder Ergebnis.' },
  { code: 'CL-IF-AO-*-Ext-*', name: 'Erweiterung des Auftrags', description: 'Weitet den Auftrag oder die Bitte aus.' },
  { code: 'CL-IF-Mot-*-FC-*', name: 'Change-Talk', description: 'Äußert eigene Beweggründe für Veränderung.' },
  { code: 'CL-IF-Mot-*-RC-*', name: 'Gründe für Veränderung', description: 'Begründet, warum eine Änderung wichtig ist.' },
  { code: 'CL-IF-RA-*-RF-*', name: 'Ressourcen Freunde/Familie', description: 'Sieht Unterstützung durch nähere Kontakte.' },
  { code: 'CL-IF-RA-*-RP-*', name: 'Ressourcen professionelle Ebene', description: 'Nutzt oder erwägt professionelle Hilfe.' },
  { code: 'CL-IF-HP-*-PosF-*', name: 'Allgemeines positives Feedback', description: 'Gibt positives Gesamtfeedback.' },
  { code: 'CL-IF-HP-*-PosFR-*', name: 'Positives Feedback zu Empfehlungen', description: 'Lobt konkrete Ratschläge oder Maßnahmen.' },
  { code: 'CL-IF-HP-*-NegFR-*', name: 'Negatives Feedback zu Empfehlungen', description: 'Kritisiert konkrete Empfehlungen.' },
  { code: 'CL-IF-HP-*-RepRA-*', name: 'Bericht zur Umsetzung', description: 'Meldet Fortschritt oder Umsetzungsschritte.' },
  { code: 'CL-IF-HP-*-Succ-*', name: 'Finaler Erfolg', description: 'Meldet gelungenes Ergebnis.' },
  { code: 'CL-IF-HP-*-Fail-*', name: 'Finales Scheitern', description: 'Meldet Scheitern oder Rückschlag.' },
  { code: 'CL-FC-*-*-F-*', name: 'Verabschiedung', description: 'Schließt das Gespräch ab.' },
  { code: 'CL-FC-*-*-UPR-*', name: 'Weitere Nutzung professioneller Ressourcen', description: 'Signalisiert Bereitschaft, weitere Angebote zu nutzen.' },
  { code: 'CL-O-*-*-O-*', name: 'Andere Aussagen', description: 'Sonstiges, nicht in andere Kategorien passend.' },
  { code: 'CL-O-*-*-UCO-*', name: 'Unangemessene Bemerkung', description: 'Grenzüberschreitende oder unpassende Aussage.' }
];
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
