/**
 * Conversation management composable.
 * Handles group info updates, member management, and muting.
 */
import axios from 'axios'

export function useConversations() {
  const updateGroupInfo = async (conversationId, { name, description }) => {
    const { data } = await axios.put(
      `/api/messaging/conversations/${conversationId}`,
      { name, description }
    )
    return data.conversation
  }

  const addMember = async (conversationId, username) => {
    const { data } = await axios.post(
      `/api/messaging/conversations/${conversationId}/members`,
      { username }
    )
    return data.conversation
  }

  const removeMember = async (conversationId, username) => {
    await axios.delete(
      `/api/messaging/conversations/${conversationId}/members/${username}`
    )
  }

  const muteConversation = async (conversationId, mute = true) => {
    await axios.post(
      `/api/messaging/conversations/${conversationId}/mute`,
      { mute }
    )
  }

  const getConversation = async (conversationId) => {
    const { data } = await axios.get(
      `/api/messaging/conversations/${conversationId}`
    )
    return data.conversation
  }

  return {
    updateGroupInfo,
    addMember,
    removeMember,
    muteConversation,
    getConversation,
  }
}
