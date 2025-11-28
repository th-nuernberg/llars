/**
 * History Ratings Composable
 *
 * Manages ratings state, localStorage persistence, API calls, and change detection.
 */

import { ref, watch } from 'vue';
import axios from 'axios';
import { useHistoryHelpers } from './useHistoryHelpers';

export function useHistoryRatings(threadId) {
  const { checkIfDisabled, toggleClassForDiv } = useHistoryHelpers();

  // Main state
  const messages = ref([]);
  const ratings = ref({
    counsellor_coherence: null,
    client_coherence: null,
    quality: null,
    overall: null
  });
  const feedback = ref(null);
  const selectedCategoryId = ref(null);
  const categoryNotes = ref(null);
  const ratedStatus = ref(null);
  const hasUnsavedChanges = ref(false);

  // Initial values for comparison
  const initialRating = ref(null);
  const initialFeedback = ref(null);
  const initialMessages = ref([]);
  const initialSelectedCategoryId = ref(null);
  const initialCategoryNotes = ref(null);

  // Disabled state for Likert scales
  const isDisabled = ref({
    counsellor_coherence: false,
    client_coherence: false,
    quality: false,
    overall: false
  });

  /**
   * Initialize component by loading data from API.
   */
  async function initializeData() {
    try {
      // Fetch messages
      const threadMessages = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/generations/${threadId.value}`
      );

      // Fetch message ratings
      const messageRatings = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/message_ratings/${threadId.value}`
      );

      // Combine messages with ratings
      messages.value = threadMessages.data.messages.map(message => {
        const ratingObj = messageRatings.data.find(rating => rating.message_id === message.message_id);
        return {
          ...message,
          rating: ratingObj ? ratingObj.rating : null
        };
      });

      // Fetch mail history ratings
      const mailhistoryResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mailhistory_ratings/${threadId.value}`
      );

      if (mailhistoryResponse.data) {
        let tempRating = {
          counsellor_coherence: mailhistoryResponse.data.rating.counsellor_coherence_rating,
          client_coherence: mailhistoryResponse.data.rating.client_coherence_rating,
          quality: mailhistoryResponse.data.rating.quality_rating,
          overall: mailhistoryResponse.data.rating.overall_rating
        };

        // Convert 0 to null for frontend (0 = disabled scale)
        Object.keys(tempRating).forEach(key => {
          if (tempRating[key] === 0) {
            tempRating[key] = null;
          }
        });

        ratings.value = tempRating;
        selectedCategoryId.value = mailhistoryResponse.data.consulting_category.consulting_category_type_id;
        categoryNotes.value = mailhistoryResponse.data.consulting_category.consulting_category_note;
        feedback.value = mailhistoryResponse.data.rating.feedback;
        ratedStatus.value = mailhistoryResponse.data.rating.rating_status;
      } else {
        ratedStatus.value = 'Not Rated';
      }

      // Store initial values for change detection
      initialRating.value = JSON.parse(JSON.stringify(ratings.value));
      initialFeedback.value = JSON.parse(JSON.stringify(feedback.value));
      initialMessages.value = JSON.parse(JSON.stringify(messages.value));
      initialSelectedCategoryId.value = JSON.parse(JSON.stringify(selectedCategoryId.value));
      initialCategoryNotes.value = JSON.parse(JSON.stringify(categoryNotes.value));

      // Load from localStorage if changes exist
      loadMailHistoryRatingsFromLocalStorage();
      loadMessageRatingsFromLocalStorage();

      hasUnsavedChanges.value = checkForChanges();

    } catch (error) {
      console.error('Error fetching email thread details or rating status:', error);
    }
  }

  /**
   * Load mail history ratings from localStorage.
   */
  function loadMailHistoryRatingsFromLocalStorage() {
    const savedData = JSON.parse(localStorage.getItem(`local_rating_changes_${threadId.value}`));
    if (savedData) {
      ratings.value = savedData.ratings;
      feedback.value = savedData.feedback;
      selectedCategoryId.value = savedData.category_id;
      categoryNotes.value = savedData.category_notes;
      hasUnsavedChanges.value = checkForChanges();
    }
  }

  /**
   * Load message ratings from localStorage.
   */
  function loadMessageRatingsFromLocalStorage() {
    const savedMessageRatings = JSON.parse(localStorage.getItem(`local_messageRating_changes_${threadId.value}`));
    if (savedMessageRatings) {
      savedMessageRatings.forEach(savedRating => {
        const message = messages.value.find(msg => msg.message_id === savedRating.message_id);
        if (message) {
          message.rating = savedRating.rating;
        }
      });
    }
  }

  /**
   * Save mail history ratings to localStorage.
   */
  function saveMailhistoryRatingsToLocalStorage() {
    if (feedback.value === "") feedback.value = null;

    const dataToSave = {
      ratings: ratings.value,
      feedback: feedback.value,
      category_id: selectedCategoryId.value,
      category_notes: categoryNotes.value
    };

    localStorage.setItem(`local_rating_changes_${threadId.value}`, JSON.stringify(dataToSave));
  }

  /**
   * Save message ratings to localStorage.
   */
  function saveMessageRatingsToLocalStorage() {
    const messageRatingsToSave = messages.value.map(message => ({
      message_id: message.message_id,
      rating: message.rating
    }));

    localStorage.setItem(`local_messageRating_changes_${threadId.value}`, JSON.stringify(messageRatingsToSave));
  }

  /**
   * Check if there are unsaved changes.
   */
  function checkForChanges() {
    // Check mail history rating changes
    if (
      initialRating.value?.counsellor_coherence !== ratings.value.counsellor_coherence ||
      initialRating.value?.client_coherence !== ratings.value.client_coherence ||
      initialRating.value?.quality !== ratings.value.quality ||
      initialRating.value?.overall !== ratings.value.overall ||
      initialFeedback.value !== feedback.value ||
      initialSelectedCategoryId.value !== selectedCategoryId.value ||
      initialCategoryNotes.value !== categoryNotes.value
    ) {
      localStorage.setItem(`hasUnsaved_ratingChanges_${threadId.value}`, JSON.stringify(true));
      return true;
    }

    // Check message rating changes
    for (let i = 0; i < initialMessages.value.length; i++) {
      if (initialMessages.value[i]?.rating !== messages.value[i]?.rating) {
        localStorage.setItem(`hasUnsaved_ratingChanges_${threadId.value}`, JSON.stringify(true));
        return true;
      }
    }

    localStorage.removeItem(`hasUnsaved_ratingChanges_${threadId.value}`);
    return false;
  }

  /**
   * Update Likert scale activation status based on ratings.
   */
  function updateLikertActivationStatus() {
    const shouldDisableCounsellorCoherence = ratings.value.client_coherence > 2;
    toggleClassForDiv('rating-category-coherence-counsellor', shouldDisableCounsellorCoherence);

    const shouldDisableClientCoherence = ratings.value.counsellor_coherence > 2;
    toggleClassForDiv('rating-category-coherence-client', shouldDisableClientCoherence);

    const shouldDisableQuality = ratings.value.counsellor_coherence > 2 || ratings.value.client_coherence > 2;
    toggleClassForDiv('rating-category-quality', shouldDisableQuality || shouldDisableClientCoherence || shouldDisableCounsellorCoherence);

    const shouldDisableOverall = ratings.value.quality > 2;
    toggleClassForDiv('rating-category-overall', shouldDisableQuality || shouldDisableOverall || shouldDisableClientCoherence || shouldDisableCounsellorCoherence);

    isDisabled.value.counsellor_coherence = checkIfDisabled('rating-category-coherence-counsellor');
    isDisabled.value.client_coherence = checkIfDisabled('rating-category-coherence-client');
    isDisabled.value.quality = checkIfDisabled('rating-category-quality');
    isDisabled.value.overall = checkIfDisabled('rating-category-overall');
  }

  /**
   * Rate an individual message.
   */
  function rateMessage(index, rating) {
    messages.value[index].rating = messages.value[index].rating === rating ? null : rating;
    saveMessageRatingsToLocalStorage();
    hasUnsavedChanges.value = checkForChanges();
  }

  /**
   * Handle category selection from CategorySelection component.
   */
  function handleCategorySelection(selectedCategory) {
    selectedCategoryId.value = selectedCategory.categoryId;
    categoryNotes.value = selectedCategory.categoryNotes;
  }

  /**
   * Save ratings to server.
   */
  async function saveRatingServerSide() {
    const ratingAndCategory = {
      counsellor_coherence_rating: ratings.value.counsellor_coherence,
      client_coherence_rating: ratings.value.client_coherence,
      quality_rating: ratings.value.quality,
      overall_rating: ratings.value.overall,
      feedback: feedback.value,
      consulting_category_id: selectedCategoryId.value,
      consulting_category_notes: categoryNotes.value,
      consider_category_for_status: true
    };

    // Handle disabled scales (set to 0 in DB)
    if (checkIfDisabled("rating-category-coherence-client")) {
      if (ratingAndCategory.client_coherence_rating === null) {
        ratingAndCategory.client_coherence_rating = 0;
      }
      ratingAndCategory.consider_category_for_status = false;
    }

    if (checkIfDisabled("rating-category-coherence-counsellor")) {
      if (ratingAndCategory.counsellor_coherence_rating === null) {
        ratingAndCategory.counsellor_coherence_rating = 0;
      }
      ratingAndCategory.consider_category_for_status = false;
    }

    if (checkIfDisabled("rating-category-quality")) {
      if (ratingAndCategory.quality_rating === null) {
        ratingAndCategory.quality_rating = 0;
      }
      ratingAndCategory.consider_category_for_status = false;
    }

    if (checkIfDisabled("rating-category-overall")) {
      if (ratingAndCategory.overall_rating === null) {
        ratingAndCategory.overall_rating = 0;
      }
      ratingAndCategory.consider_category_for_status = false;
    }

    try {
      // Save mail history ratings
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/save_mailhistory_rating/${threadId.value}`,
        ratingAndCategory,
        { headers: { 'Content-Type': 'application/json' } }
      );

      // Save message ratings
      const messageRatings = messages.value.map(message => ({
        message_id: message.message_id,
        rating: message.rating
      }));

      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/email_threads/save_message_ratings/${threadId.value}`,
        { message_ratings: messageRatings },
        { headers: { 'Content-Type': 'application/json' } }
      );

      alert('Rating und Feedback wurden erfolgreich gespeichert!');

      // Clear localStorage
      localStorage.removeItem(`local_rating_changes_${threadId.value}`);
      localStorage.removeItem(`local_messageRating_changes_${threadId.value}`);

      // Reload data
      await initializeData();

    } catch (error) {
      console.error('Error saving rating:', error);
      alert('Fehler beim Speichern des Ratings und Feedbacks.');
    }
  }

  /**
   * Setup watchers for auto-saving to localStorage.
   */
  function setupWatchers() {
    watch(
      [ratings, selectedCategoryId, categoryNotes],
      () => {
        saveMailhistoryRatingsToLocalStorage();
        hasUnsavedChanges.value = checkForChanges();
        updateLikertActivationStatus();
      },
      { deep: true }
    );

    watch(
      [feedback],
      () => {
        saveMailhistoryRatingsToLocalStorage();
        hasUnsavedChanges.value = checkForChanges();
      },
      { deep: true }
    );
  }

  return {
    // State
    messages,
    ratings,
    feedback,
    selectedCategoryId,
    categoryNotes,
    ratedStatus,
    hasUnsavedChanges,
    isDisabled,

    // Methods
    initializeData,
    rateMessage,
    handleCategorySelection,
    saveRatingServerSide,
    setupWatchers,
    updateLikertActivationStatus
  };
}
