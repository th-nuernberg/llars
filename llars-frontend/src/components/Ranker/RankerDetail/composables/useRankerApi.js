/**
 * Ranker API Composable
 *
 * Handles API calls for email threads, rankings, and navigation.
 * Extracted from RankerDetail.vue for better maintainability.
 */

import axios from 'axios';

export function useRankerApi() {
  // Fetch email threads for a specific thread ID
  async function fetchEmailThreads(threadId) {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings/${threadId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching email threads:', error);
      return null;
    }
  }

  // Fetch current ranking from server
  async function fetchServerRanking(threadId) {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/${threadId}/current_ranking`);
      console.log('Server ranking:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching server ranking:', error);
      return null;
    }
  }

  // Fetch list of ranking threads for navigation
  async function fetchRankingThreads() {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/feature_ranking_list`);
      return response.data;
    } catch (error) {
      console.error('Error fetching ranking threads:', error);
      return [];
    }
  }

  // Fetch total number of cases
  async function fetchTotalCases() {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings`);
      return response.data.length;
    } catch (error) {
      console.error('Error fetching total number of cases:', error);
      return 0;
    }
  }

  // Save ranking to server
  async function saveRankingToServer(threadId, orderedFeatures) {
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/save_ranking/${threadId}`,
        orderedFeatures,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      console.log('Ranking saved successfully:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error saving ranking:', error);
      return { success: false, error };
    }
  }

  return {
    fetchEmailThreads,
    fetchServerRanking,
    fetchRankingThreads,
    fetchTotalCases,
    saveRankingToServer
  };
}
