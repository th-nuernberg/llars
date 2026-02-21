<template>
  <div class="buckets-container">
    <!-- Gut Bucket -->
    <div class="bucket good-bucket">
      <h3>{{ $t('adminTester.buckets.good') }}</h3>
      <draggable
        v-model="goodList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
        @end="saveToLocalStorage"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>

    <!-- Mittel Bucket -->
    <div class="bucket average-bucket">
      <h3>{{ $t('adminTester.buckets.average') }}</h3>
      <draggable
        v-model="averageList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
        @end="saveToLocalStorage"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>

    <!-- Schlecht Bucket -->
    <div class="bucket bad-bucket">
      <h3>{{ $t('adminTester.buckets.bad') }}</h3>
      <draggable
        v-model="badList"
        class="list-group bucket-content"
        group="bucket"
        item-key="id"
        @end="saveToLocalStorage"
      >
        <template #item="{ element }">
          <div class="list-group-item item">{{ element.name }}</div>
        </template>
      </draggable>
    </div>
  </div>

  <!-- Neutraler Bucket -->
  <div class="neutral-bucket-container">
    <h3>{{ $t('adminTester.buckets.neutral') }}</h3>
    <draggable
      v-model="neutralList"
      class="neutral-list-group"
      group="bucket"
      item-key="id"
      @end="saveToLocalStorage"
    >
      <template #item="{ element }">
        <div class="neutral-item">{{ element.name }}</div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import draggable from 'vuedraggable';

// Initiale Daten
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

const STORAGE_KEY = 'bucket_data';

// Daten in den LocalStorage speichern
function saveToLocalStorage() {
  const data = {
    goodList: goodList.value,
    averageList: averageList.value,
    badList: badList.value,
    neutralList: neutralList.value
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// Daten aus dem LocalStorage laden
function loadFromLocalStorage() {
  const savedData = localStorage.getItem(STORAGE_KEY);
  if (savedData) {
    const parsedData = JSON.parse(savedData);
    goodList.value = parsedData.goodList || [];
    averageList.value = parsedData.averageList || [];
    badList.value = parsedData.badList || [];
    neutralList.value = parsedData.neutralList || [];
  }
}

// Daten beim Laden der Komponente aus dem LocalStorage abrufen
onMounted(() => {
  loadFromLocalStorage();
});
</script>

<style scoped>
/* Zusätzlicher Abstand oben */
.buckets-container {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px 10px 0;
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

/* Abgemilderte Farbgebung für die Buckets */
.good-bucket {
  background-color: #e8f5e9; /* Leicht grünlich */
  border: 1px solid #a5d6a7;
}

.average-bucket {
  background-color: #fffde7; /* Leicht gelblich */
  border: 1px solid #fff59d;
}

.bad-bucket {
  background-color: #ffebee; /* Leicht rötlich */
  border: 1px solid #ef9a9a;
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
  background-color: #f5f5f5; /* Leicht grauer Hintergrund */
  min-height: 150px;
  border: 1px solid #bdbdbd;
  padding: 10px;
  border-radius: 8px;
  margin-top: 30px;
  margin-left: 10px;
  margin-right: 10px;
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
