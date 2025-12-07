import { ref } from 'vue'

export function useSnackbar() {
  const showSnackbar = ref(false)
  const snackbarMessage = ref('')

  const showMessage = (message) => {
    snackbarMessage.value = message
    showSnackbar.value = true

    setTimeout(() => {
      showSnackbar.value = false
    }, 3000)
  }

  return {
    showSnackbar,
    snackbarMessage,
    showMessage
  }
}
