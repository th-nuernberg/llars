/**
 * History Generation Navigation Composable
 *
 * Handles navigation between cases (previous, next, overview).
 */

import { useRouter } from 'vue-router';
import axios from 'axios';

export function useHistoryNavigation() {
  const router = useRouter();

  /**
   * Fetch list of all cases from API.
   */
  async function fetchCaseList() {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/mailhistory_ratings`);
      return response.data.threads;
    } catch (error) {
      console.error('Error fetching case list:', error);
      return [];
    }
  }

  /**
   * Navigate to the previous case in the list.
   */
  async function navigateToPreviousCase(currentId) {
    const caseList = await fetchCaseList();

    if (!caseList || caseList.length === 0) {
      console.log("Keine Fälle verfügbar");
      return false;
    }

    const currentIndex = caseList.findIndex(c => c.thread_id === currentId);

    if (currentIndex === -1 || currentIndex === 0) {
      console.log("Erster Fall erreicht oder Fall nicht gefunden");
      return false;
    }

    const previousCase = caseList[currentIndex - 1];
    router.push({ name: 'HistoryGenerationDetail', params: { id: previousCase.thread_id } });
    return true;
  }

  /**
   * Navigate to the next case in the list.
   */
  async function navigateToNextCase(currentId) {
    const caseList = await fetchCaseList();

    if (!caseList || caseList.length === 0) {
      console.log("Keine Fälle verfügbar");
      return false;
    }

    const currentIndex = caseList.findIndex(c => c.thread_id === currentId);

    if (currentIndex === -1 || currentIndex === caseList.length - 1) {
      console.log("Letzter Fall erreicht oder Fall nicht gefunden");
      return false;
    }

    const nextCase = caseList[currentIndex + 1];
    router.push({ name: 'HistoryGenerationDetail', params: { id: nextCase.thread_id } });
    return true;
  }

  /**
   * Navigate back to the overview page.
   */
  function navigateToOverview() {
    router.push({ name: 'HistoryGenerator' });
  }

  return {
    fetchCaseList,
    navigateToPreviousCase,
    navigateToNextCase,
    navigateToOverview
  };
}
