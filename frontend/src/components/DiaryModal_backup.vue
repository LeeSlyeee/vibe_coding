<template>
  <div class="diary-panel">
      <!-- 헤더 -->
      <div class="modal-header">
        <h3 class="modal-title">
          {{ isViewMode ? '기록 내용' : `${formattedDate}` }}
        </h3>
        <div v-if="isViewMode" class="diary-timestamp">
          {{ displayDiary.created_at ? formatDateTime(displayDiary.created_at) : (diary?.created_at ? formatDateTime(diary.created_at) : '') }}
        </div>
      </div>

      <!-- 일기 작성 모드 - 폼 시작 전 초기 화면 -->
      <div v-if="!isViewMode && !showForm" class="diary-empty">
        <div class="empty-message">
          <button @click="startWriting" class="btn btn-primary" type="button">
            오늘 기록 남기기
          </button>
        </div>
      </div>

      <!-- 일기 작성 모드 - 폼 표시 -->
      <div v-else-if="!isViewMode && showForm" class="diary-form">
        <!-- 감정 선택 -->
        <EmojiSelector v-model="formData.mood" />

        <!-- 질문들 -->
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

        <!-- 버튼들 -->
        <div class="modal-actions">
          <button @click="cancelWriting" class="btn btn-secondary" type="button">
            취소
          </button>
          <button @click="handleSave" class="btn btn-primary" type="button" :disabled="!isValid || saving">
            {{ saving ? '저장 중...' : '오늘 기록하기' }}
          </button>
        </div>
      </div>

      <!-- 일기 상세보기 모드 -->
      <div v-else class="diary-view">
        <!-- 선택된 감정 -->
        <div class="view-emoji">
          <div class="emoji-container">
            <img :src="getMoodEmoji(displayDiary.mood_level)" class="emoji-large" alt="mood" />
            <div class="emoji-info">
              <span class="emoji-label">{{ getMoodName(displayDiary.mood_level) }}</span>
              <span v-if="displayDiary.ai_prediction && !showProgressBar" class="ai-prediction-badge">AI: {{ displayDiary.ai_prediction }}</span>
            </div>
          </div>
          
          <!-- AI Progress Bar (Analysis in Progress) -->
          <div v-if="showProgressBar" class="ai-progress-container">
            <div class="progress-info">
              <span class="progress-message">{{ progressData.message || 'AI가 열심히 분석하고 있어요...' }}</span>
              <span class="progress-eta" v-if="progressData.eta > 0">{{ progressData.eta }}초 남음</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: (progressData.percent > 0 ? progressData.percent : 15) + '%' }"></div>
            </div>
          </div>
          
          <div v-if="displayDiary.ai_comment && !showProgressBar" class="ai-comment-box">
             <span class="ai-icon">💌</span>
             <p class="ai-comment-text">{{ displayDiary.ai_comment }}</p>
          </div>
        </div>

        <!-- 답변들 -->
        <div class="view-answers">
          <div v-if="displayDiary.event" class="answer-item">
            <h4 class="answer-question">오늘 무슨일이 있었나요?</h4>
            <p class="answer-text">{{ displayDiary.event }}</p>
          </div>

          <div v-if="displayDiary.emotion_desc" class="answer-item">
            <h4 class="answer-question">어떤 감정이 들었나요?</h4>
            <p class="answer-text">{{ displayDiary.emotion_desc }}</p>
          </div>

          <div v-if="displayDiary.emotion_meaning" class="answer-item">
            <h4 class="answer-question">마지막으로 더 깊게 자신의 감정을 써보세요.</h4>
            <p class="answer-text">{{ displayDiary.emotion_meaning }}</p>
          </div>

          <div v-if="displayDiary.self_talk" class="answer-item">
            <h4 class="answer-question">나에게 따듯한 위로를 보내세요.</h4>
            <p class="answer-text">{{ displayDiary.self_talk }}</p>
          </div>
        </div>

        <!-- 버튼들 -->
        <div class="modal-actions">
          <button @click="handleDelete" class="btn btn-danger" type="button">
            삭제하기
          </button>
          <button @click="handleEdit" class="btn btn-secondary" type="button">
            수정하기
          </button>
          <button @click="$emit('close')" class="btn btn-primary" type="button">
            닫기
          </button>
        </div>
      </div>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted } from 'vue'
import EmojiSelector from './EmojiSelector.vue'
import QuestionAccordion from './QuestionAccordion.vue'
import { diaryAPI } from '../services/api'
import happyImg from '../assets/01.png'
import calmImg from '../assets/02.png'
import neutralImg from '../assets/03.png'
import sadImg from '../assets/04.png'
import angryImg from '../assets/05.png'

export default {
  name: 'DiaryModal',
  components: {
    EmojiSelector,
    QuestionAccordion
  },
  props: {
    date: {
      type: String,
      required: true
    },
    diary: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'saved'],
  setup(props, { emit }) {
    const isViewMode = ref(!!props.diary)
    const showForm = ref(false) 
    const saving = ref(false)
    const localSavedDiary = ref(null) 
    
    // Polling State
    const progressData = ref({
      isAnalyzing: false,
      percent: 0,
      message: '',
      eta: 0,
      timerIds: []
    })
    
    // mood mapping helper
    const moodLevels = {
        'angry': 1, 'sad': 2, 'neutral': 3, 'calm': 4, 'happy': 5
    }
    const moodLevelToName = {
        1: 'angry', 2: 'sad', 3: 'neutral', 4: 'calm', 5: 'happy'
    }

    const formData = ref({
      mood: props.diary ? moodLevelToName[props.diary.mood_level] || 'neutral' : '',
      question1: props.diary?.event || '',
      question2: props.diary?.emotion_desc || '',
      question3: props.diary?.emotion_meaning || '',
      question4: props.diary?.self_talk || ''
    })

    const formattedDate = computed(() => {
      if (!props.date) return ''
      const parts = props.date.split('-')
      if (parts.length < 3) return props.date
      const [year, month, day] = parts
      return `${parseInt(month)}월 ${parseInt(day)}일`
    })

    // Compute which diary to display
    const displayDiary = computed(() => {
      // Prioritize localSavedDiary (newly saved result)
      if (localSavedDiary.value) return localSavedDiary.value
      // Then props.diary (existing entry)
      if (props.diary) return props.diary
      // Fallback empty
      return {}
    })
    
    // Force show progress bar if text says "Analyzing..."
    const showProgressBar = computed(() => {
        const isAnalyzingState = progressData.value.isAnalyzing;
        const hasAnalyzingText = displayDiary.value.ai_prediction && 
                                 displayDiary.value.ai_prediction.includes('분석 중');
        return isAnalyzingState || hasAnalyzingText;
    })

    const isValid = computed(() => {
      return formData.value.mood && 
             formData.value.question1.trim() && 
             formData.value.question2.trim()
    })

    const emojiMap = {
      1: { icon: angryImg, name: '화나' },
      2: { icon: sadImg, name: '우울해' },
      3: { icon: neutralImg, name: '그저그래' },
      4: { icon: calmImg, name: '편안해' },
      5: { icon: happyImg, name: '행복해' },
      // Support string keys just in case
      'angry': { icon: angryImg, name: '화나' },
      'sad': { icon: sadImg, name: '우울해' },
      'neutral': { icon: neutralImg, name: '그저그래' },
      'calm': { icon: calmImg, name: '편안해' },
      'happy': { icon: happyImg, name: '행복해' }
    }

    const getMoodEmoji = (mood) => {
      return emojiMap[mood]?.icon || '' 
    }

    const getMoodName = (mood) => {
      return emojiMap[mood]?.name || ''
    }

    const formatDateTime = (datetime) => {
      if(!datetime) return ''
      const date = new Date(datetime)
      return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }

    // Polling Logic
    const startPolling = (taskId) => {
      progressData.value.isAnalyzing = true;
      progressData.value.percent = 0;
      progressData.value.message = 'AI 분석 준비 중...';
      progressData.value.eta = 15;
      
      const countdownInterval = setInterval(() => {
        if (progressData.value.eta > 0) {
          progressData.value.eta--;
        }
      }, 1000);
      
      const pollInterval = setInterval(async () => {
        try {
          const status = await diaryAPI.getTaskStatus(taskId);
          
          if (status.state === 'PROGRESS') {
            progressData.value.percent = status.process_percent;
            progressData.value.message = status.message;
            if (status.eta_seconds > 0) { 
                 progressData.value.eta = status.eta_seconds; 
            }
          } else if (status.state === 'SUCCESS') {
            stopPolling();
            progressData.value.isAnalyzing = false;
            progressData.value.percent = 100;
            
            // Reload the local saved diary
            const updatedDiary = await diaryAPI.getDiary(displayDiary.value.id);
            localSavedDiary.value = updatedDiary;
            
            emit('saved');
          } else if (status.state === 'FAILURE' || status.state === 'REVOKED') {
            stopPolling();
            progressData.value.isAnalyzing = false;
            progressData.value.message = '분석 실패';
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 1000);
      
      progressData.value.timerIds = [countdownInterval, pollInterval];
    };
    
    const stopPolling = () => {
      progressData.value.timerIds.forEach(id => clearInterval(id));
      progressData.value.timerIds = [];
    };
    
    onUnmounted(() => {
      stopPolling();
    });

    const handleSave = async () => {
      if (!isValid.value) return

      saving.value = true
      try {
        const data = {
          date: props.date,
          mood: formData.value.mood,
          question1: formData.value.question1,
          question2: formData.value.question2,
          question3: formData.value.question3,
          question4: formData.value.question4
        }
        
        let result = null;

        if (props.diary) {
          // Update
          result = await diaryAPI.updateDiary(props.diary.id, data)
        } else {
          // Create
          result = await diaryAPI.createDiary(data)
        }
        
         // Update local state to show View Mode immediately
         localSavedDiary.value = result;
         isViewMode.value = true;
         showForm.value = false;
         
         // Start Polling if task_id exists
         if (result && result.task_id) {
           startPolling(result.task_id);
         }
         
         // Notify parent list (background refresh)
         emit('saved')
         
      } catch (error) {
        console.error('Failed to save diary:', error)
        alert('저장에 실패했습니다.')
      } finally {
        saving.value = false
      }
    }

    const handleEdit = () => {
      isViewMode.value = false
      showForm.value = true
      // Pre-fill form with displayed data
      const current = displayDiary.value;
      if (current) {
          formData.value = {
            mood: moodLevelToName[current.mood_level] || 'neutral',
            question1: current.event || '',
            question2: current.emotion_desc || '',
            question3: current.emotion_meaning || '',
            question4: current.self_talk || ''
          }
      }
    }

    const startWriting = () => {
      showForm.value = true
    }

    const cancelWriting = () => {
      showForm.value = false
      emit('close')
    }

    const handleDelete = async () => {
      const targetId = displayDiary.value.id || props.diary?.id;
      if (!targetId) return
      
      if (confirm('정말 이 일기를 삭제하시겠습니까?')) {
        try {
          await diaryAPI.deleteDiary(targetId)
          alert('일기가 삭제되었습니다.')
          emit('saved') 
          emit('close')
        } catch (error) {
          console.error('Failed to delete diary:', error)
          alert('삭제에 실패했습니다.')
        }
      }
    }

    const startFallbackPolling = () => {
      // Fake Polling for when we don't have task_id (e.g. re-opened modal)
      progressData.value.isAnalyzing = true;
      progressData.value.message = 'AI가 분석하고 있습니다...';
      progressData.value.percent = 30; 
      progressData.value.eta = 10;
      
      const interval = setInterval(async () => {
         // 1. Fake Progress
         if (progressData.value.percent < 90) {
            progressData.value.percent += 5;
         }
         if (progressData.value.eta > 0) {
            progressData.value.eta--;
         }
         
         // 2. Check DB if finished (Blind Check)
         if (displayDiary.value.id) {
             try {
                const check = await diaryAPI.getDiary(displayDiary.value.id);
                if (check.ai_prediction && !check.ai_prediction.includes('분석 중')) {
                    // Finished!
                    clearInterval(interval);
                    progressData.value.isAnalyzing = false;
                    localSavedDiary.value = check; // Refresh View
                    emit('saved');
                }
             } catch(e) {}
         }
      }, 2000); // Check every 2 seconds
      
      progressData.value.timerIds.push(interval);
    }

    watch(() => props.diary, (newDiary) => {
      isViewMode.value = !!newDiary
      localSavedDiary.value = null; 
      // Reset Polling
      stopPolling();
      
      if (newDiary) {
        formData.value = {
          mood: moodLevelToName[newDiary.mood_level] || 'neutral',
          question1: newDiary.event || '',
          question2: newDiary.emotion_desc || '',
          question3: newDiary.emotion_meaning || '',
          question4: newDiary.self_talk || ''
        }
      }
    })
    
    // Watch displayDiary to trigger fallback polling if needed
    watch(() => displayDiary.value, (newVal) => {
        if (newVal.ai_prediction && 
            newVal.ai_prediction.includes('분석 중') && 
            !progressData.value.isAnalyzing) {
            console.log("Triggering Fallback Polling...");
            startFallbackPolling();
        }
    }, { immediate: true, deep: true })

    return {
      isViewMode,
      showForm,
      saving,
      formData,
      formattedDate,
      isValid,
      displayDiary,
      progressData,
      getMoodEmoji,
      getMoodName,
      showProgressBar,
      formatDateTime,
      handleSave,
      handleEdit,
      handleDelete,
      startWriting,
      cancelWriting
    }
  }
}
</script>

<style scoped>
.diary-panel {
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-xl);
  background-color: var(--bg-card);
}

.modal-header {
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
}

.diary-timestamp {
  font-size: 13px;
  color: var(--color-text-light);
}

.diary-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.diary-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: var(--spacing-xl);
}

.empty-message {
  text-align: center;
}

.empty-message .btn {
  padding: var(--spacing-md) var(--spacing-xl);
  font-size: 16px;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: space-between;
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.modal-actions .btn {
  flex: 1;
}

/* 상세보기 모드 스타일 */
.diary-view {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.view-emoji {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  background-color: rgba(255, 217, 61, 0.1);
  border-radius: var(--radius-lg);
}

.emoji-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.emoji-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.emoji-large {
  width: 72px;
  height: 72px;
  object-fit: contain;
}

.emoji-label {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text);
}

.ai-prediction-badge {
  font-size: 12px;
  color: var(--color-text-light);
  background-color: rgba(0, 0, 0, 0.05);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.ai-comment-box {
  margin-top: var(--spacing-md);
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-md);
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.ai-icon {
  font-size: 20px;
}

.ai-comment-text {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.5;
  text-align: left;
  flex: 1;
  font-weight: 500;
  white-space: pre-wrap;
  word-break: break-word;
}


.ai-progress-container {
  margin-top: var(--spacing-md);
  width: 100%;
  max-width: 400px;
  background-color: rgba(255, 255, 255, 0.6);
  padding: 16px;
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--color-text);
  font-weight: 500;
}

.progress-eta {
  color: var(--color-primary);
  font-weight: 600;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--color-primary); /* Yellow/Orange theme */
  border-radius: 4px;
  transition: width 0.5s ease-in-out;
}

.view-answers {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.answer-item {
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
  border-radius: var(--radius-md);
}

.answer-question {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--spacing-sm);
}

.answer-text {
  font-size: 14px;
  color: var(--color-text-light);
  line-height: 1.6;
  white-space: pre-wrap;
}

@media (max-width: 640px) {
  .diary-modal {
    padding: var(--spacing-lg);
  }
  
  .modal-actions {
    flex-direction: column;
  }
}
</style>
