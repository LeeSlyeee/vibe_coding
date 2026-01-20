<template>
  <div class="guide-page">
    <div class="guide-container">
      <header class="guide-header">
        <div class="header-left">
          <h2>📖 사용 설명서</h2>
          <p class="subtitle">MOOD DIARY를 100% 활용하는 방법을 알려드려요.</p>
        </div>
        <button @click="$router.push('/calendar')" class="close-btn" aria-label="닫기">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M18 6L6 18"
              stroke="#333"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M6 6L18 18"
              stroke="#333"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </header>

      <div class="guide-content">
        <div class="content-body">
          <!-- 1. 일기 쓰기 -->
          <section class="guide-section">
            <h3>📝 일기 작성하기</h3>
            <p class="section-desc">하루의 감정을 4단계로 나누어 천천히 기록해보세요.</p>
            <div class="steps-grid">
              <div class="step-card">
                <span class="step-num">1</span>
                <h4>사실 (Event)</h4>
                <p>오늘 있었던 일이나 상황을 객관적으로 적어보세요.</p>
              </div>
              <div class="step-card">
                <span class="step-num">2</span>
                <h4>감정 (Emotion)</h4>
                <p>그 상황에서 느낀 솔직한 감정들을 단어나 문장으로 표현해요.</p>
              </div>
              <div class="step-card">
                <span class="step-num">3</span>
                <h4>의미 (Meaning)</h4>
                <p>왜 그런 감정이 들었는지, 나에게 어떤 의미인지 깊이 생각해보세요.</p>
              </div>
              <div class="step-card">
                <span class="step-num">4</span>
                <h4>위로 (Self-Talk)</h4>
                <p>오늘 하루 고생한 나에게 따뜻한 위로와 격려의 말을 건네주세요.</p>
              </div>
            </div>
          </section>

          <!-- 2. AI 분석 -->
          <section class="guide-section">
            <h3>🤖 AI 감정 분석 & 코멘트</h3>
            <div class="feature-card ai-feature">
              <div class="text-content">
                <h4>60가지 섬세한 감정의 언어</h4>
                <p>
                  단순히 '좋다', '나쁘다'가 아닌, <strong>60가지의 세분화된 감정</strong>(비통함,
                  홀가분함, 설렘, 억울함 등)으로 당신의 마음을 정확하게 읽어냅니다.
                </p>
                <br />
                <h4>💬 전문 상담사급 AI 코멘트 (Gemma 2)</h4>
                <p>
                  구글의 최신 고성능 모델 <strong>Gemma 2 (2b)</strong>가 탑재되어 있습니다. 당신의
                  일기 속 <strong>문맥과 숨겨진 의미</strong>를 깊이 있게 파악하여, 전문 상담사처럼
                  따뜻한 위로를 건넵니다.
                </p>
                <p class="tip-text">
                  💡 일기 내용을 수정하면 AI가 다시 깊게 고민하여 새로운 답변을 준비해요!
                </p>
              </div>
              <div class="icon-visual">🧠</div>
            </div>
          </section>

          <!-- 3. 프라이버시 & 심층 분석 -->
          <section class="guide-section">
            <h3>📊 프라이버시 & 심층 분석</h3>

            <div class="feature-card" style="margin-bottom: 20px; border-left: 4px solid #34c759">
              <div class="ai-feature">
                <div class="text-content">
                  <h4>🔒 철통 보안 AI 상담사</h4>
                  <p>
                    당신의 소중한 일기는 외부 클라우드로 전송되지 않습니다.<br />
                    오직 <strong>안전한 로컬/개인 서버 AI</strong>가 당신만의 비밀 공간에서 일기를
                    분석하고 위로를 건넵니다. <br /><span
                      class="tip-text"
                      style="font-size: 13px; color: #888"
                      >(안심하고 속마음을 모두 털어놓으세요)</span
                    >
                  </p>
                </div>
                <div class="icon-visual">🛡️</div>
              </div>
            </div>

            <div class="feature-card" style="margin-bottom: 20px">
              <div class="ai-feature">
                <div class="text-content">
                  <h4>🧠 심층 심리 리포트</h4>
                  <p>
                    일기가 <strong>3개 이상</strong> 모이면, AI가 당신의 최근 심리 상태를 종합적으로
                    진단하는 <strong>나만의 심리 보고서</strong>를 발행해 드려요. <br /><span
                      class="tip-text"
                      style="font-size: 13px; color: #888"
                      >(나의 숨겨진 욕구, 현재 스트레스 원인, 맞춤 솔루션 제공)</span
                    >
                  </p>
                </div>
                <div class="icon-visual">📑</div>
              </div>
            </div>

            <div class="feature-card" style="margin-bottom: 20px">
              <div class="ai-feature">
                <div class="text-content">
                  <h4>🔬 과거 기록 통합 분석</h4>
                  <p>
                    리포트가 쌓이면, **과거와 현재를 비교 분석**하여 당신의 감정이 시간의 흐름에
                    따라 어떻게 치유되고 성장했는지 **장기적인 통찰**을 제공합니다.
                  </p>
                </div>
                <div class="icon-visual">🔭</div>
              </div>
            </div>

            <div class="two-col">
              <div class="feature-card">
                <h4>🧩 감정 패턴 통계</h4>
                <p style="font-size: 14px; color: #555; margin-top: 8px">
                  <strong>날씨와 기분의 상관관계</strong>, 월별 감정 흐름을 차트로 한눈에
                  확인하세요.
                </p>
              </div>
              <div class="feature-card">
                <h4>🔍 키워드 검색</h4>
                <p style="font-size: 14px; color: #555; margin-top: 8px">
                  "그때 내가 왜 힘들었더라?"<br /><strong>감정, 사건, 생각</strong> 키워드로 과거의
                  나를 찾아보세요.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "GuidePage",
  setup() {
    return {};
  },
};
</script>

<style scoped>
.guide-page {
  height: 100%;
  overflow: hidden;
  background: #f5f5f7;
  padding: 20px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.guide-container {
  max-width: 900px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.guide-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.header-left h2 {
  font-size: 28px;
  font-weight: 800;
  color: #1d1d1f;
  margin: 0 0 8px 0;
}
.subtitle {
  font-size: 15px;
  color: #86868b;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  background: #e5e5ea; /* Apple-style light gray */
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}
.close-btn:hover {
  background: #d1d1d6;
  transform: scale(1.05);
}
.close-btn:active {
  transform: scale(0.95);
}

/* Content Structure matches StatsPage style */
.guide-content {
  flex: 1;
  min-height: 0;
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
}

/* Scrollbar Styling */
.content-body::-webkit-scrollbar {
  width: 8px;
}
.content-body::-webkit-scrollbar-track {
  background: transparent;
}
.content-body::-webkit-scrollbar-thumb {
  background-color: #d1d1d6;
  border-radius: 4px;
  border: 2px solid white;
}

/* Sections */
.guide-section {
  margin-bottom: 50px;
}
.guide-section:last-child {
  margin-bottom: 0;
}

.guide-section h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1d1d1f;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-desc {
  color: #666;
  margin-bottom: 24px;
  font-size: 15px;
}

/* Steps Grid */
.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}
.step-card {
  background: #fbfbfd;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #f2f2f7;
  position: relative;
  transition: transform 0.2s;
}
.step-card:hover {
  transform: translateY(-2px);
}

.step-num {
  position: absolute;
  top: -10px;
  left: 20px;
  background: #1d1d1f;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}
.step-card h4 {
  margin: 10px 0 8px 0;
  font-size: 16px;
  font-weight: 700;
}
.step-card p {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
  margin: 0;
}

/* Feature Cards */
.feature-card {
  background: #fbfbfd;
  padding: 30px;
  border-radius: 20px;
  border: 1px solid #f0f0f5;
}
.ai-feature {
  background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ai-feature h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
}
.ai-feature p {
  margin: 0;
  color: #555;
  line-height: 1.6;
}
.icon-visual {
  font-size: 40px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 768px) {
  .content-body {
    padding: 24px;
  }
  .two-col {
    grid-template-columns: 1fr;
  }
  .ai-feature {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
}

/* Mobile Landscape & Short Screens Optimization */
/* Mobile Landscape & Short Screens Optimization */
@media (max-height: 600px) {
  .guide-page {
    /* 기존 100% 및 hidden 해제 -> 전체 스크롤 허용 */
    height: auto;
    min-height: 100%;
    overflow-y: auto; 
    padding: 15px; /* 약간 여유를 줌 */
  }

  .guide-container {
    height: auto; /* 고정 높이 해제 */
    display: block; /* Flex 해제 (필요시) */
  }

  .guide-header {
    margin-bottom: 20px;
    align-items: center;
  }
  
  .guide-content {
    /* 내부 스크롤 제거 -> 페이지 전체가 늘어나도록 함 */
    height: auto;
    flex: none;
    overflow: visible; 
  }

  .content-body {
    /* 내부 스크롤 제거 */
    overflow-y: visible;
    padding: 30px 20px;
  }

  .header-left h2 {
    font-size: 22px;
    margin-bottom: 4px;
  }
  .subtitle {
    font-size: 13px;
  }
  
  /* Grid Optimizations */
  .steps-grid {
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
  .step-card {
    padding: 16px;
  }
  
  /* Feature Cards Compact */
  .feature-card {
    padding: 20px;
  }
  .ai-feature {
    flex-direction: row; 
    gap: 20px;
    text-align: left;
  }
  .icon-visual {
    font-size: 32px;
  }
}

/* Force side-by-side for AI feature on small landscape phones if they hit the max-width: 768px rule */
@media (max-width: 768px) and (orientation: landscape) {
  .ai-feature {
    flex-direction: row;
    text-align: left;
  }
  .two-col {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
