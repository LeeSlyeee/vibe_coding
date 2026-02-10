<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
// import api from '@/api'; // Remove api instance
import axios from 'axios'; // Use raw axios

const router = useRouter();
const patients = ref([]);
const loading = ref(true);
const errorMsg = ref(''); // ERROR STATE ADDED

const isFirstLoad = ref(true);

const fetchPatients = async () => {
    // 첫 로드 시에만 로딩 표시(스피너), 이후엔 백그라운드 갱신
    if (isFirstLoad.value) {
        loading.value = true;
    }
    errorMsg.value = '';
    
    try {
        const baseURL = import.meta.env.PROD ? '/api/v1/' : 'http://127.0.0.1:8000/api/v1/';
        const res = await axios.get(`${baseURL}diaries/staff/patients/`);
        
        // 데이터 변경 확인 (단순 문자열 비교)
        const newData = res.data;
        if (JSON.stringify(newData) !== JSON.stringify(patients.value)) {
            patients.value = newData;
        }
    } catch (err) {
        // 첫 로드 실패 시에만 에러 메시지 표시 (폴링 중 일시적 에러는 무시 가능)
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
                        type="text" 
                        placeholder="이름 또는 이메일 검색" 
                        class="w-full pl-12 pr-6 py-4 rounded-xl border border-slate-300 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 text-lg shadow-sm"
                    >
                    <span class="absolute left-4 top-4 text-slate-400 text-xl">🔍</span>
                 </div>
                 <div class="text-lg text-slate-500">
                     총 <span class="font-bold text-slate-900 text-xl">{{ patients.length }}</span>명 검색됨
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
                         <th class="px-8 py-6">관리</th>
                     </tr>
                 </thead>
                 <tbody class="divide-y divide-slate-100 text-base">
                     <tr 
                        v-for="patient in patients" 
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
                         <td class="px-8 py-6">
                             <button class="text-indigo-600 hover:text-indigo-900 font-bold text-base border border-indigo-200 bg-indigo-50 px-4 py-2 rounded-lg hover:bg-indigo-100 transition">
                                 상세보기
                             </button>
                         </td>
                     </tr>
                     <tr v-if="patients.length === 0">
                         <td colspan="7" class="px-8 py-16 text-center text-slate-400 text-lg">
                             등록된 환자가 없습니다.
                         </td>
                     </tr>
                 </tbody>
             </table>
        </div>
    </div>
</template>
