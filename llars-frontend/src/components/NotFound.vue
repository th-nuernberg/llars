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
      <div class="polar-bear">
        <div class="polar-bear-head">
          <div class="polar-bear-ear left"></div>
          <div class="polar-bear-ear right"></div>
          <div class="polar-bear-snout"></div>
          <div class="polar-bear-eye left"></div>
          <div class="polar-bear-eye right"></div>
        </div>
        <div class="polar-bear-body"></div>
        <div class="polar-bear-arm left"></div>
        <div class="polar-bear-arm right"></div>
        <div class="polar-bear-leg left"></div>
        <div class="polar-bear-leg right"></div>
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

.polar-bear {
  position: absolute;
  width: 160px;
  height: 200px;
  left: 50%;
  top: 50%;
  animation: float 6s ease-in-out infinite;
}

.polar-bear-head {
  position: absolute;
  width: 100px;
  height: 80px;
  background-color: white;
  border-radius: 50px;
  top: 0;
  left: 30px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.polar-bear-ear {
  position: absolute;
  width: 30px;
  height: 30px;
  background-color: white;
  border-radius: 50%;
  top: -10px;
}

.polar-bear-ear.left {
  left: 10px;
}

.polar-bear-ear.right {
  right: 10px;
}

.polar-bear-eye {
  position: absolute;
  width: 8px;
  height: 8px;
  background-color: #2F4F4F;
  border-radius: 50%;
  top: 35px;
}

.polar-bear-eye.left {
  left: 30px;
}

.polar-bear-eye.right {
  right: 30px;
}

.polar-bear-snout {
  position: absolute;
  width: 40px;
  height: 25px;
  background-color: #2F4F4F;
  border-radius: 20px;
  bottom: 15px;
  left: 30px;
}

.polar-bear-body {
  position: absolute;
  width: 120px;
  height: 140px;
  background-color: white;
  border-radius: 60px;
  top: 60px;
  left: 20px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.polar-bear-arm {
  position: absolute;
  width: 30px;
  height: 80px;
  background-color: white;
  border-radius: 15px;
  top: 80px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.polar-bear-arm.left {
  left: 0;
  transform: rotate(20deg);
}

.polar-bear-arm.right {
  right: 0;
  transform: rotate(-20deg);
}

.polar-bear-leg {
  position: absolute;
  width: 35px;
  height: 70px;
  background-color: white;
  border-radius: 17px;
  bottom: 0;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.polar-bear-leg.left {
  left: 25px;
}

.polar-bear-leg.right {
  right: 25px;
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

.polar-bear {
  position: relative;
  margin-left: 50px;
  width: 160px;
  height: 200px;
  top: 150px;
  animation: float 8s ease-in-out infinite;
}

}
</style>
