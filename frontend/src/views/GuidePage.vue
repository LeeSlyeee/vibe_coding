<template>
  <div class="guide-page">
    <div class="guide-container">
      <header class="guide-header">
        <div class="header-left">
          <h2>📖 사용 설명서</h2>
          <p class="subtitle">maumON를 100% 활용하는 방법을 알려드려요.</p>
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
          <!-- Section 1: 일기 작성하기 -->
          <section class="guide-section">
            <div class="section-title-box">
              <h3>📝 일기 작성하기</h3>
              <p class="section-desc">하루의 감정을 4단계로 나누어 천천히 기록해보세요.</p>
            </div>
            
            <div class="steps-grid">
              <div class="step-card">
                <div class="step-num-badge">1</div>
                <div class="step-card-content">
                  <h4>사실 (Event)</h4>
                  <p>오늘 있었던 일이나 상황을 객관적으로 적어보세요.</p>
                </div>
              </div>
              
              <div class="step-card">
                <div class="step-num-badge">2</div>
                <div class="step-card-content">
                  <h4>감정 (Emotion)</h4>
                  <p>그 상황에서 느낀 솔직한 감정들을 단어나 문장으로 표현해요.</p>
                </div>
              </div>
              
              <div class="step-card">
                <div class="step-num-badge">3</div>
                <div class="step-card-content">
                  <h4>의미 (Meaning)</h4>
                  <p>왜 그런 감정이 들었는지, 나에게 어떤 의미인지 깊이 생각해보세요.</p>
                </div>
              </div>
              
              <div class="step-card">
                <div class="step-num-badge">4</div>
                <div class="step-card-content">
                  <h4>위로 (Self-Talk)</h4>
                  <p>오늘 하루 고생한 나에게 따뜻한 위로와 격려의 말을 건네주세요.</p>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 2: AI 분석 -->
          <section class="guide-section">
            <div class="section-title-box">
              <h3>🤖 AI 감정 분석 & 코멘트</h3>
              <p class="section-desc">AI가 당신의 마음을 따뜻하게 읽어드립니다.</p>
            </div>

            <div class="feature-cards-stack">
              <div class="feature-layout-card">
                <div class="feature-text">
                  <h4>60가지 섬세한 감정의 언어</h4>
                  <p>단순히 '좋다/나쁘다'가 아닌, <strong>60가지의 세분화된 감정</strong>으로 당신의 마음을 정확하게 읽어냅니다.</p>
                </div>
                <div class="feature-icon">🧠</div>
              </div>

              <div class="feature-layout-card">
                <div class="feature-text">
                  <h4>💬 AI 감정 분석 코멘트 (Gemma 2)</h4>
                  <p>구글의 최신 모델 <strong>Gemma 2 (2b)</strong>가 문맥과 숨겨진 의미를 파악하여 따뜻한 위로를 건넵니다.</p>
                </div>
                <div class="feature-icon">💬</div>
              </div>
            </div>
          </section>

          <!-- Section 3: 프라이버시 & 심층 분석 -->
          <section class="guide-section">
            <div class="section-title-box">
              <h3>📊 프라이버시 & 심층 분석</h3>
              <p class="section-desc">안전하고 깊이 있는 분석을 경험하세요.</p>
            </div>

            <div class="feature-cards-stack">
              <div class="feature-layout-card highlighted">
                <div class="feature-text">
                  <h4>🔒 철통 보안 AI 감정 분석</h4>
                  <p>외부 클라우드 전송 NO! <strong>안전한 로컬/개인 서버 AI</strong>가 당신만의 비밀 공간에서 분석합니다.</p>
                </div>
                <div class="feature-icon">🛡️</div>
              </div>

              <div class="feature-layout-card">
                <div class="feature-text">
                  <h4>🧠 심층 감정 리포트</h4>
                  <p>일기가 3개 이상 모이면, <strong>나만의 감정 분석 보고서</strong>를 발행해 드려요. (숨겨진 욕구, 스트레스 원인 분석)</p>
                </div>
                <div class="feature-icon">📑</div>
              </div>

              <div class="feature-layout-card">
                <div class="feature-text">
                  <h4>🔬 과거 기록 통합 분석</h4>
                  <p>과거와 현재를 비교 분석하여 감정의 흐름과 성장을 <strong>장기적인 통찰</strong>로 제공합니다.</p>
                </div>
                <div class="feature-icon">🔭</div>
              </div>
            </div>

            <div class="small-features-grid">
              <div class="small-feature-card">
                <h4>🧩 감정 패턴 통계</h4>
                <p>날씨와 기분의 상관관계 한눈에 보기</p>
              </div>
              <div class="small-feature-card">
                <h4>🔍 키워드 검색</h4>
                <p>감정, 사건 키워드로 과거의 나 찾기</p>
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
  height: 100vh;
  overflow: hidden;
  background: #f5f5f7;
  padding: 20px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.guide-container {
  max-width: 800px;
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
  margin-bottom: 24px;
}

.header-left h2 {
  font-size: 32px;
  font-weight: 800;
  color: #1d1d1f;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 16px;
  color: #86868b;
  margin: 0;
}

.close-btn {
  width: 36px;
  height: 36px;
  background: #e8e8ed;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn:hover {
  background: #d2d2d7;
  transform: scale(1.05);
}

.guide-content {
  flex: 1;
  min-height: 0;
  background: white;
  border-radius: 28px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 48px;
  scroll-behavior: smooth;
}

.content-body::-webkit-scrollbar {
  width: 6px;
}

.content-body::-webkit-scrollbar-track {
  background: transparent;
}

.content-body::-webkit-scrollbar-thumb {
  background-color: #d2d2d7;
  border-radius: 3px;
}

.guide-section {
  margin-bottom: 60px;
}

.guide-section:last-child {
  margin-bottom: 0;
}

.section-title-box {
  margin-bottom: 28px;
}

.guide-section h3 {
  font-size: 24px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0 0 10px 0;
  letter-spacing: -0.3px;
}

.section-desc {
  font-size: 16px;
  color: #666;
  margin: 0;
}

/* Steps Grid */
.steps-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.step-card {
  background: #fbfbfd;
  padding: 24px;
  border-radius: 20px;
  border: 1px solid #f2f2f7;
  display: flex;
  gap: 16px;
  transition: all 0.2s ease;
}

.step-card:hover {
  background: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
  transform: translateY(-2px);
}

.step-num-badge {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  background: #1d1d1f;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.step-card-content h4 {
  margin: 0 0 8px 0;
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
}

.step-card-content p {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

/* Feature Stack */
.feature-cards-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-layout-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fbfbfd;
  padding: 28px 32px;
  border-radius: 24px;
  border: 1px solid #f2f2f7;
  transition: all 0.2s ease;
}

.feature-layout-card.highlighted {
  border: 2px solid #34c759;
  background: white;
  box-shadow: 0 10px 30px rgba(52, 199, 89, 0.05);
}

.feature-text {
  flex: 1;
}

.feature-text h4 {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 700;
  color: #1d1d1f;
}

.feature-text p {
  font-size: 15px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

.feature-icon {
  font-size: 44px;
  margin-left: 24px;
  flex-shrink: 0;
}

/* Small Features */
.small-features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.small-feature-card {
  background: #fbfbfd;
  padding: 20px;
  border-radius: 18px;
  border: 1px solid #f2f2f7;
  text-align: left;
}

.small-feature-card h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 700;
  color: #1d1d1f;
}

.small-feature-card p {
  font-size: 13px;
  color: #666;
  margin: 0;
}

@media (max-width: 640px) {
  .guide-page {
    padding: 12px;
  }
  .content-body {
    padding: 24px;
  }
  .steps-grid {
    grid-template-columns: 1fr;
  }
  .small-features-grid {
    grid-template-columns: 1fr;
  }
  .feature-layout-card {
    padding: 24px;
    flex-direction: column-reverse;
    text-align: center;
    gap: 16px;
  }
  .feature-icon {
    margin-left: 0;
  }
  .header-left h2 {
    font-size: 26px;
  }
}
</style>
