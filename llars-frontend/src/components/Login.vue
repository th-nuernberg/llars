<template>
  <v-container class="fill-height" fluid>
    <div class="paint-strokes">
      <div v-for="n in 8" :key="n"></div>
    </div>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark>
            <v-toolbar-title>LLars Plattform Login</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                label="Username"
                prepend-icon="mdi-account"
                v-model="username"
                color="primary"
                required
              ></v-text-field>
              <v-text-field
                label="Passwort"
                prepend-icon="mdi-lock"
                v-model="password"
                type="password"
                color="primary"
                required
                @keyup.enter="handleLogin"
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="secondary" @click="handleLogin">Login</v-btn>
          </v-card-actions>
          <v-alert v-if="errorMessage" type="error" class="ma-4">
            {{ errorMessage }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {useKeycloak} from '@dsb-norge/vue-keycloak-js';

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const router = useRouter();
const keycloak = useKeycloak();

// Check if already authenticated on mount
onMounted(() => {
  if (keycloak.authenticated) {
    // Already logged in, redirect based on role
    const roles = keycloak.tokenParsed?.realm_access?.roles || [];
    if (roles.includes('admin')) {
      router.push('/AdminDashboard');
    } else {
      router.push('/Home');
    }
  }
});

async function handleLogin() {
  try {
    // For a seamless experience, we redirect to Keycloak login
    // The username/password fields are just for UX consistency
    // In production, you could customize Keycloak's theme to match this design

    // Redirect to Keycloak login page
    await keycloak.login({
      redirectUri: window.location.origin + '/Home',
      // You can optionally pre-fill the username
      loginHint: username.value
    });
  } catch (error) {
    console.error('Login error:', error);
    errorMessage.value = 'An error occurred during login. Please try again.';
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  position: relative;
  background: #fdfcfa;
  overflow: hidden;
}

.paint-strokes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.paint-strokes div {
  position: absolute;
  width: 100%;
  height: 100%;
  filter: blur(20px);
  mix-blend-mode: multiply;
}

/* LINKE SEITE - Helle Grüntöne (Fokus auf linke Ecken) */
.paint-strokes div:nth-child(1) {
  background: rgba(226, 234, 218, 0.5);
  top: -50%;
  left: -90%;
  width: 120%;
  height: 180%;
  transform: rotate(-15deg);
  border-radius: 65% 35% 70% 30% / 55% 45% 60% 40%;
  animation: floatStrokeLeft1 45s ease-in-out infinite;
}

.paint-strokes div:nth-child(2) {
  background: rgba(234, 238, 229, 0.4);
  top: -40%;
  left: -95%;
  width: 130%;
  height: 160%;
  transform: rotate(-25deg);
  border-radius: 55% 45% 60% 40% / 45% 55% 65% 35%;
  animation: floatStrokeLeft2 52s ease-in-out infinite;
}

.paint-strokes div:nth-child(3) {
  background: rgba(220, 230, 215, 0.45);
  bottom: -60%;
  left: -85%;
  width: 110%;
  height: 140%;
  transform: rotate(-20deg);
  border-radius: 60% 40% 65% 35% / 35% 65% 45% 55%;
  animation: floatStrokeLeft3 48s ease-in-out infinite;
}

.paint-strokes div:nth-child(4) {
  background: rgba(228, 235, 223, 0.35);
  bottom: -50%;
  left: -90%;
  width: 125%;
  height: 150%;
  transform: rotate(-30deg);
  border-radius: 70% 30% 50% 50% / 50% 50% 70% 30%;
  animation: floatStrokeLeft4 50s ease-in-out infinite;
}

/* RECHTE SEITE - Helle Beigetöne (Fokus auf rechte Ecken) */
.paint-strokes div:nth-child(5) {
  background: rgba(242, 236, 228, 0.5);
  top: -50%;
  right: -90%;
  width: 120%;
  height: 170%;
  transform: rotate(15deg);
  border-radius: 45% 55% 40% 60% / 40% 60% 70% 30%;
  animation: floatStrokeRight1 47s ease-in-out infinite;
}

.paint-strokes div:nth-child(6) {
  background: rgba(238, 233, 225, 0.4);
  top: -40%;
  right: -95%;
  width: 130%;
  height: 160%;
  transform: rotate(25deg);
  border-radius: 40% 60% 55% 45% / 60% 40% 50% 50%;
  animation: floatStrokeRight2 53s ease-in-out infinite;
}

.paint-strokes div:nth-child(7) {
  background: rgba(240, 235, 228, 0.45);
  bottom: -60%;
  right: -85%;
  width: 115%;
  height: 150%;
  transform: rotate(20deg);
  border-radius: 35% 65% 45% 55% / 55% 45% 60% 40%;
  animation: floatStrokeRight3 49s ease-in-out infinite;
}

.paint-strokes div:nth-child(8) {
  background: rgba(235, 230, 222, 0.35);
  bottom: -50%;
  right: -90%;
  width: 125%;
  height: 140%;
  transform: rotate(30deg);
  border-radius: 45% 55% 35% 65% / 65% 35% 55% 45%;
  animation: floatStrokeRight4 51s ease-in-out infinite;
}

/* Animationen anpassen für sanftere Bewegungen in den Ecken */
@keyframes floatStrokeLeft1 {
  0%, 100% { transform: rotate(-15deg) translate(0, 0) scale(1); }
  50% { transform: rotate(-12deg) translate(3%, 2%) scale(1.05); }
}

@keyframes floatStrokeLeft2 {
  0%, 100% { transform: rotate(-25deg) translate(0, 0) scale(1); }
  50% { transform: rotate(-22deg) translate(2%, -2%) scale(1.03); }
}

@keyframes floatStrokeLeft3 {
  0%, 100% { transform: rotate(-20deg) translate(0, 0) scale(1); }
  50% { transform: rotate(-18deg) translate(4%, 3%) scale(1.04); }
}

@keyframes floatStrokeLeft4 {
  0%, 100% { transform: rotate(-30deg) translate(0, 0) scale(1); }
  50% { transform: rotate(-27deg) translate(2%, -3%) scale(1.06); }
}

@keyframes floatStrokeRight1 {
  0%, 100% { transform: rotate(15deg) translate(0, 0) scale(1); }
  50% { transform: rotate(12deg) translate(-3%, 2%) scale(1.05); }
}

@keyframes floatStrokeRight2 {
  0%, 100% { transform: rotate(25deg) translate(0, 0) scale(1); }
  50% { transform: rotate(22deg) translate(-2%, -2%) scale(1.03); }
}

@keyframes floatStrokeRight3 {
  0%, 100% { transform: rotate(20deg) translate(0, 0) scale(1); }
  50% { transform: rotate(18deg) translate(-4%, 3%) scale(1.04); }
}

@keyframes floatStrokeRight4 {
  0%, 100% { transform: rotate(30deg) translate(0, 0) scale(1); }
  50% { transform: rotate(27deg) translate(-2%, -3%) scale(1.06); }
}
</style>
