<template>
  <div class="intro-container">
    <div class="content">
      <div class="logo-area">
        <div class="moon-icon">🌙</div>
        <h1 class="title">하루온</h1>
        <h2 class="subtitle">Haru-On</h2>
        <p class="tagline">당신의 하루를, 온전히</p>
      </div>

      <div class="loading-area">
        <div class="spinner"></div>
        <p class="loading-text">하루를 여는 중...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  setTimeout(() => {
    // Check if user is already authenticated to decide destination?
    // The router guard will handle /calendar -> /login redirection if needed.
    // So we just push to /calendar.
    router.replace('/calendar');
  }, 2500); // 2.5 seconds delay
});
</script>

<style scoped>
.intro-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  background-color: #6e4cdf; /* Custom Purple */
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  height: 70%; /* Adjust to push logo up and loader down */
  text-align: center;
  width: 100%;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: auto;
  margin-bottom: auto;
  transform: scale(1.1);
}

.moon-icon {
  font-size: 100px;
  filter: drop-shadow(0 10px 10px rgba(0, 0, 0, 0.2));
  margin-bottom: 24px;
}

.title {
  font-size: 40px;
  font-weight: 700;
  color: white;
  margin: 0;
  line-height: 1.2;
}

.subtitle {
  font-size: 24px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 8px 0 0 0;
}

.tagline {
  font-size: 16px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
}

.loading-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60px; /* Padding bottom similar to Swift */
}

/* Simple CSS Spinner */
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 12px;
  transform: scale(1.2);
}

.loading-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
