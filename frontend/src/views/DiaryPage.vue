<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '../stores/auth';
import api from '../api';
import { LogOut, ChevronLeft, ChevronRight, X, ArrowRight, ArrowLeft, Smile, Frown, Meh, Angry, Bird, Check, Plus, Calendar as CalendarIcon } from 'lucide-vue-next';
import { 
  format, startOfMonth, endOfMonth, eachDayOfInterval, 
  isSameDay, addMonths, subMonths, parseISO 
} from 'date-fns';
import { ko } from 'date-fns/locale';

interface Diary {
  id: number;
  event: string;
  emotion_desc: string;
  emotion_meaning: string;
  self_talk: string;
  mood_level: number;
  created_at: string;
}

const authStore = useAuthStore();
const diaries = ref<Diary[]>([]);
const currentDate = ref(new Date());
const selectedDate = ref(new Date());
const isWriting = ref(false); 
const writingStep = ref(1); // 1: Mood, 2: Fact, 3: Emotion, 4: SelfTalk

const form = ref<{
    id?: number;
    event: string;
    emotion_desc: string;
    emotion_meaning: string;
    self_talk: string;
    mood_level: number;
}>({
    event: '',
    emotion_desc: '',
    emotion_meaning: '',
    self_talk: '',
    mood_level: 0
});

const moodOptions = [
    { id: 1, label: '행복해', color: 'bg-[#FFE082]', icon: Smile }, 
    { id: 2, label: '평온해', color: 'bg-[#C5E1A5]', icon: Bird }, 
    { id: 3, label: '그저그래', color: 'bg-[#EEEEEE]', icon: Meh }, 
    { id: 4, label: '우울해', color: 'bg-[#90CAF9]', icon: Frown }, 
    { id: 5, label: '화가나', color: 'bg-[#FFAB91]', icon: Angry }, 
];

const getMood = (level: number) => moodOptions.find(m => m.id === level) || moodOptions[2];

// --- Calendar ---
const calendarDays = computed(() => {
  const start = startOfMonth(currentDate.value);
  const end = endOfMonth(currentDate.value);
  return eachDayOfInterval({ start, end });
});

const currentMonthName = computed(() => format(currentDate.value, 'M월', { locale: ko }));
const currentYear = computed(() => format(currentDate.value, 'yyyy'));

const getDiaryForDate = (date: Date) => diaries.value.find(d => isSameDay(parseISO(d.created_at), date));
const selectedDiary = computed(() => getDiaryForDate(selectedDate.value));

const getDiaryMood = (date: Date) => {
    const d = getDiaryForDate(date);
    return d ? getMood(d.mood_level) : null;
};

// --- Actions ---
const loadDiaries = async () => {
    try {
        const res = await api.get('/diaries');
        diaries.value = res.data;
    } catch (e) { console.error(e); }
};

const selectDate = (date: Date) => {
    selectedDate.value = date;
    const diary = getDiaryForDate(date);
    if (diary) {
        form.value = { ...diary };
    } else {
        form.value = { event: '', emotion_desc: '', emotion_meaning: '', self_talk: '', mood_level: 0 };
    }
};

const startWriting = () => {
    console.log('startWriting clicked');
    // Safety: Ensure form is reset if we are starting a NEW entry
    if (!selectedDiary.value) {
        form.value = { event: '', emotion_desc: '', emotion_meaning: '', self_talk: '', mood_level: 0 };
    }
    writingStep.value = 1;
    isWriting.value = true;
    console.log('isWriting set to true');
};

const closePanel = () => {
    console.log('closePanel clicked');
    isWriting.value = false;
    setTimeout(() => writingStep.value = 1, 300);
    loadDiaries();
};

const nextStep = () => {
    if (writingStep.value === 1 && form.value.mood_level === 0) return alert('기분을 선택해주세요!');
    if (writingStep.value < 4) writingStep.value++;
};

const prevStep = () => {
    if (writingStep.value > 1) writingStep.value--;
};

const handleSubmit = async () => {
    try {
        console.log('Submitting Diary:', form.value);
        if (form.value.id) {
             await api.put(`/diaries/${form.value.id}`, { ...form.value });
        } else {
             await api.post('/diaries', { ...form.value, created_at: selectedDate.value.toISOString() });
        }
        console.log('Submit Success');
        closePanel();
    } catch (e: any) {
        console.error('Submit Error:', e);
        const msg = e.response?.data?.message || e.message || '저장 실패';
        alert(`저장 실패: ${msg}`);
    }
};

const prevMonth = () => currentDate.value = subMonths(currentDate.value, 1);
const nextMonth = () => currentDate.value = addMonths(currentDate.value, 1);

onMounted(loadDiaries);
</script>

<template>
  <div class="min-h-screen bg-[#F0EFEC] flex items-center justify-center p-8 font-gowun">
    
    <!-- DESKTOP DASHBOARD CONTAINER -->
    <div class="w-full max-w-6xl h-[85vh] bg-[#FDFCF8] rounded-2xl shadow-2xl overflow-hidden flex flex-row border border-stone-200">
        
        <!-- LEFT PANEL: Sidebar / Calendar -->
        <div class="w-1/2 md:w-7/12 border-r border-stone-100 flex flex-col bg-white/50 relative">
            
            <!-- Header -->
            <header class="p-8 flex justify-between items-center">
                 <div class="flex flex-col">
                     <span class="text-xs font-bold text-stone-400 tracking-widest pl-1 mb-1">{{ currentYear }}</span>
                     <h2 class="text-4xl font-extrabold text-stone-800 tracking-tight flex items-baseline gap-2">
                        {{ currentMonthName }} <span class="text-sm font-normal text-stone-400">Memory</span>
                    </h2>
                </div>
                <div class="flex gap-2">
                    <button @click="prevMonth" class="p-3 hover:bg-stone-50 rounded-full text-stone-400 hover:text-stone-800 transition-colors border border-stone-100">
                        <ChevronLeft class="w-5 h-5" />
                    </button>
                    <button @click="nextMonth" class="p-3 hover:bg-stone-50 rounded-full text-stone-400 hover:text-stone-800 transition-colors border border-stone-100">
                        <ChevronRight class="w-5 h-5" />
                    </button>
                </div>
            </header>

            <!-- Calendar Grid -->
            <div class="flex-1 px-8 overflow-y-auto">
                <div class="grid grid-cols-7 gap-4 mb-8">
                    <div v-for="day in ['일', '월', '화', '수', '목', '금', '토']" :key="day" 
                        class="text-center text-xs text-stone-400 font-bold mb-4 uppercase tracking-wider">
                        {{ day }}
                    </div>
                    
                    <div v-for="n in startOfMonth(currentDate).getDay()" :key="`empty-${n}`"></div>

                    <div v-for="date in calendarDays" :key="date.toString()" 
                        @click="selectDate(date)"
                        class="aspect-square flex flex-col items-center justify-center cursor-pointer rounded-2xl transition-all duration-200 border-2"
                        :class="isSameDay(selectedDate, date) ? 'border-stone-800 bg-stone-50' : 'border-transparent hover:bg-stone-50'">
                        
                        <!-- Mood Sticker -->
                        <div v-if="getDiaryMood(date)" 
                            class="w-12 h-12 rounded-full flex items-center justify-center shadow-sm transition-transform hover:scale-110 mb-1"
                            :class="getDiaryMood(date)?.color">
                            <component :is="getDiaryMood(date)?.icon" class="w-6 h-6 text-stone-800/80" stroke-width="2.5" />
                        </div>
                        
                        <!-- Date Number -->
                        <span class="text-sm font-bold"
                            :class="[
                                isSameDay(selectedDate, date) ? 'text-stone-800' : 'text-stone-400',
                                !getDiaryMood(date) && 'w-8 h-8 flex items-center justify-center rounded-full hover:bg-stone-200'
                            ]">
                            {{ format(date, 'd') }}
                        </span>

                    </div>
                </div>
            </div>

            <!-- Bottom Brand -->
             <div class="p-6 border-t border-stone-50 flex justify-between items-center text-stone-300">
                <span class="text-xs font-bold tracking-widest">MOOD DIARY V2</span>
                 <button @click="authStore.logout()" class="flex items-center gap-2 hover:text-red-400 transition-colors text-xs font-bold">
                    <LogOut class="w-4 h-4" /> LOGOUT
                </button>
            </div>
        </div>

        <!-- RIGHT PANEL: Detail View & Actions -->
        <div class="w-1/2 md:w-5/12 bg-[#FDFCF8] relative flex flex-col h-full">
            
            <!-- MODE 1: WIZARD (Writing) -->
            <div v-if="isWriting" class="flex-1 flex flex-col h-full animate-fade-in relative z-10">
                <!-- Wizard Header -->
                <div class="px-8 py-6 flex justify-between items-center border-b border-stone-100">
                    <div class="flex items-center gap-3">
                        <button @click="closePanel" class="p-2 -ml-2 hover:bg-stone-100 rounded-full text-stone-400 transition-colors">
                            <X class="w-6 h-6" />
                        </button>
                         <span class="font-bold text-stone-800">{{ format(selectedDate, 'M월 d일', { locale: ko }) }} 기록</span>
                    </div>
                    
                    <!-- Steps -->
                    <div class="flex gap-2">
                        <div v-for="s in 4" :key="s" class="h-2 rounded-full transition-all duration-500"
                            :class="s <= writingStep ? 'w-8 bg-stone-800' : 'w-2 bg-stone-200'"></div>
                    </div>
                </div>

                <!-- Wizard Content -->
                <div class="p-8 flex-1 overflow-y-auto hidden-scrollbar">
                    
                    <!-- STEP 1: Mood -->
                    <div v-if="writingStep === 1" class="text-center space-y-10 pt-8">
                        <div>
                             <h3 class="text-2xl font-extrabold text-stone-800 mb-2">오늘 하루 어떠셨나요?</h3>
                             <p class="text-stone-500 font-medium">가장 잘 어울리는 표정을 골라주세요</p>
                        </div>
                        <div class="flex justify-center gap-4 flex-wrap">
                            <button v-for="mood in moodOptions" :key="mood.id"
                                @click="form.mood_level = mood.id"
                                class="w-28 aspect-[3/4] rounded-2xl border-2 transition-all flex flex-col items-center justify-center gap-3 hover:-translate-y-1 group"
                                :class="form.mood_level === mood.id ? 'border-stone-800 bg-white shadow-lg scale-105' : 'border-transparent bg-stone-50 hover:bg-white hover:shadow-md'">
                                <div class="w-14 h-14 rounded-full flex items-center justify-center transition-colors shadow-inner" :class="mood.color">
                                    <component :is="mood.icon" class="w-7 h-7 text-stone-800/80" stroke-width="2.5" />
                                </div>
                                <span class="text-base font-bold text-stone-600 group-hover:text-stone-900">{{ mood.label }}</span>
                            </button>
                        </div>
                    </div>

                     <!-- STEP 2: Fact -->
                    <div v-if="writingStep === 2" class="space-y-6 pt-4">
                        <div class="text-center mb-6">
                             <h3 class="text-2xl font-extrabold text-stone-800 mb-2">무슨 일이 있었나요?</h3>
                             <p class="text-stone-500 font-medium">사실 위주로 담백하게 기록해보세요</p>
                        </div>
                        <textarea v-model="form.event" rows="12" 
                            class="w-full bg-stone-50 border-2 border-transparent rounded-2xl p-6 text-lg text-stone-700 leading-relaxed focus:outline-none focus:border-stone-800 focus:bg-white transition-colors resize-none placeholder-stone-300" 
                            placeholder="예) 아침에 산책을 했는데 날씨가 정말 좋았어."></textarea>
                    </div>

                    <!-- STEP 3: Emotion -->
                    <div v-if="writingStep === 3" class="space-y-6 pt-4">
                         <div class="text-center mb-6">
                             <h3 class="text-2xl font-extrabold text-stone-800 mb-2">어떤 감정이 들었나요?</h3>
                             <p class="text-stone-500 font-medium">마음의 소리에 귀 기울여보세요</p>
                        </div>
                        <div class="space-y-5">
                            <div class="space-y-2">
                                <label class="text-sm font-bold text-stone-400 pl-4">감정</label>
                                <textarea v-model="form.emotion_desc" rows="4" 
                                    class="w-full bg-stone-50 rounded-2xl p-5 text-lg text-stone-700 focus:outline-none focus:ring-2 focus:ring-stone-200 resize-none transition-all focus:bg-white" 
                                    placeholder="불안하고 초조했어..."></textarea>
                            </div>
                             <div class="space-y-2">
                                <label class="text-sm font-bold text-stone-400 pl-4">의미 (선택)</label>
                                <textarea v-model="form.emotion_meaning" rows="3" 
                                    class="w-full bg-transparent border-b-2 border-stone-100 p-4 text-base text-stone-600 focus:outline-none focus:border-stone-400 resize-none transition-all" 
                                    placeholder="내가 이 일을 중요하게 생각하나 봐."></textarea>
                            </div>
                        </div>
                    </div>

                     <!-- STEP 4: Self Talk -->
                    <div v-if="writingStep === 4" class="space-y-6 pt-4">
                         <div class="text-center mb-6">
                             <h3 class="text-2xl font-extrabold text-stone-800 mb-2">나에게 한마디</h3>
                             <p class="text-stone-500 font-medium">따뜻한 위로를 건네주세요</p>
                        </div>
                        <div class="bg-[#FFFDE7] p-2 rounded-[28px] shadow-sm border border-yellow-100">
                             <textarea v-model="form.self_talk" rows="10" 
                                class="w-full bg-white/50 border-0 rounded-[20px] p-6 text-xl text-stone-800 leading-relaxed focus:outline-none resize-none text-center font-medium placeholder-stone-300" 
                                placeholder="괜찮아, 누구나 실수할 수 있어."></textarea>
                        </div>
                    </div>
                </div>

                <!-- Footer Navigation -->
                <div class="p-6 border-t border-stone-50 flex justify-between items-center bg-white">
                    <button v-if="writingStep > 1" @click="prevStep" 
                        class="w-12 h-12 rounded-full border border-stone-200 flex items-center justify-center text-stone-400 hover:text-stone-800 hover:border-stone-800 transition-all">
                        <ArrowLeft class="w-5 h-5" />
                    </button>
                    <div v-else class="w-12"></div>

                    <button v-if="writingStep < 4" @click="nextStep" 
                        class="px-8 py-3 bg-stone-800 text-white rounded-full font-bold flex items-center gap-2 hover:bg-stone-900 transition-all shadow-lg active:scale-95 disabled:opacity-50"
                        :disabled="writingStep === 1 && form.mood_level === 0">
                        다음 <ArrowRight class="w-4 h-4" />
                    </button>
                    <button v-else @click="handleSubmit" 
                        class="px-8 py-3 bg-stone-800 text-white rounded-full font-bold flex items-center gap-2 hover:bg-stone-900 transition-all shadow-lg active:scale-95">
                        기록 저장 <Check class="w-4 h-4" />
                    </button>
                </div>
            </div>

            <!-- MODE 2: DETAIL VIEW (When Diary Exists) -->
            <div v-else-if="selectedDiary" class="flex-1 flex flex-col items-center justify-center p-12 text-center animate-fade-in relative z-0">
                 <div class="w-32 h-32 rounded-full flex items-center justify-center shadow-inner mb-8"
                    :class="getMood(selectedDiary!.mood_level).color">
                    <component :is="getMood(selectedDiary!.mood_level).icon" class="w-16 h-16 text-stone-800" stroke-width="2" />
                </div>
                
                <h3 class="text-3xl font-extrabold text-stone-800 mb-2">{{ getMood(selectedDiary!.mood_level).label }}</h3>
                <p class="text-stone-400 font-bold mb-8">{{ format(selectedDate, 'yyyy년 M월 d일 EEEE', { locale: ko }) }}</p>

                <div class="w-full bg-white border border-stone-100 rounded-3xl p-8 shadow-sm text-left relative z-10">
                     <div class="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-stone-100 rounded-b-full"></div>
                     <p class="text-stone-600 leading-relaxed font-medium mb-4 whitespace-pre-wrap">{{ selectedDiary!.event }}</p>
                     
                     <div class="bg-stone-50 p-4 rounded-xl border border-stone-100 mb-4">
                         <span class="text-xs font-bold text-stone-400 block mb-1">감정</span>
                         <p class="text-stone-600 text-sm">{{ selectedDiary!.emotion_desc }}</p>
                     </div>

                     <div class="bg-[#FFFDE7] p-4 rounded-xl border border-yellow-100/50">
                         <span class="text-xs font-bold text-yellow-600/50 block mb-1">To Me</span>
                         <p class="text-stone-600 text-sm italic">"{{ selectedDiary!.self_talk }}"</p>
                     </div>
                </div>

                <div class="mt-8">
                     <button @click="startWriting" class="px-6 py-2 rounded-full border border-stone-200 text-stone-400 hover:text-stone-800 hover:border-stone-800 transition-all text-sm font-bold">수정하기</button>
                </div>
            </div>

            <!-- MODE 3: EMPTY (When No Diary) -->
            <div v-else class="flex-1 flex flex-col items-center justify-center p-12 text-center opacity-60">
                 <div class="w-24 h-24 bg-stone-100 rounded-full flex items-center justify-center mb-6 text-stone-300">
                    <CalendarIcon class="w-10 h-10" />
                 </div>
                 <h3 class="text-2xl font-bold text-stone-800 mb-2">{{ format(selectedDate, 'M월 d일', { locale: ko }) }}</h3>
                 <p class="text-stone-400 mb-8">아직 기록된 이야기가 없어요.</p>
                 
                 <button @click="startWriting" 
                    class="group relative px-8 py-4 bg-stone-800 text-white rounded-2xl font-bold shadow-lg hover:bg-stone-900 transition-all hover:-translate-y-1 active:scale-95 flex items-center gap-3">
                    <Plus class="w-5 h-5" />
                    오늘의 기록 남기기
                 </button>
            </div>

        </div>

    </div>

  </div>
</template>

<style>
.font-gowun {
    font-family: 'Gowun Dodum', sans-serif;
}
.hidden-scrollbar::-webkit-scrollbar {
  display: none;
}
.hidden-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.animate-fade-in {
    animation: fadeIn 0.4s ease-out;
}
.animate-slide-up {
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideUp {
    from { transform: translateY(40px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
</style>
