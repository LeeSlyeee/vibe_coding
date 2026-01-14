<template>
  <div class="diary-panel">
      <!-- 헤더 -->
      <div class="modal-header">
        <h3 class="modal-title">
          {{ isViewMode ? '기록 내용' : `${formattedDate}` }}
        </h3>
        <div v-if="isViewMode" class="diary-timestamp">
          {{ diary.createdAt ? formatDateTime(diary.createdAt) : '' }}
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
            <img :src="getMoodEmoji(diary.mood)" class="emoji-large" alt="mood" />
            <div class="emoji-info">
              <span class="emoji-label">{{ getMoodName(diary.mood) }}</span>
              <span v-if="diary.ai_prediction" class="ai-prediction-badge">AI: {{ diary.ai_prediction }}</span>
            </div>
          </div>
          
          <div v-if="diary.ai_comment" class="ai-comment-box">
             <span class="ai-icon">💌</span>
             <p class="ai-comment-text">{{ diary.ai_comment }}</p>
          </div>
        </div>

        <!-- 답변들 -->
        <div class="view-answers">
          <div v-if="diary.question1" class="answer-item">
            <h4 class="answer-question">오늘 무슨일이 있었나요?</h4>
            <p class="answer-text">{{ diary.question1 }}</p>
          </div>

          <div v-if="diary.question2" class="answer-item">
            <h4 class="answer-question">어떤 감정이 들었나요?</h4>
            <p class="answer-text">{{ diary.question2 }}</p>
          </div>

          <div v-if="diary.question3" class="answer-item">
            <h4 class="answer-question">마지막으로 더 깊게 자신의 감정을 써보세요.</h4>
            <p class="answer-text">{{ diary.question3 }}</p>
          </div>

          <div v-if="diary.question4" class="answer-item">
            <h4 class="answer-question">나에게 따듯한 위로를 보내세요.</h4>
            <p class="answer-text">{{ diary.question4 }}</p>
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
import { ref, computed, watch } from 'vue'
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
    const showForm = ref(false) // 작성 폼 표시 여부
    const saving = ref(false)
    
    const formData = ref({
      mood: props.diary?.mood || '',
      question1: props.diary?.question1 || '',
      question2: props.diary?.question2 || '',
      question3: props.diary?.question3 || '',
      question4: props.diary?.question4 || ''
    })

    const formattedDate = computed(() => {
      if (!props.date) return ''
      const [year, month, day] = props.date.split('-')
      return `${parseInt(month)}월 ${parseInt(day)}일`
    })

    const isValid = computed(() => {
      return formData.value.mood && 
             formData.value.question1.trim() && 
             formData.value.question2.trim()
    })

    const emojiMap = {
      'happy': { icon: happyImg, name: '행복해' },
      'calm': { icon: calmImg, name: '편안해' },
      'neutral': { icon: neutralImg, name: '그저그래' },
      'sad': { icon: sadImg, name: '우울해' },
      'angry': { icon: angryImg, name: '화나' }
    }

    const getMoodEmoji = (mood) => {
      // Return image path or empty string if not found, to handle img src
      return emojiMap[mood]?.icon || '' 
    }

    const getMoodName = (mood) => {
      return emojiMap[mood]?.name || ''
    }

    const formatDateTime = (datetime) => {
      const date = new Date(datetime)
      return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    }

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

        if (props.diary) {
          // 일기 수정
          await diaryAPI.updateDiary(props.diary.id, data)
          
          // 수정 후 상세보기 모드로 전환
          isViewMode.value = true
          showForm.value = false
          
          // 부모 컴포넌트에 saved 이벤트만 전송 (모달은 닫지 않음)
          emit('saved')
        } else {
          // 일기 생성
          await diaryAPI.createDiary(data)
          
          // 생성 후에는 모달 닫기
          emit('saved')
        }
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
    }

    const startWriting = () => {
      showForm.value = true
    }

    const cancelWriting = () => {
      showForm.value = false
      emit('close')
    }

    const handleDelete = async () => {
      if (!props.diary?.id) return
      
      if (confirm('정말 이 일기를 삭제하시겠습니까?')) {
        try {
          await diaryAPI.deleteDiary(props.diary.id)
          alert('일기가 삭제되었습니다.')
          emit('saved') // 삭제 후 목록 새로고침
          emit('close')
        } catch (error) {
          console.error('Failed to delete diary:', error)
          alert('삭제에 실패했습니다.')
        }
      }
    }

    watch(() => props.diary, (newDiary) => {
      isViewMode.value = !!newDiary
      if (newDiary) {
        formData.value = {
          mood: newDiary.mood || '',
          question1: newDiary.question1 || '',
          question2: newDiary.question2 || '',
          question3: newDiary.question3 || '',
          question4: newDiary.question4 || ''
        }
      }
    })

    return {
      isViewMode,
      showForm,
      saving,
      formData,
      formattedDate,
      isValid,
      getMoodEmoji,
      getMoodName,
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
