<template>
  <div class="share-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.go(-1)">‹</button>
      <h2>공유 및 연결</h2>
    </header>

    <div class="tab-container">
      <button 
        :class="['tab-btn', { active: activeTab === 'connect' }]"
        @click="activeTab = 'connect'"
      >
        연결하기 (보호자)
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'share' }]"
        @click="activeTab = 'share'"
      >
        공유하기 (내담자)
      </button>
    </div>

    <div class="content-area">
      <!-- 1. CONNECT TAB (Viewer) -->
      <div v-if="activeTab === 'connect'" class="tab-content">
        <section class="code-section">
          <h3>초대 코드 입력</h3>
          <p class="desc">상대방이 공유해준 코드를 입력하여 연결하세요.</p>
          
          <div class="input-wrapper">
            <input 
              v-model="inputCode" 
              type="text" 
              placeholder="8자리 코드 입력" 
              maxlength="8"
              @keyup.enter="connectWithCode"
            />
            <button @click="connectWithCode" :disabled="!inputCode || isLoading">
              {{ isLoading ? '연결 중...' : '연결하기' }}
            </button>
          </div>
        </section>

        <section class="list-section">
          <h3>연결된 사용자 목록</h3>
          <div v-if="isLoadingList" class="loading-box">목록 불러오는 중...</div>
          <div v-else-if="connectedList.length === 0" class="empty-box">
            연결된 사용자가 없습니다.
          </div>
          <ul v-else class="user-list">
            <li v-for="user in connectedList" :key="user.sharer_id" @click="goToStats(user.sharer_id)">
              <div class="user-info">
                <div class="name-row">
                    <span class="user-name">{{ user.name }}</span>
                    <span 
                        v-if="getBirthdayBadge(user.birth_date)" 
                        :class="['badge', getBirthdayBadge(user.birth_date).class]"
                    >
                        {{ getBirthdayBadge(user.birth_date).text }}
                    </span>
                </div>
                <span class="date">{{ formatDate(user.connected_at) }} 연결됨</span>
              </div>
              <span class="arrow">›</span>
            </li>
          </ul>
        </section>
      </div>

      <!-- 2. SHARE TAB (Sharer) -->
      <div v-if="activeTab === 'share'" class="tab-content">
        <section class="code-generator">
          <h3>내 공유 코드 생성</h3>
          <p class="desc">이 코드를 보호자나 친구에게 알려주세요.<br>10분간 유효합니다.</p>
          
          <div class="code-box" v-if="myCode">
            <span class="code">{{ myCode }}</span>
            <span class="timer" v-if="timeLeft > 0">({{ formatTime(timeLeft) }})</span>
            <span class="expired" v-else>만료됨</span>
          </div>

          <button class="generate-btn" @click="generateCode" :disabled="isLoading">
            {{ myCode ? '코드 재생성' : '코드 발급받기' }}
          </button>
        </section>

        <div class="info-box">
          <h4>💡 안내</h4>
          <p>
            코드가 입력되면 별도의 승인 절차 없이<br>
            상대방과 <strong>즉시 연결</strong>되며,<br>
            내 감정 통계와 리포트를 볼 수 있게 됩니다.
          </p>
        </div>

        <!-- [P1-수정4] 보호자 알림 공유 범위 설정 -->
        <section class="alert-scope-section">
          <h3>🔔 보호자에게 공유할 알림</h3>
          <p class="desc">보호자에게 전달되는 정보의 범위를 설정합니다.</p>
          
          <div class="toggle-list">
            <div class="toggle-row">
              <span class="toggle-icon">🌡️</span>
              <div class="toggle-info">
                <span class="toggle-title">기분 온도 알림</span>
                <span class="toggle-sub">매일의 감정 온도를 공유합니다</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="shareMood">
                <span class="slider"></span>
              </label>
            </div>
            <div class="toggle-row">
              <span class="toggle-icon">📊</span>
              <div class="toggle-info">
                <span class="toggle-title">분석 리포트</span>
                <span class="toggle-sub">주간/월간 감정 분석을 공유합니다</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="shareReport">
                <span class="slider"></span>
              </label>
            </div>
            <div class="toggle-row">
              <span class="toggle-icon">🚨</span>
              <div class="toggle-info">
                <span class="toggle-title">위기 감지 알림</span>
                <span class="toggle-sub">위기 신호 감지 시 즉시 알립니다</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="shareCrisis">
                <span class="slider"></span>
              </label>
            </div>
          </div>
          
          <div v-if="!shareCrisis" class="crisis-warning">
            ⚠️ 위기 알림이 꺼져 있으면 위급 상황에서 보호자가 알림을 받지 못합니다.
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

export default {
  name: 'SharePage',
  setup() {
    const router = useRouter();
    const activeTab = ref('connect'); // connect | share
    const isLoading = ref(false);
    
    // Connect Logic
    const inputCode = ref('');
    const connectedList = ref([]);
    const isLoadingList = ref(false);

    // Share Logic
    const myCode = ref('');
    const timeLeft = ref(0);
    let timerInterval = null;

    // [P1-수정4] Alert Share Scope
    const shareMood = ref(true);
    const shareReport = ref(true);
    const shareCrisis = ref(true);

    const formatDate = (isoStr) => {
        if(!isoStr) return '';
        return new Date(isoStr).toLocaleDateString();
    };

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s < 10 ? '0'+s : s}`;
    };

    // Load Connected List
    const fetchList = async () => {
        isLoadingList.value = true;
        try {
            const res = await api.get('/share/list');
            connectedList.value = res.data;
        } catch (e) {
            console.error("Failed to fetch list", e);
        } finally {
            isLoadingList.value = false;
        }
    };

    // Connect Action
    const connectWithCode = async () => {
        if(!inputCode.value) return;
        isLoading.value = true;
        try {
            const res = await api.post('/share/connect', { code: inputCode.value });
            alert(res.data.message);
            inputCode.value = '';
            fetchList(); // Refresh list
        } catch (e) {
            console.error(e);
            alert(e.response?.data?.message || "연결 실패");
        } finally {
            isLoading.value = false;
        }
    };

    // Generate Code Action
    const generateCode = async () => {
        isLoading.value = true;
        try {
            const res = await api.post('/share/code');
            myCode.value = res.data.code;
            startTimer(600); // 10 mins
        } catch (e) {
            console.error(e);
            alert("코드 생성 실패");
        } finally {
            isLoading.value = false;
        }
    };

    const startTimer = (seconds) => {
        if(timerInterval) clearInterval(timerInterval);
        timeLeft.value = seconds;
        timerInterval = setInterval(() => {
            if(timeLeft.value > 0) {
                timeLeft.value--;
            } else {
                clearInterval(timerInterval);
            }
        }, 1000);
    };

    const goToStats = (id) => {
        router.push(`/share/stats/${id}`);
    };

    const getBirthdayBadge = (birthDateStr) => {
        if (!birthDateStr) return null;
        
        const today = new Date();
        const birthDate = new Date(birthDateStr);
        if (isNaN(birthDate.getTime())) return null;

        const currentYear = today.getFullYear();
        
        // Create this year's birthday date object
        const thisYearBirthday = new Date(currentYear, birthDate.getMonth(), birthDate.getDate());
        
        // Reset times for accurate day diff
        today.setHours(0, 0, 0, 0);
        thisYearBirthday.setHours(0, 0, 0, 0);
        
        // Calculate difference in milliseconds
        const diffTime = thisYearBirthday - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return { text: '오늘 생일! 🎂', class: 'badge-today' };
        } else if (diffDays > 0 && diffDays <= 7) {
            return { text: `D-${diffDays}`, class: 'badge-upcoming' };
        } else if (diffDays < 0) {
            // Check next year for edge cases (e.g. late Dec vs early Jan)
            const nextYearBirthday = new Date(currentYear + 1, birthDate.getMonth(), birthDate.getDate());
            const nextDiffTime = nextYearBirthday - today;
            const nextDiffDays = Math.ceil(nextDiffTime / (1000 * 60 * 60 * 24));
             if (nextDiffDays > 0 && nextDiffDays <= 7) {
                return { text: `D-${nextDiffDays}`, class: 'badge-upcoming' };
            }
        }
        
        return null; // Not upcoming
    };

    onMounted(() => {
        fetchList();
    });

    return {
        activeTab,
        inputCode,
        connectedList,
        isLoading,
        isLoadingList,
        myCode,
        timeLeft,
        formatDate,
        formatTime,
        connectWithCode,
        generateCode,
        goToStats,
        getBirthdayBadge,
        shareMood,
        shareReport,
        shareCrisis
    };
  }
};
</script>

<style scoped>
.share-page {
  height: 100vh;
  background-color: #f5f5f7;
  display: flex;
  flex-direction: column;
}

.page-header {
  background: white;
  padding: 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.back-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #0071e3;
  margin-right: 16px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.tab-container {
  display: flex;
  padding: 16px;
  gap: 12px;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: #e5e5ea;
  color: #8e8e93;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #0071e3;
  color: white;
  box-shadow: 0 2px 8px rgba(0,113,227,0.3);
}

.content-area {
  flex: 1;
  padding: 0 20px 20px;
  overflow-y: auto;
}

/* Sections */
section {
  background: white;
  padding: 20px;
  border-radius: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}

h3 {
  margin: 0 0 8px 0;
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
}

.desc {
  font-size: 14px;
  color: #86868b;
  margin: 0 0 20px 0;
  line-height: 1.4;
}

/* Connect Tab */
.input-wrapper {
  display: flex;
  gap: 8px;
}
.input-wrapper input {
  flex: 1;
  padding: 12px;
  border: 1px solid #d1d1d6;
  border-radius: 12px;
  font-size: 16px;
  text-align: center;
  letter-spacing: 2px;
  text-transform: uppercase;
}
.input-wrapper button {
  padding: 0 20px;
  background: #1d1d1f;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
}

/* List */
.user-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.user-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f5f5f7;
  cursor: pointer;
}
.user-list li:last-child {
  border-bottom: none;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.user-name {
  font-weight: 600;
  font-size: 16px;
  color: #1d1d1f;
}
.date {
  font-size: 12px;
  color: #86868b;
  margin-top: 2px;
}
.arrow {
  color: #d1d1d6;
  font-size: 20px;
}

/* Share Tab */
.code-generator {
  text-align: center;
}
.code-box {
  background: #f5f5f7;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.code {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 4px;
  color: #0071e3;
  font-family: monospace;
}
.timer {
  font-size: 14px;
  color: #ff3b30;
  font-weight: 600;
}
.expired {
  color: #86868b;
  font-size: 14px;
}
.generate-btn {
  width: 100%;
  padding: 16px;
  background: #0071e3;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

/* [P1-수정4] Alert Scope Toggle */
.alert-scope-section {
  margin-top: 20px;
}
.toggle-list {
  border-top: 1px solid #f0f0f0;
}
.toggle-row {
  display: flex;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
}
.toggle-icon {
  font-size: 22px;
  width: 36px;
  flex-shrink: 0;
}
.toggle-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.toggle-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}
.toggle-sub {
  font-size: 11px;
  color: #86868b;
  margin-top: 2px;
}
.switch {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: #ccc;
  border-radius: 24px;
  transition: 0.3s;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: 0.3s;
}
.switch input:checked + .slider {
  background-color: #34c759;
}
.switch input:checked + .slider:before {
  transform: translateX(20px);
}
.crisis-warning {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff3e0;
  border-radius: 10px;
  font-size: 12px;
  color: #ff9500;
  line-height: 1.4;
}

.info-box {
  background: #fff8e6;
  padding: 20px;
  border-radius: 16px;
}
.info-box h4 {
  margin: 0 0 8px 0;
  color: #f5a623;
  font-size: 15px;
  font-weight: 600;
}
.info-box p {
  margin: 0;
  font-size: 13px;
  color: #5c4b2e;
  line-height: 1.5;
}

/* Badge Styles */
.name-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.badge {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 6px;
    font-weight: 700;
    color: white;
}

.badge-today {
    background-color: #ff3b30; /* Red */
    animation: pulse 2s infinite;
}

.badge-upcoming {
    background-color: #0071e3; /* Blue */
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}
</style>
