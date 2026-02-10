<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// import api from '@/api'; // 토큰 문제 방지를 위해 axios 직접 사용
import axios from 'axios';

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

    // [Fix] 기준일을 '오늘'이 아니라 '가장 최근 일기 작성일'로 설정
    // diaries는 이미 최신순(내림차순) 정렬되어 있으므로 첫 번째 요소가 가장 최근
    const latestDiary = diaries.value[0];
    const anchorDate = latestDiary ? new Date(latestDiary.created_at) : new Date();
    
    const chartLabels = [];
    const chartData = [];

    // anchorDate 기준으로 과거 7일 생성 (6, 5, ..., 0)
    for (let i = 6; i >= 0; i--) {
        const d = new Date(anchorDate);
        d.setDate(d.getDate() - i);
        
        // 날짜 비교를 위해 YYYY-MM-DD 형식 생성 (로컬 시간 기준)
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const dateComp = `${y}-${m}-${day}`;
        
        chartLabels.push(`${m}/${day}`);

        // 해당 날짜의 일기들 필터링
        const targetDiaries = diaries.value.filter(item => {
            const itemDate = new Date(item.created_at);
            const itemY = itemDate.getFullYear();
            const itemM = String(itemDate.getMonth() + 1).padStart(2, '0');
            const itemD = String(itemDate.getDate()).padStart(2, '0');
            return `${itemY}-${itemM}-${itemD}` === dateComp;
        });
        
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
        // [Fix] SSL 적용 완료! HTTPS 사용
        const baseURL = 'https://150.230.7.76.nip.io/api/v1/';
        // DetailView now supports POST for analysis
        console.log(`📡 Sending POST to ${baseURL}diaries/staff/patients/${userId}/`);
        
        const res = await axios.post(`${baseURL}diaries/staff/patients/${userId}/`);
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
    // OCI 데이터 등 시간대 보정을 위해 Date 객체 생성
    const d = new Date(dateString);
    if(full) return d.toLocaleString();
    return d.toLocaleDateString();
};

// [Helper] Parse monolithic content string into sections
const parseContent = (content) => {
    const result = {
        sleep: '',
        event: '',
        emotion: '',
        meaning: '',
        selftalk: ''
    };
    
    if (!content) return result;

    const sections = [
        { key: 'sleep', header: '[잠은 잘 주무셨나요?]' },
        { key: 'event', header: '[오늘 무슨일이 있었나요?]' },
        { key: 'emotion', header: '[어떤 감정이 들었나요?]' },
        { key: 'meaning', header: '[자신의 감정을 깊게 탐색해보면...]' },
        { key: 'selftalk', header: '[나에게 보내는 따뜻한 위로]' }
    ];

    let currentKey = 'event'; // Default for unstructured text
    let tempText = content;

    // Split by headers if present
    // Strategy: Search for headers and slice text between them
    
    // Sort sections by their position in text to handle out-of-order
    const foundSections = sections.map(s => ({ ...s, index: content.indexOf(s.header) }))
                                  .filter(s => s.index !== -1)
                                  .sort((a, b) => a.index - b.index);

    if (foundSections.length === 0) {
        result.event = content; // No headers found, treat all as event/content
        return result;
    }

    for (let i = 0; i < foundSections.length; i++) {
        const current = foundSections[i];
        const next = foundSections[i+1];
        
        const start = current.index + current.header.length;
        const end = next ? next.index : content.length;
        
        result[current.key] = content.slice(start, end).trim();
    }
    
    return result;
}

const fetchPatientDetail = async () => {
    try {
        const userId = route.params.id;
        // [Fix] SSL 적용 완료! HTTPS 사용
        const baseURL = 'https://150.230.7.76.nip.io/api/v1/';
        const res = await axios.get(`${baseURL}diaries/staff/patients/${userId}/`);
        console.log("🔍 [DEBUG] API Response:", res.data); // 디버깅용 로그
        
        patient.value = res.data.patient;
        console.log("🔍 [DEBUG] Patient Data:", patient.value); // 디버깅용 로그

        const rawDiaries = res.data.diaries || [];
        
        // 1. 데이터 정규화 (Normalize)
        const normalized = rawDiaries.map(d => {
            const ar = d.analysis_result || {};
            
            // [Fix] Content Parsing Logic
            // If fields are missing in AR/DB, try parsing from RAW content
            const parsed = parseContent(d.content);
            
            return {
                ...d,
                analysis_result: ar,
                display: {
                    weather: ar.weather || d.weather || '',
                    temperature: ar.temperature,
                    medication_taken: ar.medication_taken,
                    gratitude_note: ar.gratitude_note,
                    
                    // [5 Core Questions Mapping]
                    // Prioritize Structured Data -> Then Parsed Data
                    sleep_condition: ar.sleep_condition || d.sleep_condition || parsed.sleep || '',
                    sleep_desc: ar.sleep_desc || d.sleep_desc || '',
                    
                    event: ar.event || parsed.event || d.content || '',
                    
                    emotion_desc: ar.emotion_desc || ar.emotion || d.emotion || parsed.emotion || '',
                    
                    emotion_meaning: ar.emotion_meaning || d.emotion_meaning || parsed.meaning || '',
                    
                    self_talk: ar.self_talk || d.self_talk || parsed.selftalk || '',
                    
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
             // 날짜 키 추출 (YYYY-MM-DD)
             const dateKey = d.created_at.split('T')[0];
             
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
                     if (new Date(d.created_at) > new Date(existing.created_at)) {
                         dailyMap.set(dateKey, d);
                     }
                 }
             }
        });

        // 3. 날짜 내림차순 정렬하여 적용
        diaries.value = Array.from(dailyMap.values())
             .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
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

                <!-- Insight AI Card -->
                <div class="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-3xl p-8 text-white shadow-lg overflow-hidden relative group">
                     <div class="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-xl group-hover:bg-white/20 transition duration-700"></div>
                     
                     <div class="relative z-10">
                        <h3 class="text-2xl font-bold mb-2 flex items-center gap-2">
                            ✨ Insight AI
                        </h3>
                        <p class="text-indigo-100 text-sm mb-6 leading-relaxed">
                            이 환자의 전체 기록을 분석하여<br>숨겨진 심리 패턴을 발견합니다.
                        </p>
                        
                        <div v-if="insightResult" class="bg-white/10 backdrop-blur-md rounded-xl p-4 mb-4 border border-white/20 text-sm leading-relaxed animate-fade-in">
                            {{ insightResult }}
                        </div>

                        <button 
                            @click="handleAnalyze" 
                            :disabled="isAnalyzing"
                            class="w-full bg-white text-indigo-600 py-3.5 rounded-xl font-bold hover:bg-indigo-50 active:scale-95 transition flex items-center justify-center gap-2 shadow-sm"
                        >
                            <span v-if="isAnalyzing" class="animate-spin text-xl">⏳</span>
                            <span v-else>지금 분석하기</span>
                        </button>
                     </div>
                </div>
            </div>

            <!-- 우측: 차트 및 타임라인 (3칸) -->
            <div class="col-span-1 lg:col-span-3 space-y-8">
                <!-- 감정 차트 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
                        <h3 class="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                            📈 기분 변화 흐름 (최근 7일)
                        </h3>
                        <div class="h-48">
                            <Line :data="moodFlowData" :options="lineChartOptions" />
                        </div>
                    </div>
                    <div class="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
                        <h3 class="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                            📊 감정 상태 분포
                        </h3>
                        <div class="h-48 flex justify-center">
                            <Doughnut :data="riskDistData" :options="doughnutOptions" />
                        </div>
                    </div>
                </div>

                <!-- 일기 타임라인 (REDESIGNED with STRONG CARDS) -->
                <div class="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    <div class="p-6 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                        <h3 class="text-xl font-bold text-slate-800">📄 감정 일기 기록</h3>
                        <span class="text-sm text-slate-500 font-medium">최신순 정렬</span>
                    </div>
                    
                    <div class="divide-y divide-slate-100">
                        <div v-for="diary in diaries" :key="diary.id" class="p-8 hover:bg-slate-50 transition group">
                            <!-- 0. Header (Date & Score) -->
                            <div class="flex flex-wrap justify-between items-center mb-8 pb-4 border-b border-slate-100">
                                <div class="flex items-center gap-3">
                                    <span class="text-lg font-bold text-slate-700 bg-slate-100 px-4 py-2 rounded-xl border border-slate-200">{{ formatDate(diary.created_at, true) }}</span>
                                    <span v-if="diary.display.weather" class="text-sm text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 font-medium">
                                        🌤️ {{ diary.display.weather }}
                                    </span>
                                </div>
                                <div class="flex items-center gap-2 mt-2 sm:mt-0">
                                     <span class="text-sm text-slate-400 font-medium">기분 점수</span>
                                     <span class="font-extrabold text-4xl" :class="(diary.mood_score || 0) <= 3 ? 'text-red-500' : 'text-indigo-600'">
                                        {{ diary.mood_score }}
                                    </span>
                                     <span class="text-sm text-slate-300 font-bold">/ 10</span>
                                </div>
                            </div>

                            <!-- [The 5 Questions Layout - STRONG CARD DESIGN] -->
                            <div class="grid grid-cols-1 gap-6 pl-2">

                                <!-- Q1. Sleep -->
                                <div v-if="diary.display.sleep_condition || diary.display.sleep_desc" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition hover:shadow-md">
                                    <div class="bg-indigo-50/50 px-5 py-3 border-b border-indigo-100 flex items-center gap-2">
                                        <span class="text-xl">🌙</span> 
                                        <h5 class="text-indigo-900 font-bold text-base">[잠은 잘 주무셨나요?]</h5>
                                    </div>
                                    <div class="p-5 text-slate-800 text-lg leading-relaxed">
                                        <p v-if="diary.display.sleep_condition" class="font-bold mb-1">{{ diary.display.sleep_condition }}</p>
                                        <p v-if="diary.display.sleep_desc" class="text-slate-600 text-base">{{ diary.display.sleep_desc }}</p>
                                    </div>
                                </div>

                                <!-- Q2. Event -->
                                <div v-if="diary.display.event" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition hover:shadow-md">
                                    <div class="bg-blue-50/50 px-5 py-3 border-b border-blue-100 flex items-center gap-2">
                                        <span class="text-xl">📅</span> 
                                        <h5 class="text-blue-900 font-bold text-base">[오늘 무슨일이 있었나요?]</h5>
                                    </div>
                                    <div class="p-5 text-slate-800 text-lg leading-relaxed whitespace-pre-wrap">
                                        {{ diary.display.event }}
                                    </div>
                                </div>

                                <!-- Q3. Emotion -->
                                <div v-if="diary.display.emotion_desc || diary.display.emotion" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition hover:shadow-md">
                                    <div class="bg-pink-50/50 px-5 py-3 border-b border-pink-100 flex items-center gap-2">
                                        <span class="text-xl">❤️</span> 
                                        <h5 class="text-pink-900 font-bold text-base">[어떤 감정이 들었나요?]</h5>
                                    </div>
                                    <div class="p-5 text-slate-800 text-lg leading-relaxed font-medium">
                                        {{ diary.display.emotion_desc || diary.display.emotion }}
                                    </div>
                                </div>

                                <!-- Q4. Meaning -->
                                <div v-if="diary.display.emotion_meaning" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition hover:shadow-md">
                                    <div class="bg-purple-50/50 px-5 py-3 border-b border-purple-100 flex items-center gap-2">
                                        <span class="text-xl">🔍</span> 
                                        <h5 class="text-purple-900 font-bold text-base">[자신의 감정을 깊게 탐색해보면...]</h5>
                                    </div>
                                    <div class="p-5 text-slate-800 text-lg leading-relaxed italic text-slate-600">
                                        {{ diary.display.emotion_meaning }}
                                    </div>
                                </div>

                                <!-- Q5. Self Console -->
                                <div v-if="diary.display.self_talk" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition hover:shadow-md">
                                    <div class="bg-teal-50/50 px-5 py-3 border-b border-teal-100 flex items-center gap-2">
                                        <span class="text-xl">💌</span> 
                                        <h5 class="text-teal-900 font-bold text-base">[나에게 보내는 따뜻한 위로]</h5>
                                    </div>
                                    <div class="p-5 text-slate-800 text-lg leading-relaxed font-medium">
                                        {{ diary.display.self_talk }}
                                    </div>
                                </div>

                            </div>

                            <!-- AI Analysis Block -->
                            <div v-if="diary.display.ai_comment || diary.display.ai_analysis" class="mt-10">
                                <div class="bg-gradient-to-br from-indigo-50 to-white rounded-2xl p-6 border border-indigo-100 shadow-sm relative overflow-hidden">
                                     <div class="absolute top-0 left-0 w-1.5 h-full bg-indigo-500"></div>
                                    
                                    <!-- Comment -->
                                    <div v-if="diary.display.ai_comment" class="mb-4">
                                        <h4 class="text-indigo-800 font-bold text-sm mb-2 flex items-center gap-2">
                                            <span>🤖 AI 코멘트</span>
                                        </h4>
                                        <p class="text-slate-700 text-base leading-relaxed font-bold">
                                            {{ diary.display.ai_comment }}
                                        </p>
                                    </div>
                                    
                                    <!-- Prediction (Small Badge) -->
                                    <div v-if="diary.display.ai_prediction" class="mt-4 flex items-center gap-2 bg-white/50 w-fit px-3 py-1 rounded-lg border border-indigo-100 text-xs text-indigo-600 font-mono">
                                        <span>🔮 감정 예측</span>
                                        <strong>{{ diary.display.ai_prediction }}</strong>
                                    </div>
                                </div>
                            </div>

                        </div>

                        <div v-if="diaries.length === 0" class="text-center py-20 text-slate-400">
                            기록된 일기가 없습니다.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
