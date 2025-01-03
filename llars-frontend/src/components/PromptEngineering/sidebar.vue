<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="sidebar-content">
    <v-spacer></v-spacer>
      <!-- Online Users Liste -->
      <div class="users-list">
        <h3>Online Users:</h3>
        <div v-for="(user, id) in users" :key="id" class="user-item">
          <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
          {{ user.username }}
        </div>
      </div>
      <button @click="$emit('showAddBlockDialog')" class="add-block-button">
        Neuen Block hinzufügen
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  users: {
    type: Object,
    required: true
  }
});

defineEmits(['showAddBlockDialog']);
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
  height: calc(100vh - 64px); /* Subtract app bar height */
  position: fixed;
  top: 64px; /* Add top offset equal to app bar height */
  left: 0;
  overflow-y: auto;
  padding: 20px;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.add-block-button {
  width: 100%;
  padding: 8px 12px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.add-block-button:hover {
  background-color: #45a049;
}

.users-list {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.users-list h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 0.9rem;
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}
</style>
