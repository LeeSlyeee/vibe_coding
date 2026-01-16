<template>
  <div class="diary-panel">
      <!-- 1. 헤더 영역 -->
      <div class="modal-header">
        <h3 class="modal-title">
          {{ isViewMode ? '기록 내용' : `${formattedDate}` }}
          <!-- 날씨 뱃지 -->
          <div v-if="weatherInfo" class="weather-badge-premium">
              <span class="weather-icon">{{ getWeatherIcon(weatherInfo.desc) }}</span>
              <span class="weather-text">{{ weatherInfo.desc }} {{ weatherInfo.temp }}°C</span>
          </div>
          <!-- 로딩 인디케이터 (빨간색) -->
          <span v-else class="weather-loading">
              <span class="pulse"></span> 날씨 확인 중...
          </span>
        </h3>
        <div v-if="isViewMode" class="diary-timestamp">
          {{ formattedDateTime }}
        </div>
      </div>

      <!-- 2. 초기 화면 (작성 전) -->
      <div v-if="!isViewMode && !showForm" class="diary-empty">
        <div class="empty-message">
          <button @click="startWriting" class="btn btn-primary btn-large shadow-hover" type="button">
            오늘의 감정 기록하기
          </button>
          <p class="empty-hint">작은 기록이 모여 당신의 마음 지도를 만듭니다.</p>
        </div>
      </div>

      <!-- 3. 작성 폼 -->
      <div v-else-if="!isViewMode && showForm" class="diary-form">
        <EmojiSelector v-model="formData.mood" />

        <QuestionAccordion
          question="오늘 무슨일이 있었나요?"
          v-model="formData.question1"
          :required="true"
          :default-open="true"
          placeholder="오늘 있었던 일을 적어주세요..."
        />

        <QuestionAccordion
          question="어떤 감정이 들었나요?"
          v-model="formData.question2"
          :required="true"
          placeholder="무슨 일이 있었는지 자세히 적어주세요..."
        />

        <QuestionAccordion
          question="마지막으로 더 깊게 자신의 감정을 써보세요."
          v-model="formData.question3"
          placeholder="어떤 감정을 느꼈는지 적어주세요..."
        />

        <QuestionAccordion
          question="나에게 따듯한 위로를 보내세요."
          v-model="formData.question4"
          placeholder="앞으로 어떻게 하면 좋을지 생각해보세요..."
        />

        <!-- 작성 모드 하단 버튼 (인라인으로 변경) -->
        <div class="modal-actions-inline">
          <button @click="cancelWriting" class="btn btn-secondary" type="button">
            취소
          </button>
          <button @click="handleSave" class="btn btn-primary" type="button" :disabled="!isValid || saving">
            {{ saving ? '저장 중...' : '오늘 기록 완료' }}
          </button>
        </div>
      </div>

      <!-- 4. 상세보기 모드 (결과 화면) -->
      <div v-else class="diary-view">
        <div class="view-content-wrapper">
          <!-- 감성적인 감정 카드 -->
          <div class="view-emoji-premium" :class="getMoodColorClass(currentDiary.mood_level)">
            <div class="emoji-container">
              <img :src="getMoodEmoji(currentDiary.mood_level)" class="emoji-large anim-float" alt="mood" />
              <div class="emoji-info">
                <span class="emoji-label">{{ getMoodName(currentDiary.mood_level) }}</span>
                <!-- AI 뱃지는 분석 완료 시에만 보여줌 -->
                <span v-if="!isProcessing && currentDiary.ai_prediction && !currentDiary.ai_prediction.includes('분석 중')" class="ai-prediction-badge-premium">
                  AI 분석: {{ currentDiary.ai_prediction }}
                </span>
              </div>
            </div>
            
            <!-- AI 진행 상황 표시 (분석 중일 때) -->
            <div v-if="isProcessing" class="ai-loading-section">
              <div class="loading-header">
                 <span class="loading-msg">{{ loadingMessage }}</span>
                 <span class="loading-timer" v-if="eta > 0">{{ eta }}초 남음</span>
              </div>
              <div class="progress-track">
                 <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
              </div>
            </div>

            <!-- AI 코멘트 표시 (분석 완료 시) -->
            <div v-else-if="currentDiary.ai_comment" class="ai-letter-box">
               <div class="letter-header">
                  <span class="ai-icon">💌</span>
                  <span class="ai-sender">AI 심리 상담사의 편지</span>
               </div>
               <p class="ai-comment-text">{{ currentDiary.ai_comment }}</p>
            </div>
          </div>

          <!-- 질문 답변 리스트 -->
          <div class="view-answers">
            <div v-if="currentDiary.event" class="answer-item-premium">
              <h4 class="answer-question">오늘 무슨일이 있었나요?</h4>
              <p class="answer-text">{{ currentDiary.event }}</p>
            </div>
            <div v-if="currentDiary.emotion_desc" class="answer-item-premium">
              <h4 class="answer-question">어떤 감정이 들었나요?</h4>
              <p class="answer-text">{{ currentDiary.emotion_desc }}</p>
            </div>
            <div v-if="currentDiary.emotion_meaning" class="answer-item-premium">
              <h4 class="answer-question">자신의 감정을 깊게 탐색해보면...</h4>
              <p class="answer-text">{{ currentDiary.emotion_meaning }}</p>
            </div>
            <div v-if="currentDiary.self_talk" class="answer-item-premium">
              <h4 class="answer-question">나에게 보내는 따뜻한 위로</h4>
              <p class="answer-text">{{ currentDiary.self_talk }}</p>
            </div>
          </div>

          <!-- 보기 모드 하단 버튼 (인라인으로 이동 및 시원한 스타일링) -->
          <div class="modal-actions-inline">
            <button @click="handleDelete" class="btn btn-danger btn-ghost" type="button">삭제</button>
            <button @click="handleEdit" class="btn btn-secondary" type="button">수정하기</button>
            <button @click="$emit('close')" class="btn btn-primary" type="button">닫기</button>
          </div>
        </div>
      </div>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted, onMounted } from 'vue'
import EmojiSelector from './EmojiSelector.vue'
import QuestionAccordion from './QuestionAccordion.vue'
import { diaryAPI } from '../services/api'

// Images
import happyImg from '../assets/01.png'
import calmImg from '../assets/02.png'
import neutralImg from '../assets/03.png'
import sadImg from '../assets/04.png'
import angryImg from '../assets/05.png'

export default {
  name: 'DiaryModal',
  components: { EmojiSelector, QuestionAccordion },
  props: {
    date: { type: String, required: true },
    diary: { type: Object, default: null }
  },
  emits: ['close', 'saved'],
  setup(props, { emit }) {
    // [DEBUG]
    // alert("🎉 VERSION 3.0 LOADED! 확인을 누르면 날씨를 가져옵니다.");
    console.log("🔥 DiaryModal V3.0 SETUP 🔥");

    // === Utils & Data ===
    const isViewMode = ref(!!props.diary)
    const showForm = ref(false)
    const saving = ref(false)
    const localDiary = ref(null) 
    
    // === Weather State ===
    const weatherInfo = ref(null) 
    
    // 서울 시청 좌표 (기본값)
    const DEFAULT_LAT = 37.5665;
    const DEFAULT_LON = 126.9780;

    const currentDiary = computed(() => localDiary.value || props.diary || {})

    // === AI State ===
    const isProcessing = ref(false)
    const progressPercent = ref(0)
    const loadingMessage = ref('AI 분석 준비 중...')
    const eta = ref(0)
    const timerIds = ref([]) 

    // === Constants ===
    const moodLevelToName = { 1: 'angry', 2: 'sad', 3: 'neutral', 4: 'calm', 5: 'happy' }
    const emojiMap = {
      1: { icon: angryImg, name: '화나' }, 2: { icon: sadImg, name: '우울해' },
      3: { icon: neutralImg, name: '그저그래' }, 4: { icon: calmImg, name: '편안해' },
      5: { icon: happyImg, name: '행복해' }
    }

    const formData = ref({ mood: 'neutral', question1: '', question2: '', question3: '', question4: '' })

    // === Weather Helper Function ===
    const getWeatherFromAPI = async (lat, lon, date = null) => {
        try {
            console.log(`🌦️ Call Weather API: ${lat}, ${lon}, ${date || 'Today'}`);
            let url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`;
            let isPast = false;

            if (date) {
                const today = new Date().toISOString().split('T')[0];
                if (date !== today) {
                    isPast = true;
                    url = `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=${date}&end_date=${date}&daily=weathercode,temperature_2m_max`;
                }
            }

            const res = await fetch(url);
            if(!res.ok) throw new Error('API Res Error');
            const data = await res.json();
            console.log("📦 Weather Data:", data);

            let code, temp;
            if (isPast && data.daily) {
                code = data.daily.weathercode[0];
                temp = data.daily.temperature_2m_max[0];
            } else if (data.current_weather) {
                code = data.current_weather.weathercode;
                temp = data.current_weather.temperature;
            }

            if (code !== undefined) {
                const map = {
                    0: '맑음 ☀️', 1: '대체로 맑음 🌤️', 2: '구름 조금 ⛅', 3: '흐림 ☁️',
                    45: '안개 🌫️', 48: '안개 🌫️', 51: '이슬비 🌧️', 53: '이슬비 🌧️', 55: '이슬비 🌧️',
                    61: '비 ☔', 63: '비 ☔', 65: '비 ☔', 80: '소나기 ☔', 95: '뇌우 ⚡'
                };
                // 값 갱신
                weatherInfo.value = { temp, desc: map[code] || '흐림' };
                console.log("✅ Weather Updated:", weatherInfo.value);
            }
        } catch (e) {
            console.error("Weather Fail:", e);
        }
    }

    // === Main Weather Logic ===
    const checkWeather = async (date = null) => {
        console.log("📡 checkWeather Start...", date);
        // 1. 일단 서울 날씨로 즉시 시도 (Fallback 먼저)
        if (!weatherInfo.value) {
             console.log("🏙️ Using Default Seoul Weather first...");
             getWeatherFromAPI(DEFAULT_LAT, DEFAULT_LON, date);
        }

        // 2. 실제 위치 찾기 시도 (비동기)
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    console.log("📍 Geo Success:", pos.coords.latitude, pos.coords.longitude);
                    getWeatherFromAPI(pos.coords.latitude, pos.coords.longitude, date);
                },
                (err) => {
                    console.warn("⚠️ Geo Failed, trying IP...", err.code);
                    fetch('https://ipapi.co/json/')
                        .then(r => r.json())
                        .then(d => {
                            console.log("📍 IP Success:", d.latitude);
                            if(d.latitude) getWeatherFromAPI(d.latitude, d.longitude, date);
                        })
                        .catch(e => console.error(e));
                },
                { timeout: 3000 }
            );
        } else {
             console.warn("❌ Geo Not Supported in Browser");
        }
    }

    // === Computed Helpers ===
    const formattedDate = computed(() => {
        if (!props.date) return ''
        const parts = props.date.split('-')
        if (parts.length < 3) return props.date
        return `${parseInt(parts[1])}월 ${parseInt(parts[2])}일`
    })

    const formattedDateTime = computed(() => {
        const dStr = currentDiary.value.created_at || props.diary?.created_at
        if (!dStr) return ''
        const d = new Date(dStr)
        return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
    })
    
    const isValid = computed(() => formData.value.mood && formData.value.question1.trim())
    const getMoodEmoji = (lvl) => emojiMap[lvl]?.icon || ''
    const getMoodName = (lvl) => emojiMap[lvl]?.name || ''

    // === Polling & Save Handlers ===
    const clearTimers = () => { timerIds.value.forEach(id => clearInterval(id)); timerIds.value = []; }

    const finishPolling = async () => {
        clearTimers(); isProcessing.value = false; progressPercent.value = 100; emit('saved');
        if (currentDiary.value.id) localDiary.value = await diaryAPI.getDiary(currentDiary.value.id)
    }
    
    const startRealPolling = (taskId) => {
        isProcessing.value = true; progressPercent.value = 5; loadingMessage.value = "AI 분석 중..."; eta.value = 15;
        timerIds.value.push(setInterval(() => { if(eta.value > 0) eta.value-- }, 1000));
        timerIds.value.push(setInterval(async () => {
            try {
                const status = await diaryAPI.getTaskStatus(taskId)
                if (status.state === 'PROGRESS') { progressPercent.value = status.process_percent; loadingMessage.value = status.message; } 
                else if (status.state === 'SUCCESS') { finishPolling() } 
                else if (status.state === 'FAILURE') { isProcessing.value = false; clearTimers(); }
            } catch (e) {}
        }, 1000));
    }

    const startFakePolling = () => {
        isProcessing.value = true; loadingMessage.value = "이전 분석 확인..."; progressPercent.value = 30; eta.value = 10;
        timerIds.value.push(setInterval(async () => {
            if (progressPercent.value < 90) progressPercent.value += 5; if (eta.value > 0) eta.value--;
            if (currentDiary.value.id) {
                try {
                    const fresh = await diaryAPI.getDiary(currentDiary.value.id)
                    if (fresh.ai_prediction && !fresh.ai_prediction.includes('분석 중')) { localDiary.value = fresh; finishPolling(); }
                } catch(e) {}
            }
        }, 2000));
    }

    const handleSave = async () => {
        saving.value = true
        try {
            const payload = {
                date: props.date,
                mood: formData.value.mood,
                question1: formData.value.question1, question2: formData.value.question2,
                question3: formData.value.question3, question4: formData.value.question4,
                weather: weatherInfo.value ? weatherInfo.value.desc : null,
                temperature: weatherInfo.value ? weatherInfo.value.temp : null
            }
            let result = props.diary ? await diaryAPI.updateDiary(props.diary.id, payload) : await diaryAPI.createDiary(payload)
            localDiary.value = result; isViewMode.value = true; showForm.value = false;
            if (result.task_id) startRealPolling(result.task_id); else startFakePolling();
            emit('saved')
        } catch (e) { alert('저장 실패: ' + e.message) } finally { saving.value = false }
    }

    const startWriting = () => { showForm.value = true }
    const cancelWriting = () => { showForm.value = false; emit('close') }
    const handleEdit = () => {
        isViewMode.value = false; showForm.value = true;
        const d = currentDiary.value
        formData.value = {
            mood: moodLevelToName[d.mood_level] || 'neutral',
            question1: d.event||'', question2: d.emotion_desc||'',
            question3: d.emotion_meaning||'', question4: d.self_talk||''
        }
    }
    const handleDelete = async () => {
        if(!confirm('삭제?')) return;
        try { await diaryAPI.deleteDiary(currentDiary.value.id); emit('saved'); emit('close'); } catch(e) {}
    }

    // === Lifecycle & Watch ===
    watch(() => props.diary, (newVal) => {
        isViewMode.value = !!newVal
        localDiary.value = null
        clearTimers()
        isProcessing.value = false
        weatherInfo.value = null // Reset

        if (newVal) {
            // 수정/보기 모드
            formData.value = {
                mood: moodLevelToName[newVal.mood_level] || 'neutral',
                question1: newVal.event||'', question2: newVal.emotion_desc||'',
                question3: newVal.emotion_meaning||'', question4: newVal.self_talk||''
            }
            
            if (newVal.weather) {
                weatherInfo.value = { desc: newVal.weather, temp: newVal.temperature }
            } else {
                checkWeather(props.date)
            }

            if (newVal.ai_prediction && newVal.ai_prediction.includes('분석 중')) {
                startFakePolling()
            }
        } else {
            // 새 글 작성 모드
            checkWeather(null)
        }
    }, { immediate: true })

    onUnmounted(() => clearTimers())

    const getWeatherIcon = (desc) => {
        if (!desc) return '✨';
        if (desc.includes('맑음')) return '☀️';
        if (desc.includes('구름') || desc.includes('흐림')) return '☁️';
        if (desc.includes('비')) return '🌧️';
        if (desc.includes('눈')) return '❄️';
        return '✨';
    }

    const getMoodColorClass = (lvl) => {
        const map = { 1: 'mood-angry', 2: 'mood-sad', 3: 'mood-neutral', 4: 'mood-calm', 5: 'mood-happy' }
        return map[lvl] || 'mood-neutral'
    }

    return {
        isViewMode, showForm, saving, formData, weatherInfo,
        currentDiary, formattedDate, formattedDateTime, isValid, getMoodEmoji, getMoodName,
        handleSave, startWriting, cancelWriting, handleEdit, handleDelete,
        isProcessing, progressPercent, loadingMessage, eta,
        getWeatherIcon, getMoodColorClass
    }
  }
}
</script>

<style scoped>
.diary-panel { height: 100%; overflow-y: auto; padding: 0 32px 32px 32px; background: #fafafa; scroll-behavior: smooth; }
.modal-header { 
  position: sticky; 
  top: 0; 
  z-index: 1; /* 컨텐츠(z-index: 2)보다 낮게 설정하여 스크롤 시 가려지도록 함 */
  padding-top: 32px;
  padding-bottom: 40px; 
  background: transparent; /* 배경을 투명하게 하여 스크롤 시 가리는 효과 극대화 */
}
.modal-title { font-size: 24px; font-weight: 800; color: #1d1d1f; display: flex; align-items: center; justify-content: space-between; }
.diary-timestamp { font-size: 13px; color: #999; margin-top: 4px; }

.weather-badge-premium { display: flex; align-items: center; gap: 8px; background: white; padding: 6px 12px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.03); }
.weather-icon { font-size: 16px; }
.weather-text { font-size: 12px; font-weight: 600; color: #555; }

.weather-loading { font-size: 12px; color: #888; display: flex; align-items: center; gap: 6px; }
.pulse { width: 8px; height: 8px; background: #ff4757; border-radius: 50%; display: inline-block; animation: pulse-anim 1.5s infinite; }
@keyframes pulse-anim { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

.diary-empty { text-align: center; padding: 60px 20px; }
.empty-message { display: flex; flex-direction: column; align-items: center; gap: 16px; }
.empty-hint { font-size: 14px; color: #aaa; margin-top: 8px; }

.btn { padding: 12px 24px; border-radius: 12px; border: none; cursor: pointer; font-weight: 700; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.btn-primary { background: #1d1d1f; color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.btn-large { padding: 16px 40px; font-size: 16px; }
.btn-secondary { background: #f2f2f7; color: #1d1d1f; }
.btn-danger { background: #ff3b30; color: white; }
.btn-ghost { background: transparent; color: #ff3b30; border: 1px solid rgba(255, 59, 48, 0.15); }
.btn-ghost:hover { background: rgba(255, 59, 48, 0.05); border-color: #ff3b30; }

.modal-actions-inline { 
  display: flex; 
  justify-content: flex-end; 
  gap: 16px; 
  margin-top: 60px; 
  padding: 40px 0 20px; 
  border-top: 1px solid rgba(0,0,0,0.06);
  position: relative;
  z-index: 5;
}

.diary-view { position: relative; }
.view-content-wrapper { 
  position: relative; 
  z-index: 2; /* 헤더를 덮기 위해 더 높은 z-index 부여 */
  background: #fafafa; /* 헤더를 가릴 solid 배경색 */
  margin-top: -20px; /* 자연스러운 겹침을 위한 마진 조절 */
  padding-top: 1px; /* 마진 상쇄 방지 */
}

.view-emoji-premium { border-radius: 28px; padding: 40px; display: flex; flex-direction: column; align-items: center; gap: 24px; margin-bottom: 32px; transition: all 0.4s ease; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
.mood-happy { background: linear-gradient(135deg, #FFFDE7 0%, #FFE082 100%); }
.mood-calm { background: linear-gradient(135deg, #F1F8E9 0%, #A5D6A7 100%); }
.mood-neutral { background: linear-gradient(135deg, #FAFAFA 0%, #E0E0E0 100%); }
.mood-sad { background: linear-gradient(135deg, #E3F2FD 0%, #90CAF9 100%); }
.mood-angry { background: linear-gradient(135deg, #FFEBEE 0%, #EF9A9A 100%); }

.emoji-container { display: flex; flex-direction: column; align-items: center; gap: 16px; margin-bottom: 8px; }
.emoji-large { width: 110px; height: 110px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.12)); }
.anim-float { animation: float 4s ease-in-out infinite; }
@keyframes float { 0% { transform: translateY(0); } 50% { transform: translateY(-12px); } 100% { transform: translateY(0); } }

.emoji-label { font-size: 26px; font-weight: 800; color: rgba(0,0,0,0.8); letter-spacing: -0.5px; }
.ai-prediction-badge-premium { font-size: 13px; font-weight: 700; color: white; background: rgba(0,0,0,0.25); padding: 7px 16px; border-radius: 24px; backdrop-filter: blur(8px); }

.ai-letter-box { background: rgba(255,255,255,0.96); padding: 28px; border-radius: 24px; width: 100%; box-shadow: 0 12px 32px rgba(0,0,0,0.06); border: 1px solid rgba(255,255,255,0.8); }
.letter-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.ai-icon { font-size: 22px; }
.ai-sender { font-size: 15px; font-weight: 700; color: #222; }
.ai-comment-text { font-size: 16px; line-height: 1.8; color: #444; white-space: pre-wrap; font-weight: 500; }

.ai-loading-section { width: 100%; background: rgba(255,255,255,0.6); padding: 24px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.3); }
.progress-track { width: 100%; height: 8px; background: rgba(0,0,0,0.06); border-radius: 10px; overflow: hidden; margin-top: 12px; }
.progress-fill { height: 100%; background: #1d1d1f; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }

.view-answers { display: flex; flex-direction: column; gap: 28px; padding-bottom: 60px; }
.answer-item-premium { background: white; padding: 32px; border-radius: 24px; border: 1px solid rgba(0,0,0,0.02); box-shadow: 0 6px 20px rgba(0,0,0,0.03); transition: transform 0.3s ease; }
.answer-item-premium:hover { transform: translateY(-4px); }
.answer-question { font-size: 14px; color: #999; margin-bottom: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.answer-text { font-size: 17px; color: #1d1d1f; line-height: 1.7; white-space: pre-wrap; font-weight: 500; }
</style>
