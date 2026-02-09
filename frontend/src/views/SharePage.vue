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
              placeholder="6자리 코드 입력" 
              maxlength="6"
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
                <span class="user-name">{{ user.name }}</span>
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
        goToStats
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

.info-box {
  background: #fff8e6;
  padding: 20px;
  border-radius: 16px;
}
.info-box h4 {
  margin: 0 0 8px 0;
  color: #f5a623;
  font-size: 15px;
}
.info-box p {
  margin: 0;
  font-size: 13px;
  color: #5c4b2e;
  line-height: 1.5;
}
</style>
