import { ref } from 'vue'

export function useDialogs() {
  // Add Block Dialog
  const showAddBlockDialog = ref(false)
  const newBlockName = ref('')

  const closeAddBlockDialog = () => {
    showAddBlockDialog.value = false
    newBlockName.value = ''
  }

  // Delete Block Dialog
  const showDeleteBlockDialog = ref(false)
  const blockToDelete = ref(null)

  const openDeleteBlockDialog = (block) => {
    blockToDelete.value = block
    showDeleteBlockDialog.value = true
  }

  const closeDeleteBlockDialog = () => {
    showDeleteBlockDialog.value = false
    blockToDelete.value = null
  }

  // JSON Upload Choice Dialog
  const showUploadChoiceDialog = ref(false)
  const pendingJsonData = ref(null)

  const openUploadChoiceDialog = (jsonData) => {
    pendingJsonData.value = jsonData
    showUploadChoiceDialog.value = true
  }

  const closeUploadChoiceDialog = () => {
    showUploadChoiceDialog.value = false
    pendingJsonData.value = null
  }

  // Block Title Editing
  const editingBlockId = ref(null)
  const editingBlockTitle = ref('')

  const startEditBlockTitle = (block) => {
    editingBlockId.value = block.id
    editingBlockTitle.value = block.title
  }

  const resetBlockTitleEdit = () => {
    editingBlockId.value = null
    editingBlockTitle.value = ''
  }

  // Test Prompt Dialog
  const showTestPromptDialog = ref(false)

  const openTestPromptDialog = () => {
    showTestPromptDialog.value = true
  }

  // Variable Manager Dialog
  const showVariableManager = ref(false)

  const openVariableManager = () => {
    showVariableManager.value = true
  }

  return {
    // Add Block
    showAddBlockDialog,
    newBlockName,
    closeAddBlockDialog,

    // Delete Block
    showDeleteBlockDialog,
    blockToDelete,
    openDeleteBlockDialog,
    closeDeleteBlockDialog,

    // Upload Choice
    showUploadChoiceDialog,
    pendingJsonData,
    openUploadChoiceDialog,
    closeUploadChoiceDialog,

    // Block Title Edit
    editingBlockId,
    editingBlockTitle,
    startEditBlockTitle,
    resetBlockTitleEdit,

    // Test Prompt
    showTestPromptDialog,
    openTestPromptDialog,

    // Variable Manager
    showVariableManager,
    openVariableManager
  }
}
