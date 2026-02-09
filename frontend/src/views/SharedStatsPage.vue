<template>
  <div class="shared-stats-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.go(-1)">‹</button>
      <div v-if="stats" class="header-info">
        <h2>{{ stats.user_name }}님의 마음</h2>
        <span class="sync-time" v-if="stats.last_sync">
            마지막 업데이트: {{ formatDate(stats.last_sync) }}
        </span>
      </div>
      <div v-else>
        <h2>불러오는 중...</h2>
      </div>
    </header>

    <div class="content-area" v-if="stats">
      <!-- 1. Mood Chart -->
      <section class="card chart-card">
        <h3>📊 최근 7일 기분 흐름</h3>
        <div class="chart-wrapper">
          <Line v-if="chartData" :data="chartData" :options="chartOptions" />
          <p v-else class="no-data">데이터가 부족합니다.</p>
        </div>
      </section>

      <!-- 2. AI Report -->
      <section class="card report-card">
        <h3>💌 최근 AI 리포트</h3>
        <div class="report-content" v-if="stats.latest_report">
           <div class="text" v-html="formattedReport"></div>
        </div>
        <div v-else class="empty-report">
            아직 생성된 리포트가 없습니다.
        </div>
      </section>
      
      <!-- 3. Risk Level (Optional/Simple) -->
      <section class="card risk-card" v-if="stats.risk_level >= 3">
        <div class="warning-box">
             ⚠️ <strong>주의 필요</strong>
             <p>최근 감정 상태가 불안정할 수 있습니다.<br>따뜻한 관심이 필요해요.</p>
        </div>
      </section>
    </div>

    <div v-if="isLoading" class="loading-overlay">
        <div class="spinner"></div>
        <p>데이터를 동기화하고 있어요...</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import api from '../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default {
  name: 'SharedStatsPage',
  components: { Line },
  setup() {
    const route = useRoute();
    const stats = ref(null);
    const isLoading = ref(true);

    const formatDate = (isoStr) => {
        if(!isoStr) return '';
        const d = new Date(isoStr);
        return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${d.getMinutes() < 10 ? '0'+d.getMinutes() : d.getMinutes()}`;
    };

    const formattedReport = computed(() => {
        if(!stats.value?.latest_report) return '';
        return stats.value.latest_report.replace(/\n/g, '<br>');
    });

    // Chart Data
    const chartData = computed(() => {
        if(!stats.value?.recent_moods || stats.value.recent_moods.length === 0) return null;
        
        // Sort by date ascending
        const sorted = [...stats.value.recent_moods].reverse(); // API returns desc usually, check backend
        // Backend Aggregation: {"$sort": {"created_at": -1}}, limit 7. So [Today, Yesterday...]
        // We need to reverse it to show [Oldest -> Newest] on chart.
        
        return {
            labels: sorted.map(m => m.date.slice(5)), // "MM-DD"
            datasets: [{
                label: '기분',
                data: sorted.map(m => m.mood),
                borderColor: '#0071e3',
                backgroundColor: 'rgba(0, 113, 227, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#0071e3',
                pointBorderWidth: 2
            }]
        };
    });

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const val = ctx.raw;
                        const map = {1:'🤬 화남', 2:'😢 우울', 3:'😐 보통', 4:'😌 편안', 5:'🥰 행복'};
                        return map[val] || val;
                    }
                }
            }
        },
        scales: {
            y: {
                min: 0,
                max: 6,
                ticks: {
                    stepSize: 1,
                    callback: (v) => ({1:'🤬', 2:'😢', 3:'😐', 4:'😌', 5:'🥰'}[v] || '')
                },
                grid: { color: '#f5f5f7' }
            },
            x: {
                grid: { display: false }
            }
        }
    };

    const fetchData = async () => {
        isLoading.value = true;
        try {
            const res = await api.get(`/share/insights/${route.params.id}`);
            stats.value = res.data;
        } catch (e) {
            console.error(e);
            alert("데이터를 불러오지 못했습니다.");
        } finally {
            isLoading.value = false;
        }
    };

    onMounted(() => {
        fetchData();
    });

    return {
        stats,
        isLoading,
        chartData,
        chartOptions,
        formatDate,
        formattedReport
    };
  }
};
</script>

<style scoped>
.shared-stats-page {
  min-height: 100vh;
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
  position: sticky;
  top: 0;
  z-index: 10;
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

.header-info {
    display: flex;
    flex-direction: column;
}

.header-info h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #1d1d1f;
}

.sync-time {
    font-size: 12px;
    color: #86868b;
    margin-top: 2px;
}

.content-area {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}

.card h3 {
  margin: 0 0 16px 0;
  font-size: 17px;
  font-weight: 700;
  color: #1d1d1f;
}

/* Chart */
.chart-wrapper {
  height: 250px;
  width: 100%;
}

/* Report */
.report-content .text {
    font-size: 15px;
    line-height: 1.6;
    color: #333;
}
.empty-report {
    color: #86868b;
    text-align: center;
    padding: 20px;
}

/* Risk */
.warning-box {
    background: #fff5f5;
    border: 1px solid #ff3b30;
    color: #ff3b30;
    padding: 16px;
    border-radius: 12px;
    text-align: center;
}
.warning-box strong {
    font-size: 16px;
    display: block;
    margin-bottom: 4px;
}
.warning-box p {
    font-size: 13px;
    margin: 0;
    opacity: 0.9;
}

/* Loading */
.loading-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(255,255,255,0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 100;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0071e3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
