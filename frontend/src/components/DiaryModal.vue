<template>
  <div class="diary-panel">
      <!-- 1. 헤더 영역 -->
      <div class="modal-header">
        <h3 class="modal-title">
          {{ isViewMode ? '기록 내용' : `${formattedDate}` }}
        </h3>
        <div v-if="isViewMode" class="diary-timestamp">
          {{ formattedDateTime }}
        </div>
      </div>

      <!-- 2. 초기 화면 (작성 전) -->
      <div v-if="!isViewMode && !showForm" class="diary-empty">
        <div class="empty-message">
          <button @click="startWriting" class="btn btn-primary" type="button">
            오늘 기록 남기기
          </button>
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

        <div class="modal-actions">
          <button @click="cancelWriting" class="btn btn-secondary" type="button">
            취소
          </button>
          <button @click="handleSave" class="btn btn-primary" type="button" :disabled="!isValid || saving">
            {{ saving ? '저장 중...' : '오늘 기록하기' }}
          </button>
        </div>
      </div>

      <!-- 4. 상세보기 모드 (결과 화면) -->
      <div v-else class="diary-view">
        <!-- 감정 아이콘 -->
        <div class="view-emoji">
          <div class="emoji-container">
            <img :src="getMoodEmoji(currentDiary.mood_level)" class="emoji-large" alt="mood" />
            <div class="emoji-info">
              <span class="emoji-label">{{ getMoodName(currentDiary.mood_level) }}</span>
              <!-- AI 뱃지는 분석 완료 시에만 보여줌 -->
              <span v-if="!isProcessing && currentDiary.ai_prediction && !currentDiary.ai_prediction.includes('분석 중')" class="ai-prediction-badge">
                AI: {{ currentDiary.ai_prediction }}
              </span>
            </div>
          </div>
          
          <!-- [핵심] AI 진행 상황 표시 (분석 중일 때) -->
          <div v-if="isProcessing" class="ai-loading-section">
            <div class="loading-header">
               <span class="loading-msg">{{ loadingMessage }}</span>
               <span class="loading-timer" v-if="eta > 0">{{ eta }}초 남음</span>
            </div>
            <div class="progress-track">
               <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>

          <!-- [핵심] AI 코멘트 표시 (분석 완료 시) -->
          <div v-else-if="currentDiary.ai_comment" class="ai-comment-box">
             <span class="ai-icon">💌</span>
             <p class="ai-comment-text">{{ currentDiary.ai_comment }}</p>
          </div>
        </div>

        <!-- 질문 답변 리스트 -->
        <div class="view-answers">
          <div v-if="currentDiary.event" class="answer-item">
            <h4 class="answer-question">오늘 무슨일이 있었나요?</h4>
            <p class="answer-text">{{ currentDiary.event }}</p>
          </div>
          <div v-if="currentDiary.emotion_desc" class="answer-item">
            <h4 class="answer-question">어떤 감정이 들었나요?</h4>
            <p class="answer-text">{{ currentDiary.emotion_desc }}</p>
          </div>
          <div v-if="currentDiary.emotion_meaning" class="answer-item">
            <h4 class="answer-question">마지막으로 더 깊게 자신의 감정을 써보세요.</h4>
            <p class="answer-text">{{ currentDiary.emotion_meaning }}</p>
          </div>
          <div v-if="currentDiary.self_talk" class="answer-item">
            <h4 class="answer-question">나에게 따듯한 위로를 보내세요.</h4>
            <p class="answer-text">{{ currentDiary.self_talk }}</p>
          </div>
        </div>

        <!-- 하단 버튼 -->
        <div class="modal-actions">
          <button @click="handleDelete" class="btn btn-danger" type="button">삭제하기</button>
          <button @click="handleEdit" class="btn btn-secondary" type="button">수정하기</button>
          <button @click="$emit('close')" class="btn btn-primary" type="button">닫기</button>
        </div>
      </div>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted } from 'vue'
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
    // === Utils & Data ===
    const isViewMode = ref(!!props.diary)
    const showForm = ref(false)
    const saving = ref(false)
    
    // 이 변수가 화면에 보여지는 실제 데이터입니다.
    // 처음엔 props.diary를 쓰지만, 저장 후에는 서버 응답값을 씁니다.
    const localDiary = ref(null) 

    const currentDiary = computed(() => {
        return localDiary.value || props.diary || {}
    })

    // === AI Progress State ===
    const isProcessing = ref(false)
    const progressPercent = ref(0)
    const loadingMessage = ref('AI 분석 준비 중...')
    const eta = ref(0)
    const timerIds = ref([]) // interval ID 관리

    // === Constants ===
    const moodLevels = { 'angry': 1, 'sad': 2, 'neutral': 3, 'calm': 4, 'happy': 5 }
    const moodLevelToName = { 1: 'angry', 2: 'sad', 3: 'neutral', 4: 'calm', 5: 'happy' }
    const emojiMap = {
      1: { icon: angryImg, name: '화나' }, 2: { icon: sadImg, name: '우울해' },
      3: { icon: neutralImg, name: '그저그래' }, 4: { icon: calmImg, name: '편안해' },
      5: { icon: happyImg, name: '행복해' }
    }

    // === Form Data ===
    const formData = ref({
      mood: 'neutral',
      question1: '', question2: '', question3: '', question4: ''
    })

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

    // === Methods ===
    const getMoodEmoji = (lvl) => emojiMap[lvl]?.icon || ''
    const getMoodName = (lvl) => emojiMap[lvl]?.name || ''

    // === AI Polling Logic (The Core) ===
    const clearTimers = () => {
        timerIds.value.forEach(id => clearInterval(id))
        timerIds.value = []
    }

    // 1. 진짜 Polling (Task ID 있을 때)
    const startRealPolling = (taskId) => {
        console.log("🚀 Starting Real Polling for Task:", taskId)
        isProcessing.value = true
        progressPercent.value = 5
        loadingMessage.value = "AI가 일기를 읽고 있습니다..."
        eta.value = 15

        // Countdown
        const cdTimer = setInterval(() => { if(eta.value > 0) eta.value-- }, 1000)
        timerIds.value.push(cdTimer)

        // Status Check
        const pollTimer = setInterval(async () => {
            try {
                const status = await diaryAPI.getTaskStatus(taskId)
                console.log("Polling Status:", status)

                if (status.state === 'PROGRESS') {
                    progressPercent.value = status.process_percent
                    loadingMessage.value = status.message
                    if(status.eta_seconds > 0) eta.value = status.eta_seconds
                } 
                else if (status.state === 'SUCCESS') {
                    console.log("✅ Analysis Complete!")
                    finishPolling()
                } 
                else if (status.state === 'FAILURE') {
                    console.error("❌ Analysis Failed")
                    isProcessing.value = false
                    loadingMessage.value = "분석 실패"
                    clearTimers()
                }
            } catch (e) { console.error(e) }
        }, 1000)
        timerIds.value.push(pollTimer)
    }

    // 2. 가짜 Polling (Task ID 없을 때, 재접속 시)
    const startFakePolling = () => {
        console.log("👻 Starting Fallback Polling")
        isProcessing.value = true
        loadingMessage.value = "이전 분석 작업을 확인 중입니다..."
        progressPercent.value = 30
        eta.value = 10

        const interval = setInterval(async () => {
            // Fake Progress Animation
            if (progressPercent.value < 90) progressPercent.value += 5
            if (eta.value > 0) eta.value--

            // Check DB directly
            if (currentDiary.value.id) {
                try {
                    const fresh = await diaryAPI.getDiary(currentDiary.value.id)
                    // 만약 '분석 중' 텍스트가 사라졌다면 완료된 것!
                    if (fresh.ai_prediction && !fresh.ai_prediction.includes('분석 중')) {
                        console.log("✅ DB Check: Analysis Finished!")
                        localDiary.value = fresh 
                        finishPolling()
                    }
                } catch (e) {}
            }
        }, 2000)
        timerIds.value.push(interval)
    }

    const finishPolling = async () => {
        clearTimers()
        isProcessing.value = false
        progressPercent.value = 100
        
        // 최종 데이터 갱신
        if (currentDiary.value.id) {
            const finalData = await diaryAPI.getDiary(currentDiary.value.id)
            localDiary.value = finalData
        }
        emit('saved')
    }

    // === Handlers ===
    const handleSave = async () => {
        saving.value = true
        try {
            const payload = {
                date: props.date,
                mood: formData.value.mood,
                question1: formData.value.question1, 
                question2: formData.value.question2,
                question3: formData.value.question3, 
                question4: formData.value.question4
            }

            let result = null
            if (props.diary) result = await diaryAPI.updateDiary(props.diary.id, payload)
            else result = await diaryAPI.createDiary(payload)

            // 즉시 화면 갱신 (로딩 상태)
            localDiary.value = result
            isViewMode.value = true
            showForm.value = false

            // Polling 시작
            if (result.task_id) startRealPolling(result.task_id)
            else startFakePolling() // Task ID 없으면 Fallback

            emit('saved')
        } catch (e) {
            alert('저장 실패: ' + e.message)
        } finally {
            saving.value = false
        }
    }

    const startWriting = () => { showForm.value = true }
    const cancelWriting = () => { showForm.value = false; emit('close') }
    const handleEdit = () => {
        isViewMode.value = false
        showForm.value = true
        // 데이터 채우기
        const d = currentDiary.value
        formData.value = {
            mood: moodLevelToName[d.mood_level] || 'neutral',
            question1: d.event||'', question2: d.emotion_desc||'',
            question3: d.emotion_meaning||'', question4: d.self_talk||''
        }
    }
    const handleDelete = async () => {
        if(!confirm('삭제하시겠습니까?')) return
        try {
            await diaryAPI.deleteDiary(currentDiary.value.id)
            emit('saved'); emit('close')
        } catch(e) { alert('삭제 실패') }
    }

    // === Watchers ===
    // 1. Props 변경 시 초기화
    watch(() => props.diary, (newVal) => {
        isViewMode.value = !!newVal
        localDiary.value = null 
        clearTimers()
        isProcessing.value = false
        
        if (newVal) {
             // 폼 데이터 초기화
             formData.value = {
                mood: moodLevelToName[newVal.mood_level] || 'neutral',
                question1: newVal.event||'', question2: newVal.emotion_desc||'',
                question3: newVal.emotion_meaning||'', question4: newVal.self_talk||''
            }
            // 2. 이미 열었을 때 '분석 중'이면 Fallback Polling 시작
            if (newVal.ai_prediction && newVal.ai_prediction.includes('분석 중')) {
                startFakePolling()
            }
        }
    }, { immediate: true })

    onUnmounted(() => clearTimers())

    return {
        isViewMode, showForm, saving, formData,
        currentDiary, formattedDate, formattedDateTime, isValid,
        getMoodEmoji, getMoodName,
        handleSave, startWriting, cancelWriting, handleEdit, handleDelete,
        // AI State
        isProcessing, progressPercent, loadingMessage, eta
    }
  }
}
</script>

<style scoped>
/* 기존 스타일 유지 + AI Progress Bar 스타일 추가 */
.diary-panel { height: 100%; overflow-y: auto; padding: 24px; background: #fff; }
.modal-header { border-bottom: 2px solid #eee; padding-bottom: 16px; margin-bottom: 24px; }
.modal-title { font-size: 18px; font-weight: bold; margin-bottom: 4px; }
.diary-timestamp { font-size: 13px; color: #888; }

.diary-empty, .diary-form { display: flex; flex-direction: column; gap: 20px; }
.empty-message { text-align: center; padding: 40px 0; }
.btn { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; font-size: 14px; transition: 0.2s; }
.btn-primary { background: #FFD93D; color: #333; } /* Yellow Theme */
.btn-primary:hover { background: #FFC107; }
.btn-primary:disabled { background: #eee; cursor: not-allowed; }
.btn-secondary { background: #717171; color: white; display: inline-block; margin-right: 8px;}
.btn-danger { background: #ff4757; color: white; display: inline-block; margin-right: 8px;}
.modal-actions { margin-top: 24px; border-top: 1px solid #eee; padding-top: 16px; display: flex; justify-content: flex-end; }

/* View Mode */
.view-emoji { background: #FFF9C4; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; margin-bottom: 24px; }
.emoji-container { display: flex; align-items: center; gap: 16px; }
.emoji-large { width: 80px; height: 80px; }
.emoji-info { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.emoji-label { font-size: 18px; font-weight: bold; }
.ai-prediction-badge { font-size: 12px; background: rgba(0,0,0,0.1); padding: 4px 8px; border-radius: 4px; }

.ai-comment-box { background: rgba(255,255,255,0.8); padding: 16px; border-radius: 8px; width: 100%; display: flex; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.ai-comment-text { font-size: 14px; line-height: 1.6; white-space: pre-wrap; }

/* [NEW] AI Loading Section Style */
.ai-loading-section { width: 100%; background: rgba(255,255,255,0.6); padding: 16px; border-radius: 8px; margin-top: 12px; }
.loading-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: #555; margin-bottom: 8px; }
.loading-msg { color: #333; }
.loading-timer { color: #FF9800; }
.progress-track { width: 100%; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #FFD93D; transition: width 0.5s ease; }

.view-answers { display: flex; flex-direction: column; gap: 20px; }
.answer-item { background: #f8f9fa; padding: 16px; border-radius: 8px; }
.answer-question { font-size: 14px; color: #333; margin-bottom: 8px; font-weight: bold; }
.answer-text { font-size: 14px; color: #666; line-height: 1.6; white-space: pre-wrap; }
</style>
