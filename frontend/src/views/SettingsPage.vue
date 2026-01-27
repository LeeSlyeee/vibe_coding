<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>설정</h2>
    </div>

    <div class="settings-content">
      <!-- Section 1: 내 정보 -->
      <section class="settings-section">
        <h3 class="section-title">내 정보</h3>
        <div class="profile-card">
          <div class="profile-icon">👤</div>
          <div class="profile-info">
            <p class="profile-name">사용자</p>
            <p class="profile-desc">Web Mode</p>
          </div>
        </div>
      </section>

      <!-- Section 2: B2G 연동 (핵심) -->
      <section class="settings-section">
        <h3 class="section-title">기관 연동 (B2G)</h3>
        
        <!-- Case A: 연동 안 됨 -->
        <div v-if="!isLinked" class="link-card not-linked">
          <div class="card-header">
             <h4>보건소/상담센터 연결하기</h4>
             <p>담당 선생님께 전달받은 코드를 입력하세요.</p>
          </div>
          
          <div class="input-group">
            <input 
              type="text" 
              v-model="inputCode" 
              placeholder="예: SEOUL-001" 
              :disabled="isLoading"
              @keyup.enter="handleConnect"
            />
            <button @click="handleConnect" :disabled="!inputCode || isLoading">
              {{ isLoading ? '연결 중...' : '연결' }}
            </button>
          </div>
          <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
        </div>

        <!-- Case B: 연동 됨 -->
        <div v-if="isLinked" class="link-card linked">
          <div class="linked-header">
            <span class="check-icon">✅</span>
            <span class="linked-title">보건소 연동됨</span>
          </div>
          <p class="linked-desc">현재 담당 선생님과 연결되어 있습니다.</p>
          
          <div class="code-display">
            <span class="label">연동 코드:</span>
            <span class="code">{{ centerCode }}</span>
          </div>

          <div class="sync-info" v-if="lastSyncDate">
            마지막 전송: {{ formatDate(lastSyncDate) }}
          </div>
          
          <button class="disconnect-btn" @click="handleDisconnect">연동 해제</button>
        </div>
      </section>

      <!-- Section 3: 앱 정보 -->
      <section class="settings-section">
        <h3 class="section-title">앱 정보</h3>
        <div class="info-row">
            <span>버전</span>
            <span class="text-gray">1.0.0 (Web)</span>
        </div>
        <div class="info-row">
            <span>개발자</span>
            <span class="text-gray">Maum-on Team</span>
        </div>
      </section>

      <!-- Section 4: 계정 관리 -->
      <section class="logout-section">
        <button class="logout-full-btn" @click="handleLogout">
          로그아웃
        </button>
      </section>
    </div>

    <!-- Alert Modal -->
    <div v-if="showAlert" class="modal-overlay">
        <div class="modal-box">
            <p style="white-space: pre-line">{{ alertMessage }}</p>
            <button @click="showAlert = false">확인</button>
        </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { B2GService } from '../services/B2GService';
import { authAPI } from '../services/api';

export default {
  name: 'SettingsPage',
  setup() {
    const router = useRouter();
    const isLinked = ref(false);
    const centerCode = ref('');
    const inputCode = ref('');
    const isLoading = ref(false);
    const errorMsg = ref('');
    const lastSyncDate = ref(null);
    
    // Alert State
    const showAlert = ref(false);
    const alertMessage = ref('');

    // Fetch user info for profile name could be added here
    
    const refreshStatus = () => {
      isLinked.value = B2GService.isLinked();
      centerCode.value = B2GService.getCenterCode();
      lastSyncDate.value = B2GService.getLastSyncDate();
    };

    onMounted(() => {
      refreshStatus();
    });

    const handleConnect = async () => {
      if (!inputCode.value) return;
      
      isLoading.value = true;
      errorMsg.value = '';

      try {
        const result = await B2GService.connect(inputCode.value);
        if (result.success) {
            alertMessage.value = result.message;
            showAlert.value = true;
            inputCode.value = ''; // clear
            refreshStatus();
        }
      } catch (err) {
        errorMsg.value = err;
      } finally {
        isLoading.value = false;
      }
    };

    const handleDisconnect = () => {
      if(confirm('정말 연동을 해제하시겠습니까?')) {
        B2GService.disconnect();
        refreshStatus();
      }
    };

    const handleLogout = () => {
        // App.vue의 로그아웃 로직을 재사용하거나 직접 구현
        // 여기서는 안전하게 이벤트를 발생시키거나 직접 처리
        if(confirm('정말 로그아웃 하시겠습니까?')) {
            localStorage.removeItem("token");
            localStorage.removeItem("authToken");
            router.push("/login");
        }
    };

    const formatDate = (isoString) => {
        if(!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString();
    }

    return {
      isLinked,
      centerCode,
      inputCode,
      isLoading,
      errorMsg,
      lastSyncDate,
      showAlert,
      alertMessage,
      handleConnect,
      handleDisconnect,
      handleLogout,
      formatDate
    };
  }
};
</script>

<style scoped>
.settings-page {
  padding-bottom: 80px; /* Bottom Nav Space */
  background-color: #f5f5f7;
  min-height: 100vh;
}

.page-header {
  background: white;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1d1d1f;
}

.settings-content {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.settings-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  color: #86868b;
  margin-bottom: 8px;
  padding-left: 4px;
  font-weight: 600;
}

/* Profile Card */
.profile-card {
  background: white;
  padding: 16px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.profile-icon {
  font-size: 32px;
  background: #f5f5f7;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.profile-name {
  font-weight: 700;
  font-size: 18px;
  margin: 0;
}

.profile-desc {
  font-size: 13px;
  color: #86868b;
  margin: 4px 0 0 0;
}

/* Link Card */
.link-card {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.card-header p {
  margin: 4px 0 12px 0;
  font-size: 13px;
  color: #86868b;
}

.input-group {
  display: flex;
  gap: 8px;
}

.input-group input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e5e5ea;
  border-radius: 10px;
  font-size: 15px;
}

.input-group button {
  padding: 0 20px;
  background: #0071e3;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.input-group button:disabled {
  background: #d1d1d6;
}

.error-text {
  color: #ff3b30;
  font-size: 13px;
  margin-top: 8px;
}

/* Linked State */
.linked-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.linked-title {
  color: #34c759;
  font-weight: 700;
  font-size: 16px;
}

.linked-desc {
  font-size: 14px;
  color: #1d1d1f;
  margin-bottom: 16px;
}

.code-display {
  background: #f5f5f7;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.code-display .label {
  font-size: 13px;
  color: #86868b;
}

.code-display .code {
  font-family: monospace;
  font-weight: 700;
  font-size: 16px;
}

.sync-info {
  font-size: 12px;
  color: #86868b;
  text-align: right;
  margin-bottom: 12px;
}

.disconnect-btn {
  width: 100%;
  padding: 10px;
  background: white;
  border: 1px solid #ff3b30;
  color: #ff3b30;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

/* Info Row */
.info-row {
  background: white;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #f5f5f7;
}
.info-row:first-of-type {
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}
.info-row:last-of-type {
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    border-bottom: none;
}

.text-gray {
  color: #86868b;
}

/* Logout */
.logout-full-btn {
  width: 100%;
  padding: 16px;
  background: white;
  border: none;
  border-radius: 16px;
  color: #ff3b30;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

/* Modal */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
}

.modal-box {
    background: white;
    padding: 24px;
    border-radius: 16px;
    text-align: center;
    width: 80%;
    max-width: 300px;
}
.modal-box button {
    margin-top: 16px;
    padding: 8px 24px;
    background: #0071e3;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
</style>
