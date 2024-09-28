<template>
  <div class="buckets-container">
    <!-- Gut Bucket -->
    <div class="bucket good-bucket">
      <h3>Gut</h3>
      <draggable
        v-model="goodList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>

    <!-- Mittel Bucket -->
    <div class="bucket average-bucket">
      <h3>Mittel</h3>
      <draggable
        v-model="averageList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>

    <!-- Schlecht Bucket -->
    <div class="bucket bad-bucket">
      <h3>Schlecht</h3>
      <draggable
        v-model="badList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>
  </div>

  <!-- Neutraler Bucket -->
  <div class="neutral-bucket-container">
    <h3>Neutral</h3>
    <draggable
      v-model="neutralList"
      class="neutral-list-group"
      group="bucket"
      item-key="id"
    >
      <template #item="{ element }">
        <div class="neutral-item">{{ element.name }}</div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import draggable from 'vuedraggable';

const goodList = ref([]);
const averageList = ref([]);
const badList = ref([]);

const neutralList = ref([
  { name: "John 1", id: 0 },
  { name: "Joao 2", id: 1 },
  { name: "Jean 3", id: 2 },
  { name: "Jonny 4", id: 3 },
  { name: "Guisepe 5", id: 4 }
]);
</script>

<style scoped>
/* Stile für die Buckets */
.buckets-container {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 30px;
}

.bucket {
  flex: 1;
  border: 1px solid #ddd;
  padding: 10px;
  border-radius: 8px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* Farbgebung für die einzelnen Buckets */
.good-bucket {
  background-color: #e0f2f1; /* Leicht grünlich */
  border: 1px solid #4caf50;
}

.average-bucket {
  background-color: #fffde7; /* Leicht gelblich */
  border: 1px solid #ffeb3b;
}

.bad-bucket {
  background-color: #ffebee; /* Leicht rötlich */
  border: 1px solid #f44336;
}

.bucket-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

/* Stil für die Listenelemente */
.item {
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 5px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: grab;
}

/* Neutraler Bucket */
.neutral-bucket-container {
  background-color: #fff9c4; /* Leicht gelber Hintergrund */
  min-height: 150px;
  border: 1px solid #ffeb3b;
  padding: 10px;
  border-radius: 8px;
  margin-top: 30px;
}

.neutral-list-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.neutral-item {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 5px;
  background-color: #bbdefb;
  width: 100px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: grab;
}
</style>
