<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const errorMsg = ref('');
const authStore = useAuthStore();
const router = useRouter();

// 비밀번호 찾기 모달 관련
const showResetModal = ref(false);
const resetForm = ref({ username: '', first_name: '', new_password: '' });
const resetMsg = ref('');
const resetSuccess = ref(false);

const handleLogin = async () => {
    try {
        await authStore.login(username.value, password.value);
        const redirect = typeof router.currentRoute.value.query.redirect === 'string'
            ? router.currentRoute.value.query.redirect
            : '/admin/dashboard';
        router.push(redirect);
    } catch (err) {
        errorMsg.value = '로그인이 실패했습니다. 아이디와 비밀번호를 확인해주세요.';
    }
};

const handleResetPassword = async () => {
    resetMsg.value = '';
    resetSuccess.value = false;
    try {
        await authStore.resetPassword(resetForm.value);
        resetSuccess.value = true;
        resetMsg.value = '비밀번호가 성공적으로 변경되었습니다.';
        setTimeout(() => {
            showResetModal.value = false;
            resetForm.value = { username: '', first_name: '', new_password: '' };
            resetMsg.value = '';
        }, 2000);
    } catch (err) {
        resetSuccess.value = false;
        resetMsg.value = err.response?.data?.message || err.response?.data?.non_field_errors?.[0] || '정보가 일치하지 않거나 오류가 발생했습니다.';
    }
};
</script>

<template>
    <div class="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-blue-50 p-4 font-sans relative">
        <!-- Background Decor -->
        <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
            <div class="absolute top-[10%] -left-[10%] w-[60%] h-[60%] bg-blue-100/30 rounded-full blur-3xl"></div>
            <div class="absolute bottom-[10%] -right-[10%] w-[50%] h-[50%] bg-indigo-100/30 rounded-full blur-3xl"></div>
        </div>

        <div class="relative z-10 w-full max-w-md backdrop-blur-xl bg-white/80 rounded-3xl p-8 shadow-2xl border border-white/50 ring-1 ring-slate-900/5">
            <div class="text-center mb-8">
                <span class="text-3xl mb-2 block">🔐</span>
                <h2 class="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-indigo-700">관리자 로그인</h2>
                <p class="text-sm text-slate-500 mt-2">Maum-On Staff Access</p>
            </div>
            
            <form @submit.prevent="handleLogin" class="space-y-5">
                <div class="space-y-1">
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">아이디</label>
                    <input 
                        v-model="username" 
                        type="text" 
                        class="w-full rounded-xl border border-slate-200 bg-slate-50/50 p-3.5 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-400"
                        placeholder="admin_id"
                        required
                    />
                </div>
                
                <div class="space-y-1">
                    <div class="flex justify-between items-center ml-1">
                        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider">비밀번호</label>
                        <button type="button" @click="showResetModal = true" class="text-xs text-indigo-500 hover:text-indigo-700 font-medium hover:underline">비밀번호 찾기</button>
                    </div>
                    <input 
                        v-model="password" 
                        type="password" 
                        class="w-full rounded-xl border border-slate-200 bg-slate-50/50 p-3.5 focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder:text-slate-400"
                        placeholder="••••••••"
                        required
                    />
                </div>

                <div v-if="errorMsg" class="p-3 rounded-lg bg-red-50 border border-red-100 flex items-center gap-2">
                    <span class="text-red-500 text-lg">⚠️</span>
                    <span class="text-sm text-red-600 font-medium">{{ errorMsg }}</span>
                </div>

                <button 
                    type="submit" 
                    class="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 hover:shadow-indigo-300 hover:from-blue-700 hover:to-indigo-700 transform transition-all active:scale-[0.98]"
                >
                    로그인 확인
                </button>
            </form>
            
            <div class="mt-8 text-center border-t border-slate-100 pt-6">
                <p class="text-sm text-slate-500">
                    계정이 없으신가요? 
                    <router-link to="/signup" class="font-bold text-indigo-600 hover:text-indigo-800 transition-colors ml-1">
                        담당자 등록 요청
                    </router-link>
                </p>
            </div>
        </div>

        <!-- 비밀번호 찾기 모달 -->
        <div v-if="showResetModal" class="fixed inset-0 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm z-50 p-4">
            <div class="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl animate-fade-in-up">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-lg font-bold text-slate-800">비밀번호 재설정</h3>
                    <button @click="showResetModal = false" class="text-slate-400 hover:text-slate-600 text-xl font-bold">×</button>
                </div>
                
                <p class="mb-5 text-sm text-slate-500 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                    가입하신 <strong>아이디</strong>와 <strong>이름(실명)</strong>을 입력하시면 새로운 비밀번호를 설정할 수 있습니다.
                </p>
                
                <form @submit.prevent="handleResetPassword" class="space-y-3">
                    <input v-model="resetForm.username" placeholder="아이디" class="w-full rounded-lg border border-slate-200 p-3 text-sm focus:ring-2 focus:ring-indigo-100 outline-none" required />
                    <input v-model="resetForm.first_name" placeholder="이름 (실명)" class="w-full rounded-lg border border-slate-200 p-3 text-sm focus:ring-2 focus:ring-indigo-100 outline-none" required />
                    <input v-model="resetForm.new_password" type="password" placeholder="새 비밀번호" class="w-full rounded-lg border border-slate-200 p-3 text-sm focus:ring-2 focus:ring-indigo-100 outline-none" required />
                    
                    <div v-if="resetMsg" :class="resetSuccess ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'" class="text-xs p-3 rounded-lg font-medium border border-transparent">
                        {{ resetMsg }}
                    </div>

                    <div class="flex justify-end gap-2 mt-2 pt-2">
                        <button type="button" @click="showResetModal = false" class="rounded-lg bg-slate-100 px-4 py-2.5 text-sm font-bold text-slate-600 hover:bg-slate-200 transition-colors">취소</button>
                        <button type="submit" class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-indigo-700 shadow-md transition-colors">변경하기</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<style>
@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up {
    animation: fade-in-up 0.3s ease-out forwards;
}
</style>
