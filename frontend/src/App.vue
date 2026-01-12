<script setup lang="ts">
import { useAuthStore } from './stores/auth';
import AuthPage from './views/AuthPage.vue';
import DiaryPage from './views/DiaryPage.vue';

const authStore = useAuthStore();
</script>

<template>
  <div v-if="!authStore.isAuthenticated">
    <AuthPage />
  </div>
  <div v-else>
    <DiaryPage />
  </div>
</template>
