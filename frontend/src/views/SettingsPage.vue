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
        
        <!-- Share Link Button -->
        <div class="link-card" style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between; cursor: pointer;"
             @click="$router.push('/share')">
           <div>
              <h4 style="margin: 0; font-size: 16px;">🤝 보호자/친구 연결</h4>
              <p style="margin: 4px 0 0 0; font-size: 12px; color: #86868b;">가족이나 친구에게 내 감정 통계를 공유하세요.</p>
           </div>
           <span style="font-size: 20px; color: #d1d1d6;">›</span>
        </div>
      </section>

      <!-- Section 2: B2G 연동 (핵심) -->
      <section class="settings-section">
        <h3 class="section-title">기관 연동 (B2G)</h3>
        
        <!-- Case A: 연동 안 됨 -->
        <div v-if="!isLinked" class="link-card not-linked">
          <div class="card-header">
             <h4>보건소/정신건강복지센터 연결하기</h4>
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
          
          <div style="margin-top: 12px; padding-top: 12px; border-top: 1px dashed #e5e5ea;">
            <button class="force-sync-btn" @click="handleForceSync" :disabled="isLoading">
                🔄 데이터 강제 동기화 (서버 확인)
            </button>
            <p class="sync-desc">연동 상태가 이상하거나 데이터가 보이지 않을 때 눌러주세요.</p>
          </div>
        </div>
      </section>

      <!-- [New] Section 3: 멤버십 (Membership) -->
      <section class="settings-section">
        <h3 class="section-title">멤버십</h3>
        
        <!-- Case 1: 보건소 연동 사용자 -->
        <div v-if="isLinked" class="link-card linked" style="background-color: #f0f9ff; border-color: #bae6fd;">
            <div class="linked-header">
                <span class="check-icon">🏢</span>
                <span class="linked-title" style="color: #0369a1;">기관 연동 멤버십</span>
            </div>
            <p class="linked-desc" style="color: #0284c7;">보건소 연동으로 프리미엄 혜택이 적용됩니다.</p>
            <div class="code-display" style="margin-top: 8px;">
                <span style="color: #16a34a; font-weight: bold;">✅ 적용됨</span>
            </div>
        </div>

        <!-- Case 2: 일반 사용자 (미연동) -->
        <div v-else class="link-card not-linked" @click="handleUpgrade" style="cursor: pointer; background-color: #faf5ff; border-color: #e9d5ff;">
            <div class="card-header" style="display: flex; flex-direction: row; align-items: center; justify-content: space-between;">
                 <div>
                    <h4 style="color: #6b21a8; font-weight: bold; font-size: 1.1rem; margin: 0;">마음챙김 플러스 +</h4>
                    <p style="color: #9333ea; margin-top: 4px; font-size: 0.9rem;">더 깊은 분석과 무제한 감정 분석을 받아보세요.</p>
                 </div>
                 <div style="font-size: 1.5rem; color: #a855f7;">✨</div>
            </div>
            <div style="text-align: right; color: #94a3b8; margin-top: 8px; font-weight: bold;">➔</div>
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
            <span class="text-gray">maumON Team</span>
        </div>
      </section>

      <!-- Section 3.5: 법적 고지 (Legal Disclaimer) -->
      <section class="settings-section">
        <h3 class="section-title">⚖️ 법적 고지</h3>
        <div style="background: white; padding: 16px; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
          <p style="font-size: 14px; font-weight: 600; color: #1d1d1f; margin: 0 0 8px 0;">
            마음온은 감정 기록 보조 도구입니다
          </p>
          <p style="font-size: 12px; color: #86868b; line-height: 1.6; margin: 0 0 12px 0;">
            본 서비스는 의료 행위, 심리 치료, 또는 전문 상담을 대체하지 않습니다.
            AI가 제공하는 분석과 코멘트는 참고용이며, 의료적 판단으로 간주될 수 없습니다.
          </p>
          
          <div style="border-top: 1px solid #f5f5f7; padding-top: 12px; margin-bottom: 12px;">
            <p style="font-size: 12px; font-weight: 600; color: #ff3b30; margin: 0 0 6px 0;">⚠️ 긴급 상황 안내</p>
            <p style="font-size: 12px; color: #86868b; line-height: 1.6; margin: 0;">
              정신건강 위기 상황에서는 반드시 전문 의료기관 또는 아래 긴급전화를 이용해 주세요.<br/>
              • 자살예방 상담전화: 1393<br/>
              • 정신건강 위기상담전화: 1577-0199<br/>
              • 경찰: 112
            </p>
          </div>
          
          <div style="border-top: 1px solid #f5f5f7; padding-top: 12px;">
            <p style="font-size: 12px; font-weight: 600; color: #1d1d1f; margin: 0 0 6px 0;">📋 개인정보 처리</p>
            <p style="font-size: 12px; color: #86868b; line-height: 1.6; margin: 0;">
              기본적으로 모든 데이터는 사용자 기기에만 저장됩니다.
              기관 연동 시에만 사용자가 동의한 정보가 암호화되어 전송됩니다.
            </p>
          </div>
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
import api from '../services/api'; 

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

    const refreshStatus = async () => {
      try {
          // [Fix] 서버에서 최신 정보(User Me)를 가져와서 동기화
          const userRes = await api.get('/user/me'); // authAPI.getUserInfo()와 동일한 엔드포인트
          if (userRes && userRes.data) {
              const info = userRes.data;
              // DB 정보로 로컬 스토리지 갱신
              const code = info.linked_center_code || info.center_code || "";
              const isLinkedVal = !!code;
              
              localStorage.setItem("b2g_center_code", code);
              localStorage.setItem("b2g_is_linked", isLinkedVal.toString());
              
              isLinked.value = isLinkedVal;
              centerCode.value = code;
          }
      } catch (e) {
          console.error("Failed to refresh status from server", e);
          // 실패 시 캐시된 데이터라도 보여줌
          isLinked.value = localStorage.getItem("b2g_is_linked") === "true";
          centerCode.value = localStorage.getItem("b2g_center_code") || "";
      }
      
      lastSyncDate.value = localStorage.getItem("b2g_last_sync");
    };

    onMounted(() => {
      refreshStatus();
    });

    const handleConnect = async () => {
      if (!inputCode.value) return;
      
      isLoading.value = true;
      errorMsg.value = '';

      try {
        // [Direct API Call]
        console.log(`🚀 [Settings] Connecting to OCI server: ${inputCode.value}`);
        
        // [Standard API Call] Check verification
        const response = await api.post('/centers/verify-code/', { 
            center_code: inputCode.value,
            user_nickname: localStorage.getItem('user_nickname') || 'WebUser'
        });

        if (response.data.valid) {
            // [New] Step 2: Persist to DB immediately
            try {
                 await api.post('/b2g_sync/connect/', { center_id: response.data.center_id })
                 console.log("DB Linked from Settings")
            } catch (connErr) {
                 console.error("Connect failed in Settings", connErr)
            }

            // 성공 처리 - 로컬 스토리지 업데이트 대신 리프레시 수행
            alertMessage.value = response.data.message || "연동되었습니다!";
            showAlert.value = true;
            inputCode.value = ''; 
            
            // [Fix] 서버에서 최신 정보 받아오기 (확실한 동기화)
            await refreshStatus(); 
        }
      } catch (err) {
        console.error("❌ [Settings] Connection Error:", err);
        // 상세 에러 표시 (디버깅용)
        let msg = `⛔ 오류 발생: ${err.message}`;
        if (err.code) msg += ` (${err.code})`;
        
        if (err.response) {
            msg += `\n[Server ${err.response.status}] `;
            if (err.response.data && err.response.data.error) {
                msg += err.response.data.error;
            } else {
                 msg += JSON.stringify(err.response.data).substring(0, 50) + "...";
            }
        }
        
        errorMsg.value = msg;
        // 디버깅 메시지도 띄움
        alertMessage.value = msg; 
        showAlert.value = true;

      } finally {
        isLoading.value = false;
      }
    };

    const handleDisconnect = () => {
      if(confirm('정말 연동을 해제하시겠습니까?')) {
        localStorage.removeItem("b2g_center_code");
        localStorage.removeItem("b2g_is_linked");
        localStorage.removeItem("b2g_last_sync");
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

    const handleUpgrade = () => {
        alertMessage.value = "🌟 마음챙김 플러스\n\n현재 무료 시범 운영 중입니다.\n가까운 보건소에 문의하세요!";
        showAlert.value = true;
    };

    const formatDate = (isoString) => {
        if(!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString();
    }

    const handleForceSync = async () => {
        if (confirm("서버와 통신하여 연동 상태를 강제로 동기화하시겠습니까?")) {
            isLoading.value = true;
            try {
                await refreshStatus();
                // [Self-Healing] 만약 로컬엔 코드가 없는데 서버엔 있다면 복구됨
                // 만약 로컬엔 있는데 서버엔 없다면? -> 끊김 (정상)
                alert("동기화가 완료되었습니다.\n현재 연동 상태: " + (isLinked.value ? "연동됨" : "미연동"));
            } catch (e) {
                alert("동기화 실패: " + e.message);
            } finally {
                isLoading.value = false;
            }
        }
    };

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
      handleForceSync,
      handleUpgrade,
      formatDate
    };
  }
};
</script>

<style scoped>
.settings-page {
  background-color: #f5f5f7;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  background: white;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
  z-index: 10;
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
  flex: 1;
  overflow-y: auto;
  width: 100%;
  padding-bottom: 120px; /* Safe area for bottom navigation */
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

.force-sync-btn {
    width: 100%;
    padding: 10px;
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    color: #0284c7;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.force-sync-btn:hover {
    background: #e0f2fe;
}
.sync-desc {
    font-size: 11px;
    color: #94a3b8;
    text-align: center;
    margin-top: 4px;
}
</style>
