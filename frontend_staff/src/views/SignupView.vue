<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

// 상태 관리
const formData = ref({
    center_id: '',
    first_name: '',
    username: '',
    email: '',
    password: '',
    passwordConfirm: ''
});

const centers = ref([]);
const errorMsg = ref('');
const isLoading = ref(false);

const authStore = useAuthStore();
const router = useRouter();

// 센터 목록 불러오기
onMounted(async () => {
    centers.value = await authStore.fetchCenters();
});

// 회원가입 처리
const handleRegister = async () => {
    errorMsg.value = '';
    
    // 유효성 검사
    if (formData.value.password !== formData.value.passwordConfirm) {
        errorMsg.value = '비밀번호가 일치하지 않습니다.';
        return;
    }
    
    if (!formData.value.center_id) {
        errorMsg.value = '소속 센터를 선택해주세요.';
        return;
    }

    isLoading.value = true;
    try {
        await authStore.register({
            center_id: formData.value.center_id,
            first_name: formData.value.first_name,
            username: formData.value.username,
            email: formData.value.email,
            password: formData.value.password
        });
        alert('회원가입이 완료되었습니다. 로그인해주세요.');
        router.push('/login');
    } catch (err) {
        console.error(err);
        if (err.response && err.response.data) {
            const data = err.response.data;
            
            // 1. 응답이 배열인 경우 (예: ["에러 메시지"])
            if (Array.isArray(data)) {
                errorMsg.value = data.join('\n');
            } 
            // 2. 응답이 객체인 경우
            else if (typeof data === 'object') {
                const keys = Object.keys(data);
                if (keys.length > 0) {
                    const firstKey = keys[0];
                    const msg = Array.isArray(data[firstKey]) 
                        ? data[firstKey].join(', ') 
                        : data[firstKey];
                    
                    // non_field_errors는 키 표시 생략
                    if (firstKey === 'non_field_errors' || firstKey === 'detail') {
                        errorMsg.value = msg;
                    } else {
                        // 키(필드명)를 한글로 변환해서 보여주면 더 좋음 (간단 매핑)
                        const fieldMap = {
                            'username': '아이디',
                            'password': '비밀번호',
                            'email': '이메일',
                            'first_name': '이름',
                            'center_id': '소속 센터'
                        };
                        const label = fieldMap[firstKey] || firstKey;
                        errorMsg.value = `${label}: ${msg}`;
                    }
                } else {
                    errorMsg.value = '알 수 없는 오류가 발생했습니다.';
                }
            } else {
                errorMsg.value = String(data); // 문자열 등 기타 형식이면 그대로 출력
            }
        } else {
            errorMsg.value = '서버 연결 오류가 발생했습니다.';
        }
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
    <div class="flex min-h-screen flex-col items-center justify-center bg-gray-100 p-4">
        <div class="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
            <h2 class="mb-6 text-center text-2xl font-bold text-gray-800">회원가입</h2>
            
            <form @submit.prevent="handleRegister" class="space-y-4">
                <!-- 소속 센터 선택 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">소속 센터</label>
                    <select 
                        v-model="formData.center_id"
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                    >
                        <option value="" disabled>센터를 선택하세요</option>
                        <option v-for="center in centers" :key="center.id" :value="center.id">
                            {{ center.name }} ({{ center.region }})
                        </option>
                    </select>
                </div>

                <!-- 이름(실명) -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">이름</label>
                    <input 
                        v-model="formData.first_name" 
                        type="text" 
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                        placeholder="실명을 입력하세요"
                    />
                </div>

                <!-- 아이디 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">아이디</label>
                    <input 
                        v-model="formData.username" 
                        type="text" 
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                        placeholder="영문, 숫자 포함"
                    />
                </div>

                <!-- 이메일 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">이메일</label>
                    <input 
                        v-model="formData.email" 
                        type="email" 
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                        placeholder="example@email.com"
                    />
                </div>
                
                <!-- 비밀번호 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">비밀번호</label>
                    <input 
                        v-model="formData.password" 
                        type="password" 
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                        placeholder="비밀번호 입력"
                    />
                </div>

                <!-- 비밀번호 확인 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700">비밀번호 확인</label>
                    <input 
                        v-model="formData.passwordConfirm" 
                        type="password" 
                        class="mt-1 block w-full rounded border border-gray-300 p-2 focus:border-indigo-500 focus:ring-indigo-500"
                        required
                        placeholder="비밀번호 재입력"
                    />
                </div>

                <div v-if="errorMsg" class="text-sm text-red-600 font-semibold">
                    {{ errorMsg }}
                </div>

                <button 
                    type="submit" 
                    class="w-full rounded bg-indigo-600 px-4 py-2 font-bold text-white hover:bg-indigo-700 transition"
                    :disabled="isLoading"
                >
                    {{ isLoading ? '가입 중...' : '회원가입 완료' }}
                </button>
            </form>
            
            <p class="mt-4 text-center text-sm text-gray-600">
                이미 계정이 있으신가요? <router-link to="/login" class="text-indigo-600 hover:underline">로그인하기</router-link>
            </p>
        </div>
    </div>
</template>
