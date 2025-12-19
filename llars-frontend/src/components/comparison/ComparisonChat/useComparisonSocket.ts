/**
 * Comparison Socket Composable
 *
 * Manages Socket.IO connection and all comparison-related events.
 */

import { ref, watch, onMounted, Ref } from 'vue';
import { io, Socket } from 'socket.io-client';
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage';

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true';
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling'];

export interface Message {
  messageId: number;
  idx: number;
  type: 'user' | 'bot_pair';
  content?: string | { llm1: string; llm2: string };
  selected?: string | null;
  streaming?: { llm1: boolean; llm2: boolean };
  timestamp: string;
}

export interface JustificationData {
  messageId: number;
  user_selection: string;
  ai_selection: string;
  ai_reason: string;
}

export interface UseComparisonSocketOptions {
  sessionId: Ref<number>;
  onMessageUpdate?: () => void;
  onSuggestionStateChange?: (generating: boolean) => void;
}

export function useComparisonSocket(options: UseComparisonSocketOptions) {
  const { sessionId, onMessageUpdate, onSuggestionStateChange } = options;

  const socket = ref<Socket | null>(null);
  const messages = ref<Message[]>([]);
  const isProcessing = ref(false);
  const generatingSuggestion = ref(false);
  const showJustificationDialog = ref(false);
  const currentJustification = ref<JustificationData | null>(null);

  /**
   * Find message by ID.
   */
  const findMessageById = (messageId: number): Message | undefined => {
    return messages.value.find(m => m.messageId === messageId);
  };

  /**
   * Add or update a message in the list.
   */
  const addOrUpdateMessage = (messageData: any, scrollCallback?: () => void) => {
    const existingIndex = messages.value.findIndex(m => m.messageId === messageData.messageId);

    const message: Message = {
      messageId: messageData.messageId,
      idx: messageData.idx,
      type: messageData.type,
      content: messageData.content,
      selected: messageData.selected || null,
      timestamp: messageData.timestamp,
      streaming: messageData.type === 'bot_pair' ? { llm1: false, llm2: false } : undefined
    };

    if (existingIndex >= 0) {
      messages.value[existingIndex] = message;
    } else {
      messages.value.push(message);
      messages.value.sort((a, b) => a.idx - b.idx);
    }

    scrollCallback?.();
  };

  /**
   * Initialize socket connection and event handlers.
   */
  const initializeSocket = (scrollCallback?: () => void) => {
    const username = localStorage.getItem('username') || 'Gast';
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token);

    const query: Record<string, string> = { username: username };
    if (token) {
      query.token = token;
    }

    socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`, {
      path: '/socket.io/',
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket,
      query,
      headers: {
        'Content-Type': 'application/json; charset=utf-8'
      }
    });

    socket.value.on('connect', () => {
      if (sessionId.value) {
        console.log('Socket connected for comparison');
        socket.value?.emit('join_comparison_session', {
          sessionId: sessionId.value
        });
      }
    });

    socket.value.on('messages_loaded', (data: any) => {
      console.log('Messages loaded:', data);
      messages.value = data.messages.map((msg: any) => ({
        messageId: msg.messageId,
        idx: msg.idx,
        type: msg.type,
        content: msg.content,
        selected: msg.selected || null,
        timestamp: msg.timestamp,
        streaming: msg.type === 'bot_pair' ? { llm1: false, llm2: false } : undefined
      }));
      scrollCallback?.();
    });

    socket.value.on('message_created', (messageData: any) => {
      console.log('Message created:', messageData);
      addOrUpdateMessage(messageData, scrollCallback);
    });

    socket.value.on('message_updated', (data: any) => {
      console.log('Message updated:', data);

      if (data.message) {
        addOrUpdateMessage(data.message, scrollCallback);
      }

      // Check if justification dialog should be shown
      if (data.requires_justification && data.ai_evaluation) {
        currentJustification.value = {
          messageId: data.message.messageId,
          user_selection: data.ai_evaluation.user_selection,
          ai_selection: data.ai_evaluation.ai_selection,
          ai_reason: data.ai_evaluation.ai_reason
        };
        showJustificationDialog.value = true;
      }

      onMessageUpdate?.();
    });

    socket.value.on('streaming_started', (data: any) => {
      console.log('Streaming started:', data);
      const message = findMessageById(data.messageId);
      if (message && message.streaming) {
        data.llmTypes.forEach((llmType: string) => {
          if (message.streaming) {
            message.streaming[llmType as keyof typeof message.streaming] = true;
          }
        });
      }
    });

    socket.value.on('streaming_update', (data: any) => {
      const { messageId, llmType, fullContent } = data;
      const message = findMessageById(messageId);

      if (message && message.type === 'bot_pair' && typeof message.content === 'object') {
        message.content[llmType as keyof typeof message.content] = fullContent;
        scrollCallback?.();
      }
    });

    socket.value.on('streaming_complete', (data: any) => {
      console.log('Streaming complete:', data);
      const { messageId, llmType, finalContent } = data;
      const message = findMessageById(messageId);

      if (message) {
        if (message.streaming) {
          message.streaming[llmType as keyof typeof message.streaming] = false;
        }

        if (message.type === 'bot_pair' && typeof message.content === 'object') {
          message.content[llmType as keyof typeof message.content] = finalContent;
        }

        if (!message.streaming?.llm1 && !message.streaming?.llm2) {
          isProcessing.value = false;
        }
      }
    });

    socket.value.on('streaming_error', (data: any) => {
      console.error('Streaming error:', data);
      const { messageId, llmType, error } = data;
      const message = findMessageById(messageId);

      if (message) {
        if (message.streaming) {
          message.streaming[llmType as keyof typeof message.streaming] = false;
        }

        if (message.type === 'bot_pair' && typeof message.content === 'object') {
          message.content[llmType as keyof typeof message.content] = error;
        }

        if (!message.streaming?.llm1 && !message.streaming?.llm2) {
          isProcessing.value = false;
        }
      }
    });

    socket.value.on('suggestion_generated', (data: any) => {
      console.log('Suggestion generated:', data);
      generatingSuggestion.value = false;
      onSuggestionStateChange?.(false);
      return data.suggestion;
    });

    socket.value.on('suggestion_error', (data: any) => {
      console.error('Suggestion error:', data);
      generatingSuggestion.value = false;
      onSuggestionStateChange?.(false);
    });

    socket.value.on('justification_saved', (data: any) => {
      console.log('Justification saved:', data);
    });

    socket.value.on('error', (data: any) => {
      console.error('Socket error:', data);
      isProcessing.value = false;
    });

    socket.value.on('disconnect', () => {
      console.log('Socket disconnected');
      isProcessing.value = false;
    });
  };

  /**
   * Send a message through the socket.
   */
  const sendMessage = (messageContent: string) => {
    if (!messageContent.trim() || isProcessing.value) return false;

    isProcessing.value = true;
    socket.value?.emit('comparison_message', {
      sessionId: sessionId.value,
      message: messageContent
    });
    return true;
  };

  /**
   * Select a response (rate it).
   */
  const selectResponse = (messageId: number, selection: string) => {
    const message = findMessageById(messageId);
    if (message && socket.value) {
      socket.value.emit('rate_response', {
        sessionId: sessionId.value,
        messageId: messageId,
        selection: selection
      });
    }
  };

  /**
   * Generate a suggestion.
   */
  const generateSuggestion = () => {
    if (!socket.value || generatingSuggestion.value) return;

    generatingSuggestion.value = true;
    onSuggestionStateChange?.(true);

    socket.value.emit('generate_suggestion', {
      sessionId: sessionId.value
    });
  };

  /**
   * Submit justification for rating deviation.
   */
  const submitJustification = (justification: string) => {
    if (justification.trim() && currentJustification.value) {
      socket.value?.emit('submit_justification', {
        messageId: currentJustification.value.messageId,
        justification: justification.trim()
      });
    }
  };

  /**
   * Close justification dialog.
   */
  const closeJustificationDialog = () => {
    showJustificationDialog.value = false;
    currentJustification.value = null;
  };

  /**
   * Setup session watcher.
   */
  const setupSessionWatcher = () => {
    watch(sessionId, (newId) => {
      if (newId && socket.value) {
        messages.value = [];
        socket.value.emit('join_comparison_session', {
          sessionId: newId
        });
      }
    });
  };

  return {
    // State
    socket,
    messages,
    isProcessing,
    generatingSuggestion,
    showJustificationDialog,
    currentJustification,

    // Methods
    initializeSocket,
    findMessageById,
    sendMessage,
    selectResponse,
    generateSuggestion,
    submitJustification,
    closeJustificationDialog,
    setupSessionWatcher
  };
}
