<template>
  <div class="guide-page">
    <div class="guide-container">
      <header class="guide-header">
         <div class="header-left">
           <h2>📖 사용 설명서</h2>
           <p class="subtitle">MOOD DIARY를 100% 활용하는 방법을 알려드려요.</p>
         </div>
         <button @click="$router.push('/calendar')" class="close-btn">
            <span class="icon">✖</span> 닫기
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
                            단순히 '좋다', '나쁘다'가 아닌, <strong>60가지의 세분화된 감정</strong>(비통함, 홀가분함, 설렘, 억울함 등)으로 당신의 마음을 정확하게 읽어냅니다.
                        </p>
                        <br>
                        <h4>전문 심리 상담사 같은 코멘트</h4>
                        <p>
                             국내 최고 수준의 한국어 AI 모델(Polyglot-Ko)이 당신의 일기 속 <strong>문맥과 숨겨진 의미</strong>를 파악하여, 
                             마치 상담사가 옆에서 이야기하듯 따뜻하고 깊이 있는 위로를 건넵니다.
                        </p>
                        <p class="tip-text">
                             💡 일기 내용을 수정하면 AI가 다시 깊게 고민하여 새로운 답변을 준비해요!
                        </p>
                    </div>
                    <div class="icon-visual">🧠</div>
                </div>
            </section>

            <!-- 3. 통계 및 검색 -->
            <section class="guide-section two-col">
                <div class="feature-card">
                    <h3>📊 감정 통계</h3>
                    <p>
                        <strong>[분석]</strong> 페이지에서 AI가 분석한 <strong>감정 흐름</strong>, 나의 <strong>월별 기록 습관</strong>, 그리고 <strong>날씨와 기분의 상관관계</strong>를 직관적인 차트로 확인해보세요.
                    </p>
                </div>
                <div class="feature-card">
                    <h3>🔍 일기 검색</h3>
                    <p>
                        지난 일기가 기억나지 않나요? 상단 검색창을 통해 <strong>사건, 감정, 생각, 위로</strong> 등 기록한 모든 내용에서 키워드를 찾아보세요.
                    </p>
                </div>
            </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GuidePage',
  setup() {
    return {}
  }
}
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
  background: white;
  border: 1px solid #d2d2d7;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.close-btn:hover {
  background: #f5f5f7;
  transform: scale(1.02);
}
.close-btn .icon { font-size: 12px; }

/* Content Structure matches StatsPage style */
.guide-content {
  flex: 1;
  min-height: 0;
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
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
.content-body::-webkit-scrollbar { width: 8px; }
.content-body::-webkit-scrollbar-track { background: transparent; }
.content-body::-webkit-scrollbar-thumb {
  background-color: #d1d1d6;
  border-radius: 4px;
  border: 2px solid white;
}

/* Sections */
.guide-section {
    margin-bottom: 50px;
}
.guide-section:last-child { margin-bottom: 0; }

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
.step-card:hover { transform: translateY(-2px); }

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
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
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
.ai-feature h4 { margin: 0 0 8px 0; font-size: 18px; }
.ai-feature p { margin: 0; color: #555; line-height: 1.6; }
.icon-visual { font-size: 40px; }

.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 768px) {
    .content-body { padding: 24px; }
    .two-col { grid-template-columns: 1fr; }
    .ai-feature { flex-direction: column; text-align: center; gap: 16px; }
}
</style>
