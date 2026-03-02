<template>
  <div class="calendar-page">
    <div class="calendar-layout">
      <!-- 왼쪽: 캘린더 -->
      <div class="calendar-section">
        <!-- 월 네비게이션 & 검색 바 -->
        <div class="calendar-header-v2">
          <div class="month-navigation-v2">
            <button @click="previousMonth" class="nav-btn-v2" type="button">‹</button>
            <h2 class="current-month-v2">{{ formattedMonth }}</h2>
            <button @click="nextMonth" class="nav-btn-v2" type="button">›</button>
          </div>

          <div class="header-right-section">
            <div class="search-box-v2">
              <div class="search-input-wrapper">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="검색"
                  class="search-input-v2"
                  @keyup.enter="handleSearch"
                />
                <button @click="handleSearch" class="search-btn-v2">🔍</button>
              </div>
            </div>
          </div>
        </div>
        <!-- 일기 요약 통계 -->
        <transition name="fade">
          <div
            v-if="diaries.length > 0 && !isSearching"
            class="stats-premium-banner cursor-pointer"
            @click="$router.push('/stats')"
          >
            <div class="stat-group">
              <span class="stat-icon">📅</span>
              <span class="stat-info"
                >이번 달 <strong>{{ diaries.length }}개</strong>의 기록</span
              >
            </div>
            <div class="stat-divider-v2"></div>
            <div class="stat-group">
              <span class="stat-icon">{{ dominantMood.emoji }}</span>
              <span class="stat-info"
                >주로 <strong>{{ dominantMood.name }}</strong> 감정</span
              >
            </div>

            <!-- Arrow Icon for navigation hint -->
            <div class="stat-arrow">›</div>
          </div>
        </transition>

        <!-- 마음 온도 카드 -->
        <transition name="fade">
          <div
            v-if="moodTemp.loaded"
            class="mood-temp-card"
            :style="{ borderLeft: '4px solid ' + moodTemp.color }"
          >
            <div
              class="mood-temp-gauge"
              :style="{ backgroundColor: moodTemp.color + '20', color: moodTemp.color }"
            >
              {{ moodTemp.temperature.toFixed(1) }}°
            </div>
            <div class="mood-temp-info">
              <div class="mood-temp-title">
                마음 온도 <span :style="{ color: moodTemp.color }">{{ moodTemp.label }}</span>
              </div>
              <div class="mood-temp-desc">{{ moodTemp.description }}</div>
            </div>
          </div>
        </transition>

        <!-- Premium Modal -->
        <div v-if="showPremiumModal" class="modal-overlay">
          <div class="modal-card premium-modal">
            <button class="close-btn" @click="showPremiumModal = false">×</button>
            <div class="premium-header">
              <h1>마음챙김 플러스 +</h1>
              <p>더 깊은 이해와 치유를 위한 선택</p>
            </div>

            <div class="premium-features">
              <div class="feature-item">
                <span class="icon">📊</span>
                <div class="text">
                  <h3>심층 분석 리포트</h3>
                  <p>나의 감정 패턴과 원인을 깊이 있게 분석해드려요.</p>
                </div>
              </div>
              <div class="feature-item">
                <span class="icon">💬</span>
                <div class="text">
                  <h3>AI 감정 케어</h3>
                  <p>24시간 언제든 내 마음을 기록하고 따뜻한 위로를 받으세요.</p>
                </div>
              </div>
              <div class="feature-item">
                <span class="icon">📈</span>
                <div class="text">
                  <h3>월간 감정 통계</h3>
                  <p>한 달간의 감정 변화를 그래프로 한눈에 확인하세요.</p>
                </div>
              </div>
            </div>

            <div
              class="dobong-notice"
              style="
                background: #f0fdf4;
                padding: 15px;
                border-radius: 12px;
                margin-bottom: 20px;
                text-align: left;
                border: 1px solid #dcfce7;
              "
            >
              <p
                style="
                  margin: 0;
                  color: #15803d;
                  font-size: 13px;
                  line-height: 1.5;
                  font-weight: 500;
                "
              >
                <strong>🏥 보건소/정신건강복지센터 안내</strong><br />
                관할 보건소나 정신건강복지센터에서 서비스를 받으시면 무료 업그레이드가 가능합니다.
              </p>
            </div>

            <div class="price-section">
              <span class="original-price">₩9,900</span>
              <span class="current-price">₩4,900 <small>/월</small></span>
              <span class="badge">런칭 특가 50%</span>
            </div>

            <button class="btn-primary full-width" @click="handleUpgrade">지금 시작하기</button>
            <p class="terms">언제든 해지 가능합니다.</p>
          </div>
        </div>

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

    <!-- Chat Diary FAB -->
    <button class="chat-fab" @click="goToChatDiary" title="한마디 남기기">
      <span class="material-icons">chat</span>
    </button>
  </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import CalendarGrid from "../components/CalendarGrid.vue";
import DiaryModal from "../components/DiaryModal.vue";
import { diaryAPI, authAPI } from "../services/api";
import api from "../services/api";

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

    // Premium Logic
    const isPremium = ref(false);
    const userRiskLevel = ref(1);
    const showPremiumModal = ref(false);

    // 마음 온도
    const moodTemp = ref({
      temperature: 36.5,
      label: "측정 중",
      description: "",
      color: "#86868b",
      loaded: false,
    });

    const fetchMoodTemperature = async () => {
      try {
        const res = await api.get("/mood-temperature");
        if (res && res.data) {
          moodTemp.value = { ...res.data, loaded: true };
        }
      } catch (e) {
        console.error("Mood temperature fetch failed", e);
      }
    };

    const checkUserStatus = async () => {
      try {
        const user = await authAPI.getUserInfo();
        isPremium.value = user.is_premium || false;
        userRiskLevel.value = user.risk_level || 1;
      } catch (e) {
        console.error("User info check failed", e);
      }
    };

    const handleUpgrade = async () => {
      if (confirm("4,900원을 결제하시겠습니까? (테스트)")) {
        try {
          await authAPI.upgradeAccount();
          alert("결제가 완료되었습니다! 이제 프리미엄 기능을 사용하실 수 있습니다.");
          showPremiumModal.value = false;
          await checkUserStatus(); // Refresh status
        } catch (e) {
          alert("결제 처리에 실패했습니다.");
        }
      }
    };

    const formattedMonth = computed(() => {
      return `${currentYear.value}년 ${currentMonth.value}월`;
    });

    const dominantMood = computed(() => {
      if (diaries.value.length === 0) return { name: "-", emoji: "😶" };

      // Korean Label -> Internal Key Mapping (Expanded)
      const labelToKey = {
        행복: "happy",
        기쁨: "happy",
        사랑: "happy",
        설렘: "happy",
        즐거움: "happy",
        흥분: "happy",
        행복해: "happy",
        평온: "calm",
        편안: "calm",
        감사: "calm",
        다짐: "calm",
        안도: "calm",
        평온해: "calm",
        편안해: "calm",
        평범: "neutral",
        무던: "neutral",
        보통: "neutral",
        지루함: "neutral",
        그저그래: "neutral",
        우울: "sad",
        슬픔: "sad",
        지침: "sad",
        피곤: "sad",
        외로움: "sad",
        후회: "sad",
        상처: "sad",
        우울해: "sad",
        분노: "angry",
        화남: "angry",
        짜증: "angry",
        스트레스: "angry",
        싫어: "angry",
        불안: "angry",
        걱정: "angry",
        화가나: "angry",
      };

      const counts = diaries.value.reduce((acc, d) => {
        let key = d.mood; // Default fallback

        let aiLabel = null;
        // Priority 1: AI Emotion field
        if (d.ai_emotion && d.ai_emotion !== "분석중" && d.ai_emotion !== "대기중") {
          aiLabel = d.ai_emotion.trim();
        }
        // Priority 2: AI Prediction Parsing
        else if (d.ai_prediction) {
          let fullText = d.ai_prediction;
          if (
            (fullText.startsWith("'") && fullText.endsWith("'")) ||
            (fullText.startsWith('"') && fullText.endsWith('"'))
          ) {
            fullText = fullText.slice(1, -1);
          }
          const parts = fullText.match(/^([^(]+)(\s\(\d+(\.\d+)?%\))?$/);
          if (parts) {
            aiLabel = parts[1].trim();
          } else {
            aiLabel = fullText.trim();
          }
        }

        if (aiLabel && labelToKey[aiLabel]) {
          key = labelToKey[aiLabel];
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
          // [Fix] Prioritize user-selected date over creation timestamp
          date: d.date || (d.created_at ? d.created_at.split("T")[0] : null),
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
          date: d.date || (d.created_at ? d.created_at.split("T")[0] : null),
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
          date:
            loadedDiary.date ||
            (loadedDiary.created_at ? loadedDiary.created_at.split("T")[0] : null),
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
            date:
              loadedDiary.date ||
              (loadedDiary.created_at ? loadedDiary.created_at.split("T")[0] : null),
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
              date:
                loadedDiary.date ||
                (loadedDiary.created_at ? loadedDiary.created_at.split("T")[0] : null),
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
      checkUserStatus();
      fetchMoodTemperature();
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
      isPremium,
      userRiskLevel,
      showPremiumModal,
      handleUpgrade,
      viewDiary,
      goToChatDiary: () => {
        if (selectedDate.value) {
          router.push(`/diary/chat/${selectedDate.value}`);
        } else {
          router.push("/diary/chat");
        }
      },
      moodTemp,
    };
  },
};
</script>

<style>
/* 마음 온도 카드 */
.mood-temp-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: white;
  padding: 14px 18px;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}
.mood-temp-gauge {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  flex-shrink: 0;
}
.mood-temp-info {
  flex: 1;
}
.mood-temp-title {
  font-size: 13px;
  color: #86868b;
  margin-bottom: 2px;
}
.mood-temp-title span {
  font-weight: 700;
  font-size: 14px;
}
.mood-temp-desc {
  font-size: 12px;
  color: #aeaeb2;
  line-height: 1.4;
}

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

/* Chat Diary FAB - Global */
.chat-fab {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #4a90e2; /* Primary Blue */
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4);
  display: flex !important;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 9999 !important; /* Always on top */
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}
.chat-fab:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.5);
}
.chat-fab:active {
  transform: scale(0.95);
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

.header-right-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box-v2 {
  flex: 0 0 240px;
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

/* Premium Capsule Button (Small Header Style) */
.premium-capsule-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transition: all 0.2s;
  height: 40px;
}

.premium-capsule-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.premium-capsule-btn .p-text {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-card {
  background: white;
  border-radius: 24px;
  width: 100%;
  max-width: 480px;
  position: relative;
  animation: slideUp 0.3s ease-out;
}

.premium-modal {
  padding: 40px;
  text-align: center;
}

.premium-header h1 {
  font-size: 28px;
  color: #1d1d1f;
  margin-bottom: 8px;
}

.premium-header p {
  color: #555;
  margin-bottom: 32px;
}

.premium-features {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.feature-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.feature-item .icon {
  font-size: 24px;
  background: #f5f5f7;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.feature-item .text h3 {
  font-size: 16px;
  margin: 0 0 4px 0;
  color: #1d1d1f;
}

.feature-item .text p {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.4;
}

.price-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.original-price {
  text-decoration: line-through;
  color: #999;
  font-size: 16px;
}

.current-price {
  font-size: 32px;
  font-weight: 800;
  color: #6366f1;
}

.current-price small {
  font-size: 16px;
  color: #666;
  font-weight: 400;
}

.badge {
  background: #ffe4e6;
  color: #e11d48;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 700;
}

.full-width {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  border-radius: 16px;
}

.terms {
  font-size: 12px;
  color: #999;
  margin-top: 16px;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
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
