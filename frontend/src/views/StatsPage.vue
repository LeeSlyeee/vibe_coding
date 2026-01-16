<template>
  <div class="stats-page">
    <div class="stats-container">
      <header class="stats-header">
         <div class="header-left">
           <h2>나의 감정 분석 리포트</h2>
           <p class="subtitle">나의 마음 흐름을 다양한 관점에서 살펴보세요.</p>
         </div>
         <button @click="$router.push('/calendar')" class="close-btn">
            <span class="icon">✖</span> 닫기
         </button>
      </header>

      <!-- Navigation Tabs -->
      <nav class="stats-nav">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['nav-item', { active: currentTab === tab.id }]"
            @click="currentTab = tab.id"
          >
            <span class="nav-icon">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
      </nav>

      <div class="stats-content">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
           <div class="spinner"></div>
           <p>데이터를 분석하고 있습니다...</p>
        </div>

        <div v-else class="content-body">
            <!-- 1. 월별 기록 추이 (Monthly Daily Charts) -->
            <transition name="fade" mode="out-in">
                <div v-if="currentTab === 'monthly'" key="monthly" class="chart-section">
                    <div class="section-info">
                        <h3>📅 월별 상세 기록</h3>
                        <p>각 달마다 나의 기록 습관을 확인해보세요.</p>
                    </div>
                    
                    <div class="charts-grid">
                        <div v-for="chart in monthlyCharts" :key="chart.month" class="month-chart-card">
                            <h4 class="month-title">{{ chart.month }}</h4>
                            <div class="chart-wrapper sub-chart">
                                <Bar :data="chart.data" :options="chart.options" />
                            </div>
                        </div>
                        
                        <div v-if="monthlyCharts.length === 0" class="no-data">
                            데이터가 충분하지 않습니다.
                        </div>
                    </div>
                </div>

                <!-- 2. 감정 분포 (Mood Distribution) -->
                <div v-else-if="currentTab === 'mood'" key="mood" class="chart-section mood-layout">
                    <div class="section-info">
                        <h3>😊 감정 분포</h3>
                        <p>나의 주된 감정 상태는 무엇일까요?</p>
                    </div>
                    <div class="mood-content">
                        <div class="chart-wrapper donut-chart">
                            <Doughnut :data="moodChartData" :options="doughnutOptions" />
                        </div>
                        <div class="mood-legend">
                            <div v-for="(item, index) in moodLegendData" :key="index" class="legend-item">
                                <span class="dot" :style="{ background: item.color }"></span>
                                <span class="label">{{ item.label }}</span>
                                <span class="value">{{ item.count }}회 ({{ item.percent }}%)</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 3. 날씨별 기록 (Weather Stats) -->
                <div v-else-if="currentTab === 'weather'" key="weather" class="chart-section">
                     <div class="section-info">
                        <h3>🌤️ 날씨와 감정</h3>
                        <p>어떤 날씨에 일기를 자주 썼을까요?</p>
                    </div>
                    <div class="chart-wrapper main-chart">
                        <Bar :data="weatherChartData" :options="weatherBarOptions" />
                    </div>
                </div>
            </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, reactive } from 'vue'
import { diaryAPI } from '../services/api'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js'
import { Bar, Doughnut } from 'vue-chartjs'

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement)

export default {
  name: 'StatsPage',
  components: { Bar, Doughnut },
  setup() {
    const loading = ref(true)
    const currentTab = ref('monthly')
    const rawStats = ref({ monthly: [], moods: [], weather: [], daily: [] })

    const tabs = [
        { id: 'monthly', label: '월별 기록', icon: '📅' },
        { id: 'mood', label: '감정 분포', icon: '🎨' },
        { id: 'weather', label: '날씨 통계', icon: '☁️' }
    ]

    // === Chart Options ===
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(0,0,0,0.8)',
                padding: 12,
                cornerRadius: 8,
                displayColors: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: '#f0f0f0' },
                ticks: { display: false } // Hide Y axis labels for cleaner look in small charts
            },
            x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, maxRotation: 0, autoSkip: true }
            }
        },
        animation: { duration: 1000 }
    }

    const weatherBarOptions = {
        ...commonOptions,
        scales: {
            y: { beginAtZero: true, grid: { color: '#f0f0f0' }, stacked: true },
            x: { grid: { display: false }, stacked: true }
        },
        plugins: {
            legend: { 
                display: true, 
                position: 'bottom',
                labels: { font: { size: 11 }, padding: 15, usePointStyle: true }
            },
            tooltip: { ...commonOptions.plugins.tooltip }
        }
    }
    
    // Doughnut specific options
    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
            legend: { display: false },
            tooltip: { 
                callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.raw}회` }
            }
        }
    }

    // === Computed Data for Charts ===
    
    // 1. Monthly Daily Charts (NEW) (unchanged)
    const monthlyCharts = computed(() => {
        if (!rawStats.value.daily) return []

        const grouped = {}
        rawStats.value.daily.forEach(item => {
            const month = item._id.substring(0, 7)
            if (!grouped[month]) grouped[month] = {}
            grouped[month][item._id] = item.count
        })

        const sortedMonths = Object.keys(grouped).sort().reverse()

        return sortedMonths.map(monthStr => {
            const [year, month] = monthStr.split('-').map(Number)
            const daysInMonth = new Date(year, month, 0).getDate()
            
            const labels = []
            const data = []
            
            for (let i = 1; i <= daysInMonth; i++) {
                labels.push(i)
                const dateKey = `${monthStr}-${String(i).padStart(2, '0')}`
                data.push(grouped[monthStr][dateKey] || 0)
            }

            return {
                month: `${year}년 ${month}월`,
                data: {
                    labels,
                    datasets: [{
                        label: '작성',
                        data,
                        backgroundColor: '#1d1d1f',
                        borderRadius: 4,
                        barPercentage: 0.6
                    }]
                },
                options: commonOptions
            }
        })
    })

    // 2. Mood Data
    const moodMap = {
        1: { label: '화남 😠', color: '#EF9A9A' },
        2: { label: '우울 😢', color: '#90CAF9' },
        3: { label: '그저그럼 😐', color: '#E0E0E0' },
        4: { label: '편안 😌', color: '#A5D6A7' },
        5: { label: '행복 😊', color: '#FFE082' }
    }

    const moodChartData = computed(() => {
        const dataMap = {}
        rawStats.value.moods.forEach(m => dataMap[m._id] = m.count)
        
        const labels = []
        const data = []
        const backgroundColor = []
        const order = [5, 4, 3, 2, 1]
        
        order.forEach(id => {
            if (dataMap[id]) {
                const info = moodMap[id]
                labels.push(info.label)
                data.push(dataMap[id])
                backgroundColor.push(info.color)
            }
        })
        
        if (data.length === 0) return { labels: ['Empty'], datasets: [{ data: [1], backgroundColor: ['#eee'] }] }

        return {
            labels,
            datasets: [{ backgroundColor, borderWidth: 0, data }]
        }
    })

    const moodLegendData = computed(() => {
        const total = rawStats.value.moods.reduce((acc, cur) => acc + cur.count, 0) || 1
        const list = []
        const order = [5, 4, 3, 2, 1]
        const dataMap = {}
        rawStats.value.moods.forEach(m => dataMap[m._id] = m.count)

        order.forEach(id => {
            if (dataMap[id]) {
                const info = moodMap[id]
                const count = dataMap[id]
                list.push({
                    label: info.label,
                    color: info.color,
                    count,
                    percent: Math.round((count / total) * 100)
                })
            }
        })
        return list
    })

    // 3. Weather Data (New Stacked Logic)
    const weatherChartData = computed(() => {
        if (!rawStats.value.weather || rawStats.value.weather.length === 0) {
             return { labels: [], datasets: [] }
        }

        const labels = rawStats.value.weather.map(w => w._id)
        
        // Define order: Happy -> Calm -> Neutral -> Sad -> Angry
        const order = [5, 4, 3, 2, 1]
        
        const datasets = order.map(moodId => {
            const info = moodMap[moodId]
            const data = rawStats.value.weather.map(w => {
                 // w.moods is an array of { mood: <id>, count: <val> }
                 const found = w.moods ? w.moods.find(m => m.mood === moodId) : null
                 return found ? found.count : 0
            })
            
            return {
                label: info.label,
                backgroundColor: info.color,
                data: data,
                borderRadius: 4,
                // barPercentage: 0.6
            }
        })

        return {
            labels,
            datasets: datasets
        }
    })

    onMounted(async () => {
        try {
            const res = await diaryAPI.getStatistics()
            rawStats.value = { ...res, daily: res.daily || [] }
        } catch (e) {
            console.error(e)
        } finally {
            loading.value = false
        }
    })

    return {
        loading,
        currentTab,
        tabs,
        monthlyCharts, 
        moodChartData, doughnutOptions, moodLegendData,
        weatherChartData, weatherBarOptions
    }
  }
}
</script>

<style scoped>
.stats-page {
  height: 100%;
  overflow: hidden;
  background: #f5f5f7;
  padding: 20px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.stats-container {
  max-width: 900px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.stats-header {
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

/* Navigation Tabs */
.stats-nav {
  flex-shrink: 0;
  display: flex;
  background: white;
  padding: 6px;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
  gap: 8px;
}
.nav-item {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #86868b;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.nav-item:hover {
  background: rgba(0,0,0,0.02);
  color: #1d1d1f;
}
.nav-item.active {
  background: #1d1d1f;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.nav-icon { font-size: 18px; }

/* Content Area */
.stats-content {
  flex: 1;
  min-height: 0;
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Clips scrollbar at corners */
}

.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
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

.loading-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #86868b;
}
.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f2f2f7;
  border-top-color: #1d1d1f;
  border-radius: 50%;
  animation: spin 1s infinite linear;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Chart Sections */
.chart-section {
  padding-bottom: 20px;
}
.section-info { margin-bottom: 30px; text-align: center; }
.section-info h3 { font-size: 22px; margin: 0 0 8px; color: #1d1d1f; }
.section-info p { color: #86868b; margin: 0; font-size: 15px; }

.charts-grid {
    display: flex;
    flex-direction: column;
    gap: 40px;
}
.month-chart-card {
    background: #fbfbfd;
    padding: 24px;
    border-radius: 20px;
    border: 1px solid #f2f2f7;
}
.month-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 16px 0;
    color: #1d1d1f;
}

.chart-wrapper {
  flex: 1;
  position: relative;
  width: 100%;
}
.main-chart { min-height: 350px; }
.sub-chart { min-height: 200px; } 
.donut-chart { min-height: 300px; max-width: 400px; margin: 0 auto; }

/* Mood Layout Specifics */
.mood-layout .mood-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}
.mood-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 200px;
}
.legend-item {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #444;
  background: #fbfbfd;
  padding: 10px 16px;
  border-radius: 12px;
  border: 1px solid #f2f2f7;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 12px;
}
.label { flex: 1; font-weight: 600; }
.value { font-weight: 400; color: #86868b; font-size: 13px; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .stats-header { flex-direction: column; gap: 16px; }
  .close-btn { align-self: flex-end; }
  .mood-layout .mood-content { flex-direction: column; }
  .stats-content { padding: 24px; }
}
</style>
