import { ref } from 'vue'
import axios from 'axios'

export function usePromptDetails(promptId) {
  const promptName = ref('')
  const promptOwner = ref('')
  const promptOwnerAvatar = ref(null)
  const sharedWithUsers = ref([])

  const fetchPromptDetails = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId.value}`
      )

      // Backend returns { success: true, data: { name, owner, owner_avatar, shared_with, ... } }
      const promptData = response.data?.data || response.data

      if (promptData) {
        promptName.value = promptData.name || ''
        promptOwner.value = promptData.owner || ''
        promptOwnerAvatar.value = promptData.owner_avatar || null
        sharedWithUsers.value = promptData.shared_with || []
      }
    } catch (error) {
      console.error('Fehler beim Laden der Prompt-Details:', error)
    }
  }

  return {
    promptName,
    promptOwner,
    promptOwnerAvatar,
    sharedWithUsers,
    fetchPromptDetails
  }
}
