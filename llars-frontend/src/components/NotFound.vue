<template>
  <div class="not-found-container">
    <div class="content">
      <h1 class="title">404</h1>
      <h2 class="subtitle">Oops! Seite nicht gefunden</h2>
      <p class="message">Die von Ihnen gesuchte Seite scheint im Cyberspace verloren gegangen zu sein.</p>
      <button @click="goHome" class="home-button">
        Zur Startseite
      </button>
    </div>
    <div class="animation-container">
      <div class="astronaut">
        <div class="astronaut-helmet"></div>
        <div class="astronaut-body"></div>
        <div class="astronaut-arm left"></div>
        <div class="astronaut-arm right"></div>
        <div class="astronaut-leg left"></div>
        <div class="astronaut-leg right"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function goHome() {
  router.push('/');
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #ffffff;
  color: #2F4F4F;
  font-family: Arial, sans-serif;
}

.content {
  text-align: center;
  z-index: 1;
}

.title {
  font-size: 8rem;
  margin-bottom: 0;
  color: #b0ca97;
}

.subtitle {
  font-size: 2rem;
  margin-top: 0;
  color: #556B2F;
}

.message {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #2F4F4F;
}

.home-button {
  padding: 10px 20px;
  font-size: 1rem;
  background-color: #f1efd5;
  color: #2F4F4F;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.home-button:hover {
  background-color: #b0ca97;
}

.animation-container {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.astronaut {
  position: absolute;
  width: 100px;
  height: 150px;
  left: 50%;
  top: 50%;
  animation: float 6s ease-in-out infinite;
}

.astronaut-helmet {
  position: absolute;
  width: 60px;
  height: 60px;
  background-color: #f1efd5;
  border-radius: 50%;
  top: 0;
  left: 20px;
}

.astronaut-body {
  position: absolute;
  width: 80px;
  height: 100px;
  background-color: #b0ca97;
  border-radius: 40px;
  top: 40px;
  left: 10px;
}

.astronaut-arm {
  position: absolute;
  width: 20px;
  height: 60px;
  background-color: #b0ca97;
  top: 60px;
}

.astronaut-arm.left {
  left: 0;
  transform: rotate(20deg);
}

.astronaut-arm.right {
  right: 0;
  transform: rotate(-20deg);
}

.astronaut-leg {
  position: absolute;
  width: 25px;
  height: 80px;
  background-color: #b0ca97;
  bottom: 0;
}

.astronaut-leg.left {
  left: 15px;
}

.astronaut-leg.right {
  right: 15px;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 6rem;
  }

  .subtitle {
    font-size: 1.5rem;
  }

  .message {
    font-size: 1rem;
  }
}
</style>
