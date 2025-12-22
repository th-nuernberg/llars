import { ref } from 'vue'
import axios from 'axios'

export function usePromptDetails(promptId) {
  const promptName = ref('')
  const promptOwner = ref('')
  const sharedWithUsers = ref([])

  const fetchPromptDetails = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId.value}`
      )

      // Backend returns { success: true, data: { name, owner, shared_with, ... } }
      const promptData = response.data?.data || response.data

      if (promptData) {
        promptName.value = promptData.name || ''
        promptOwner.value = promptData.owner || ''
        sharedWithUsers.value = promptData.shared_with || []
        console.log('[PromptDetails] Loaded:', {
          name: promptName.value,
          owner: promptOwner.value,
          sharedWith: sharedWithUsers.value
        })
      }
    } catch (error) {
      console.error('Fehler beim Laden der Prompt-Details:', error)
    }
  }

  return {
    promptName,
    promptOwner,
    sharedWithUsers,
    fetchPromptDetails
  }
}
