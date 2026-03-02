<template>
  <div class="diary-panel" ref="panelRef">
    <!-- 1. 헤더 영역 -->
    <div class="modal-header">
      <h3 class="modal-title">
        {{ isViewMode ? "기록 내용" : `${formattedDate}` }}
        <!-- 날씨 뱃지 -->
        <div v-if="weatherInfo" class="weather-badge-premium">
          <span class="weather-icon">{{ getWeatherIcon(weatherInfo.desc) }}</span>
          <span class="weather-text">{{ weatherInfo.desc }} {{ weatherInfo.temp }}°C</span>
        </div>
        <!-- 로딩 인디케이터 (빨간색) -->
        <span v-else class="weather-loading"> <span class="pulse"></span> 날씨 확인 중... </span>
      </h3>
      <div v-if="isViewMode" class="diary-timestamp">
        {{ formattedDateTime }}
      </div>
    </div>

    <!-- 2. 초기 화면 (작성 전) -->
    <div v-if="!isViewMode && !showForm" class="diary-empty">
      <div class="empty-message">
        <!-- 통합 인사이트 말풍선 (항상 표시, 로딩/결과 텍스트만 변경) -->
        <div class="insight-bubble insight-bubble-purple">
          <span class="insight-icon">🧘‍♀️</span>
          <span style="color: #4a148c">
            {{
              isLoadingInsight
                ? "마음의 흐름을 읽고 있어요..."
                : mindsetInsight || "오늘 하루는 어떠셨나요? 편안하게 기록해보세요."
            }}
          </span>
        </div>

        <p class="empty-hint">작은 기록이 모여 당신의 마음 지도를 만듭니다.</p>

        <!-- 버튼 -->
        <button @click="startWriting" class="btn btn-primary btn-large shadow-hover" type="button">
          오늘의 감정 기록하기
        </button>
      </div>
    </div>

    <!-- 3. 작성 폼 -->
    <div v-else-if="!isViewMode && showForm" class="diary-form">
      <!-- Voice Loading Indicator (Global) -->
      <div v-if="isTranscribing" class="voice-loading-overlay">
        <div class="voice-loader-box">
          <span class="pulse-mini"></span>
          <span>AI가 받아적고 있어요...</span>
        </div>
      </div>

      <EmojiSelector v-model="formData.mood" />

      <!-- Common: Sleep -->
      <QuestionAccordion
        :question="uiMode === 'red' ? '잠은 푹 주무셨나요? (수면의 질)' : '잠은 잘 주무셨나요?'"
        v-model="formData.question_sleep"
        :required="true"
        :placeholder="'수면 시간이나 수면의 질에 대해 적어주세요...'"
        :recording="activeField === 'question_sleep'"
        @record="toggleRecording('question_sleep')"
      />

      <!-- Common: Event -->
      <QuestionAccordion
        question="오늘 있었던 일은?"
        v-model="formData.question1"
        :required="true"
        :default-open="true"
        placeholder="자유롭게 적어주세요..."
        :recording="activeField === 'question1'"
        @record="toggleRecording('question1')"
      />

      <!-- Red Mode Specific: Physical Symptoms (REMOVED) -->

      <!-- Red Mode Specific: Mood Intensity Slider (REMOVED) -->

      <QuestionAccordion
        question="어떤 감정이 들었나요?"
        v-model="formData.question2"
        :required="true"
        placeholder="감정을 구체적으로 적어주세요..."
        :recording="activeField === 'question2'"
        @record="toggleRecording('question2')"
      />

      <QuestionAccordion
        question="마지막으로 더 깊게 자신의 감정을 써보세요."
        v-model="formData.question3"
        placeholder="감정의 원인을 찾아보세요..."
        :recording="activeField === 'question3'"
        @record="toggleRecording('question3')"
      />

      <QuestionAccordion
        question="나에게 해주고 싶은 말 (칭찬, 위로)"
        v-model="formData.question4"
        placeholder="스스로에게 힘이 되는 말을 적어보세요..."
        :recording="activeField === 'question4'"
        @record="toggleRecording('question4')"
      />

      <!-- Red Mode: Safety Check (REMOVED) -->

      <!-- Medication Check: Only for Severe/Paid Users (Red Mode) -->
      <!-- 경증 사용자(Green)는 약물 체크 불가 -->
      <div
        v-if="uiMode === 'red'"
        class="medication-check-section"
        style="margin-top: 16px; padding: 0 10px"
      >
        <label class="checkbox-container">
          <input type="checkbox" v-model="formData.medication_taken" />
          <span class="checkmark"></span>
          <span style="font-weight: 600; font-size: 15px; margin-left: 8px; color: #555"
            >💊 오늘 약은 챙겨 드셨나요?</span
          >
        </label>
      </div>

      <!-- 작성 모드 하단 버튼 (인라인으로 변경) -->
      <div class="modal-actions-inline">
        <button @click="cancelWriting" class="btn btn-secondary" type="button">취소</button>
        <button
          @click="handleSave"
          class="btn btn-primary"
          type="button"
          :disabled="!isValid || saving"
        >
          {{ saving ? "저장 중..." : "오늘 기록 완료" }}
        </button>
      </div>
    </div>

    <!-- 4. 상세보기 모드 (결과 화면) -->
    <div v-else class="diary-view">
      <div class="view-content-wrapper">
        <!-- 감성적인 감정 카드 -->
        <div class="view-emoji-premium" :class="getMoodColorClass(displayMoodLevel)">
          <div class="emoji-container">
            <img :src="getMoodEmoji(displayMoodLevel)" class="emoji-large anim-float" alt="mood" />
            <!-- 감정 이름 위로 배치 -->
            <span class="emoji-label primary-label">{{ getMoodName(displayMoodLevel) }}</span>

            <!-- AI 분석 결과 아래로 배치 -->
            <span
              v-if="
                !isProcessing &&
                currentDiary.ai_prediction &&
                !currentDiary.ai_prediction.includes('분석 중')
              "
              class="ai-prediction-badge-premium"
            >
              {{ currentDiary.ai_prediction }}
            </span>
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
              <span class="ai-sender">마음온의 편지</span>
            </div>
            <p class="ai-comment-text">{{ currentDiary.ai_comment }}</p>
            <p style="font-size: 10px; color: #b0b0b0; margin-top: 8px; text-align: right;">💡 AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.</p>
            <p style="font-size: 10px; color: #ff9500; margin-top: 2px; text-align: right;">⚠️ 위기 감지는 보조적 수단이며, 100% 정확성을 보장하지 않습니다.</p>
          </div>
        </div>

        <!-- 질문 답변 리스트 (Parsed Content) -->
        <div class="view-answers">
          <div v-if="parsedContent.sleep" class="answer-item-premium">
            <h4 class="answer-question">잠은 잘 주무셨나요?</h4>
            <p class="answer-text">{{ parsedContent.sleep }}</p>
          </div>
          <div v-if="parsedContent.event" class="answer-item-premium">
            <h4 class="answer-question">오늘 무슨일이 있었나요?</h4>
            <p class="answer-text">{{ parsedContent.event }}</p>
          </div>
          <div v-if="parsedContent.emotion" class="answer-item-premium">
            <h4 class="answer-question">어떤 감정이 들었나요?</h4>
            <p class="answer-text">{{ parsedContent.emotion }}</p>
          </div>
          <div v-if="parsedContent.meaning" class="answer-item-premium">
            <h4 class="answer-question">자신의 감정을 깊게 탐색해보면...</h4>
            <p class="answer-text">{{ parsedContent.meaning }}</p>
          </div>
          <div v-if="parsedContent.selftalk" class="answer-item-premium">
            <h4 class="answer-question">나에게 보내는 따뜻한 위로</h4>
            <p class="answer-text">{{ parsedContent.selftalk }}</p>
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
import { ref, computed, watch, onUnmounted, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import EmojiSelector from "./EmojiSelector.vue";
import QuestionAccordion from "./QuestionAccordion.vue";
import { diaryAPI } from "../services/api";

// Images
import happyImg from "../assets/01.png";
import calmImg from "../assets/02.png";
import neutralImg from "../assets/03.png";
import sadImg from "../assets/04.png";
import angryImg from "../assets/05.png";

export default {
  name: "DiaryModal",
  components: { EmojiSelector, QuestionAccordion },
  props: {
    date: { type: String, required: true },
    diary: { type: Object, default: null },
  },
  emits: ["close", "saved"],
  setup(props, { emit }) {
    const router = useRouter();
    console.log("🔥 DiaryModal V3.1 SETUP (Cleaned) 🔥");

    // === Refs & Data ===
    const isViewMode = ref(!!props.diary);
    const showForm = ref(false);
    const saving = ref(false);
    const localDiary = ref(null);
    const panelRef = ref(null);
    const currentDiary = computed(() => localDiary.value || props.diary || {});

    // === Mode Logic ===
    const userRiskLevel = ref(1);
    const uiMode = computed(() => (userRiskLevel.value >= 3 ? "red" : "green"));
    const symptomOptions = [
      "두통/어지러움",
      "소화불량/식욕저하",
      "불면/과수면",
      "가슴 답답함",
      "만성 피로",
    ];

    // === Form Data ===
    const formData = ref({
      mood: "neutral",
      question_sleep: "",
      question1: "",
      question2: "",
      question3: "",
      question4: "",
      mode: "green",
      mood_intensity: 5,
      symptoms: [],
      gratitude_note: "",
      safety_flag: false,
      medication_taken: false,
    });

    // === Weather & AI Insight Data ===
    const weatherInfo = ref(null);
    const weatherInsight = ref("");
    const mindsetInsight = ref("");
    const isLoadingInsight = ref(false);

    // === AI Processing State ===
    const isProcessing = ref(false);
    const progressPercent = ref(0);
    const loadingMessage = ref("AI 분석 준비 중...");
    const eta = ref(0);
    const timerIds = ref([]);

    // === Voice Recording State ===
    const isRecording = ref(false);
    const isTranscribing = ref(false);
    const activeField = ref(null);
    let mediaRecorder = null;
    let audioChunks = [];

    // === Constants ===
    const moodLevelToName = { 1: "angry", 2: "sad", 3: "neutral", 4: "calm", 5: "happy" };
    const emojiMap = {
      1: { icon: angryImg, name: "화나" },
      2: { icon: sadImg, name: "우울해" },
      3: { icon: neutralImg, name: "그저그래" },
      4: { icon: calmImg, name: "편안해" },
      5: { icon: happyImg, name: "행복해" },
    };

    // === Formatting Helpers ===
    const formattedDate = computed(() => {
      if (!props.date) return "";
      const parts = props.date.split("-");
      if (parts.length < 3) return props.date;
      return `${parseInt(parts[1])}월 ${parseInt(parts[2])}일`;
    });

    const formattedDateTime = computed(() => {
      const dStr = currentDiary.value.created_at || props.diary?.created_at;
      if (!dStr) return "";
      const d = new Date(dStr);
      return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    });

    // === Parsed Content for Restored Diaries ===
    const parsedContent = computed(() => {
      const d = currentDiary.value;
      const raw = d.event || d.content || "";

      // If NOT restored format (checks for specific header), treat as legacy/simple
      if (!raw.includes("[잠은 잘 주무셨나요?]")) {
        return {
          sleep: d.sleep_condition || d.sleep_desc,
          event: d.event,
          emotion: d.emotion_desc,
          meaning: d.emotion_meaning,
          selftalk: d.self_talk,
        };
      }

      // Restored Format Parsing
      const result = { sleep: "", event: "", emotion: "", meaning: "", selftalk: "" };
      let currentSection = "";
      
      const lines = raw.split("\n");
      for (const line of lines) {
          const t = line.trim();
          if (!t) continue;
          
          if (t.includes("[잠은 잘 주무셨나요?]")) currentSection = "sleep";
          else if (t.includes("[오늘 무슨일이 있었나요?]") || t.includes("[오늘 있었던 일은?]")) currentSection = "event";
          else if (t.includes("[어떤 감정이 들었나요?]")) currentSection = "emotion";
          else if (t.includes("[자신의 감정을 깊게 탐색해보면...]")) currentSection = "meaning";
          else if (t.includes("[나에게 보내는 따뜻한 위로]")) currentSection = "selftalk";
          else if (currentSection) {
              result[currentSection] += (result[currentSection] ? "\n" : "") + line;
          }
      }
      
      // [Safety Fallback] If parsing failed to extract event, use raw text if it doesn't look like a structured format
      if (!result.event && d.event && !result.sleep) {
          result.event = d.event;
      }
      
      return result;
    });

    const isValid = computed(
      () =>
        formData.value.mood &&
        formData.value.question1.trim() &&
        formData.value.question_sleep.trim(),
    );

    // [Fix] Robust Mood Mapping (Number or String)
    const normalizeMood = (val) => {
      if (!val) return 3; // Default Neutral
      if (typeof val === "number") {
        if (val > 5) return 5;
        if (val < 1) return 1;
        return Math.round(val);
      }
      const map = { happy: 5, calm: 4, neutral: 3, sad: 2, angry: 1 };
      return map[val] || 3;
    };

    // [New] AI Keyword Mapping (Sync with CalendarGrid)
    const koreanToMoodKey = {
      행복: 5,
      기쁨: 5,
      사랑: 5,
      설렘: 5,
      즐거움: 5,
      흥분: 5,
      재미: 5,
      신남: 5,
      만족: 5,
      평온: 4,
      편안: 4,
      감사: 4,
      다짐: 4,
      안도: 4,
      차분: 4,
      평범: 3,
      무던: 3,
      보통: 3,
      지루함: 3,
      혼란: 3,
      모호: 3,
      우울: 2,
      슬픔: 2,
      지침: 2,
      피곤: 2,
      외로움: 2,
      후회: 2,
      상처: 2,
      어려움: 2,
      힘듦: 2,
      괴로움: 2,
      어리움: 2,
      지쳐있음: 2,
      피로: 2,
      무력: 2,
      낙담: 2,
      분노: 1,
      화남: 1,
      짜증: 1,
      스트레스: 1,
      싫어: 1,
      불안: 1,
      걱정: 1,
      답답함: 1,
      억울: 1,
    };

    // [New] Computed Mood logic: AI > User
    const displayMoodLevel = computed(() => {
      const d = currentDiary.value;
      if (!d) return 3;

      console.log(`[DiaryModal] Calculating Mood for ID ${d.id}`);
      console.log(`- AI Pred: ${d.ai_prediction}, AI Emo: ${d.ai_emotion}`);
      console.log(`- User Mood: ${d.mood_level} / ${d.mood}`);

      // 1. Try AI Emotion Field
      if (d.ai_emotion && d.ai_emotion !== "분석중" && d.ai_emotion !== "대기중") {
        const key = d.ai_emotion.trim();
        if (koreanToMoodKey[key]) {
          console.log(`-> Mapped via AI Emotion (${key}): ${koreanToMoodKey[key]}`);
          return koreanToMoodKey[key];
        }
      }

      // 2. Try AI Prediction Field
      if (d.ai_prediction) {
        let text = d.ai_prediction;
        if (
          (text.startsWith("'") && text.endsWith("'")) ||
          (text.startsWith('"') && text.endsWith('"'))
        )
          text = text.slice(1, -1);
        const match = text.match(/^([^(]+)(\s\(\d+(\.\d+)?%\))?$/);
        const label = match ? match[1].trim() : text.trim();

        if (koreanToMoodKey[label]) {
          console.log(`-> Mapped via AI Prediction (${label}): ${koreanToMoodKey[label]}`);
          return koreanToMoodKey[label];
        } else {
          console.log(`-> Mapping Failed for label: ${label}`);
        }
      }

      // 3. Fallback to User Mood
      const userM = normalizeMood(d.mood_level || d.mood);
      console.log(`-> Fallback to User Mood: ${userM}`);
      return userM;
    });

    const getMoodEmoji = (lvl) => emojiMap[normalizeMood(lvl)]?.icon || "";
    const getMoodName = (lvl) => emojiMap[normalizeMood(lvl)]?.name || "";
    const getMoodColorClass = (lvl) => {
      const n = normalizeMood(lvl);
      const map = {
        1: "mood-angry",
        2: "mood-sad",
        3: "mood-neutral",
        4: "mood-calm",
        5: "mood-happy",
      };
      return map[n] || "mood-neutral";
    };
    const getWeatherIcon = (desc) => {
      if (!desc) return "✨";
      if (desc.includes("맑음")) return "☀️";
      if (desc.includes("구름") || desc.includes("흐림")) return "☁️";
      if (desc.includes("비")) return "🌧️";
      if (desc.includes("눈")) return "❄️";
      return "✨";
    };

    // === API & Polling Logic ===
    const clearTimers = () => {
      timerIds.value.forEach((id) => clearInterval(id));
      timerIds.value = [];
    };

    const finishPolling = async () => {
      clearTimers();
      isProcessing.value = false;
      progressPercent.value = 100;

      if (currentDiary.value.id) {
        try {
          const fresh = await diaryAPI.getDiary(currentDiary.value.id);
          localDiary.value = fresh;

          if (fresh.followup_required) {
            console.log("🚨 Follow-up Required! Switching to Chatbot...");
            emit("close");
            localStorage.setItem(
              "followup_context",
              JSON.stringify({
                diaryId: fresh.id,
                question: fresh.followup_question || "오늘 기록하신 내용을 조금 더 이야기해볼까요?",
              }),
            );
            router.push(`/chat/${props.date}`);
            return;
          }
        } catch (e) {
          console.error(e);
        }
      }
      emit("saved");
    };

    const startRealPolling = (taskId) => {
      isProcessing.value = true;
      progressPercent.value = 5;
      loadingMessage.value = "AI 분석 중...";
      eta.value = 15;
      timerIds.value.push(
        setInterval(() => {
          if (eta.value > 0) eta.value--;
        }, 1000),
      );
      timerIds.value.push(
        setInterval(async () => {
          try {
            const status = await diaryAPI.getTaskStatus(taskId);
            if (status.state === "PROGRESS") {
              progressPercent.value = status.process_percent;
              loadingMessage.value = status.message;
            } else if (status.state === "SUCCESS") finishPolling();
            else if (status.state === "FAILURE") {
              isProcessing.value = false;
              clearTimers();
            }
          } catch (e) {}
        }, 1000),
      );
    };

    const startFakePolling = () => {
      isProcessing.value = true;
      loadingMessage.value = "분석 결과 확인 중...";
      progressPercent.value = 30;
      eta.value = 5;
      timerIds.value.push(
        setInterval(async () => {
          if (progressPercent.value < 90) progressPercent.value += 10;
          if (eta.value > 0) eta.value--;
          if (currentDiary.value.id) {
            try {
              const fresh = await diaryAPI.getDiary(currentDiary.value.id);
              if (fresh.ai_prediction && !fresh.ai_prediction.includes("분석 중")) {
                localDiary.value = fresh;
                finishPolling();
              }
            } catch (e) {}
          }
        }, 1500),
      );
    };

    const handleSave = async () => {
      saving.value = true;
      try {
        const payload = {
          date: props.date,
          mood: formData.value.mood,
          sleep_condition: formData.value.question_sleep,
          question1: formData.value.question1,
          question2: formData.value.question2,
          question3: formData.value.question3,
          question4: formData.value.question4,
          weather: weatherInfo.value ? weatherInfo.value.desc : null,
          temperature: weatherInfo.value ? weatherInfo.value.temp : null,
          mode: uiMode.value,
          mood_intensity: formData.value.mood_intensity,
          symptoms: formData.value.symptoms,
          gratitude_note: formData.value.gratitude_note,
          safety_flag: formData.value.safety_flag,
          medication_taken: formData.value.medication_taken,
        };
        const result = props.diary
          ? await diaryAPI.updateDiary(props.diary.id, payload)
          : await diaryAPI.createDiary(payload);
        localDiary.value = result;
        isViewMode.value = true;
        showForm.value = false;
        if (result.task_id) startRealPolling(result.task_id);
        else startFakePolling();
        emit("saved");
      } catch (e) {
        alert("저장 실패: " + e.message);
      } finally {
        saving.value = false;
      }
    };

    const handleDelete = async () => {
      if (!confirm("정말 삭제하시겠습니까?")) return;
      try {
        await diaryAPI.deleteDiary(currentDiary.value.id);
        emit("saved");
        emit("close");
      } catch (e) {}
    };

    // === Weather & Insight ===
    const fetchMindsetInsight = async () => {
      if (mindsetInsight.value) return;
      isLoadingInsight.value = true;
      const weatherDesc = weatherInfo.value ? weatherInfo.value.desc : null;
      try {
        const minTime = new Promise((resolve) => setTimeout(resolve, 1500));
        const [res] = await Promise.all([
          diaryAPI
            .getMindsetInsight(props.date, weatherDesc)
            .catch(() => ({ message: "오늘 하루는 어떠셨나요?" })),
          minTime,
        ]);
        mindsetInsight.value = res.message || "오늘 하루는 어떠셨나요?";
      } catch (e) {
        mindsetInsight.value = "편안하게 기록해보세요.";
      } finally {
        isLoadingInsight.value = false;
      }
    };

    const getWeatherFromAPI = async (lat, lon, date = null) => {
      // (Simplified for brevity, same logic as before)
      try {
        let url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&timezone=auto`;
        if (date) {
          const today = new Date().toISOString().split("T")[0];
          if (date < today)
            url = `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=${date}&end_date=${date}&daily=weathercode,temperature_2m_max&timezone=auto`;
        }
        const res = await fetch(url);
        const data = await res.json();
        let code, temp;
        if (data.daily) {
          code = data.daily.weathercode[0];
          temp = data.daily.temperature_2m_max[0];
        } else if (data.current_weather) {
          code = data.current_weather.weathercode;
          temp = data.current_weather.temperature;
        }

        if (code !== undefined) {
          const map = {
            0: "맑음 ☀️",
            1: "대체로 맑음 🌤️",
            2: "구름 조금 ⛅",
            3: "흐림 ☁️",
            61: "비 ☔",
            95: "뇌우 ⚡",
          };
          weatherInfo.value = { temp, desc: map[code] || "흐림" };
          if (!props.diary) fetchMindsetInsight();
        }
      } catch (e) {
        if (!props.diary) fetchMindsetInsight();
      }
    };

    const checkWeather = (date) => {
      if (!weatherInfo.value) getWeatherFromAPI(37.5665, 126.978, date); // Default Seoul
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) =>
          getWeatherFromAPI(pos.coords.latitude, pos.coords.longitude, date),
        );
      }
    };

    // === Voice Recording ===
    const toggleRecording = (field) => {
      if (activeField.value === field && isRecording.value) stopRecording();
      else startRecording(field);
    };
    const startRecording = async (field) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        activeField.value = field;
        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
          isRecording.value = false;
          activeField.value = null;
          const blob = new Blob(audioChunks, { type: "audio/webm" });
          if (blob.size < 100) return;
          isTranscribing.value = true;
          const fd = new FormData();
          fd.append("file", blob, "voice.webm");
          fd.append("auto_fill", "false");
          try {
            const res = await diaryAPI.transcribeVoice(fd);
            if (res.text) formData.value[field] = (formData.value[field] || "") + " " + res.text;
          } catch (e) {
            alert("변환 실패");
          } finally {
            isTranscribing.value = false;
            stream.getTracks().forEach((t) => t.stop());
          }
        };
        mediaRecorder.start();
        isRecording.value = true;
      } catch (e) {
        alert("마이크 오류");
      }
    };
    const stopRecording = () => {
      if (mediaRecorder) mediaRecorder.stop();
    };

    // === UI Handlers ===
    const startWriting = () => {
      showForm.value = true;
      formData.value.mode = uiMode.value;
    };
    const cancelWriting = () => {
      showForm.value = false;
      emit("close");
    };
    const handleEdit = () => {
      isViewMode.value = false;
      showForm.value = true;
      const d = currentDiary.value;
      const parsed = parsedContent.value;

      formData.value = {
        mood: moodLevelToName[d.mood_level] || "neutral",
        question_sleep: parsed.sleep || "",
        question1: parsed.event || "",
        question2: parsed.emotion || "",
        question3: parsed.meaning || "",
        question4: parsed.selftalk || "",
        mode: d.mode || "green",
        mood_intensity: d.mood_intensity || 5,
        symptoms: d.symptoms || [],
        gratitude_note: d.gratitude_note || "",
        safety_flag: d.safety_flag || false,
        medication_taken: d.medication_taken || false,
      };
    };

    // === Lifecycle ===
    onMounted(() => {
      const stored = localStorage.getItem("risk_level");
      if (stored) userRiskLevel.value = parseInt(stored, 10);
    });

    watch(
      [() => props.diary, () => props.date],
      ([newDiary, newDate], [oldDiary, oldDate]) => {
        if (newDate === oldDate && newDiary?.id === oldDiary?.id) return;

        isViewMode.value = !!newDiary;
        showForm.value = false;
        localDiary.value = null;
        clearTimers();
        isProcessing.value = false;

        if (newDiary) {
          weatherInfo.value = newDiary.weather
            ? { desc: newDiary.weather, temp: newDiary.temperature }
            : null;
          if (newDiary.ai_prediction?.includes("분석 중")) {
            if (newDiary.task_id) startRealPolling(newDiary.task_id);
            else startFakePolling();
          }
        } else {
          // New Entry
          formData.value = {
            mood: "neutral",
            question_sleep: "",
            question1: "",
            question2: "",
            question3: "",
            question4: "",
            mode: userRiskLevel.value >= 3 ? "red" : "green",
            mood_intensity: 5,
            symptoms: [],
            gratitude_note: "",
            safety_flag: false,
          };
          checkWeather(newDate);
        }
      },
      { immediate: true },
    );

    onUnmounted(() => clearTimers());

    return {
      isViewMode,
      showForm,
      saving,
      formData,
      weatherInfo,
      weatherInsight,
      panelRef,
      currentDiary,
      formattedDate,
      formattedDateTime,
      isValid,
      parsedContent,
      displayMoodLevel, // [New]
      getMoodEmoji,
      getMoodName,
      getMoodColorClass,
      getWeatherIcon,
      handleSave,
      startWriting,
      cancelWriting,
      handleEdit,
      handleDelete,
      isProcessing,
      progressPercent,
      loadingMessage,
      eta,
      mindsetInsight,
      isLoadingInsight,
      isRecording,
      isTranscribing,
      toggleRecording,
      activeField,
      uiMode,
      symptomOptions,
    };
  },
};
</script>

<style scoped>
.diary-panel {
  height: 100%;
  overflow-y: auto;
  padding: 0 32px 32px 32px;
  background: #fafafa;
  scroll-behavior: smooth;
}
.modal-header {
  position: sticky;
  top: 0;
  z-index: 10; /* 헤더가 컨텐츠 위에 오도록 충분히 높게 설정 */
  padding-top: 32px;
  padding-bottom: 24px; /* 패딩 약간 축소 */
  background: #fafafa; /* 투명 배경 제거하고 불투명 배경색 적용하여 겹침 방지 */
  border-bottom: 1px solid rgba(0, 0, 0, 0.03); /* 스크롤 시 구분을 위한 미세한 경계선 */
}
.modal-title {
  font-size: 24px;
  font-weight: 800;
  color: #1d1d1f;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.diary-timestamp {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

.weather-badge-premium {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  padding: 6px 12px;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.03);
}
.weather-icon {
  font-size: 16px;
}
.weather-text {
  font-size: 12px;
  font-weight: 600;
  color: #555;
}

.weather-loading {
  font-size: 12px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 6px;
}
.pulse {
  width: 8px;
  height: 8px;
  background: #ff4757;
  border-radius: 50%;
  display: inline-block;
  animation: pulse-anim 1.5s infinite;
}
@keyframes pulse-anim {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.4;
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.diary-empty {
  text-align: center;
  padding: 60px 20px;
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.empty-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.empty-hint {
  font-size: 14px;
  color: #aaa;
  margin-top: 8px;
}

.insight-bubble {
  background: white;
  padding: 16px 24px;
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 15px;
  color: #444;
  font-weight: 600;
  max-width: 320px;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  position: relative;
}
.insight-bubble::before {
  /* Border Triangle */
  content: "";
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-bottom: 7px solid rgba(0, 0, 0, 0.04);
}
.insight-bubble::after {
  /* Background Mask Triangle */
  content: "";
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid white;
}

/* ... existing code ... */

.insight-bubble-purple {
  background: #f3e5f5;
  border-color: rgba(74, 20, 140, 0.1);
}
.insight-bubble-purple::before {
  border-bottom-color: rgba(74, 20, 140, 0.1);
}
.insight-bubble-purple::after {
  border-bottom-color: #f3e5f5;
}
.insight-icon {
  font-size: 20px;
}
.fade-in {
  animation: fadeIn 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(10px);
}
@keyframes fadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.btn {
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary {
  background: #1d1d1f;
  color: white;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.btn-large {
  padding: 16px 40px;
  font-size: 16px;
}
.btn-secondary {
  background: #f2f2f7;
  color: #1d1d1f;
}
.btn-danger {
  background: #ff3b30;
  color: white;
}
.btn-ghost {
  background: transparent;
  color: #ff3b30;
  border: 1px solid rgba(255, 59, 48, 0.15);
}
.btn-ghost:hover {
  background: rgba(255, 59, 48, 0.05);
  border-color: #ff3b30;
}

.modal-actions-inline {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 60px;
  padding: 40px 0 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  position: relative;
  z-index: 5;
}

.diary-view {
  position: relative;
}
.view-content-wrapper {
  position: relative;
  z-index: 2; /* 헤더를 덮기 위해 더 높은 z-index 부여 */
  background: #fafafa; /* 헤더를 가릴 solid 배경색 */
  margin-top: -20px; /* 자연스러운 겹침을 위한 마진 조절 */
  padding-top: 1px; /* 마진 상쇄 방지 */
}

.view-emoji-premium {
  border-radius: 28px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  transition: all 0.4s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
}
.mood-happy {
  background: linear-gradient(135deg, #fffde7 0%, #ffe082 100%);
}
.mood-calm {
  background: linear-gradient(135deg, #f1f8e9 0%, #a5d6a7 100%);
}
.mood-neutral {
  background: linear-gradient(135deg, #fafafa 0%, #e0e0e0 100%);
}
.mood-sad {
  background: linear-gradient(135deg, #e3f2fd 0%, #90caf9 100%);
}
.mood-angry {
  background: linear-gradient(135deg, #ffebee 0%, #ef9a9a 100%);
}

.emoji-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}
.emoji-large {
  width: 110px;
  height: 110px;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.12));
}
.anim-float {
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-12px);
  }
  100% {
    transform: translateY(0);
  }
}

.emoji-label {
  font-size: 26px;
  font-weight: 800;
  color: rgba(0, 0, 0, 0.8);
  letter-spacing: -0.5px;
}
.primary-label {
  margin-bottom: 8px;
}
.ai-prediction-badge-premium {
  font-size: 13px;
  font-weight: 700;
  color: white;
  background: rgba(0, 0, 0, 0.25);
  padding: 7px 16px;
  border-radius: 24px;
  backdrop-filter: blur(8px);
}

.ai-letter-box {
  background: rgba(255, 255, 255, 0.96);
  padding: 28px;
  border-radius: 24px;
  width: 100%;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.letter-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ai-icon {
  font-size: 22px;
}
.ai-sender {
  font-size: 15px;
  font-weight: 700;
  color: #222;
}
.ai-comment-text {
  font-size: 16px;
  line-height: 1.8;
  color: #444;
  white-space: pre-wrap;
  font-weight: 500;
}

.ai-loading-section {
  width: 100%;
  background: rgba(255, 255, 255, 0.6);
  padding: 24px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.progress-track {
  width: 100%;
  height: 8px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  overflow: hidden;
  margin-top: 12px;
}
.progress-fill {
  height: 100%;
  background: #1d1d1f;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.view-answers {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding-bottom: 60px;
}
.answer-item-premium {
  background: white;
  padding: 32px;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.02);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.03);
  transition: transform 0.3s ease;
}
.answer-item-premium:hover {
  transform: translateY(-4px);
}
.answer-question {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.answer-text {
  font-size: 17px;
  color: #1d1d1f;
  line-height: 1.7;
  white-space: pre-wrap;
  font-weight: 500;
}

.mindset-bubble {
  background: #f3e5f5; /* Gentle Purple */
  padding: 16px 20px;
  border-radius: 16px;
  margin-bottom: 24px;
  border: 1px solid rgba(0, 0, 0, 0.03);
  animation: slideDown 0.4s ease-out;
}
.mindset-content {
  display: flex;
  gap: 12px;
  align-items: center;
}
.mindset-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}
.mindset-text {
  font-size: 15px;
  color: #4a148c;
  font-weight: 600;
  line-height: 1.5;
  word-break: keep-all;
}

.mindset-loading {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.pulse-mini {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: pulse-anim 1s infinite;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn 0.4s ease-out;
}

/* Symptom Chips */
.symptom-check-section {
  margin-bottom: 24px;
  background: #fff0f0; /* Light Red tint for warning context */
  padding: 16px;
  border-radius: 12px;
}
.section-label {
  display: block;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 14px;
  color: #c62828;
}
.symptom-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.symptom-chip {
  padding: 8px 16px;
  background: white;
  border: 1px solid #ffcdd2;
  border-radius: 20px;
  font-size: 13px;
  color: #b71c1c;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.symptom-chip.active {
  background: #ff5252;
  color: white;
  border-color: #ff5252;
  font-weight: 600;
}

/* Slider */
.slider-section {
  margin-bottom: 24px;
  padding: 0 10px;
}
.slider-container {
  display: flex;
  align-items: center;
  gap: 16px;
}
.range-slider {
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  outline: none;
}
.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ff5252;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.slider-value {
  font-size: 18px;
  font-weight: 800;
  color: #ff5252;
  min-width: 24px;
}
.slider-hint {
  font-size: 11px;
  color: #999;
  margin-top: 6px;
  text-align: right;
}

/* Safety Checkbox */
.safety-check-box {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #ef9a9a;
  border-radius: 12px;
  background: #ffebee;
}
.warning-text {
  color: #c62828;
  font-weight: 600;
  font-size: 14px;
  margin-left: 8px;
}
.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
}
input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #c62828;
}

/* Voice UI */
.voice-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.btn-voice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 30px;
  border: 1px solid rgba(0, 0, 0, 0.08); /* Subtle border */
  background: white;
  color: #333;
  font-weight: 700;
  font-size: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  width: 100%;
  justify-content: center;
  cursor: pointer;
}
.btn-voice:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  border-color: #1d1d1f;
}
.btn-voice.recording {
  background: #ff3b30;
  color: white;
  border-color: #ff3b30;
  animation: pulse-red 2s infinite;
}
.voice-loading {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}
@keyframes pulse-red {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(255, 59, 48, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0);
  }
}

.voice-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  backdrop-filter: blur(2px);
  border-radius: 20px;
}
.voice-loader-box {
  background: white;
  padding: 16px 24px;
  border-radius: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #555;
  font-weight: 600;
}
</style>
