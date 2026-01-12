<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';

const isLogin = ref(true);
const username = ref('');
const password = ref('');
const errorMsg = ref('');
const authStore = useAuthStore();

const handleSubmit = async () => {
    errorMsg.value = '';
    if (isLogin.value) {
        const success = await authStore.login(username.value, password.value);
        if (!success) errorMsg.value = '로그인 실패. 아이디/비번을 확인하세요.';
    } else {
        const success = await authStore.register(username.value, password.value);
        if (success) {
            alert('가입 완료! 로그인 해주세요.');
            isLogin.value = true;
        } else {
            errorMsg.value = '회원가입 실패. 이미 존재하는 아이디일 수 있습니다.';
        }
    }
};
</script>

<template>
  <div class="min-h-screen flex bg-white">
    <!-- Left Panel: Image & Branding -->
    <div class="hidden lg:flex w-1/2 relative bg-stone-100 overflow-hidden">
      <img src="/images/login_bg.png" alt="Mood Diary Background" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0 bg-black/10"></div> <!-- Subtle overlay -->
      <div class="relative z-10 flex flex-col justify-between p-16 w-full h-full text-white">
        <div>
           <!-- Optional Logo Area -->
           <div class="w-10 h-10 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center border border-white/30">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
           </div>
        </div>
        <div>
           <h1 class="text-5xl font-serif font-medium leading-tight mb-4 drop-shadow-sm">Your Daily <br/> Mood Journey</h1>
           <p class="text-lg text-white/90 font-light max-w-md">기억하고 싶은 순간들, 나의 감정을 기록하는 특별한 공간.</p>
        </div>
        <div class="text-xs text-white/50 transform translate-y-2">
           © 2026 Mood Diary V2
        </div>
      </div>
    </div>

    <!-- Right Panel: Form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 lg:p-24 bg-white relative">
       <!-- Mobile Only Bg Hint -->
       <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-amber-100 to-stone-200 lg:hidden"></div>

       <div class="max-w-[400px] w-full space-y-10">
          <div class="text-left">
            <h2 class="text-3xl font-bold text-stone-900 tracking-tight">
              {{ isLogin ? 'Welcome back' : 'Create an account' }}
            </h2>
            <p class="mt-3 text-stone-500">
               {{ isLogin ? '오늘 하루는 어떠셨나요? 당신의 이야기를 들려주세요.' : '새로운 여정을 시작하기 위해 계정을 만들어주세요.' }}
            </p>
          </div>

          <form class="space-y-6" @submit.prevent="handleSubmit">
            <div class="space-y-5">
              <div>
                <label for="username" class="block text-sm font-semibold text-stone-700 mb-2">Username</label>
                <input v-model="username" id="username" name="username" type="text" required 
                    class="block w-full px-4 py-3.5 bg-stone-50 border border-stone-200 rounded-xl focus:ring-2 focus:ring-black focus:border-black transition-all placeholder-stone-400 text-stone-900" 
                    placeholder="아이디를 입력하세요" />
              </div>
              <div>
                <div class="flex items-center justify-between mb-2">
                    <label for="password" class="block text-sm font-semibold text-stone-700">Password</label>
                    <!-- Optional: Forgot Password Link -->
                </div>
                <input v-model="password" id="password" name="password" type="password" required 
                    class="block w-full px-4 py-3.5 bg-stone-50 border border-stone-200 rounded-xl focus:ring-2 focus:ring-black focus:border-black transition-all placeholder-stone-400 text-stone-900" 
                    placeholder="비밀번호를 입력하세요" />
              </div>
            </div>

            <p v-if="errorMsg" class="text-rose-600 text-sm font-medium bg-rose-50 px-4 py-3 rounded-lg flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {{ errorMsg }}
            </p>

            <button type="submit" 
                class="w-full flex justify-center py-4 px-4 border border-transparent text-base font-bold rounded-xl text-white bg-stone-900 hover:bg-black focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-stone-900 transition-all shadow-lg hover:shadow-xl transform active:scale-[0.98]">
              {{ isLogin ? 'Sign In' : 'Sign Up' }}
            </button>
          </form>

          <div class="relative">
             <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-stone-200"></div></div>
             <div class="relative flex justify-center text-sm"><span class="px-2 bg-white text-stone-400">Or</span></div>
          </div>

          <div class="text-center">
             <button @click="isLogin = !isLogin" class="text-sm font-medium text-stone-600 hover:text-stone-900 transition-colors">
                {{ isLogin ? '계정이 없으신가요? 회원가입' : '이미 계정이 있으신가요? 로그인' }}
             </button>
          </div>
       </div>
    </div>
  </div>
</template>
