<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const centerCode = ref('');
const searchedCenter = ref(null);
const verificationCodeId = ref(null); // 검증된 코드 ID 저장용
const loading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const router = useRouter();

// 1. 기관 코드(일회용 코드) 검증
const verifyCode = async () => {
    loading.value = true;
    errorMsg.value = '';
    searchedCenter.value = null;
    verificationCodeId.value = null;
    successMsg.value = '';

    try {
        const response = await api.post('centers/verify-code/', { center_code: centerCode.value });
        if (response.data.valid) {
            searchedCenter.value = response.data.center;
            verificationCodeId.value = response.data.verification_code_id; // 저장
        }
    } catch (err) {
        console.error("[B2G] 코드 검증 에러:", err.response?.status, err.response?.data);

        if (err.response && err.response.data.error) {
            errorMsg.value = err.response.data.error;
        } else {
            errorMsg.value = '코드 확인 중 오류가 발생했습니다.';
        }
    } finally {
        loading.value = false;
    }
};

// 2. 연동 신청 (코드 사용 처리 포함)
const connectCenter = async () => {
    if (!searchedCenter.value) return;

    if (!confirm(`'${searchedCenter.value.name}'과 연동하시겠습니까?\n\n※ 연동 시 귀하의 감정 데이터 요약본이 담당자에게 공유됩니다.`)) {
        return;
    }

    try {
        await api.post('connect/request/', { 
            center_id: searchedCenter.value.id,
            verification_code_id: verificationCodeId.value // 함께 전송
        });
        alert('연동이 완료되었습니다!');
        router.push('/');
    } catch (err) {
        if (err.response?.status === 409) {
             alert('이미 연동된 기관입니다.');
             router.push('/');
        } else {
             alert('연동 요청 실패: ' + (err.response?.data?.error || '알 수 없는 오류'));
        }
    }
};
</script>

<template>
    <div class="flex min-h-screen flex-col items-center justify-center bg-yellow-200 p-6">
        <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h2 class="mb-6 text-center text-2xl font-bold text-gray-800">기관 연동 (Fix Version)</h2>
            <p class="mb-4 text-sm text-gray-600">
                담당자에게 전달받은 <strong>일회용 인증 코드</strong>를 입력해주세요.<br>
                (예: X7Y2Z9...)
            </p>

            <div class="flex gap-2">
                <input 
                    v-model="centerCode" 
                    type="text" 
                    placeholder="인증 코드 입력" 
                    class="flex-1 rounded border border-gray-300 p-2 uppercase focus:border-indigo-500 focus:ring-indigo-500"
                    @keyup.enter="verifyCode"
                />
                <button 
                    @click="verifyCode" 
                    :disabled="loading"
                    class="rounded bg-indigo-600 px-4 py-2 font-bold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                    코드 확인 (v2)
                </button>
            </div>

            <p v-if="errorMsg" class="mt-2 text-sm text-red-600">{{ errorMsg }}</p>

            <!-- 검색 결과 -->
            <div v-if="searchedCenter" class="mt-6 rounded border border-indigo-100 bg-indigo-50 p-4">
                <h3 class="font-bold text-indigo-900">{{ searchedCenter.name }}</h3>
                <p class="text-sm text-indigo-700">{{ searchedCenter.region }}</p>
                
                <div class="mt-4 border-t border-indigo-200 pt-3 text-xs text-gray-600">
                    <p class="mb-2">⚠️ 연동 시 <strong>위험 징후 데이터</strong>가 공유됩니다.</p>
                </div>

                <button 
                    @click="connectCenter"
                    class="mt-2 w-full rounded bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700"
                >
                    동의하고 연동하기
                </button>
            </div>
            
            <div class="mt-6 text-center">
                <button @click="router.push('/')" class="text-sm text-gray-500 hover:text-gray-700">돌아가기</button>
            </div>
        </div>
    </div>
</template>
