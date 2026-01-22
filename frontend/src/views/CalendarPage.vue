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
          <div
            v-if="diaries.length > 0 && !isSearching"
            class="stats-premium-banner cursor-pointer"
            @click="$router.push('/stats')"
          >
            <div class="stat-group">
              <span class="stat-icon">📅</span>
              <span class="stat-info"
                >이번 달 <strong>{{ diaries.length }}개</strong>의 기록이 있습니다</span
              >
            </div>
            <div class="stat-divider-v2"></div>
            <div class="stat-group">
              <span class="stat-icon">{{ dominantMood.emoji }}</span>
              <span class="stat-info"
                >주로 <strong>{{ dominantMood.name }}</strong> 감정을 느끼셨네요</span
              >
            </div>

            <!-- Arrow Icon for navigation hint -->
            <div class="stat-arrow">›</div>
          </div>
        </transition>

        <!-- 검색 결과 리스트 (검색 중일 때) -->
        <div v-if="isSearching" class="search-results-overlay">
          <div class="search-header">
            <h3>검색 결과: "{{ searchQuery }}"</h3>
            <button @click="closeSearch" class="close-search">닫기</button>
          </div>
          <div class="results-list" v-if="searchResults.length > 0">
            <div
              v-for="item in searchResults"
              :key="item.id"
              class="search-item"
              @click="viewDiary(item)"
            >
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
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import CalendarGrid from "../components/CalendarGrid.vue";
import DiaryModal from "../components/DiaryModal.vue";
import { diaryAPI } from "../services/api";

export default {
  name: "CalendarPage",
  components: {
    CalendarGrid,
    DiaryModal,
  },
  setup() {
    const router = useRouter();
    const currentYear = ref(new Date().getFullYear());
    const currentMonth = ref(new Date().getMonth() + 1);
    const diaries = ref([]);
    const selectedDate = ref(null);
    const selectedDiary = ref(null);
    const searchQuery = ref("");
    const searchResults = ref([]);
    const isSearching = ref(false);

    const formattedMonth = computed(() => {
      return `${currentYear.value}년 ${currentMonth.value}월`;
    });

    const dominantMood = computed(() => {
      if (diaries.value.length === 0) return { name: "-", emoji: "😶" };

      // Korean Label -> Internal Key Mapping
      const labelToKey = {
        행복해: "happy",
        기쁨: "happy",
        평온해: "calm",
        편안해: "calm",
        그저그래: "neutral",
        평범: "neutral",
        우울해: "sad",
        슬픔: "sad",
        화가나: "angry",
        분노: "angry",
      };

      const counts = diaries.value.reduce((acc, d) => {
        let key = d.mood; // Default fallback

        // Try to use AI Prediction
        if (d.ai_prediction) {
          // Extract 'label' from "AI... 'label (95%)'..." or just "label"
          const match = d.ai_prediction.match(/'([^']+)'/);
          if (match && match[1]) {
            // "평온해 (90%)" -> "평온해"
            let label = match[1].split("(")[0].trim();
            if (labelToKey[label]) {
              key = labelToKey[label];
            }
          }
        }

        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {});

      let maxMood = "neutral";
      let maxCount = -1;
      for (const [mood, count] of Object.entries(counts)) {
        if (count > maxCount) {
          maxCount = count;
          maxMood = mood;
        }
      }

      const moodMap = {
        happy: { name: "행복", emoji: "😊" },
        calm: { name: "평온", emoji: "😌" },
        neutral: { name: "평범", emoji: "😐" },
        sad: { name: "우울", emoji: "😢" },
        angry: { name: "화남", emoji: "😠" },
      };
      return moodMap[maxMood] || { name: "평범", emoji: "😐" };
    });

    const previousMonth = () => {
      if (currentMonth.value === 1) {
        currentMonth.value = 12;
        currentYear.value--;
      } else {
        currentMonth.value--;
      }
      loadDiaries();
    };

    const nextMonth = () => {
      if (currentMonth.value === 12) {
        currentMonth.value = 1;
        currentYear.value++;
      } else {
        currentMonth.value++;
      }
      loadDiaries();
    };

    const loadDiaries = async () => {
      try {
        const data = await diaryAPI.getDiaries(currentYear.value, currentMonth.value);
        // 백엔드가 배열을 직접 반환하며, created_at을 date로 변환 필요
        const diaryArray = Array.isArray(data) ? data : data.diaries || [];

        // mood_level 숫자를 mood 문자열로 변환하는 매핑
        const moodMap = {
          1: "angry",
          2: "sad",
          3: "neutral",
          4: "calm",
          5: "happy",
        };

        diaries.value = diaryArray.map((d) => ({
          ...d,
          date: d.created_at ? d.created_at.split("T")[0] : d.date,
          mood: d.mood_level ? moodMap[d.mood_level] : d.mood || null,
        }));
      } catch (error) {
        console.error("Failed to load diaries:", error);
        diaries.value = [];
      }
    };

    const handleSearch = async () => {
      if (!searchQuery.value.trim()) return;
      try {
        isSearching.value = true;
        // Search API call (assuming we add it to backend/api)
        // For now, let's just search in current month as a prototype,
        // but ideally this should be a global search.
        const response = await diaryAPI.searchDiaries(searchQuery.value);
        searchResults.value = response.map((d) => ({
          ...d,
          date: d.created_at ? d.created_at.split("T")[0] : d.date,
        }));
      } catch (error) {
        console.error("Search failed:", error);
      }
    };

    const closeSearch = () => {
      isSearching.value = false;
      searchQuery.value = "";
    };

    const viewDiary = async (item) => {
      selectedDate.value = item.date;
      try {
        const loadedDiary = await diaryAPI.getDiary(item.id);
        const moodMap = { 1: "angry", 2: "sad", 3: "neutral", 4: "calm", 5: "happy" };
        selectedDiary.value = {
          ...loadedDiary,
          date: loadedDiary.created_at ? loadedDiary.created_at.split("T")[0] : loadedDiary.date,
          mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
          question1: loadedDiary.event || "",
          question2: loadedDiary.emotion_desc || "",
          question3: loadedDiary.emotion_meaning || "",
          question4: loadedDiary.self_talk || "",
        };
        isSearching.value = false; // Close results to show detail
      } catch (e) {
        selectedDiary.value = item;
      }
    };

    const handleDateClick = async (date) => {
      const today = new Date();
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

      if (date.dateString > todayStr) {
        return;
      }

      selectedDate.value = date.dateString;

      // 해당 날짜의 일기가 있는지 확인 (created_at과 date 둘 다 체크)
      const existingDiary = diaries.value.find((d) => {
        const diaryDate = d.date || (d.created_at ? d.created_at.split("T")[0] : null);
        return diaryDate === date.dateString;
      });

      if (existingDiary) {
        // 일기가 있으면 상세보기
        try {
          const loadedDiary = await diaryAPI.getDiary(existingDiary.id);

          // mood_level 숫자를 mood 문자열로 변환
          const moodMap = {
            1: "angry",
            2: "sad",
            3: "neutral",
            4: "calm",
            5: "happy",
          };

          // 백엔드 필드명을 프론트엔드 형식으로 변환
          selectedDiary.value = {
            ...loadedDiary,
            date: loadedDiary.created_at ? loadedDiary.created_at.split("T")[0] : loadedDiary.date,
            mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
            question1: loadedDiary.event || "",
            sleep_condition: loadedDiary.sleep_condition || loadedDiary.sleep_desc || "",
            question2: loadedDiary.emotion_desc || "",
            question3: loadedDiary.emotion_meaning || "",
            question4: loadedDiary.self_talk || "",
          };
        } catch (error) {
          console.error("Failed to load diary:", error);
          selectedDiary.value = existingDiary;
        }
      } else {
        // 일기가 없으면 새로 작성
        selectedDiary.value = null;
      }
    };

    const closePanel = () => {
      selectedDate.value = null;
      selectedDiary.value = null;
    };

    const handleDiarySaved = async () => {
      // 일기 저장 후 목록 다시 로드
      await loadDiaries();

      // 현재 선택된 날짜가 있으면 해당 일기 다시 로드
      if (selectedDate.value) {
        const existingDiary = diaries.value.find((d) => {
          const diaryDate = d.date || (d.created_at ? d.created_at.split("T")[0] : null);
          return diaryDate === selectedDate.value;
        });

        if (existingDiary) {
          try {
            const loadedDiary = await diaryAPI.getDiary(existingDiary.id);

            // mood_level 숫자를 mood 문자열로 변환
            const moodMap = {
              1: "angry",
              2: "sad",
              3: "neutral",
              4: "calm",
              5: "happy",
            };

            // 최신 데이터로 selectedDiary 업데이트
            selectedDiary.value = {
              ...loadedDiary,
              date: loadedDiary.created_at
                ? loadedDiary.created_at.split("T")[0]
                : loadedDiary.date,
              mood: loadedDiary.mood_level ? moodMap[loadedDiary.mood_level] : null,
              question1: loadedDiary.event || "",
              sleep_condition: loadedDiary.sleep_condition || loadedDiary.sleep_desc || "",
              question2: loadedDiary.emotion_desc || "",
              question3: loadedDiary.emotion_meaning || "",
              question4: loadedDiary.self_talk || "",
            };
          } catch (error) {
            console.error("Failed to reload diary:", error);
          }
        }
      }
    };

    // New Report Functions

    onMounted(() => {
      loadDiaries();
    });



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
      handleSearch,
      closeSearch,
      handleSearch,
      closeSearch,
      viewDiary,
    };
  },
};
</script>

<style>
/* Global override to ensure no scrollbars */
html,
body {
  overflow: hidden;
  height: 100%;
}
</style>

<style scoped>
/* Previous Styles Maintainted... */
.cursor-pointer {
  cursor: pointer;
  transition: transform 0.2s;
}
.cursor-pointer:hover {
  transform: scale(1.02);
}
.stat-arrow {
  margin-left: auto;
  font-size: 24px;
  color: #ccc;
  font-weight: 300;
}
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
  min-width: 0;
  gap: var(--spacing-lg);
  width: 100%;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.calendar-section,
.diary-section {
  min-width: 0;
  width: 100%;
  height: auto;
  max-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.diary-section {
  overflow-y: auto;
}

.calendar-section {
  background-color: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
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

.calendar-header-v2 {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
}

.nav-btn-v2:hover {
  background: #f5f5f7;
  transform: scale(1.1);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
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
  box-shadow:
    0 0 0 3px rgba(0, 0, 0, 0.03),
    0 4px 12px rgba(0, 0, 0, 0.05);
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

/* 퀵 링크 스타일 */
.quick-links {
    display: flex;
    gap: 12px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #f0f0f0;
}

.quick-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
}

.guide-btn {
    background: #eef2ff;
    color: #4f46e5;
}

.stats-btn-main {
    background: #f0fdf4;
    color: #16a34a;
}

.quick-btn:hover {
    transform: translateY(-2px);
    filter: brightness(0.95);
}

.stats-premium-banner {
  display: flex;
  align-items: center;
  gap: 40px;
  background: white;
  padding: 24px 32px;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.02);
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1024px) {
  .calendar-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .calendar-page {
    padding: 0;
    height: 100%; /* Fill available space */
    display: flex; /* Ensure flex layout */
    flex-direction: column;
  }

  .calendar-section {
    padding: 8px; /* Reduce padding to prevent overflow */
    height: 100%;
    border-radius: 0;
    overflow-y: auto;
    flex: 1; /* Take up remaining space */
  }

  .calendar-layout {
    display: block;
    height: 100%;
  }

  /* Stack Header Elements */
  .calendar-header-v2 {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .month-navigation-v2 {
    justify-content: space-between;
    width: 100%;
    padding: 0 10px;
  }

  .search-box-v2 {
    flex: 1;
    width: 100%;
  }

  /* Mobile Fullscreen Diary Panel (Bottom Sheet style) */
  .diary-section {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 60px; /* Leave space for bottom nav */
    z-index: 50; /* Lower than bottom nav (100) */
    margin: 0;
    border-radius: 0;
    padding-bottom: 20px; /* Inner padding */
    animation: slideUp 0.3s ease-out;
    background-color: var(--bg-primary); /* Ensure background is opaque */
    padding-bottom: calc(20px + env(safe-area-inset-bottom));
    /* 헤더에 가리지 않도록 상단 여백 추가 */
    padding-top: 80px;
  }

  .diary-section.mobile-active {
    display: flex;
  }

  .current-month-v2 {
    font-size: 24px;
  }

  .stats-premium-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 20px;
  }

  .stat-divider-v2 {
    display: none;
  } /* Hide divider on mobile */

  .stat-arrow {
    display: none;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Mobile Landscape Split View Optimization */
@media (max-height: 800px) and (orientation: landscape) {
  .calendar-page {
    display: block !important;
    padding: 20px !important;
    /* 고정 높이 해제 -> 전체 스크롤 허용 */
    height: auto !important;
    min-height: 100vh !important;
    overflow-y: auto !important;
    box-sizing: border-box !important;
  }

  .calendar-layout {
    display: grid !important;
    grid-template-columns: 1.2fr 1fr !important;
    gap: 20px !important;
    /* 높이 자동 조절 */
    height: auto !important;
    min-height: 0 !important;
    overflow: visible !important;
  }

  /* 1. Left: Calendar Panel */
  .calendar-section {
    width: 100% !important;
    /* 컨텐츠 크기만큼 늘어남 */
    height: auto !important;
    min-height: 400px !important; /* 최소 높이 보장 */
    border-radius: 16px !important;
    padding: 15px !important;
    overflow: visible !important; /* 내부 스크롤 제거 */
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    flex: none !important;
  }

  /* 2. Right: Diary Panel */
  .diary-section {
    display: flex !important;
    flex-direction: column !important;
    position: static !important;
    width: 100% !important;
    /* 컨텐츠 크기만큼 늘어남 */
    height: auto !important;
    min-height: 400px !important;
    margin: 0 !important;
    z-index: 1 !important;
    background-color: white !important;
    padding-bottom: 0 !important;
    animation: none !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    overflow: visible !important;
    flex: none !important;
  }

  /* 모바일 오버레이 애니메이션 제거 */
  .diary-section.mobile-active {
    animation: none !important;
  }

  /* 헤더 최적화 */
  .calendar-header-v2 {
    flex-direction: row !important;
    justify-content: space-between !important;
    gap: 10px !important;
    margin-bottom: 15px;
  }

  .month-navigation-v2 {
    padding: 0 !important;
    width: auto !important;
  }

  .current-month-v2 {
    font-size: 20px !important;
  }

  .nav-btn-v2 {
    width: 30px !important;
    height: 30px !important;
    font-size: 16px !important;
  }

  /* 검색창 숨김 (공간 확보) or 축소 */
  .search-box-v2 {
    display: none !important;
  }

  /* 통계 배너 숨김 (공간 확보) */
  .stats-premium-banner {
    display: none !important;
  }

  /* Global scroll unlock specific to this view */
  html,
  body {
    overflow-y: auto !important;
    height: auto !important;
  }
}
</style>
