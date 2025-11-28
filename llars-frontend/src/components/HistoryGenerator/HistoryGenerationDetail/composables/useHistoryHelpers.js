/**
 * History Generation Helpers Composable
 *
 * Formatting, class helpers, and content sanitization.
 */

import DOMPurify from 'dompurify';

export function useHistoryHelpers() {
  /**
   * Sanitize and format message content for display.
   * Converts newlines to <br> and only allows safe HTML tags.
   */
  function formatContent(content) {
    if (!content) return '';

    // Convert newlines to <br>
    const sanitizedContent = content.replace(/\n/g, '<br>');

    // Sanitize and only allow safe tags
    const cleanContent = DOMPurify.sanitize(sanitizedContent, {
      ALLOWED_TAGS: ['br', 'a'],
      ALLOWED_ATTR: ['href'],
    });

    // Remove any dangerous tags that might have been missed
    return cleanContent.replace(/<(iframe|script|embed|object)[^>]*>.*?<\/\1>/gi, (match) => {
      return DOMPurify.sanitize(match, { ALLOWED_TAGS: [] });
    });
  }

  /**
   * Format timestamp for German locale display.
   */
  function formatTimestamp(timestamp) {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
    const date = new Date(timestamp);
    return date.toLocaleDateString('de-DE', options).replace(',', ' um') + ' Uhr';
  }

  /**
   * Get CSS class based on sender type.
   * Distinguishes between client (Ratsuchende) and counselor (Beratende).
   */
  function getMessageClass(sender) {
    const normalizedSender = sender.toLowerCase().trim();

    const clientVariants = ['ratsuchende person', 'ratsuchender', 'ratsuchend', 'ratsuchende'];
    const counselorVariants = ['beratende person', 'berater', 'beratend', 'beratende'];

    if (clientVariants.includes(normalizedSender)) {
      return 'same-sender';
    } else if (counselorVariants.includes(normalizedSender)) {
      return 'different-sender';
    }

    console.warn(`Unrecognized sender type: ${sender}`);
    return 'different-sender';
  }

  /**
   * Check if a DOM element has the 'disabled' class.
   */
  function checkIfDisabled(elementID) {
    const element = document.getElementById(elementID);
    return element?.classList.contains('disabled') || false;
  }

  /**
   * Toggle 'disabled' class on a DOM element.
   */
  function toggleClassForDiv(elementId, shouldDisable) {
    const div = document.getElementById(elementId);
    if (!div) return;

    if (shouldDisable) {
      div.classList.add('disabled');
    } else {
      div.classList.remove('disabled');
    }
  }

  return {
    formatContent,
    formatTimestamp,
    getMessageClass,
    checkIfDisabled,
    toggleClassForDiv
  };
}
