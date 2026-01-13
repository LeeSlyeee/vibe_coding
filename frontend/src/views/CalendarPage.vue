<template>
  <div class="calendar-page">
    <div class="calendar-layout">
      <!-- 왼쪽: 캘린더 -->
      <div class="calendar-section">
        <!-- 월 네비게이션 -->
        <div class="month-navigation">
          <button @click="previousMonth" class="nav-btn" type="button">
            ‹
          </button>
          <h2 class="current-month">{{ formattedMonth }}</h2>
          <button @click="nextMonth" class="nav-btn" type="button">
            ›
          </button>
        </div>

        <!-- 달력 그리드 -->
        <CalendarGrid
          :year="currentYear"
          :month="currentMonth"
          :diaries="diaries"
          :selected-date="selectedDate"
          @date-click="handleDateClick"
        />
      </div>

      <!-- 오른쪽: 일기 작성/상세보기 패널 -->
      <div class="diary-section">
        <DiaryModal
          v-if="selectedDate"
          :date="selectedDate"
          :diary="selectedDiary"
          @close="closePanel"
          @saved="handleDiarySaved"
        />
        <div v-else class="empty-panel">
          <p>날짜를 선택하여 일기를 작성하거나 확인하세요</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import CalendarGrid from '../components/CalendarGrid.vue'
import DiaryModal from '../components/DiaryModal.vue'
import { diaryAPI } from '../services/api'

export default {
  name: 'CalendarPage',
  components: {
    CalendarGrid,
    DiaryModal
  },
  setup() {
    const currentYear = ref(new Date().getFullYear())
    const currentMonth = ref(new Date().getMonth() + 1)
    const diaries = ref([])
    const selectedDate = ref(null)
    const selectedDiary = ref(null)

    const formattedMonth = computed(() => {
      return `${currentYear.value}년 ${currentMonth.value}월`
    })

    const previousMonth = () => {
      if (currentMonth.value === 1) {
        currentMonth.value = 12
        currentYear.value--
      } else {
        currentMonth.value--
      }
      loadDiaries()
    }

    const nextMonth = () => {
      if (currentMonth.value === 12) {
        currentMonth.value = 1
        currentYear.value++
      } else {
        currentMonth.value++
      }
      loadDiaries()
    }

    const loadDiaries = async () => {
      try {
        const data = await diaryAPI.getDiaries(currentYear.value, currentMonth.value)
        // 백엔드가 배열을 직접 반환하며, created_at을 date로 변환 필요
        const diaryArray = Array.isArray(data) ? data : (data.diaries || [])
        
        // mood_level 숫자를 mood 문자열로 변환하는 매핑
        const moodMap = {
          1: 'angry',    // 화남
          2: 'sad',      // 우울함
          3: 'neutral',  // 그저그래
          4: 'calm',     // 편안함
          5: 'happy'     // 행복함
        }
        
        diaries.value = diaryArray.map(d => ({
          ...d,
          date: d.created_at ? d.created_at.split('T')[0] : d.date,
          mood: d.mood_level ? moodMap[d.mood_level] : (d.mood || null)  // mood_level 숫자를 문자열로 변환
        }))
      } catch (error) {
        console.error('Failed to load diaries:', error)
        diaries.value = []
      }
    }

    const handleDateClick = async (date) => {
      selectedDate.value = date.dateString
      
      // 해당 날짜의 일기가 있는지 확인 (created_at과 date 둘 다 체크)
      const existingDiary = diaries.value.find(d => {
        const diaryDate = d.date || (d.created_at ? d.created_at.split('T')[0] : null)
        return diaryDate === date.dateString
      })
      
      if (existingDiary) {
        // 일기가 있으면 상세보기
        try {
          const loadedDiary = await diaryAPI.getDiary(existingDiary.id)
          
          // mood_level 숫자를 mood 문자열로 변환
          const moodMap = {
            1: 'angry',
            2: 'sad',
            3: 'neutral',
            4: 'calm',
            5: 'happy'
          }
          
          // 백엔드 필드명을 프론트엔드 형식으로 변환
          selectedDiary.value = {
            ...loadedDiary,
            date: loadedDiary.created_at ? loadedDiary.created_at.split('T')[0] : loadedDiary.date,
            mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
            question1: loadedDiary.event || '',
            question2: loadedDiary.emotion_desc || '',
            question3: loadedDiary.emotion_meaning || '',
            question4: loadedDiary.self_talk || ''
          }
        } catch (error) {
          console.error('Failed to load diary:', error)
          selectedDiary.value = existingDiary
        }
      } else {
        // 일기가 없으면 새로 작성
        selectedDiary.value = null
      }
    }

    const closePanel = () => {
      selectedDate.value = null
      selectedDiary.value = null
    }

    const handleDiarySaved = async () => {
      // 일기 저장 후 목록 다시 로드
      await loadDiaries()
      
      // 현재 선택된 날짜가 있으면 해당 일기 다시 로드
      if (selectedDate.value) {
        const existingDiary = diaries.value.find(d => {
          const diaryDate = d.date || (d.created_at ? d.created_at.split('T')[0] : null)
          return diaryDate === selectedDate.value
        })
        
        if (existingDiary) {
          try {
            const loadedDiary = await diaryAPI.getDiary(existingDiary.id)
            
            // mood_level 숫자를 mood 문자열로 변환
            const moodMap = {
              1: 'angry',
              2: 'sad',
              3: 'neutral',
              4: 'calm',
              5: 'happy'
            }
            
            // 최신 데이터로 selectedDiary 업데이트
            selectedDiary.value = {
              ...loadedDiary,
              date: loadedDiary.created_at ? loadedDiary.created_at.split('T')[0] : loadedDiary.date,
              mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
              question1: loadedDiary.event || '',
              question2: loadedDiary.emotion_desc || '',
              question3: loadedDiary.emotion_meaning || '',
              question4: loadedDiary.self_talk || ''
            }
          } catch (error) {
            console.error('Failed to reload diary:', error)
          }
        }
      }
    }

    onMounted(() => {
      loadDiaries()
    })

    return {
      currentYear,
      currentMonth,
      formattedMonth,
      diaries,
      selectedDate,
      selectedDiary,
      previousMonth,
      nextMonth,
      handleDateClick,
      closePanel,
      handleDiarySaved
    }
  }
}
</script>

<style scoped>
.calendar-page {
  min-height: calc(100vh - 56px);
  padding: var(--spacing-xl);
  background-color: var(--bg-primary);
}

.calendar-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  max-width: 1400px;
  margin: 0 auto;
}

.calendar-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-lg);
}

.diary-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.empty-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--spacing-xl);
  color: var(--color-text-light);
  text-align: center;
}

.month-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 2px solid var(--color-border);
}

.current-month {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
}

.nav-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  background-color: var(--bg-card);
  border-radius: var(--radius-md);
  font-size: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
}

.nav-btn:hover {
  background-color: var(--color-hover);
  border-color: var(--color-primary);
  transform: scale(1.05);
}

@media (max-width: 1024px) {
  .calendar-layout {
    grid-template-columns: 1fr;
  }
  
  .diary-section {
    min-height: 500px;
  }
}

@media (max-width: 768px) {
  .calendar-page {
    padding: var(--spacing-md);
  }
  
  .calendar-section {
    padding: var(--spacing-lg);
  }
  
  .current-month {
    font-size: 18px;
  }
}
</style>
