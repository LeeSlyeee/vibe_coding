<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const router = useRouter();
const patients = ref([]);
const loading = ref(true);
const errorMsg = ref('');
const searchQuery = ref('');

const isFirstLoad = ref(true);

// ====== 삭제 관련 상태 ======
const deleteModal = ref({
    show: false,
    step: 1, // 1: 경고, 2: 확인 정보, 3: 최종 확인 (이름 입력)
    patient: null,
    confirmInfo: null, // 서버로부터 받은 확인 정보
    typedUsername: '', // 최종 확인용 이름 입력
    loading: false,
    error: '',
    success: '',
});

// 검색 필터링
const filteredPatients = computed(() => {
    if (!searchQuery.value.trim()) return patients.value;
    const q = searchQuery.value.toLowerCase().trim();
    return patients.value.filter(p =>
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.username && p.username.toLowerCase().includes(q)) ||
        (p.email && p.email.toLowerCase().includes(q))
    );
});

const fetchPatients = async () => {
    if (isFirstLoad.value) {
        loading.value = true;
    }
    errorMsg.value = '';
    
    try {
        const res = await api.get('diaries/staff/patients/');
        const newData = res.data;
        if (JSON.stringify(newData) !== JSON.stringify(patients.value)) {
            patients.value = newData;
        }
    } catch (err) {
        if (isFirstLoad.value) {
            console.error("환자 목록 로드 실패:", err);
            errorMsg.value = `데이터 로드 실패: ${err.message}`;
            if (err.response) {
                 errorMsg.value += ` (${err.response.status})`;
            }
        }
    } finally {
        loading.value = false;
        isFirstLoad.value = false;
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
};

const goToDetail = (userId) => {
    router.push(`/admin/patients/${userId}`);
};

// ====== 삭제 로직 ======

// Step 1: 삭제 버튼 클릭 → 경고 모달 표시
const openDeleteModal = (patient, event) => {
    event.stopPropagation(); // 행 클릭(상세보기) 이벤트 전파 방지
    deleteModal.value = {
        show: true,
        step: 1,
        patient: { ...patient },
        confirmInfo: null,
        typedUsername: '',
        loading: false,
        error: '',
        success: '',
    };
};

// Step 2: 1차 경고 확인 → 서버에 삭제 전 확인 정보 요청
const proceedToStep2 = async () => {
    deleteModal.value.loading = true;
    deleteModal.value.error = '';
    try {
        const res = await api.post(`diaries/staff/patients/${deleteModal.value.patient.username}/delete/`);
        deleteModal.value.confirmInfo = res.data;
        deleteModal.value.step = 2;
    } catch (err) {
        deleteModal.value.error = err.response?.data?.error || '확인 정보를 가져오는데 실패했습니다.';
    } finally {
        deleteModal.value.loading = false;
    }
};

// Step 3: 2차 확인 → 최종 사용자 이름 입력 단계 진입
const proceedToStep3 = () => {
    deleteModal.value.step = 3;
    deleteModal.value.typedUsername = '';
};

// Final: 최종 삭제 실행
const executeDelete = async () => {
    const modal = deleteModal.value;
    if (modal.typedUsername !== modal.patient.username) {
        modal.error = '입력한 사용자 ID가 일치하지 않습니다.';
        return;
    }
    
    modal.loading = true;
    modal.error = '';
    try {
        const res = await api.delete(`diaries/staff/patients/${modal.patient.username}/delete/`, {
            data: {
                confirm_code: modal.confirmInfo.confirm_code,
                confirm_timestamp: modal.confirmInfo.confirm_timestamp,
                confirmed_username: modal.typedUsername,
            }
        });
        modal.success = res.data.message;
        modal.step = 4; // 완료 단계
        // 목록에서 제거
        patients.value = patients.value.filter(p => p.username !== modal.patient.username);
    } catch (err) {
        modal.error = err.response?.data?.error || '삭제에 실패했습니다.';
        if (err.response?.data?.detail) {
            modal.error += ` ${err.response.data.detail}`;
        }
    } finally {
        modal.loading = false;
    }
};

const closeDeleteModal = () => {
    deleteModal.value.show = false;
};

let intervalId = null;

onMounted(() => {
    fetchPatients();
    intervalId = setInterval(fetchPatients, 5000);
});

onUnmounted(() => {
    if (intervalId) clearInterval(intervalId);
});
</script>

<template>
    <div class="min-h-screen bg-slate-50 p-6 font-sans">
        <header class="mb-10 flex items-center gap-6">
             <button @click="router.push('/admin/dashboard')" class="flex items-center text-slate-500 hover:text-slate-800 transition text-lg">
                <span class="mr-2 text-xl">←</span> 대시보드
            </button>
            <h1 class="text-4xl font-extrabold text-slate-800 tracking-tight">등록된 환자 목록</h1>
        </header>

        <div class="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
             <div class="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                 <div class="relative w-96">
                    <input 
                        v-model="searchQuery"
                        type="text" 
                        placeholder="이름 또는 이메일 검색" 
                        class="w-full pl-12 pr-6 py-4 rounded-xl border border-slate-300 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 text-lg shadow-sm"
                    >
                    <span class="absolute left-4 top-4 text-slate-400 text-xl">🔍</span>
                 </div>
                 <div class="text-lg text-slate-500">
                     총 <span class="font-bold text-slate-900 text-xl">{{ filteredPatients.length }}</span>명 검색됨
                 </div>
             </div>

             <div v-if="errorMsg" class="p-6 bg-red-50 border-b border-red-100 text-center">
                 <p class="text-red-600 font-bold mb-1">⚠️ 오류 발생</p>
                 <p class="text-red-500 text-sm">{{ errorMsg }}</p>
             </div>

             <div v-if="loading" class="p-20 text-center">
                 <div class="spinner border-4 border-slate-200 border-t-indigo-600 rounded-full w-12 h-12 mx-auto animate-spin"></div>
                 <p class="mt-4 text-slate-500">데이터를 불러오고 있습니다...</p>
             </div>

             <table v-else class="w-full text-left border-collapse">
                 <thead class="bg-slate-50 text-slate-500 text-sm uppercase font-semibold">
                     <tr>
                         <th class="px-8 py-6">환자명 (ID)</th>
                         <th class="px-8 py-6">이메일</th>
                         <th class="px-8 py-6">등록일</th>
                         <th class="px-8 py-6 text-center">총 일기</th>
                         <th class="px-8 py-6 text-center">위험 감지</th>
                         <th class="px-8 py-6 text-center">상태</th>
                         <th class="px-8 py-6 text-center">관리</th>
                     </tr>
                 </thead>
                 <tbody class="divide-y divide-slate-100 text-base">
                     <tr 
                        v-for="patient in filteredPatients" 
                        :key="patient.id" 
                        class="hover:bg-indigo-50/30 transition cursor-pointer"
                        @click="goToDetail(patient.id)"
                    >
                          <td class="px-8 py-6">
                             <div class="flex flex-col">
                                 <span class="font-bold text-slate-800 text-lg">{{ patient.name || '실명없음' }}</span>
                                 <span class="text-sm text-slate-400 font-mono">({{ patient.username }})</span>
                             </div>
                          </td>
                         <td class="px-8 py-6 text-slate-600">{{ patient.email }}</td>
                         <td class="px-8 py-6 text-slate-500">{{ formatDate(patient.joined_at) }}</td>
                         <td class="px-8 py-6 text-center font-medium">{{ patient.diary_count }}</td>
                         <td class="px-8 py-6 text-center">
                             <span v-if="patient.risk_count > 0" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-red-100 text-red-800">
                                 {{ patient.risk_count }}회
                             </span>
                             <span v-else class="text-slate-400">-</span>
                         </td>
                         <td class="px-8 py-6 text-center">
                             <span class="bg-green-100 text-green-800 text-sm px-3 py-1 rounded-full font-bold">활동중</span>
                         </td>
                         <td class="px-8 py-6 text-center">
                             <div class="flex items-center justify-center gap-2">
                                 <button 
                                     class="text-indigo-600 hover:text-indigo-900 font-bold text-sm border border-indigo-200 bg-indigo-50 px-3 py-2 rounded-lg hover:bg-indigo-100 transition"
                                 >
                                     상세보기
                                 </button>
                                 <button 
                                     @click="openDeleteModal(patient, $event)"
                                     class="text-red-500 hover:text-red-700 font-bold text-sm border border-red-200 bg-red-50 px-3 py-2 rounded-lg hover:bg-red-100 transition"
                                 >
                                     삭제
                                 </button>
                             </div>
                         </td>
                     </tr>
                     <tr v-if="filteredPatients.length === 0">
                         <td colspan="7" class="px-8 py-16 text-center text-slate-400 text-lg">
                             등록된 환자가 없습니다.
                         </td>
                     </tr>
                 </tbody>
             </table>
        </div>

        <!-- ====== 삭제 확인 모달 (3단계) ====== -->
        <Teleport to="body">
            <div v-if="deleteModal.show" class="fixed inset-0 z-50 flex items-center justify-center">
                <!-- 오버레이 (배경) -->
                <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="deleteModal.step < 4 ? null : closeDeleteModal()"></div>
                
                <!-- 모달 본체 -->
                <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-modal-in">
                    
                    <!-- ===== Step 1: 경고 ===== -->
                    <div v-if="deleteModal.step === 1">
                        <div class="bg-red-50 px-8 pt-8 pb-6 text-center border-b border-red-100">
                            <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                                <span class="text-3xl">⚠️</span>
                            </div>
                            <h2 class="text-2xl font-bold text-red-800">환자 삭제 경고</h2>
                            <p class="mt-2 text-red-600 text-sm">이 작업은 되돌릴 수 없습니다</p>
                        </div>
                        <div class="px-8 py-6">
                            <div class="bg-slate-50 rounded-xl p-5 mb-6">
                                <div class="flex items-center gap-3 mb-3">
                                    <div class="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center font-bold text-slate-600">
                                        {{ (deleteModal.patient?.name || '?')[0] }}
                                    </div>
                                    <div>
                                        <p class="font-bold text-slate-800 text-lg">{{ deleteModal.patient?.name || '이름없음' }}</p>
                                        <p class="text-sm text-slate-400 font-mono">{{ deleteModal.patient?.username }}</p>
                                    </div>
                                </div>
                                <div class="flex gap-4 text-sm text-slate-500 mt-2">
                                    <span>📝 일기 <strong class="text-slate-700">{{ deleteModal.patient?.diary_count || 0 }}건</strong></span>
                                    <span v-if="deleteModal.patient?.risk_count > 0">🚨 위험감지 <strong class="text-red-600">{{ deleteModal.patient?.risk_count }}회</strong></span>
                                </div>
                            </div>
                            <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                                <p class="text-amber-800 text-sm font-medium">
                                    ⚠️ 삭제 시 해당 환자의 <strong>모든 일기 데이터, 감정 분석 결과, 위험 감지 기록</strong>이 영구적으로 삭제됩니다. 이 작업은 복구가 불가능합니다.
                                </p>
                            </div>
                            <div class="flex gap-3">
                                <button 
                                    @click="closeDeleteModal"
                                    class="flex-1 py-3 px-4 border border-slate-300 rounded-xl text-slate-600 font-semibold hover:bg-slate-50 transition"
                                >
                                    취소
                                </button>
                                <button 
                                    @click="proceedToStep2"
                                    :disabled="deleteModal.loading"
                                    class="flex-1 py-3 px-4 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition disabled:opacity-50"
                                >
                                    <span v-if="deleteModal.loading">확인 중...</span>
                                    <span v-else>삭제 진행</span>
                                </button>
                            </div>
                            <p v-if="deleteModal.error" class="mt-3 text-red-500 text-sm text-center">{{ deleteModal.error }}</p>
                        </div>
                    </div>

                    <!-- ===== Step 2: 서버 확인 정보 ===== -->
                    <div v-if="deleteModal.step === 2">
                        <div class="bg-orange-50 px-8 pt-8 pb-6 text-center border-b border-orange-100">
                            <div class="w-16 h-16 mx-auto mb-4 bg-orange-100 rounded-full flex items-center justify-center">
                                <span class="text-3xl">🔍</span>
                            </div>
                            <h2 class="text-2xl font-bold text-orange-800">삭제 대상 확인</h2>
                            <p class="mt-2 text-orange-600 text-sm">아래 정보를 정확히 확인해주세요</p>
                        </div>
                        <div class="px-8 py-6">
                            <div class="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100 mb-6">
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">환자명</span>
                                    <span class="font-bold text-slate-800">{{ deleteModal.confirmInfo?.patient?.name }}</span>
                                </div>
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">사용자 ID</span>
                                    <span class="font-bold text-slate-800 font-mono">{{ deleteModal.confirmInfo?.patient?.username }}</span>
                                </div>
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">센터 코드</span>
                                    <span class="font-bold text-slate-800">{{ deleteModal.confirmInfo?.patient?.center_code || '없음' }}</span>
                                </div>
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">가입일</span>
                                    <span class="font-bold text-slate-800">{{ formatDate(deleteModal.confirmInfo?.patient?.created_at) }}</span>
                                </div>
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">총 일기 수</span>
                                    <span class="font-bold text-red-600">{{ deleteModal.confirmInfo?.diary_count }}건 영구 삭제</span>
                                </div>
                                <div class="flex justify-between px-5 py-3">
                                    <span class="text-slate-500">위험 감지 기록</span>
                                    <span class="font-bold" :class="deleteModal.confirmInfo?.risk_count > 0 ? 'text-red-600' : 'text-slate-800'">
                                        {{ deleteModal.confirmInfo?.risk_count }}건
                                    </span>
                                </div>
                            </div>
                            <div class="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                                <p class="text-red-700 text-sm font-medium">
                                    🚨 {{ deleteModal.confirmInfo?.warning }}
                                </p>
                            </div>
                            <div class="flex gap-3">
                                <button 
                                    @click="deleteModal.step = 1"
                                    class="flex-1 py-3 px-4 border border-slate-300 rounded-xl text-slate-600 font-semibold hover:bg-slate-50 transition"
                                >
                                    이전으로
                                </button>
                                <button 
                                    @click="proceedToStep3"
                                    class="flex-1 py-3 px-4 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition"
                                >
                                    최종 확인으로
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- ===== Step 3: 최종 확인 (이름 직접 입력) ===== -->
                    <div v-if="deleteModal.step === 3">
                        <div class="bg-red-600 px-8 pt-8 pb-6 text-center">
                            <div class="w-16 h-16 mx-auto mb-4 bg-red-500 rounded-full flex items-center justify-center">
                                <span class="text-3xl">🗑️</span>
                            </div>
                            <h2 class="text-2xl font-bold text-white">최종 삭제 확인</h2>
                            <p class="mt-2 text-red-200 text-sm">삭제를 확정하려면 사용자 ID를 정확히 입력하세요</p>
                        </div>
                        <div class="px-8 py-6">
                            <div class="mb-6">
                                <label class="block text-sm font-semibold text-slate-700 mb-2">
                                    아래에 <span class="font-mono bg-red-100 text-red-700 px-2 py-0.5 rounded">{{ deleteModal.patient?.username }}</span> 를 정확히 입력하세요
                                </label>
                                <input 
                                    v-model="deleteModal.typedUsername"
                                    type="text"
                                    :placeholder="deleteModal.patient?.username"
                                    class="w-full px-4 py-3 border-2 rounded-xl text-lg font-mono focus:outline-none transition"
                                    :class="deleteModal.typedUsername === deleteModal.patient?.username 
                                        ? 'border-red-500 bg-red-50 text-red-700 focus:ring-2 focus:ring-red-500' 
                                        : 'border-slate-300 focus:border-slate-400'"
                                    autocomplete="off"
                                    spellcheck="false"
                                >
                            </div>
                            <p v-if="deleteModal.error" class="mb-4 text-red-500 text-sm text-center font-medium">❌ {{ deleteModal.error }}</p>
                            <div class="flex gap-3">
                                <button 
                                    @click="deleteModal.step = 2; deleteModal.error = ''"
                                    class="flex-1 py-3 px-4 border border-slate-300 rounded-xl text-slate-600 font-semibold hover:bg-slate-50 transition"
                                >
                                    이전으로
                                </button>
                                <button 
                                    @click="executeDelete"
                                    :disabled="deleteModal.typedUsername !== deleteModal.patient?.username || deleteModal.loading"
                                    class="flex-1 py-3 px-4 rounded-xl font-semibold transition"
                                    :class="deleteModal.typedUsername === deleteModal.patient?.username && !deleteModal.loading
                                        ? 'bg-red-600 text-white hover:bg-red-700 cursor-pointer'
                                        : 'bg-slate-200 text-slate-400 cursor-not-allowed'"
                                >
                                    <span v-if="deleteModal.loading">삭제 처리 중...</span>
                                    <span v-else>영구 삭제 실행</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- ===== Step 4: 삭제 완료 ===== -->
                    <div v-if="deleteModal.step === 4">
                        <div class="bg-green-50 px-8 pt-8 pb-6 text-center border-b border-green-100">
                            <div class="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                                <span class="text-3xl">✅</span>
                            </div>
                            <h2 class="text-2xl font-bold text-green-800">삭제 완료</h2>
                        </div>
                        <div class="px-8 py-6">
                            <p class="text-center text-slate-700 mb-6">{{ deleteModal.success }}</p>
                            <button 
                                @click="closeDeleteModal"
                                class="w-full py-3 px-4 bg-slate-800 text-white rounded-xl font-semibold hover:bg-slate-900 transition"
                            >
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<style scoped>
@keyframes modal-in {
    from {
        opacity: 0;
        transform: scale(0.95) translateY(10px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}
.animate-modal-in {
    animation: modal-in 0.2s ease-out;
}
</style>
