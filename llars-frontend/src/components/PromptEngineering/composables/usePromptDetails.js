import { ref } from 'vue'

export function usePromptDetails(promptId) {
  const promptName = ref('')
  const promptOwner = ref('')
  const sharedWithUsers = ref([])

  const fetchPromptDetails = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId.value}`
      )
      const data = await response.json()

      if (response.ok) {
        promptName.value = data.name
        promptOwner.value = data.owner
        sharedWithUsers.value = data.shared_with || []
      } else {
        console.error('Fehler beim Abrufen der Prompt-Details:', data.error)
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
