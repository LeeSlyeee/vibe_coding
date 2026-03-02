<template>
  <div class="safety-overlay">
    <div class="safety-card">
      <div class="safety-header">
        <h2>🆘 긴급 도움 요청</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="emergency-contacts">
        <a href="tel:1393" class="contact-item highlight">
          <span class="icon">📞</span>
          <div class="info">
            <span class="name">자살예방 상담전화</span>
            <span class="number">1393</span>
          </div>
          <span class="action">전화하기</span>
        </a>

        <a href="tel:1577-0199" class="contact-item">
          <span class="icon">🏥</span>
          <div class="info">
            <span class="name">정신건강 상담전화</span>
            <span class="number">1577-0199</span>
          </div>
          <span class="action">전화하기</span>
        </a>

        <a href="tel:112" class="contact-item">
          <span class="icon">👮</span>
          <div class="info">
            <span class="name">경찰청 (긴급신고)</span>
            <span class="number">112</span>
          </div>
          <span class="action">전화하기</span>
        </a>

        <a href="https://www.mentalhealth.go.kr" target="_blank" class="contact-item" style="background: #ebf5fb;">
          <span class="icon">🔍</span>
          <div class="info">
            <span class="name" style="color: #2196f3;">가까운 정신건강복지센터 찾기</span>
            <span class="number" style="font-size: 12px; color: #999;">mentalhealth.go.kr</span>
          </div>
          <span class="action" style="color: #2196f3;">바로가기</span>
        </a>
      </div>

      <div class="safety-message">
        <p>
          당신은 혼자가 아닙니다.<br>
          지금 힘든 순간도 반드시 지나갑니다.<br>
          전문가의 도움을 받아보세요.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SafetyModal',
  emits: ['close']
}
</script>

<style scoped>
.safety-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease-out;
}

.safety-card {
  background: white;
  width: 90%;
  max-width: 360px;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  animation: slideUp 0.3s ease-out;
}

.safety-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.safety-header h2 {
  margin: 0;
  color: #e74c3c;
  font-size: 20px;
  font-weight: 800;
}

.close-btn {
  background: #f1f3f5;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  color: #868e96;
}

.contact-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  margin-bottom: 12px;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.contact-item:hover {
  background: white;
  border-color: #2196f3;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.1);
  transform: translateY(-2px);
}

.contact-item.highlight {
  background: #fff5f5;
  border-color: #ffc9c9;
}

.contact-item.highlight:hover {
  background: #ffe3e3;
}

.icon {
  font-size: 24px;
  margin-right: 16px;
}

.info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.number {
  font-size: 18px;
  font-weight: 800;
  color: #212529;
}

.action {
  font-size: 12px;
  color: white;
  background: #212529;
  padding: 6px 12px;
  border-radius: 20px;
}

.contact-item.highlight .action {
  background: #e74c3c;
}

.safety-message {
  text-align: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  color: #868e96;
  font-size: 13px;
  line-height: 1.6;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
