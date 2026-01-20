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
            <!-- 0. 감정 흐름 (Flow) -->
            <transition name="fade" mode="out-in">
                <div v-if="currentTab === 'flow'" key="flow" class="chart-section">
                     <div class="section-info">
                         <h3>📈 감정 흐름</h3>
                         <p>나의 기분이 시간의 흐름에 따라 어떻게 변해왔는지 확인해보세요.</p>
                     </div>
                     <div class="chart-wrapper main-chart">
                         <Line :data="flowChartData" :options="flowChartOptions" />
                     </div>
                </div>

                <div v-else-if="currentTab === 'monthly'" key="monthly" class="chart-section">
                    <div class="section-info">
                        <h3>📅 월별 상세 기록</h3>
                        <p>각 날짜별로 기록된 나의 기분 변화를 확인해보세요.</p>
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

                <!-- 4. AI 심층 리포트 (New) -->
                <div v-else-if="currentTab === 'report'" key="report" class="chart-section report-section">
                    <div class="section-info">
                        <h3>🔮 AI 심층 심리 분석</h3>
                        <p>전문 AI 상담사가 나의 기록을 바탕으로 마음의 지도를 그려드립니다.</p>
                        <p>분석하고 완료까지 약 10분정도 소요됩니다.</p>
                    </div>

                    <div class="report-container">
                        <!-- 1. 생성 전 (버튼) -->
                        <div v-if="!isGeneratingReport && !formattedReportContent" class="report-initial">
                             <div class="report-icon-large">🧘</div>
                             <p>최근 50개의 일기 기록을 종합적으로 분석하여<br>현재 심리 상태 진단과 맞춤형 조언을 제공합니다.</p>
                             <button @click="handleGenerateReport" class="generate-btn">
                                심층 리포트 생성하기
                             </button>
                             <p class="notice">* 생성에는 약 10분이 소요됩니다.</p>
                        </div>

                        <!-- 2. 생성 중 (로딩) -->
                        <div v-else-if="isGeneratingReport" class="report-loading">
                            <div class="spinner-large"></div>
                            <p class="loading-text">AI가 내면의 목소리를 듣고 있어요...</p>
                            <p class="loading-sub">잠시만 기다려주세요 (최대 10분)</p>
                        </div>

                        <!-- 3. 결과 (리포트) -->
                        <div v-else class="report-result">
                            <div class="report-meta">
                                <span class="report-date">{{ new Date().toLocaleDateString() }} 기준 분석</span>
                                <div class="report-actions">
                                    <button @click="handleGenerateLongTermReport" class="meta-btn" :disabled="isGeneratingLongTerm">
                                        <span v-if="isGeneratingLongTerm">분석 중...</span>
                                        <span v-else>🧠 과거 기록 통합 분석 (Meta-Analysis)</span>
                                    </button>
                                    <button @click="handleGenerateReport" class="regenerate-btn">다시 분석하기</button>
                                </div>
                            </div>
                            
                            <!-- 메타 분석 결과 (Long Term) -->
                            <div v-if="longTermReportContent" class="long-term-box">
                                <h4>🧠 장기 심리 변화 분석 (Meta-Insight)</h4>
                                <div class="report-text" v-html="formattedLongTermContent"></div>
                            </div>
                            
                            <!-- 기본 리포트 -->
                            <div class="report-content-box">
                                <div class="report-text" v-html="formattedReportContent"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, reactive, onUnmounted } from 'vue'
import { diaryAPI } from '../services/api'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement, PointElement, LineElement)

export default {
  name: 'StatsPage',
  components: { Bar, Doughnut, Line },
  setup() {
    const loading = ref(true)
    const currentTab = ref('flow') // Default to 'flow'
    const rawStats = ref({ monthly: [], moods: [], weather: [], daily: [], timeline: [] })
    
    // Report State
    const isGeneratingReport = ref(false)
    const reportContent = ref('')
    
    // Long-term Report State
    const isGeneratingLongTerm = ref(false)
    const longTermReportContent = ref('')

    const tabs = [
        { id: 'flow', label: '감정 흐름', icon: '📈' },
        { id: 'monthly', label: '월별 기록', icon: '📅' },
        { id: 'mood', label: '감정 분포', icon: '🎨' },
        { id: 'weather', label: '날씨 통계', icon: '☁️' },
        { id: 'report', label: 'AI 심층 진단', icon: '🔮' }
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
                ticks: { display: false } 
            },
            x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, maxRotation: 0, autoSkip: true }
            }
        },
        animation: { duration: 1000 }
    }

    // Flow Chart Options (Line)
    const flowChartOptions = {
        ...commonOptions,
        scales: {
            y: {
                min: 0,
                max: 6,
                grid: { color: '#f0f0f0' },
                ticks: {
                    stepSize: 1,
                    callback: function(value) {
                         const map = { 1: '😠', 2: '😢', 3: '😐', 4: '😌', 5: '😊' }
                         return map[value] || ''
                    },
                    font: { size: 20 }
                }
            },
            x: {
                grid: { display: false },
                ticks: { display: false } // Hide Date Labels
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const index = context.dataIndex
                        const timelineItem = rawStats.value.timeline[index]
                        const map = { 1: '화남/부정', 2: '우울/슬픔', 3: '보통', 4: '편안/안정', 5: '행복/기쁨' }
                        
                        let label = `기분: ${map[context.raw] || context.raw}`
                        if (timelineItem && timelineItem.ai_label) {
                            // "슬픔 (비통함) (85.2%)" -> "슬픔 (비통함)" for cleaner tooltip
                            const cleanLabel = timelineItem.ai_label.split('(')[0] + (timelineItem.ai_label.includes('(') ? '(' + timelineItem.ai_label.split('(')[1].split(')')[0] + ')' : '')
                            label += ` | AI 분석: ${cleanLabel}`
                        }
                        return label
                    }
                }
            }
        }
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
    
    // 0. Flow Data (Timeline)
    const flowChartData = computed(() => {
        const timeline = rawStats.value.timeline || []
        
        // 데이터가 너무 많으면 적당히 샘플링하거나 최근 30~50개만 보여주기? 일단 전체 보여줌.
        // UI가 깨지지 않게 Chart.js가 알아서 처리해주길 기대.
        
        return {
            labels: timeline.map(t => t.date.slice(5)), // MM-DD만 표시
            datasets: [{
                label: '기분 흐름',
                data: timeline.map(t => t.mood_level),
                borderColor: '#1d1d1f',
                backgroundColor: 'rgba(29, 29, 31, 0.1)',
                tension: 0.4, // 곡선
                pointBackgroundColor: '#1d1d1f',
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: true
            }]
        }
    })


    // 1. Monthly Daily Charts (NEW) (unchanged)
    const monthlyCharts = computed(() => {
        if (!rawStats.value.daily) return []

        const grouped = {}
        rawStats.value.daily.forEach(item => {
            const month = item._id.substring(0, 7)
            if (!grouped[month]) grouped[month] = {}
            grouped[month][item._id] = item.count // Now stores mood level
        })

        const sortedMonths = Object.keys(grouped).sort().reverse()

        return sortedMonths.map(monthStr => {
            const [year, month] = monthStr.split('-').map(Number)
            const daysInMonth = new Date(year, month, 0).getDate()
            
            const labels = []
            const data = []
            const bgColors = []
            
            for (let i = 1; i <= daysInMonth; i++) {
                labels.push(i)
                const dateKey = `${monthStr}-${String(i).padStart(2, '0')}`
                const moodVal = grouped[monthStr][dateKey] || 0
                data.push(moodVal)
                bgColors.push(moodVal ? (moodMap[moodVal] ? moodMap[moodVal].color : '#1d1d1f') : 'rgba(0,0,0,0.03)')
            }

            return {
                month: `${year}년 ${month}월`,
                data: {
                    labels,
                    datasets: [{
                        label: '기분',
                        data,
                        backgroundColor: bgColors,
                        borderRadius: 4,
                        barPercentage: 0.7
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        y: {
                            min: 0,
                            max: 5,
                            grid: { display: false },
                            ticks: {
                                stepSize: 1,
                                callback: (v) => v === 0 ? '' : {1:'😠', 2:'😢', 3:'😐', 4:'😌', 5:'😊'}[v],
                                font: { size: 14 }
                            }
                        },
                        x: {
                            ...commonOptions.scales.x,
                            ticks: { font: { size: 9 }, autoSkip: false }
                        }
                    },
                    plugins: {
                        ...commonOptions.plugins,
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const val = ctx.raw
                                    const labelMap = { 1: '화남', 2: '슬픔', 3: '평범', 4: '편안', 5: '행복' }
                                    return val > 0 ? ` 기분: ${labelMap[val]} (${val})` : ' 기록 없음'
                                }
                            }
                        }
                    }
                }
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

    // === Report Logic ===
    const formattedReportContent = computed(() => {
       if (!reportContent.value) return ''
       return reportContent.value
         .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
         .replace(/\n\n/g, '<br><br>')
         .replace(/\n/g, '<br>')
    })
    
    const formattedLongTermContent = computed(() => {
       if (!longTermReportContent.value) return ''
       return longTermReportContent.value
         .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') 
         .replace(/\n\n/g, '<br><br>')
         .replace(/\n/g, '<br>')
    })

    let pollingInterval = null
    let longTermPollingInterval = null

    const checkStatus = async () => {
        try {
            const res = await diaryAPI.getReportStatus()
            if (res.status === 'processing') {
                isGeneratingReport.value = true
                if (!pollingInterval) pollingInterval = setInterval(checkStatus, 3000)
            } else if (res.status === 'completed') {
                isGeneratingReport.value = false
                reportContent.value = res.report
                if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
            } else if (res.status === 'failed') {
                isGeneratingReport.value = false
                reportContent.value = "리포트 생성에 실패했습니다. (AI 오류)"
                if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
            } else {
                isGeneratingReport.value = false
                if (pollingInterval) { clearInterval(pollingInterval); pollingInterval = null; }
            }
        } catch (e) {
            console.error("Polling error:", e)
        }
    }

    const checkLongTermStatus = async () => {
        try {
            const res = await diaryAPI.getLongTermReportStatus()
            if (res.status === 'processing') {
                isGeneratingLongTerm.value = true
                if (!longTermPollingInterval) longTermPollingInterval = setInterval(checkLongTermStatus, 3000)
            } else if (res.status === 'completed') {
                isGeneratingLongTerm.value = false
                longTermReportContent.value = res.insight
                if (longTermPollingInterval) { clearInterval(longTermPollingInterval); longTermPollingInterval = null; }
            } else if (res.status === 'failed') {
                isGeneratingLongTerm.value = false
                longTermReportContent.value = "분석에 실패했습니다."
                if (longTermPollingInterval) { clearInterval(longTermPollingInterval); longTermPollingInterval = null; }
            } else {
                // none or unexpected
                isGeneratingLongTerm.value = false
                if (longTermPollingInterval) { clearInterval(longTermPollingInterval); longTermPollingInterval = null; }
            }
        } catch (e) {
            console.error("LongTerm Polling error:", e)
        }
    }

    const handleGenerateReport = async () => {
       isGeneratingReport.value = true
       reportContent.value = ''
       longTermReportContent.value = '' // Clear previous meta analysis
       
       try {
          await diaryAPI.startReportGeneration()
          if (pollingInterval) clearInterval(pollingInterval)
          pollingInterval = setInterval(checkStatus, 3000)
       } catch (e) {
          isGeneratingReport.value = false
          if (e.response && e.response.status === 400) {
              // 400 Bad Request: Not enough diaries
              const msg = e.response.data.message || "분석을 위해서는 최소 3일 이상의 기록이 필요해요."
              alert(msg)
              reportContent.value = "" // Clear loading text
          } else {
              reportContent.value = "요청 실패: " + (e.message || "알 수 없는 오류")
          }
       }
    }
    
    const handleGenerateLongTermReport = async () => {
        if (isGeneratingLongTerm.value) return
        
        isGeneratingLongTerm.value = true
        longTermReportContent.value = ''
        
        try {
            await diaryAPI.startLongTermReportGeneration()
            
            if (longTermPollingInterval) clearInterval(longTermPollingInterval)
            longTermPollingInterval = setInterval(checkLongTermStatus, 3000)
            
        } catch (e) {
            isGeneratingLongTerm.value = false
            alert(e.response?.data?.message || "분석 요청 실패: " + e.message)
        }
    }

    onMounted(async () => {
        try {
            // Load Charts
            const res = await diaryAPI.getStatistics()
            rawStats.value = { ...res, daily: res.daily || [], timeline: res.timeline || [] }
            
            // Resume Polling if needed
            checkStatus() 
            checkLongTermStatus()
            
        } catch (e) {
            console.error(e)
        } finally {
            loading.value = false
        }
    })

    // Cleanup on unmount
    onUnmounted(() => {
        if (pollingInterval) clearInterval(pollingInterval)
        if (longTermPollingInterval) clearInterval(longTermPollingInterval)
    })

    return {
        loading,
        currentTab,
        tabs,
        monthlyCharts, flowChartData, flowChartOptions,
        moodChartData, doughnutOptions, moodLegendData,
        weatherChartData, weatherBarOptions,
        
        // Report Exports
        isGeneratingReport,
        reportContent,
        formattedReportContent,
        handleGenerateReport,
        
        // Long Term
        isGeneratingLongTerm,
        longTermReportContent,
        formattedLongTermContent,
        handleGenerateLongTermReport
    }
  }
}
</script>

<style scoped>
/* Previous Styles (omitted) */
.long-term-box {
    background: #f0fdf4; /* Light Green Tint */
    border: 1px solid #bbf7d0;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.long-term-box h4 {
    margin: 0 0 16px 0;
    color: #166534;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.report-actions {
    display: flex;
    gap: 10px;
}
.meta-btn {
    background: #10b981;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.meta-btn:hover:not(:disabled) {
    background: #059669;
    transform: scale(1.02);
}
.meta-btn:disabled {
    opacity: 0.7;
    cursor: wait;
}
/* ... Rest of styles */
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
  .stats-page {
      padding: 16px; 
      padding-bottom: 90px; /* Space for bottom nav */
      height: 100%;
      overflow-y: auto; /* Scroll page, not just content */
  }
  
  .stats-container { height: auto; display: block; }
  
  .stats-header { 
      flex-direction: column; 
      gap: 12px; 
      align-items: flex-start;
  }
  
  .close-btn { 
      position: absolute;
      top: 16px;
      right: 16px;
  }
  
  /* Horizontal Scrollable Tabs */
  .stats-nav {
      overflow-x: auto;
      white-space: nowrap;
      padding: 10px 4px; /* More clickable area */
      margin-bottom: 16px;
      -webkit-overflow-scrolling: touch;
  }
  
  .stats-nav::-webkit-scrollbar { display: none; }
  
  .nav-item {
      flex: 0 0 auto; /* Don't shrink */
      padding: 10px 16px;
  }

  .mood-layout .mood-content { flex-direction: column; }
  
  .stats-content { 
      padding: 20px; 
      height: auto; 
      border-radius: 20px;
      box-shadow: none; /* Simplier look on mobile */
      border: 1px solid #f0f0f0;
  }
  
  .content-body { padding: 0; overflow: visible; }
  
  .report-meta {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
  }
  
  .report-actions {
      width: 100%;
      flex-direction: column;
  }
  
  .meta-btn, .regenerate-btn {
      width: 100%;
      justify-content: center;
  }
}

/* === Report Section Styles === */
.report-section {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.report-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fbfbfd;
    border-radius: 20px;
    padding: 30px;
    border: 1px solid #f2f2f7;
    min-height: 400px;
}

/* Initial State */
.report-initial {
    text-align: center;
    max-width: 400px;
}
.report-icon-large {
    font-size: 60px;
    margin-bottom: 20px;
}
.report-initial p {
    color: #666;
    line-height: 1.6;
    margin-bottom: 30px;
}
.generate-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 14px 32px;
    border-radius: 30px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}
.generate-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(118, 75, 162, 0.4);
}
.notice {
    margin-top: 16px !important;
    font-size: 13px !important;
    color: #999 !important;
}

/* Loading State */
.report-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.spinner-large {
    width: 50px;
    height: 50px;
    border: 5px solid #e0e0e0;
    border-top: 5px solid #764ba2;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 24px;
}
.loading-text {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
}
.loading-sub {
    color: #888;
    font-size: 14px;
}

/* Result State */
.report-result {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.report-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #eee;
}
.report-date {
    font-size: 14px;
    color: #888;
    background: #eee;
    padding: 4px 12px;
    border-radius: 12px;
}
.regenerate-btn {
    background: none;
    border: 1px solid #ddd;
    padding: 6px 12px;
    border-radius: 15px;
    font-size: 13px;
    cursor: pointer;
    color: #666;
    transition: all 0.2s;
}
.regenerate-btn:hover {
    background: #f5f5f5;
    color: #333;
}
.report-content-box {
    flex: 1;
    overflow-y: auto;
    padding: 0 10px;
    font-size: 16px;
    line-height: 1.8;
    color: #333;
    white-space: pre-wrap; /* Preserve formatting */
}
.report-content-box::-webkit-scrollbar {
  width: 6px;
}
.report-content-box::-webkit-scrollbar-thumb {
  background-color: #ddd;
  border-radius: 3px;
}
</style>
