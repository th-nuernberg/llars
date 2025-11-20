/**
 * HTML Sanitization Utility using DOMPurify
 *
 * This utility provides safe HTML sanitization to prevent XSS attacks.
 * All v-html directives should use these functions.
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content with default safe configuration
 * Allows basic formatting tags but removes all script/event handlers
 *
 * @param {string} html - Raw HTML content to sanitize
 * @returns {string} Sanitized HTML safe for v-html
 */
export function sanitizeHtml(html) {
  if (!html) return '';

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'div', 'span', 'a'],
    ALLOWED_ATTR: ['href', 'class', 'style'],
    ALLOW_DATA_ATTR: false,
  });
}

/**
 * Sanitize HTML content with custom configuration
 *
 * @param {string} html - Raw HTML content to sanitize
 * @param {object} config - DOMPurify configuration options
 * @returns {string} Sanitized HTML safe for v-html
 */
export function sanitizeHtmlCustom(html, config = {}) {
  if (!html) return '';

  return DOMPurify.sanitize(html, config);
}

/**
 * Convert newlines to <br> tags and sanitize
 *
 * @param {string} text - Plain text with newlines
 * @returns {string} Sanitized HTML with line breaks
 */
export function sanitizeText(text) {
  if (!text) return '';

  const htmlWithBreaks = text.replace(/\n/g, '<br>');
  return DOMPurify.sanitize(htmlWithBreaks, {
    ALLOWED_TAGS: ['br'],
  });
}

/**
 * Strip all HTML tags and return plain text
 *
 * @param {string} html - HTML content to strip
 * @returns {string} Plain text without any HTML
 */
export function stripHtml(html) {
  if (!html) return '';

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [],
  });
}
