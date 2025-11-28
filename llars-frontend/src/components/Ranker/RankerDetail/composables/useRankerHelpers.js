/**
 * Ranker Helpers Composable
 *
 * Utility functions for formatting, translations, and UI helpers.
 * Extracted from RankerDetail.vue for better maintainability.
 */

import { ref } from 'vue';
import { sanitizeHtml } from '@/utils/sanitize';

export function useRankerHelpers() {
  const emailPaneExpanded = ref(true);
  const senderColors = ref({});

  const dragOptions = ref({
    animation: 200,
    group: 'description',
    disabled: false,
    ghostClass: 'ghost',
  });

  // Toggle email pane visibility
  function toggleEmailPane() {
    emailPaneExpanded.value = !emailPaneExpanded.value;
  }

  // Toggle minimize state of an element
  function toggleMinimize(element) {
    element.minimized = !element.minimized;
  }

  // Check if content is long enough to need a toggle
  function isLongContent(content) {
    const maxCharsPerLine = 80;
    return content.length > (maxCharsPerLine * 3);
  }

  // Get tooltip text for feature type
  function getTooltipText(type) {
    const tooltips = {
      abstract_summary: 'Diese Zusammenfassung gibt einen Überblick über den Fall.',
      generated_category: 'Dies ist die generierte Kategorie des Falls.',
      generated_subject: 'Das Feature "Generierter Betreff" beschreibt einen prägnanten und individuellen Betreff, der aus der ersten Nachricht der ratsuchenden Person generiert wurde.\n\nDer Betreff soll den Hauptinhalt der Anfrage klar und verständlich in maximal 6 Wörtern zusammenfassen, ohne unnötige Formalitäten oder zusätzliche Phrasen.\n\nDie Qualität des "Generierter Betreff" wird danach bewertet, wie gut es den Kerninhalt der Erstnachricht präzise und direkt wiedergibt. Ein guter Betreff ermöglicht es dem Beratungsteam, schnell einen Überblick über das Anliegen zu erhalten und effektiv darauf zu reagieren.',
      order_clarification: 'Hier werden Unklarheiten in der Anfrage geklärt.',
      situation_summary: 'Das Feature "Situationsbeschreibung" fasst die aktuelle Situation der ratsuchenden Person in den Bereichen sozial, beruflich und persönlich zusammen.\n\nDiese Zusammenfassungen basieren auf der bisherigen Kommunikation. Zusätzlich können relevante Aspekte in weiteren Feldern wie "zusätzlicher_aspekt" beschrieben werden.\n\nJeder Bereich wird durch Stichpunkte dargestellt, die aus maximal zwei Sätzen bestehen und die wichtigsten Informationen prägnant zusammenfassen.\n\nDie Qualität der "Situationsbeschreibung" wird danach bewertet, wie genau und umfassend sie die soziale, berufliche und persönliche Lage der ratsuchenden Person wiedergibt, ohne unnötige Formalitäten oder Ausschweifungen.',
    };

    return tooltips[type] || 'Allgemeine Informationen zum Feature.';
  }

  // Translate feature type to German
  function translateFeatureType(type) {
    const translations = {
      abstract_summary: 'Abstrakte Fallzusammenfassung',
      generated_category: 'Generierte Kategorie',
      generated_subject: 'Generierter Betreff',
      order_clarification: 'Ordnungsklärung',
      situation_summary: 'Situationsbeschreibung'
    };
    return translations[type] || type;
  }

  // Format timestamp for display
  function formatTimestamp(timestamp) {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
    const date = new Date(timestamp);
    return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
  }

  // Format feature content based on type
  function formatFeatureContent(type, content) {
    switch (type) {
      case 'generated_subject':
        try {
          const subjectObj = JSON.parse(content);
          return sanitizeHtml(subjectObj.Betreff || content);
        } catch (error) {
          console.error('Error parsing generated_subject JSON:', error);
          return sanitizeHtml(content);
        }

      case 'situation_summary':
        try {
          const summaryObj = JSON.parse(content);
          let formattedContent = '<div class="situation-summary">';
          for (const [key, values] of Object.entries(summaryObj)) {
            const capitalizedKey = sanitizeHtml(key.charAt(0).toUpperCase() + key.slice(1));
            formattedContent += `<p><strong>${capitalizedKey}:</strong></p>`;
            formattedContent += '<ul>';
            values.forEach(item => {
              formattedContent += `<li>${sanitizeHtml(item)}</li>`;
            });
            formattedContent += '</ul>';
          }
          formattedContent += '</div>';

          formattedContent += `
            <style>
              .situation-summary ul {
                padding-left: 20px;
                margin-top: 5px;
                margin-bottom: 15px;
              }
              .situation-summary p {
                margin-bottom: 5px;
              }
            </style>
          `;

          return sanitizeHtml(formattedContent);
        } catch (error) {
          console.error('Error parsing situation_summary JSON:', error);
          return sanitizeHtml(content);
        }

      default:
        return sanitizeHtml(content);
    }
  }

  // Get message class based on sender
  function getMessageClass(sender) {
    return senderColors.value[sender];
  }

  // Update sender colors for messages
  function updateSenderColors(messages) {
    let lastSender = '';
    let currentColor = 'same-sender';
    messages.forEach(message => {
      if (message.sender !== lastSender) {
        currentColor = currentColor === 'same-sender' ? 'different-sender' : 'same-sender';
        lastSender = message.sender;
      }
      senderColors.value[message.sender] = currentColor;
    });
  }

  // Generate color for text (hash-based)
  function getColorForText(text) {
    const hash = hashCode(text);

    const baseHue = 65;
    const baseSaturation = 68;
    const baseLightness = 86;

    const hueVariation = (hash & 0xFF) % 21 - 10;
    const saturationVariation = ((hash >> 8) & 0xFF) % 31 - 15;
    const lightnessVariation = ((hash >> 16) & 0xFF) % 21 - 10;

    const hue = (baseHue + hueVariation + 360) % 360;
    const saturation = Math.max(40, Math.min(100, baseSaturation + saturationVariation));
    const lightness = Math.max(70, Math.min(95, baseLightness + lightnessVariation));

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  }

  function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash;
  }

  // Drag handlers
  function handleDragStart() {
    document.body.classList.add("dragging");
  }

  function handleDragEnd() {
    document.body.classList.remove("dragging");
  }

  return {
    // State
    emailPaneExpanded,
    senderColors,
    dragOptions,

    // Methods
    toggleEmailPane,
    toggleMinimize,
    isLongContent,
    getTooltipText,
    translateFeatureType,
    formatTimestamp,
    formatFeatureContent,
    getMessageClass,
    updateSenderColors,
    getColorForText,
    handleDragStart,
    handleDragEnd
  };
}
