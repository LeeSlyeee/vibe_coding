<template>
  <div class="assessment-container">
    <div class="assessment-card">
      <div class="header">
        <h1>😊 마음 체크업 (PHQ-9)</h1>
        <p>
          지난 2주 동안, 당신은 다음과 같은 문제들로 인해<br />얼마나 자주 방해를 받았나요?
        </p>
      </div>

      <div class="progress-bar">
        <div class="progress" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <div class="question-container" v-if="currentStep < questions.length">
        <h2 class="question-text">
          {{ currentStep + 1 }}. {{ questions[currentStep].text }}
        </h2>
        <div class="options">
          <button
            v-for="(option, idx) in options"
            :key="idx"
            class="option-btn"
            @click="selectOption(idx)"
          >
            {{ option }}
          </button>
        </div>
      </div>

      <div class="result-container" v-else>
        <div class="spinner" v-if="loading"></div>
        <div v-else class="result-content">
          <h2>분석 완료!</h2>
          <p class="score-text">당신의 점수: {{ totalScore }}점</p>
          <div class="severity-box" :class="severityClass">
            {{ severityLabel }}
          </div>
          <p class="description">{{ severityDescription }}</p>

          <button class="start-btn" @click="goToCalendar">
            시작하기
          </button>
        </div>
      </div>
      <!-- 기관 코드 연동 섹션 (새로 추가됨) -->
      <div class="linkage-section" v-if="currentStep < questions.length && !isLinked">
          <p class="linkage-title">혹시 기관 코드가 있으신가요?</p>
          <div class="input-group">
            <input 
              type="text" 
              class="input-code"
              v-model="inputCode" 
              placeholder="코드 입력" 
              @keyup.enter="handleConnect"
            />
            <button class="btn-connect" @click="handleConnect" :disabled="isLoadingCode || !inputCode">
              {{ isLoadingCode ? '확인..' : '인증' }}
            </button>
          </div>
          <p v-if="errorCode" class="error-text">{{ errorCode }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { medicationAPI } from "../services/medication";
import api from "../services/api";

export default {
  name: "AssessmentPage",
  setup() {
    const router = useRouter();
    const currentStep = ref(0);
    const answers = ref([]);
    const totalScore = ref(0);
    const loading = ref(false);
    const severityLabel = ref("");
    
    // PHQ-9 Questions (Korean)
    const questions = [
      { text: "기분이 가라앉거나, 우울하거나, 희망이 없다고 느꼈다." },
      { text: "일이나 취미 생활에 흥미나 즐거움을 느끼지 못했다." },
      { text: "잠들기 어렵거나 자꾸 깨거나, 혹은 너무 많이 잤다." },
      { text: "피곤하다고 느끼거나 기운이 없었다." },
      { text: "입맛이 없거나, 혹은 너무 많이 먹었다." },
      { text: "나 자신이 싫거나, 실패자라고 느끼거나, 가족을 실망시켰다고 느꼈다." },
      { text: "신문을 읽거나 TV를 보는 것과 같은 일에 집중하기 어려웠다." },
      { text: "다른 사람들이 눈치 챌 정도로 평소보다 말이나 행동이 느려졌다. 혹은 너무 안절부절못해서 평소보다 많이 돌아다녔다." },
      { text: "차라리 죽는 것이 낫겠다고 생각하거나, 어떻게든 자해를 하려고 생각했다." },
    ];

    const options = ["전혀 없음 (0점)", "며칠 동안 (1점)", "2주 중 절반 이상 (2점)", "거의 매일 (3점)"];

    const progressPercent = computed(() => {
        if (currentStep.value >= questions.length) return 100;
        return ((currentStep.value) / questions.length) * 100;
    });

    const selectOption = async (score) => {
      answers.value.push(score);
      totalScore.value += score;

      if (currentStep.value < questions.length - 1) {
        currentStep.value++;
      } else {
        currentStep.value++; // Finish
        await submitResult();
      }
    };

    const submitResult = async () => {
      loading.value = true;
      try {
        await medicationAPI.submitAssessment({
          score: totalScore.value,
          answers: answers.value
        });
        
        loading.value = false;
        
        // Severity Logic for Display
        const s = totalScore.value;
        if (s <= 4) severityLabel.value = "안정 (Minimal)";
        else if (s <= 9) severityLabel.value = "경증 (Mild)";
        else if (s <= 14) severityLabel.value = "중등도 (Moderate)";
        else if (s <= 19) severityLabel.value = "중증 (Moderately Severe)";
        else severityLabel.value = "심각 (Severe)";

      } catch (e) {
        console.error("Assessment submit error", e);
        loading.value = false;
        alert("저장에 실패했습니다. 다시 시도해주세요.");
      }
    };

    const severityClass = computed(() => {
        const s = totalScore.value;
        if (s <= 4) return 'safe';
        if (s <= 9) return 'mild';
        if (s <= 14) return 'moderate';
        return 'severe';
    });

    const severityDescription = computed(() => {
        const s = totalScore.value;
        if (s <= 4) return "마음이 매우 건강한 상태입니다! 지금처럼 긍정적인 생활을 유지하세요.";
        if (s <= 9) return "가벼운 우울감이 있지만 일상생활에는 큰 지장이 없습니다. 기분 전환이 필요해요.";
        if (s <= 14) return "우울감이 지속되고 있습니다. 규칙적인 생활과 전문가와의 가벼운 상담을 추천드려요.";
        if (s <= 19) return "상당한 우울감을 느끼고 계시네요. 전문가와의 상담을 적극적으로 고려해보세요.";
        return "매우 힘든 상태입니다. 지금 바로 전문 상담 기관(☎ 1393, 1577-0199)에 연락해주세요.";
    });

    const goToCalendar = () => {
        localStorage.setItem("assessment_completed", "true"); // Client side flag sync
        router.push("/calendar");
    };

    // --- [New] Center Code Linkage Logic ---
    const inputCode = ref('');
    const isLoadingCode = ref(false);
    const errorCode = ref('');
    const isLinked = ref(false);

    onMounted(async () => {
        try {
            // Check if already linked
            const res = await api.get('/user/me');
            if (res.data.center_code) {
                isLinked.value = true;
                // [Fix] Linked users skip assessment and go straight to calendar
                // Verify localStorage is synced
                localStorage.setItem("b2g_center_code", res.data.center_code);
                localStorage.setItem("b2g_is_linked", "true");
                
                console.log("Already linked to center:", res.data.center_code);
                router.push('/calendar');
            }
        } catch (e) {
            console.log("User info check failed (probably guest or network error)");
        }
    });

    const handleConnect = async () => {
      if (!inputCode.value) return;
      
      isLoadingCode.value = true;
      errorCode.value = '';

      try {
        console.log(`🚀 [Assessment] Connecting to OCI server: ${inputCode.value}`);
        
        // [Standard API Call] 
        const response = await api.post('/centers/verify-code/', { 
            center_code: inputCode.value,
            user_nickname: localStorage.getItem('user_nickname') || 'WebUser'
        });

        if (response.data.valid) {
            // [New] Step 2: Persist to DB immediately
            try {
                 await api.post('/b2g_sync/connect/', { center_id: response.data.center_id })
                 console.log("DB Linked from Assessment")
            } catch (connErr) {
                 console.error("Connect failed in Assessment", connErr)
            }

            // 성공 처리
            localStorage.setItem("b2g_center_code", inputCode.value.toUpperCase());
            localStorage.setItem("b2g_is_linked", "true");
            localStorage.setItem("assessment_completed", "true"); // Force Pass!
            isLinked.value = true;
            
            alert(response.data.message || "연동되었습니다! 검사를 건너뜁니다.");
            router.push('/calendar');
        }
      } catch (err) {
        console.error("❌ [Assessment] Connection Error:", err);
        let msg = "오류가 발생했습니다.";
        if (err.response && err.response.data && err.response.data.error) {
            msg = err.response.data.error;
        }
        errorCode.value = msg;
      } finally {
        isLoadingCode.value = false;
      }
    };

    return {
      currentStep,
      questions,
      options,
      selectOption,
      progressPercent,
      loading,
      totalScore,
      severityLabel,
      severityClass,
      severityDescription,
      goToCalendar,
      // New
      inputCode,
      isLoadingCode,
      errorCode,
      handleConnect,
      isLinked
    };
  },
};
</script>

<style scoped>
.assessment-container {
  /* [Fix] 화면 전체를 덮고 최상단에 뜨도록 강제 (z-index Max) */
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 2147483647 !important; 
  
  /* 내부 중앙 정렬 */
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  align-items: center !important;
  
  background-color: #f5f5f7 !important;
  margin: 0 !important;
  padding: 20px !important;
  box-sizing: border-box !important;
}

.assessment-card {
  background: white;
  width: 100%;
  max-width: 500px;
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
  text-align: center;
  
  /* Flex Item 중앙 정렬 보정 */
  margin: auto !important;
}

.header h1 {
  font-size: 24px;
  margin-bottom: 10px;
  color: #1d1d1f;
}

.header p {
  color: #86868b;
  font-size: 14px;
  margin-bottom: 30px;
  line-height: 1.5;
}

/* Progress bar */
.progress-bar {
  width: 100%;
  height: 6px;
  background: #eee;
  border-radius: 3px;
  margin-bottom: 40px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #007aff;
  transition: width 0.3s ease;
}

/* Questions */
.question-text {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 30px;
  color: #1d1d1f;
  min-height: 60px; /* Prevent layout shift */
  word-break: keep-all;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-btn {
  background: white;
  border: 1px solid #d2d2d7;
  padding: 16px;
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  color: #1d1d1f;
}

.option-btn:hover {
  background: #f5f5f7;
  border-color: #007aff;
  color: #007aff;
}

.option-btn:active {
  transform: scale(0.98);
}

/* Result */
.severity-box {
  display: inline-block;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 700;
  margin: 20px 0;
}

.severity-box.safe { background: #e8f5e9; color: #2e7d32; }
.severity-box.mild { background: #fff3e0; color: #ef6c00; }
.severity-box.moderate { background: #ffebee; color: #c62828; }
.severity-box.severe { background: #ffebee; color: #b71c1c; border: 2px solid #b71c1c; }

.description {
    color: #424245;
    line-height: 1.6;
    margin-bottom: 30px;
}

.start-btn {
    background: #007aff;
    color: white;
    border: none;
    padding: 16px 40px;
    border-radius: 30px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    transition: transform 0.2s;
}
.start-btn:hover {
    transform: scale(1.05);
}

.spinner {
    border: 4px solid rgba(0,0,0,0.1);
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border-left-color: #007aff;
    animation: spin 1s linear infinite;
    margin: 40px auto;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

@media (max-width: 600px) {
    .assessment-card { padding: 24px; }
    .question-text { font-size: 18px; }
}

/* New Linkage Section Styles */
.linkage-section {
    margin-top: 40px;
    padding-top: 30px;
    border-top: 1px solid #eee;
    text-align: center;
}
.linkage-title {
    font-size: 14px;
    color: #86868b;
    margin-bottom: 12px;
    font-weight: 600;
}
.input-group {
    display: flex;
    gap: 8px;
    max-width: 300px;
    margin: 0 auto;
}
.input-code {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #e5e5ea;
    border-radius: 10px;
    font-size: 15px;
    text-transform: uppercase;
}
.btn-connect {
    padding: 0 16px;
    background: #5856d6;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    font-size: 14px;
}
.btn-connect:disabled {
    background: #d1d1d6;
}
.error-text {
    color: #ff3b30;
    font-size: 13px;
    margin-top: 8px;
}
</style>
