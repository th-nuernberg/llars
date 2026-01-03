/**
 * LatexEditorPane Constants
 *
 * Shared constants for LaTeX editing functionality.
 * Used by both LatexEditorPane and LatexAI editor components.
 *
 * @module LatexEditorPane/constants
 */

// AI Collab color for AI-generated changes (distinct lavender/purple)
export const AI_COLLAB_COLOR = '#b39ddb'
export const AI_COLLAB_USERNAME = 'AI Assistant'

/**
 * LaTeX command completions for autocompletion
 */
export const LATEX_COMMAND_COMPLETIONS = [
  { label: '\\documentclass', type: 'keyword', info: 'Dokumentklasse', apply: '\\documentclass{}' },
  { label: '\\usepackage', type: 'keyword', info: 'Paket laden', apply: '\\usepackage{}' },
  { label: '\\begin', type: 'keyword', info: 'Umgebung starten', apply: '\\begin{}' },
  { label: '\\end', type: 'keyword', info: 'Umgebung beenden', apply: '\\end{}' },
  { label: '\\section', type: 'keyword', info: 'Abschnitt', apply: '\\section{}' },
  { label: '\\subsection', type: 'keyword', info: 'Unterabschnitt', apply: '\\subsection{}' },
  { label: '\\subsubsection', type: 'keyword', info: 'Unter-Unterabschnitt', apply: '\\subsubsection{}' },
  { label: '\\paragraph', type: 'keyword', info: 'Paragraph', apply: '\\paragraph{}' },
  { label: '\\textbf', type: 'function', info: 'Fett', apply: '\\textbf{}' },
  { label: '\\textit', type: 'function', info: 'Kursiv', apply: '\\textit{}' },
  { label: '\\emph', type: 'function', info: 'Hervorheben', apply: '\\emph{}' },
  { label: '\\underline', type: 'function', info: 'Unterstreichen', apply: '\\underline{}' },
  { label: '\\item', type: 'keyword', info: 'Listenpunkt', apply: '\\item ' },
  { label: '\\label', type: 'keyword', info: 'Label', apply: '\\label{}' },
  { label: '\\ref', type: 'keyword', info: 'Referenz', apply: '\\ref{}' },
  { label: '\\pageref', type: 'keyword', info: 'Seitenreferenz', apply: '\\pageref{}' },
  { label: '\\cite', type: 'keyword', info: 'Zitat', apply: '\\cite{}' },
  { label: '\\citet', type: 'keyword', info: 'Textzitat', apply: '\\citet{}' },
  { label: '\\citep', type: 'keyword', info: 'Klammerzitat', apply: '\\citep{}' },
  { label: '\\includegraphics', type: 'keyword', info: 'Grafik', apply: '\\includegraphics[]{}' },
  { label: '\\caption', type: 'keyword', info: 'Caption', apply: '\\caption{}' },
  { label: '\\centering', type: 'keyword', info: 'Zentrieren', apply: '\\centering' },
  { label: '\\footnote', type: 'keyword', info: 'Fussnote', apply: '\\footnote{}' },
  { label: '\\url', type: 'keyword', info: 'URL', apply: '\\url{}' },
  { label: '\\href', type: 'keyword', info: 'Link', apply: '\\href{}{}' },
  { label: '\\title', type: 'keyword', info: 'Titel', apply: '\\title{}' },
  { label: '\\author', type: 'keyword', info: 'Autor', apply: '\\author{}' },
  { label: '\\date', type: 'keyword', info: 'Datum', apply: '\\date{}' },
  { label: '\\maketitle', type: 'keyword', info: 'Titelseite', apply: '\\maketitle' },
  { label: '\\tableofcontents', type: 'keyword', info: 'Inhaltsverzeichnis', apply: '\\tableofcontents' },
  { label: '\\newcommand', type: 'keyword', info: 'Neues Kommando', apply: '\\newcommand{}{}' },
  { label: '\\renewcommand', type: 'keyword', info: 'Kommando aendern', apply: '\\renewcommand{}{}' },
  { label: '\\input', type: 'keyword', info: 'Datei einfügen', apply: '\\input{}' },
  { label: '\\include', type: 'keyword', info: 'Datei einbinden', apply: '\\include{}' },
  { label: '\\frac', type: 'function', info: 'Bruch', apply: '\\frac{}{}' },
  { label: '\\sqrt', type: 'function', info: 'Wurzel', apply: '\\sqrt{}' },
  { label: '\\sum', type: 'keyword', info: 'Summe', apply: '\\sum' },
  { label: '\\int', type: 'keyword', info: 'Integral', apply: '\\int' }
]

/**
 * LaTeX environment names for autocompletion
 */
export const LATEX_ENVIRONMENT_NAMES = [
  'itemize',
  'enumerate',
  'description',
  'figure',
  'table',
  'tabular',
  'equation',
  'align',
  'quote',
  'verbatim',
  'center'
]

/**
 * AI @-commands for LaTeX AI workspace autocompletion
 */
export const AI_COMMAND_COMPLETIONS = [
  { label: '@ai', type: 'text', info: 'Freie KI-Anfrage', boost: 10, apply: '@ai ' },
  { label: '@rewrite', type: 'text', info: 'Text umformulieren', boost: 9, apply: '@rewrite ' },
  { label: '@expand', type: 'text', info: 'Text erweitern', boost: 8, apply: '@expand ' },
  { label: '@summarize', type: 'text', info: 'Text zusammenfassen', boost: 7, apply: '@summarize ' },
  { label: '@fix', type: 'text', info: 'LaTeX/Grammatik korrigieren', boost: 6, apply: '@fix ' },
  { label: '@translate', type: 'text', info: 'Übersetzen (z.B. @translate en)', boost: 5, apply: '@translate ' },
  { label: '@cite', type: 'text', info: 'Zitat aus RAG finden', boost: 4, apply: '@cite ' },
  { label: '@abstract', type: 'text', info: 'Abstract generieren', boost: 3, apply: '@abstract' },
  { label: '@titles', type: 'text', info: 'Titel vorschlagen', boost: 2, apply: '@titles' }
]

/**
 * Text formatting toolbar buttons
 */
export const TEXT_FORMAT_BUTTONS = [
  { id: 'bold', icon: 'mdi-format-bold', label: 'Fett', shortcut: 'Ctrl+B', snippet: '\\textbf{$SEL$}', wrap: true },
  { id: 'italic', icon: 'mdi-format-italic', label: 'Kursiv', shortcut: 'Ctrl+I', snippet: '\\textit{$SEL$}', wrap: true },
  { id: 'underline', icon: 'mdi-format-underline', label: 'Unterstrichen', shortcut: 'Ctrl+U', snippet: '\\underline{$SEL$}', wrap: true },
  { id: 'emph', icon: 'mdi-format-text', label: 'Hervorheben', snippet: '\\emph{$SEL$}', wrap: true },
  { id: 'typewriter', icon: 'mdi-code-tags', label: 'Typewriter', snippet: '\\texttt{$SEL$}', wrap: true }
]

/**
 * Structure toolbar buttons (sections, paragraphs)
 */
export const STRUCTURE_BUTTONS = [
  { id: 'section', icon: 'mdi-format-header-1', label: 'Section', snippet: '\\section{$CURSOR$}\n' },
  { id: 'subsection', icon: 'mdi-format-header-2', label: 'Subsection', snippet: '\\subsection{$CURSOR$}\n' },
  { id: 'subsubsection', icon: 'mdi-format-header-3', label: 'Subsubsection', snippet: '\\subsubsection{$CURSOR$}\n' },
  { id: 'paragraph', icon: 'mdi-format-pilcrow', label: 'Paragraph', snippet: '\\paragraph{$CURSOR$}\n' }
]

/**
 * List toolbar buttons
 */
export const LIST_BUTTONS = [
  { id: 'itemize', icon: 'mdi-format-list-bulleted', label: 'Aufzählung (Bullets)', snippet: '\\begin{itemize}\n  \\item $CURSOR$\n\\end{itemize}\n' },
  { id: 'enumerate', icon: 'mdi-format-list-numbered', label: 'Nummerierte Liste', snippet: '\\begin{enumerate}\n  \\item $CURSOR$\n\\end{enumerate}\n' },
  { id: 'description', icon: 'mdi-format-list-text', label: 'Description', snippet: '\\begin{description}\n  \\item[$CURSOR$] \n\\end{description}\n' }
]

/**
 * Content toolbar buttons (figures, tables, code blocks)
 */
export const CONTENT_BUTTONS = [
  { id: 'figure', icon: 'mdi-image', label: 'Abbildung', snippet: '\\begin{figure}[htbp]\n  \\centering\n  \\includegraphics[width=0.8\\textwidth]{$CURSOR$}\n  \\caption{Caption}\n  \\label{fig:label}\n\\end{figure}\n' },
  { id: 'table', icon: 'mdi-table', label: 'Tabelle', hasMenu: true }, // Special handling with size picker
  { id: 'code', icon: 'mdi-code-braces', label: 'Code Block', snippet: '\\begin{verbatim}\n$CURSOR$\n\\end{verbatim}\n' },
  { id: 'quote', icon: 'mdi-format-quote-close', label: 'Zitat', snippet: '\\begin{quote}\n  $CURSOR$\n\\end{quote}\n' }
]

/**
 * Math toolbar buttons
 */
export const MATH_BUTTONS = [
  { id: 'inline-math', icon: 'mdi-function-variant', label: 'Inline Math', snippet: '$$$SEL$$', wrap: true },
  { id: 'display-math', icon: 'mdi-function', label: 'Display Math', snippet: '\\[\n  $SEL$\n\\]\n', wrap: true },
  { id: 'equation', icon: 'mdi-sigma', label: 'Equation (numbered)', snippet: '\\begin{equation}\n  $CURSOR$\n  \\label{eq:label}\n\\end{equation}\n' },
  { id: 'align', icon: 'mdi-equal', label: 'Align (multi-line)', snippet: '\\begin{align}\n  $CURSOR$ &=  \\\\\n  &= \n\\end{align}\n' },
  { id: 'frac', icon: 'mdi-division', label: 'Bruch', snippet: '\\frac{$CURSOR$}{}', wrap: false }
]

/**
 * Reference toolbar buttons
 */
export const REF_BUTTONS = [
  { id: 'cite', icon: 'mdi-book-open-page-variant', label: 'Zitieren', snippet: '\\cite{$CURSOR$}' },
  { id: 'ref', icon: 'mdi-link-variant', label: 'Referenz', snippet: '\\ref{$CURSOR$}' },
  { id: 'label', icon: 'mdi-tag', label: 'Label', snippet: '\\label{$CURSOR$}' },
  { id: 'footnote', icon: 'mdi-message-text-outline', label: 'Fußnote', snippet: '\\footnote{$CURSOR$}' },
  { id: 'url', icon: 'mdi-web', label: 'URL', snippet: '\\url{$CURSOR$}' }
]

/**
 * Generate LaTeX table code based on rows and columns
 * @param {number} rows - Number of rows
 * @param {number} cols - Number of columns
 * @returns {string} LaTeX table snippet
 */
export function generateTableSnippet(rows, cols) {
  const colSpec = 'l' + 'c'.repeat(cols - 1)
  const headers = Array.from({ length: cols }, (_, i) => `Header ${i + 1}`).join(' & ')
  const emptyRow = Array.from({ length: cols }, () => ' ').join(' & ')

  let tableContent = `\\begin{table}[htbp]\n  \\centering\n  \\caption{Caption}\n  \\label{tab:label}\n  \\begin{tabular}{${colSpec}}\n    \\hline\n    ${headers} \\\\\n    \\hline\n`

  for (let r = 0; r < rows; r++) {
    if (r === 0) {
      tableContent += `    $CURSOR$${emptyRow.substring(1)} \\\\\n`
    } else {
      tableContent += `    ${emptyRow} \\\\\n`
    }
  }

  tableContent += `    \\hline\n  \\end{tabular}\n\\end{table}\n`
  return tableContent
}
