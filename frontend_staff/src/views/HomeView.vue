<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { onMounted } from 'vue';

const router = useRouter();
const authStore = useAuthStore();

const goLogin = () => router.push('/login');

const goDashboard = () => {
  if (authStore.isAuthenticated) {
    router.push('/admin/dashboard');
  } else {
    // alert('로그인이 필요합니다.'); // UX: Remove alert, just redirect
    router.push('/login');
  }
};
</script>

<template>
  <main class="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-blue-50 p-6 font-sans">
    
    <!-- Background Decor -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-blue-200/20 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute top-[40%] -right-[10%] w-[40%] h-[40%] bg-indigo-200/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
    </div>

    <div class="relative z-10 w-full max-w-lg">
      
      <!-- Header -->
      <div class="text-center mb-12">
        <div class="inline-block mb-4 p-3 bg-white rounded-2xl shadow-sm">
            <span class="text-4xl">☀️</span>
        </div>
        <h1 class="mb-3 text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 tracking-tight leading-tight">
          maumON
        </h1>
        <p class="text-xl text-slate-500 font-medium tracking-wide">
          마음온 · 마음의 온도를 잇다
        </p>
      </div>
      
      <!-- Card -->
      <div class="backdrop-blur-xl bg-white/70 rounded-3xl p-8 shadow-2xl border border-white/50 ring-1 ring-slate-900/5 transition-all hover:shadow-xl duration-500">
        
        <!-- Header in Card -->
        <div class="text-center mb-8 pb-6 border-b border-indigo-50">
            <h2 class="text-lg font-bold text-slate-700 mb-1">Staff Portal Access</h2>
            <p class="text-sm text-slate-400">보건소 및 정신건강복지센터 담당자 전용</p>
        </div>

        <div v-if="authStore.isAuthenticated" class="space-y-6">
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-2xl border border-blue-100/50">
                <div class="flex items-center gap-3 mb-1">
                    <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <p class="text-indigo-900 font-bold text-lg">
                        {{ authStore.user?.username || '관리자' }}님
                    </p>
                </div>
                <p class="text-indigo-600/80 text-sm ml-5">안전하게 접속 중입니다.</p>
            </div>
            
            <div class="grid grid-cols-1 gap-3">
                <button 
                  @click="goDashboard" 
                  class="group relative flex items-center justify-center w-full py-4 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transform transition-all hover:-translate-y-0.5 active:translate-y-0"
                >
                  <span class="text-lg">통합 대시보드 입장</span>
                  <span class="absolute right-6 opacity-70 group-hover:translate-x-1 transition-transform">→</span>
                </button>
                
                <button 
                  @click="authStore.logout" 
                  class="w-full py-4 px-6 rounded-xl bg-white border border-slate-200 text-slate-600 font-bold hover:bg-slate-50 hover:text-slate-800 transition-colors"
                >
                  로그아웃
                </button>
            </div>
        </div>

        <div v-else class="space-y-8">
            <div class="bg-amber-50 rounded-lg p-4 flex gap-3 items-start">
                <span class="text-amber-500 mt-0.5 text-lg">🔒</span>
                <p class="text-sm text-amber-800/80 leading-relaxed">
                    본 시스템은 인가된 의료진 및 담당자만 접근 가능합니다. 
                    승인된 계정으로 로그인해 주세요.
                </p>
            </div>

            <button 
              @click="goLogin" 
              class="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-lg shadow-xl shadow-blue-200 hover:shadow-blue-300 transform transition-all hover:-translate-y-0.5 active:translate-y-0"
            >
              담당자 로그인
            </button>
        </div>
      </div>
      
      <!-- Footer -->
      <p class="mt-8 text-center text-xs text-slate-400 font-medium">
          Maum-On B2G Clinical System v2.0 <br>
          Authorized Access Only
      </p>
    </div>
  </main>
</template>

<style scoped>
/* Glassmorphism helpers if needed via CSS directly */
</style>
