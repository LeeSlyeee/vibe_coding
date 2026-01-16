<template>
  <div class="calendar-page">
    <div class="calendar-layout">
      <!-- 왼쪽: 캘린더 -->
      <div class="calendar-section">
        <!-- 월 네비게이션 & 검색 바 -->
        <!-- 상단 네비게이션 (시원시원한 디자인) -->
        <div class="calendar-header-v2">
          <div class="month-navigation-v2">
            <button @click="previousMonth" class="nav-btn-v2" type="button">‹</button>
            <h2 class="current-month-v2">{{ formattedMonth }}</h2>
            <button @click="nextMonth" class="nav-btn-v2" type="button">›</button>
          </div>
          
          <div class="search-box-v2">
            <div class="search-input-wrapper">
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="어떤 기록을 찾으시나요?" 
                class="search-input-v2"
                @keyup.enter="handleSearch"
              />
              <button @click="handleSearch" class="search-btn-v2">🔍</button>
            </div>
          </div>
        </div>
        <!-- 일기 요약 통계 -->
        <!-- 일기 요약 통계 (고급스럽고 미니멀한 버젼) -->
        <transition name="fade">
          <div v-if="diaries.length > 0 && !isSearching" class="stats-premium-banner">
             <div class="stat-group">
                <span class="stat-icon">📅</span>
                <span class="stat-info">이번 달 <strong>{{ diaries.length }}개</strong>의 기록이 있습니다</span>
             </div>
             <div class="stat-divider-v2"></div>
             <div class="stat-group">
                <span class="stat-icon">{{ dominantMood.emoji }}</span>
                <span class="stat-info">주로 <strong>{{ dominantMood.name }}</strong> 감정을 느끼셨네요</span>
             </div>
          </div>
        </transition>
        <!-- 검색 결과 리스트 (검색 중일 때) -->
        <div v-if="isSearching" class="search-results-overlay">
           <div class="search-header">
              <h3>검색 결과: "{{ searchQuery }}"</h3>
              <button @click="closeSearch" class="close-search">닫기</button>
           </div>
           <div class="results-list" v-if="searchResults.length > 0">
              <div v-for="item in searchResults" :key="item.id" class="search-item" @click="viewDiary(item)">
                 <div class="search-item-date">{{ item.date }}</div>
                 <div class="search-item-text">{{ item.event }}</div>
              </div>
           </div>
           <p v-else class="no-results">검색 결과가 없습니다.</p>
        </div>

        <!-- 달력 그리드 (일반 모드) -->
        <CalendarGrid
          v-else
          :year="currentYear"
          :month="currentMonth"
          :diaries="diaries"
          :selected-date="selectedDate"
          @date-click="handleDateClick"
        />
      </div>

      <!-- 오른쪽: 일기 작성/상세보기 패널 -->
      <div class="diary-section" :class="{ 'mobile-active': !!selectedDate }">
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
    const searchQuery = ref('')
    const searchResults = ref([])
    const isSearching = ref(false)

    const formattedMonth = computed(() => {
      return `${currentYear.value}년 ${currentMonth.value}월`
    })

    const dominantMood = computed(() => {
        if (diaries.value.length === 0) return { name: '-', emoji: '😶' }
        const counts = diaries.value.reduce((acc, d) => {
            acc[d.mood] = (acc[d.mood] || 0) + 1
            return acc
        }, {})
        
        let maxMood = 'neutral'
        let maxCount = -1
        for (const [mood, count] of Object.entries(counts)) {
            if (count > maxCount) {
                maxCount = count
                maxMood = mood
            }
        }
        
        const moodMap = {
          'happy': { name: '행복', emoji: '😊' },
          'calm': { name: '평온', emoji: '😌' },
          'neutral': { name: '평범', emoji: '😐' },
          'sad': { name: '우울', emoji: '😢' },
          'angry': { name: '화남', emoji: '😠' }
        }
        return moodMap[maxMood] || { name: '평범', emoji: '😐' }
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
          1: 'angry', 2: 'sad', 3: 'neutral', 4: 'calm', 5: 'happy'
        }
        
        diaries.value = diaryArray.map(d => ({
          ...d,
          date: d.created_at ? d.created_at.split('T')[0] : d.date,
          mood: d.mood_level ? moodMap[d.mood_level] : (d.mood || null)
        }))
      } catch (error) {
        console.error('Failed to load diaries:', error)
        diaries.value = []
      }
    }

    const handleSearch = async () => {
      if (!searchQuery.value.trim()) return
      try {
        isSearching.value = true
        // Search API call (assuming we add it to backend/api)
        // For now, let's just search in current month as a prototype, 
        // but ideally this should be a global search.
        const response = await diaryAPI.searchDiaries(searchQuery.value)
        searchResults.value = response.map(d => ({
            ...d,
            date: d.created_at ? d.created_at.split('T')[0] : d.date
        }))
      } catch (error) {
        console.error('Search failed:', error)
      }
    }

    const closeSearch = () => {
        isSearching.value = false
        searchQuery.value = ''
    }

    const viewDiary = async (item) => {
        selectedDate.value = item.date
        try {
            const loadedDiary = await diaryAPI.getDiary(item.id)
            const moodMap = { 1: 'angry', 2: 'sad', 3: 'neutral', 4: 'calm', 5: 'happy' }
            selectedDiary.value = {
                ...loadedDiary,
                date: loadedDiary.created_at ? loadedDiary.created_at.split('T')[0] : loadedDiary.date,
                mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
                question1: loadedDiary.event || '',
                question2: loadedDiary.emotion_desc || '',
                question3: loadedDiary.emotion_meaning || '',
                question4: loadedDiary.self_talk || ''
            }
            isSearching.value = false // Close results to show detail
        } catch (e) {
            selectedDiary.value = item
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
      handleDiarySaved,
      searchQuery,
      searchResults,
      isSearching,
      dominantMood,
     handleSearch,
      closeSearch,
      viewDiary
    }
  }
}
</script>

<style>
/* Global override to ensure no scrollbars */
html, body {
  overflow: hidden;
  height: 100%;
}
</style>

<style scoped>

.calendar-page {
  height: calc(100vh - 56px); /* Fixed height instead of min-height */
  padding: var(--spacing-lg); /* Reduce padding slightly */
  background-color: var(--bg-primary);
  overflow: hidden; /* Prevent scroll */
  box-sizing: border-box;
}

.calendar-layout {
  display: grid;
  grid-template-columns: 5.5fr 4.5fr;
  /* Ensure children respect the ratio and don't collapse */
  min-width: 0; 
  gap: var(--spacing-lg); /* Reduce gap slightly */
  width: 100%;
  height: 100%; /* Fill parent */
  max-width: 1400px;
  margin: 0 auto;
}

.calendar-section, .diary-section {
    min-width: 0;
    width: 100%;
    /* height: 100%; Remove fixed height forcing 100% stretch */
    height: auto; 
    max-height: 100%; /* Allow it to fill but not forced if content is small */
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Container itself shouldn't scroll, but its content will */
}

.diary-section {
    overflow-y: auto; /* Enable vertical scroll for diary content */
}

.calendar-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg); /* Reduce padding inside card */
  box-shadow: var(--shadow-lg);
}

.diary-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
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

/* V2 Header & Stats Styles */
.calendar-header-v2 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 8px 0;
}

.month-navigation-v2 {
  display: flex;
  align-items: center;
  gap: 20px;
}

.current-month-v2 {
  font-size: 28px;
  font-weight: 800;
  color: #1d1d1f;
  letter-spacing: -1px;
}

.nav-btn-v2 {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.06);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

.nav-btn-v2:hover {
  background: #f5f5f7;
  transform: scale(1.1);
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.search-box-v2 {
  flex: 0 0 320px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-v2 {
  width: 100%;
  padding: 12px 48px 12px 20px;
  background: #f5f5f7;
  border: none;
  border-radius: 25px;
  font-size: 15px;
  color: #1d1d1f;
  transition: all 0.3s ease;
}

.search-input-v2:focus {
  background: white;
  box-shadow: 0 0 0 3px rgba(0,0,0,0.03), 0 4px 12px rgba(0,0,0,0.05);
  outline: none;
}

.search-btn-v2 {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.search-btn-v2:hover {
  opacity: 1;
}

.stats-premium-banner {
  display: flex;
  align-items: center;
  gap: 40px;
  background: white;
  padding: 24px 32px;
  border-radius: 24px;
  margin-bottom: 32px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.03);
  border: 1px solid rgba(0,0,0,0.02);
}

.stat-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  font-size: 24px;
}

.stat-info {
  font-size: 15px;
  color: #666;
  font-weight: 500;
}

.stat-info strong {
  color: #1d1d1f;
  font-weight: 700;
  margin: 0 2px;
}

.stat-divider-v2 {
  width: 1px;
  height: 24px;
  background: #eee;
}

.search-results-overlay {
  flex: 1;
  overflow-y: auto;
  background: white;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.close-search {
  background: #eee;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-item {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: 0.2s;
}

.search-item:hover {
  background: #f9f9f9;
  border-color: #000;
}

.search-item-date {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.search-item-text {
  font-size: 14px;
  color: #333;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
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
    grid-template-columns: 1fr; /* Keep 1 column for tablet but handle stack */
  }
}

@media (max-width: 768px) {
  .calendar-page {
    padding: var(--spacing-sm);
  }
  
  .calendar-section {
    padding: var(--spacing-md);
    height: 100%;
    border-radius: var(--radius-lg);
  }
  
  .calendar-layout {
    display: block; /* No grid on mobile */
  }

  /* Make Diary Section a Full Screen Modal on Mobile */
  .diary-section {
    display: none; /* Hidden by default */
    position: fixed;
    top: 56px; /* Below header */
    left: 0;
    width: 100%;
    height: calc(100% - 56px);
    z-index: 1000;
    margin: 0;
    border-radius: 0;
    animation: slideUp 0.3s ease-out;
  }
  
  .diary-section.mobile-active {
    display: flex; /* Show when active */
  }
  
  .current-month {
    font-size: 18px;
  }
}

/* Mobile Landscape Mode Adjustment */
@media (max-width: 915px) and (orientation: landscape) {
  .calendar-page {
    height: 100vh; /* Full viewport height */
    padding: var(--spacing-xs);
    overflow: hidden;
  }

  .calendar-layout {
    display: grid;
    grid-template-columns: 1fr 1fr; /* Side by side 50:50 */
    gap: var(--spacing-sm);
    height: 100%;
  }

  /* Reset Calendar Section */
  .calendar-section {
    height: 100%;
    overflow-y: auto; /* Scrollable if needed */
    padding: var(--spacing-sm);
  }

  /* Reset Diary Section from Mobile Modal to Side Panel */
  .diary-section {
    display: flex !important; /* Force display */
    position: static; /* Not fixed anymore */
    width: 100%;
    height: 100%;
    border-radius: var(--radius-lg);
    background-color: var(--bg-card);
    z-index: 1; /* Reset z-index */
    animation: none; /* No slide up */
  }
  
  /* Adjust internal spacing for landscape */
  .nav-btn {
    width: 32px;
    height: 32px;
    font-size: 18px;
  }
  
  .current-month {
    font-size: 16px;
  }
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
