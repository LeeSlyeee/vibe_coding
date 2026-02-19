<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/api';
// import axios from 'axios';

import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement,
  Filler
} from 'chart.js'
import { Line, Doughnut } from 'vue-chartjs'

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, PointElement, LineElement, Filler)

const route = useRoute();
const router = useRouter();
const patient = ref(null);
const diaries = ref([]);
const loading = ref(true);

// Chart Options
const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
        y: { beginAtZero: true, max: 10, grid: { color: '#f3f4f6' } },
        x: { grid: { display: false } }
    }
};

const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: { legend: { position: 'right' } }
};

// Computed: 기분 흐름 차트 (최신 데이터 기준 7일)
const moodFlowData = computed(() => {
    if (!diaries.value || diaries.value.length === 0) {
        return { labels: [], datasets: [] };
    }

    // 접속일(오늘) 기준 과거 7일
    const today = new Date();
    
    const chartLabels = [];
    const chartData = [];

    for (let i = 6; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().split('T')[0];
        
        chartLabels.push(dateStr.slice(5).replace('-', '/'));

        // 해당 날짜의 일기들 (하루에 여러 개일 수 있음)
        const targetDiaries = diaries.value.filter(item => (item.date || item.created_at || '').startsWith(dateStr));
        
        if (targetDiaries.length > 0) {
            // 하루 평균 점수
            const sum = targetDiaries.reduce((acc, cur) => acc + (cur.mood_score || 0), 0);
            chartData.push(sum / targetDiaries.length);
        } else {
            chartData.push(null);
        }
    }

    return {
        labels: chartLabels,
        datasets: [{
            label: '기분 점수',
            data: chartData,
            borderColor: '#4F46E5',
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            tension: 0.4,
            fill: true,
            spanGaps: true 
        }]
    };
});

// Computed: 위험도 분포 차트
const riskDistData = computed(() => {
    if (!diaries.value || diaries.value.length === 0) {
        return {
             labels: ['안정', '주의', '위험'],
             datasets: [{ data: [0,0,0], backgroundColor: ['#10B981', '#FBBF24', '#EF4444'], borderWidth: 0 }]
        };
    }

    const dangerous = diaries.value.filter(d => (d.mood_score || 0) <= 2).length;
    const caution = diaries.value.filter(d => (d.mood_score || 0) === 3 || (d.mood_score || 0) === 4).length;
    const stable = diaries.value.filter(d => (d.mood_score || 0) >= 5).length;
    
    return {
        labels: ['안정', '주의', '위험'],
        datasets: [{
            data: [stable, caution, dangerous],
            backgroundColor: ['#10B981', '#FBBF24', '#EF4444'],
            borderWidth: 0,
            hoverOffset: 4
        }]
    };
});

// Insight AI State
const insightResult = ref("");
const isAnalyzing = ref(false);

const handleAnalyze = async () => {
    console.log("🖱️ [InsightAI] Button Clicked");
    
    if (isAnalyzing.value) {
        console.log("busy...");
        return;
    }
    
    isAnalyzing.value = true;
    try {
        const userId = route.params.id;

        // [Fix] Use api instance (Auto BaseURL & Auth)
        console.log(`📡 Sending POST to diaries/staff/patients/${userId}/`);
        
        const res = await api.post(`diaries/staff/patients/${userId}/`);
        console.log("✅ Response:", res.data);
        
        insightResult.value = res.data.result;
    } catch(err) {
        console.error("❌ Analysis Error:", err);
        alert(`분석 실패: ${err.message}`);
    } finally {
        isAnalyzing.value = false;
    }
};


const formatDate = (dateString, full = false) => {
    if (!dateString) return '-';
    // YYYY-MM-DD 형식인 경우 (date 필드) → 시간대 이슈 방지
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
        const [y, m, d] = dateString.split('-');
        return `${y}. ${parseInt(m)}. ${parseInt(d)}.`;
    }
    // ISO/datetime 형식 (created_at 필드)
    const dt = new Date(dateString);
    if (full) return dt.toLocaleString('ko-KR');
    return dt.toLocaleDateString('ko-KR');
};

const fetchPatientDetail = async () => {
    try {
        const userId = route.params.id;
        // [Fix] Use api instance (Auto BaseURL & Auth)
        const res = await api.get(`diaries/staff/patients/${userId}/`);
        console.log("🔍 [DEBUG] API Response:", res.data); // 디버깅용 로그
        
        patient.value = res.data.patient;
        console.log("🔍 [DEBUG] Patient Data:", patient.value); // 디버깅용 로그

        const rawDiaries = res.data.diaries || [];
        
        // 1. 데이터 정규화 (Normalize)
        const normalized = rawDiaries.map(d => {
            const ar = d.analysis_result || {};
            return {
                ...d,
                analysis_result: ar,
                display: {
                    weather: ar.weather || d.weather || '',
                    temperature: ar.temperature,
                    medication_taken: ar.medication_taken,
                    gratitude_note: ar.gratitude_note,
                    
                    sleep_condition: ar.sleep_condition || d.sleep_condition || '',
                    sleep_desc: ar.sleep_desc || d.sleep_desc || '',
                    self_talk: ar.self_talk || d.self_talk || '',
                    emotion_meaning: ar.emotion_meaning || d.emotion_meaning || '',
                    
                    ai_comment: ar.ai_comment || ar.comment || d.ai_comment || '',
                    ai_advice: ar.ai_advice || ar.advice || d.ai_advice || '',
                    ai_analysis: ar.ai_analysis || ar.analysis || d.ai_analysis || '',
                    ai_prediction: ar.ai_prediction || ar.prediction || d.ai_prediction || ''
                }
            };
        });

        // 2. 날짜별 중복 제거 (하루 1개 대표 일기 선정)
        const dailyMap = new Map();
        
        normalized.forEach(d => {
             // 날짜 키 추출 (YYYY-MM-DD, Local Time)
             // [Fix] UTC 문자열을 로컬 시간으로 변환하여 날짜 충돌 방지
             const dateObj = d.date ? new Date(d.date + 'T00:00:00') : new Date(d.created_at);
             const year = dateObj.getFullYear();
             const month = String(dateObj.getMonth() + 1).padStart(2, '0');
             const day = String(dateObj.getDate()).padStart(2, '0');
             const dateKey = `${year}-${month}-${day}`;
             
             if (!dailyMap.has(dateKey)) {
                 dailyMap.set(dateKey, d);
             } else {
                 const existing = dailyMap.get(dateKey);
                 
                 // [선정 기준] 
                 // 1순위: 데이터 풍부도 (날씨나 AI 코멘트가 있는 걸 우선)
                 const getScore = (item) => (item.display.weather ? 10 : 0) + (item.display.ai_comment ? 5 : 0);
                 
                 const existingScore = getScore(existing);
                 const newScore = getScore(d);
                 
                 if (newScore > existingScore) {
                     dailyMap.set(dateKey, d);
                 } else if (newScore === existingScore) {
                     // 2순위: 동점이면 최신 작성일 기준
                     if (new Date(d.created_at || d.date) > new Date(existing.created_at || existing.date)) {
                         dailyMap.set(dateKey, d);
                     }
                 }
             }
        });

        // 3. 날짜 내림차순 정렬하여 적용
        diaries.value = Array.from(dailyMap.values())
             .sort((a, b) => new Date(b.date || b.created_at) - new Date(a.date || a.created_at));
        
    } catch (err) {
        console.error(err);
        alert('환자 정보를 불러오는데 실패했습니다.');
        router.push('/admin/patients');
    } finally {
        loading.value = false;
    }
};

let intervalId = null;
import { onUnmounted } from 'vue';

onMounted(() => {
    fetchPatientDetail();
    // 5초마다 데이터 갱신 (실시간 모니터링)
    intervalId = setInterval(fetchPatientDetail, 5000);
});

onUnmounted(() => {
    if (intervalId) clearInterval(intervalId);
});


</script>

<template>
    <div class="min-h-screen bg-slate-50 p-6 font-sans">
        <!-- 헤더 & 뒤로가기 -->
        <header class="mb-10 flex items-center justify-between">
             <div class="flex items-center gap-6">
                <button @click="router.back()" class="flex items-center text-slate-500 hover:text-slate-800 transition font-bold bg-white px-5 py-2.5 rounded-xl border border-slate-200 text-lg">
                    <span class="mr-2 text-xl">←</span> 뒤로가기
                </button>
                <h1 class="text-4xl font-extrabold text-slate-800 tracking-tight">환자 상세 대시보드</h1>
             </div>
             <div class="text-lg text-slate-500 text-right">
                <div class="text-sm text-slate-400">Patient ID</div>
                <div class="font-mono font-bold text-xl">{{ route.params.id }}</div>
             </div>
        </header>

        <div v-if="loading" class="text-center py-20">
            <div class="text-slate-400 animate-pulse">데이터 로딩 및 분석 중...</div>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- 좌측: 환자 프로필 (1칸) -->
            <div class="col-span-1 space-y-8">
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                    <div class="flex flex-col items-center text-center mb-8">
                         <div class="w-28 h-28 rounded-full bg-indigo-50 border-4 border-indigo-100 flex items-center justify-center text-5xl mb-4 shadow-inner">
                            👤
                         </div>
                         <h2 class="text-3xl font-extrabold text-slate-800 mb-1">{{ patient?.name || '실명없음' }}</h2>
                         <p class="text-sm text-slate-400 font-mono bg-slate-50 px-3 py-1 rounded mb-2">({{ patient?.username }})</p>
                         <p class="text-base text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full mt-2 font-medium">{{ patient?.email }}</p>
                    </div>
                    
                    <div class="space-y-6 text-base border-t border-slate-50 pt-6">
                        <div class="flex justify-between items-center">
                            <span class="text-slate-500">등록일</span>
                            <span class="font-bold text-slate-700">{{ formatDate(patient?.joined_at) }}</span>
                        </div>
                        <div class="flex justify-between items-center bg-slate-50 p-4 rounded-xl">
                            <span class="text-slate-500">총 기록</span>
                            <span class="font-extrabold text-indigo-600 text-lg">{{ diaries.length }}개</span>
                        </div>
                         <div class="flex justify-between items-center bg-red-50 p-4 rounded-xl">
                            <span class="text-red-500 font-bold">위험 감지</span>
                            <span class="font-extrabold text-red-600 text-lg">
                                {{ diaries.filter(d => (d.mood_score || 0) <= 2).length }}회
                            </span>
                        </div>
                    </div>
                </div>

                <!-- AI 요약 카드 -->
                 <!-- AI 요약 카드 (Clean Style) -->
                 <div class="bg-white p-8 rounded-3xl shadow-sm border border-indigo-100">
                    <h3 class="font-bold mb-6 flex items-center gap-3 text-indigo-900 text-xl">
                        <span>🔮 Insight AI</span>
                        <span class="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded border border-indigo-200 font-bold">BETA</span>
                    </h3>
                    
                    <div v-if="insightResult" class="bg-indigo-50/50 p-5 rounded-xl mb-6 text-base text-slate-700 leading-relaxed animate-fade-in border border-indigo-100 shadow-sm" style="white-space: pre-wrap;">{{ insightResult }}</div>
                    <p v-else class="text-slate-500 text-sm leading-relaxed mb-6">
                        최근 일기 데이터를 기반으로 환자의 감정 상태와 위험 징후를 심층 분석합니다.
                    </p>

                    <button 
                        type="button"
                        @click.prevent="handleAnalyze" 
                        :disabled="isAnalyzing"
                        class="w-full py-4 px-6 rounded-xl text-base font-bold transition flex items-center justify-center gap-3
                               disabled:opacity-50 disabled:cursor-not-allowed
                               bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg active:scale-[0.98]">
                        <span v-if="isAnalyzing" class="animate-pulse">🧠 분석 중...</span>
                        <span v-else>📑 상세 분석 리포트 생성</span>
                    </button>
                 </div>
            </div>

            <!-- 우측: 대시보드 및 타임라인 (3칸) -->
            <div class="col-span-3 space-y-8">
                
                <!-- 개인화 차트 영역 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- 1. 기분 변화 추이 -->
                    <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                        <h3 class="text-lg font-bold text-slate-700 mb-6 flex items-center">
                            📉 최근 기분 변화 추이
                            <span class="ml-2 text-xs text-slate-400 font-normal bg-slate-100 px-2 py-0.5 rounded-full">(데이터 기준 7일)</span>
                        </h3>
                        <div class="h-64">
                            <Line :data="moodFlowData" :options="lineChartOptions" />
                        </div>
                    </div>

                    <!-- 2. 감정 상태 분포 -->
                    <div class="bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                        <h3 class="text-lg font-bold text-slate-700 mb-6">🚨 감정 상태 분포</h3>
                        <div class="h-64 relative flex items-center justify-center">
                            <Doughnut :data="riskDistData" :options="doughnutOptions" />
                        </div>
                    </div>
                </div>

                <!-- 일기 타임라인 -->
                <div class="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    <div class="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                        <h3 class="text-xl font-bold text-slate-800">📄 일기 기록 히스토리</h3>
                        <span class="text-sm text-slate-500 font-medium">최신순 정렬</span>
                    </div>
                    
                    <div class="divide-y divide-slate-100">
                        <div v-for="diary in diaries" :key="diary.id" class="p-8 hover:bg-slate-50 transition">
                            <div class="flex justify-between items-start mb-4">
                                <div class="flex items-center gap-4">
                                    <span class="text-base font-bold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg">
                                        {{ formatDate(diary.date || diary.created_at) }}
                                        <span v-if="diary.created_at" class="text-xs text-slate-400 ml-1">({{ new Date(diary.created_at + (diary.created_at.endsWith('Z') ? '' : 'Z')).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) }} 작성)</span>
                                    </span>
                                    <span v-if="(diary.mood_score || 0) <= 2" class="bg-red-100 text-red-700 text-xs px-3 py-1.5 rounded-full font-bold">⚠️ 위험</span>
                                    <span v-else-if="(diary.mood_score || 0) <= 4" class="bg-yellow-100 text-yellow-700 text-xs px-3 py-1.5 rounded-full font-bold">주의</span>
                                </div>
                                <div class="flex items-center gap-2">
                                     <span class="text-sm text-slate-400 font-medium">기분 점수</span>
                                     <span class="font-extrabold text-3xl" :class="(diary.mood_score || 0) <= 3 ? 'text-red-500' : 'text-indigo-600'">
                                        {{ diary.mood_score }}
                                    </span>
                                     <span class="text-sm text-slate-300 font-bold">/ 10</span>
                                </div>
                            </div>

                            <!-- 1. 메타 데이터 (날씨, 약물, 감사노트 등) -->
                            <div class="flex flex-wrap gap-3 mb-4 text-sm text-slate-600 font-medium">
                                <span v-if="diary.display.weather" class="bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg border border-blue-100">
                                    🌤️ {{ diary.display.weather }}
                                    <span v-if="diary.display.temperature">({{ diary.display.temperature }})</span>
                                </span>
                                <span v-if="diary.display.medication_taken" class="bg-green-50 text-green-700 px-3 py-1.5 rounded-lg border border-green-100">💊 약물 복용함</span>
                                <span v-if="diary.display.gratitude_note" class="bg-yellow-50 text-yellow-800 px-3 py-1.5 rounded-lg border border-yellow-100">🙏 감사: {{ diary.display.gratitude_note }}</span>
                            </div>

                            <!-- 2. 일기 본문 -->
                            <p class="text-slate-800 text-lg leading-relaxed mb-6 whitespace-pre-wrap font-book bg-slate-50/50 p-4 rounded-xl border border-slate-100/50">{{ diary.content }}</p>

                            <!-- 3. 추가 심리 데이터 (수면, 혼잣말, 감정) -->
                            <div v-if="diary.display.sleep_condition || diary.display.self_talk || diary.display.emotion_meaning" class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div v-if="diary.display.sleep_condition" class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                    <h5 class="text-sm font-bold text-slate-600 mb-1">💤 수면 상태</h5>
                                    <p class="text-base text-slate-800">{{ diary.display.sleep_condition }}</p>
                                    <p v-if="diary.display.sleep_desc" class="text-xs text-slate-400 mt-2">{{ diary.display.sleep_desc }}</p>
                                </div>
                                <div v-if="diary.display.self_talk" class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                    <h5 class="text-sm font-bold text-slate-600 mb-1">🗣️ 나에게 한마디</h5>
                                    <p class="text-base text-slate-800">{{ diary.display.self_talk }}</p>
                                </div>
                                <div v-if="diary.display.emotion_meaning" class="col-span-1 md:col-span-2 bg-slate-50 p-4 rounded-xl border border-slate-100">
                                    <h5 class="text-sm font-bold text-slate-600 mb-1">❤️ 감정의 의미</h5>
                                    <p class="text-base text-slate-800">{{ diary.display.emotion_meaning }}</p>
                                </div>
                            </div>

                            <!-- 4. AI 분석 결과 Box -->
                            <div v-if="diary.display.ai_comment || diary.display.ai_analysis">
                                <div class="bg-indigo-50/60 rounded-xl p-6 text-base border border-indigo-100 flex flex-col gap-4 shadow-sm">
                                    <!-- Comment -->
                                    <div v-if="diary.display.ai_comment">
                                        <h4 class="text-indigo-800 font-bold text-sm mb-2 flex items-center gap-2">
                                            <span>🤖 AI 코멘트</span>
                                        </h4>
                                        <p class="text-slate-700 text-base leading-relaxed">
                                            {{ diary.display.ai_comment }}
                                        </p>
                                    </div>
                                    
                                    <!-- Advice -->
                                    <div v-if="diary.display.ai_advice" class="pl-4 border-l-4 border-green-200 mt-2">
                                        <h4 class="text-green-800 font-bold text-sm mb-1">🍃 맞춤 조언</h4>
                                        <p class="text-slate-700 text-base leading-relaxed">
                                            {{ diary.display.ai_advice }}
                                        </p>
                                    </div>
                                    
                                    <!-- Analysis -->
                                    <div v-if="diary.display.ai_analysis" class="pl-4 border-l-4 border-blue-200 mt-2">
                                        <h4 class="text-blue-800 font-bold text-sm mb-1">📊 심층 분석</h4>
                                        <p class="text-slate-700 text-base leading-relaxed">
                                            {{ diary.display.ai_analysis }}
                                        </p>
                                    </div>
                                    
                                    <!-- Prediction -->
                                    <div v-if="diary.display.ai_prediction" class="pl-4 border-l-4 border-purple-200 mt-2">
                                        <h4 class="text-purple-800 font-bold text-sm mb-1">🔮 감정 예측</h4>
                                        <p class="text-slate-700 text-base leading-relaxed">
                                            {{ diary.display.ai_prediction }}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-if="diaries.length === 0" class="text-center py-12 text-slate-400">
                            기록된 일기가 없습니다.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
