/**
 * Comparison Helpers Composable
 *
 * Utility functions for formatting and message handling.
 */

import { ref, computed, nextTick, Ref } from 'vue';
import type { Message } from './useComparisonSocket';

export function useComparisonHelpers(messages: Ref<Message[]>) {
  const messagesContainer = ref<HTMLElement | null>(null);
  const newMessage = ref('');
  const userJustification = ref('');

  /**
   * Check if user can send a message (last response must be rated).
   */
  const canSendMessage = computed(() => {
    const lastMessage = messages.value[messages.value.length - 1];
    return !lastMessage ||
      lastMessage.type === 'user' ||
      (lastMessage.type === 'bot_pair' && lastMessage.selected);
  });

  /**
   * Format timestamp for display.
   */
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * Check if a message is currently streaming.
   */
  const isStreaming = (message: Message): boolean => {
    return message.streaming?.llm1 || message.streaming?.llm2 || false;
  };

  /**
   * Format selection for display.
   */
  const formatSelection = (selection: string): string => {
    switch (selection) {
      case 'llm1': return 'Modell 1 ist besser';
      case 'llm2': return 'Modell 2 ist besser';
      case 'tie': return 'Beide gleich gut';
      default: return selection;
    }
  };

  /**
   * Get response content for a specific LLM.
   */
  const getResponseContent = (message: Message, llmType: 'llm1' | 'llm2'): string => {
    if (typeof message.content === 'object' && message.content) {
      return message.content[llmType] || '';
    }
    return '';
  };

  /**
   * Scroll messages container to bottom.
   */
  const scrollToBottom = () => {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTo({
          top: messagesContainer.value.scrollHeight,
          behavior: 'smooth'
        });
      }
    });
  };

  /**
   * Set messages container ref.
   */
  const setMessagesContainer = (element: HTMLElement | null) => {
    messagesContainer.value = element;
  };

  /**
   * Clear new message input.
   */
  const clearNewMessage = () => {
    newMessage.value = '';
  };

  /**
   * Set suggestion as new message.
   */
  const setSuggestion = (suggestion: string) => {
    newMessage.value = suggestion;
  };

  /**
   * Clear justification input.
   */
  const clearJustification = () => {
    userJustification.value = '';
  };

  return {
    // Refs
    messagesContainer,
    newMessage,
    userJustification,

    // Computed
    canSendMessage,

    // Methods
    formatTimestamp,
    isStreaming,
    formatSelection,
    getResponseContent,
    scrollToBottom,
    setMessagesContainer,
    clearNewMessage,
    setSuggestion,
    clearJustification
  };
}
