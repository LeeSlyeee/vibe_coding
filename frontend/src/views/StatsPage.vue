<template>
  <div class="stats-page">
    <div class="stats-container">
      <!-- iOS Style Header -->
      <header class="stats-header ios-header">
        <div class="header-left">
          <h2>마음 분석</h2>
          <p class="subtitle">데이터로 보는 나의 하루</p>
        </div>
        <button @click="$router.push('/calendar')" class="close-btn">
          <span class="icon">✖</span>
        </button>
      </header>

      <!-- iOS Style Scrollable Tabs -->
      <nav class="stats-nav ios-tabs">
        <div class="scroll-wrapper">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="['nav-item', { active: currentTab === tab.id }]"
            @click="currentTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>
      </nav>

      <div class="stats-content-area">
        <!-- Authenticated Content -->
        <div class="content-body-wrapper">
          <!-- Loading State -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
          </div>

          <div v-else class="content-body">
            <transition name="fade" mode="out-in">
              <!-- 1. Flow Chart (Card Style) -->
              <div v-if="currentTab === 'flow'" key="flow" class="chart-card">
                <div class="card-header">
                  <span class="card-icon">📈</span>
                  <h3>감정 흐름</h3>
                </div>
                <div class="chart-wrapper main-chart">
                  <div :style="{ width: flowChartWidth, minWidth: '100%', height: '300px' }">
                    <Line :data="flowChartData" :options="flowChartOptions" />
                  </div>
                </div>
              </div>

              <!-- 2. Monthly Chart -->
              <div v-else-if="currentTab === 'monthly'" key="monthly" class="chart-list">
                <div v-for="chart in monthlyCharts" :key="chart.month" class="chart-card">
                  <div class="card-header">
                    <span class="card-icon">📅</span>
                    <h3>{{ chart.month }}</h3>
                  </div>
                  <div class="chart-wrapper sub-chart">
                    <Bar :data="chart.data" :options="chart.options" />
                  </div>
                </div>
                <div v-if="monthlyCharts.length === 0" class="no-data-card">
                  <p>데이터가 없습니다.</p>
                </div>
              </div>

              <!-- 3. Mood Distribution -->
              <div v-else-if="currentTab === 'mood'" key="mood" class="chart-card">
                <div class="card-header">
                  <span class="card-icon">🎨</span>
                  <h3>감정 비중</h3>
                </div>
                <div class="mood-layout-ios">
                  <div class="donut-wrapper">
                    <Doughnut :data="moodChartData" :options="doughnutOptions" />
                    <div class="donut-center-text">
                      <span class="total-num">{{ totalMoodCount }}</span>
                      <span class="total-label">TOTAL</span>
                    </div>
                  </div>
                  <div class="mood-legend-ios">
                    <div v-for="item in moodLegendData" :key="item.label" class="legend-row">
                      <div class="row-left">
                        <span class="dot" :style="{ background: item.color }"></span>
                        <span class="l-label">{{ item.label }}</span>
                      </div>
                      <span class="l-val">{{ item.count }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 4. Weather -->
              <div v-else-if="currentTab === 'weather'" key="weather" class="chart-card">
                <div class="card-header">
                  <span class="card-icon">🌤️</span>
                  <h3>날씨와 기분</h3>
                </div>
                <div class="chart-wrapper main-chart">
                  <Bar :data="weatherChartData" :options="weatherBarOptions" />
                </div>
              </div>

              <!-- 5. AI Report -->
              <div v-else-if="currentTab === 'report'" key="report" class="chart-card report-card">
                <div class="card-header">
                  <span class="card-icon" style="color: purple">✨</span>
                  <h3>AI 심층 리포트</h3>
                </div>

                <div class="report-content-ios">
                  <div v-if="!formattedReportContent && !isGeneratingReport" class="start-box">
                    <button @click="handleGenerateReport" class="ios-btn-gradient">
                      ✨ 지금 바로 분석 시작하기
                    </button>
                  </div>
                  <div v-else-if="isGeneratingReport" class="loading-box">
                    <div class="spinner"></div>
                    <transition name="fade" mode="out-in">
                      <p
                        :key="loadingStepText"
                        style="margin-top: 15px; font-weight: 500; min-height: 24px; color: #666"
                      >
                        {{ loadingStepText }}
                      </p>
                    </transition>
                  </div>
                  <div v-else class="result-box-wrapper">
                    <div class="result-box">
                      <h4>💬 3줄 요약</h4>
                      <div class="r-text" v-html="formattedReportContent"></div>
                      <button @click="handleGenerateReport" class="ios-btn-outline-blue">
                        🔄 다시 분석
                      </button>
                    </div>

                    <div class="long-term-section">
                      <div v-if="!formattedLongTermContent && !isGeneratingLongTerm">
                        <button @click="handleGenerateLongTermReport" class="ios-btn-green">
                          🧠 장기 기억 패턴 분석하기
                        </button>
                      </div>
                      <div v-else-if="isGeneratingLongTerm" class="loading-box-small">
                        <div class="spinner-small"></div>
                        <transition name="fade" mode="out-in">
                          <span
                            :key="longTermStepText"
                            style="display: inline-block; min-width: 150px"
                          >
                            {{ longTermStepText }}
                          </span>
                        </transition>
                      </div>
                      <div v-else class="result-box green-box">
                        <h4>🧠 메타 분석</h4>
                        <div class="r-text" v-html="formattedLongTermContent"></div>
                        <button @click="handleRetryLongTermReport" class="ios-btn-outline-green">
                          🔄 메타 분석 다시하기
                        </button>
                      </div>
                    </div>

                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </div>

    
    <!-- Custom Modal for Alerts -->
    <transition name="fade">
      <div v-if="showModal" class="modal-overlay" @click="showModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-icon">ℹ️</div>
          <h3>안내</h3>
          <p>{{ modalMessage }}</p>
          <button @click="showModal = false" class="modal-btn">확인</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, onMounted, onActivated, computed, reactive, onUnmounted, onErrorCaptured } from "vue";
import api, { diaryAPI } from "../services/api";
import { medicationAPI } from "../services/medication";
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
  LineElement,
  Filler,
} from "chart.js";
import { Bar, Doughnut, Line } from "vue-chartjs";
import { useRouter } from "vue-router";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
);

export default {
  name: "StatsPage",
  components: { Bar, Doughnut, Line },
  setup() {
    const router = useRouter();
    const loading = ref(false);
    const isLinked = ref(true); // Always open for Web
    const currentTab = ref("flow");

    const rawStats = ref({ monthly: [], moods: [], weather: [], daily: [], timeline: [] });
    const medLogs = ref([]);
    const errorMsg = ref(null);

    onErrorCaptured((err) => {
      console.error("StatsPage Capture:", err);
      return false;
    });

    function generateMockData() {
      // Mock data logic from copy file
      const days = [];
      const today = new Date();
      for (let i = 6; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        days.push({
          date: d.toISOString().split("T")[0],
          mood_level: Math.floor(Math.random() * 3) + 3,
          medication: i % 2 === 0,
        });
      }
      return {
        timeline: days,
        moods: [
          { _id: 5, count: 12 },
          { _id: 4, count: 5 },
          { _id: 3, count: 2 },
          { _id: 2, count: 4 },
          { _id: 1, count: 1 },
        ],
        weather: [],
        daily: [],
        medication_rate: 80,
      };
    }

    async function loadData() {
      loading.value = true;
      try {
        const [statsRes, medsRes] = await Promise.all([
          diaryAPI.getStatistics().catch(() => null),
          medicationAPI.getMedicationLogs().catch(() => []),
        ]);

        if (statsRes && statsRes.timeline && statsRes.timeline.length > 0) {
          rawStats.value = {
            ...statsRes,
            daily: statsRes.daily || [],
            timeline: statsRes.timeline || [],
          };
        } else {
          console.warn("Using Mock Data");
          rawStats.value = generateMockData();
        }

        medLogs.value = medsRes || [];
      } catch (e) {
        console.warn("Using Mock Data (Fallback)");
        rawStats.value = generateMockData();
      } finally {
        loading.value = false;
        // Check for existing reports immediately after loading data
        checkStatus();
        checkLongTermStatus();
      }
    }

    onMounted(() => {
      loadData();
    });

    // Report State
    const isGeneratingReport = ref(false);
    const reportContent = ref("");
    const isGeneratingLongTerm = ref(false);
    const longTermReportContent = ref("");

    // Loading Animation
    const loadingStepText = ref("AI가 일기장을 읽고 있어요...");
    const longTermStepText = ref("기억을 더듬는 중..."); // [NEW]
    const stepInterval = ref(null);
    const pollingInterval = ref(null);
    const longTermPollingInterval = ref(null);
    const longTermStepInterval = ref(null); // [NEW]

    const loadingSteps = [
        "📖 일기장을 꼼꼼히 읽고 있어요...",
        "💡 감정을 글로 적는 것만으로도 뇌가 편안해집니다.",
        "🔍 숨겨진 감정 패턴을 찾고 있어요...",
        "🧠 뇌과학적으로 '멍 때리기'는 창의력의 원천이에요.",
        "✨ 깊이 있는 통찰을 위해 시간이 조금 걸립니다...",
        "🍵 따뜻한 차 한 잔의 여유를 가져보세요.",
        "💭 오늘의 기분을 깊이 이해하고 있습니다...",
        "💡 스트레스는 깊은 호흡만으로도 감소해요.",
        "✨ 멋진 리포트를 작성하고 있습니다..."
    ]

    const tabs = [
        { id: "flow", label: "흐름" },
        { id: "monthly", label: "월별" },
        { id: "mood", label: "분포" },
        { id: "weather", label: "날씨" },
        { id: "report", label: "AI분석" },
    ];

    const totalMoodCount = computed(() => {
      if (!rawStats.value.moods) return 0;
      return rawStats.value.moods.reduce((acc, cur) => acc + cur.count, 0);
    });

    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(255,255,255, 0.9)",
          titleColor: "#000",
          bodyColor: "#666",
          borderColor: "rgba(0,0,0,0.1)",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 12,
          displayColors: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#f5f5f7", borderDash: [5, 5] },
          ticks: { display: false },
        },
        x: { grid: { display: false }, ticks: { font: { size: 10 }, color: "#86868b" } },
      },
      animation: { duration: 800, easing: "easeOutQuart" },
    };

    const flowChartOptions = {
      ...commonOptions,
      interaction: { intersect: false, mode: "index" },
      scales: {
        y: {
          min: 0,
          max: 6,
          grid: { color: "#f2f2f7" },
          ticks: {
            stepSize: 1,
            callback: (v) => (v === 0 ? "" : { 1: "🤬", 2: "😢", 3: "😐", 4: "😌", 5: "🥰" }[v]),
            font: { size: 16 },
          },
        },
        x: { grid: { display: false }, ticks: { display: true, maxTicksLimit: 6 } },
      },
    };

    const weatherBarOptions = {
      ...commonOptions,
      scales: {
        y: { beginAtZero: true, display: false, stacked: true },
        x: { grid: { display: false }, stacked: true },
      },
      plugins: {
        legend: { display: true, position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } },
      },
    };

    const doughnutOptions = {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "75%",
      plugins: { legend: { display: false } },
    };

    const flowChartData = computed(() => {
      const timeline = rawStats.value.timeline || [];
      return {
        labels: timeline.map((t) => t.date.slice(5)),
        datasets: [
          {
            label: "기분",
            data: timeline.map((t) => t.mood_level),
            borderColor: "#0071E3",
            backgroundColor: "rgba(0, 113, 227, 0.1)",
            tension: 0.4,
            pointBackgroundColor: "#0071E3",
            pointBorderColor: "#fff",
            pointBorderWidth: 0,
            pointRadius: 0,
            pointHoverRadius: 6,
            fill: true,
          },
        ],
      };
    });

    const flowChartWidth = computed(() => "1200px");

    const moodMap = {
      1: { label: "화남", color: "#FF3B30" }, // Red (Anger)
      2: { label: "우울", color: "#5E5CE6" }, // Purple (Melancholy)
      3: { label: "보통", color: "#64D2FF" }, // Mint Blue (Neutral/Calm) - [CHANGED]
      4: { label: "편안", color: "#34C759" }, // Green (Relaxed/Nature) - [CHANGED]
      5: { label: "행복", color: "#FFCC00" }, // Yellow (Happy/Sun)
    };

    const monthlyCharts = computed(() => {
      if (!rawStats.value.daily) return [];
      // Simple Monthly Grouping Logic
      const grouped = {};
      rawStats.value.daily.forEach((item) => {
        const m = item._id.substring(0, 7);
        if (!grouped[m]) grouped[m] = {};
        grouped[m][item._id] = item.count;
      });
      return Object.keys(grouped)
        .sort()
        .reverse()
        .map((mStr) => {
          const [y, m] = mStr.split("-");
          const labels = Object.keys(grouped[mStr])
            .sort()
            .map((d) => d.slice(8));
          const data = Object.values(grouped[mStr]);
          
          // [FIX] Apply color based on mood level
          const backgroundColors = data.map(val => {
              const level = Math.round(val);
              return moodMap[level] ? moodMap[level].color : "#0071E3";
          });

          return {
            month: `${y}년 ${m}월`,
            data: {
              labels,
              datasets: [{ 
                  label: "기분", 
                  data, 
                  backgroundColor: backgroundColors, // Dynamic Colors
                  borderRadius: 4 
              }],
            },
            options: {
              ...commonOptions,
              scales: {
                y: { display: false, min: 0, max: 6 },
                x: { display: true, grid: { display: false } },
              },
              plugins: {
                ...commonOptions.plugins, // Inherit base plugins
                tooltip: {
                    ...commonOptions.plugins.tooltip, // Inherit base tooltip styles
                    callbacks: {
                        label: function(context) {
                            const val = Math.round(context.raw);
                            const moodLabel = moodMap[val] ? moodMap[val].label : val;
                            return `기분: ${moodLabel}`;
                            // 원한다면 `기분: ${moodLabel} (${val})` 형식도 가능하지만 깔끔하게 한글만.
                        }
                    }
                }
              }
            },
          };
        });
    });

    const moodChartData = computed(() => {
      const d = {};
      (rawStats.value.moods || []).forEach((m) => (d[m._id] = m.count));
      const labels = [],
        data = [],
        bg = [];
      [5, 4, 3, 2, 1].forEach((id) => {
        if (d[id]) {
          labels.push(moodMap[id].label);
          data.push(d[id]);
          bg.push(moodMap[id].color);
        }
      });
      if (data.length === 0)
        return { labels: ["Empty"], datasets: [{ data: [1], backgroundColor: ["#f2f2f7"] }] };
      return { labels, datasets: [{ backgroundColor: bg, borderWidth: 0, data }] };
    });

    const moodLegendData = computed(() => {
      const total = (rawStats.value.moods || []).reduce((a, b) => a + b.count, 0) || 1;
      return [5, 4, 3, 2, 1]
        .map((id) => {
          const count = ((rawStats.value.moods || []).find((m) => m._id === id) || { count: 0 })
            .count;
          return { label: moodMap[id].label, color: moodMap[id].color, count };
        })
        .filter((i) => i.count > 0);
    });

    const weatherChartData = computed(() => {
      const wData = rawStats.value.weather || [];
      return {
        labels: wData.map((w) => w._id),
        datasets: [5, 4, 3, 2, 1].map((id) => ({
          label: moodMap[id].label,
          data: wData.map((w) => {
            const f = w.moods ? w.moods.find((m) => m.mood === id) : null;
            return f ? f.count : 0;
          }),
          backgroundColor: moodMap[id].color,
          borderRadius: 4,
        })),
      };
    });

    // Report Polling Logic (Refactored for Stability)
    const checkStatus = async () => {
      // [Fix] 프리미엄 권한 체크 로직 추가
      // 만약 권한이 없다면 초기에 차단하지만, 이미 들어와서 폴링 중이라면 서버 응답을 신뢰
      // 여기서는 결과만 확인
      try {
        const res = await diaryAPI.getReportStatus();
        if (res.status === "completed") {
          isGeneratingReport.value = false;
          reportContent.value = res.report;
          // Clear intervals
          if (pollingInterval.value) clearInterval(pollingInterval.value);
          if (stepInterval.value) clearInterval(stepInterval.value);
        } else if (res.status === "failed") {
          isGeneratingReport.value = false;
          reportContent.value = "분석에 실패했습니다. 다시 시도해주세요.";
          if (pollingInterval.value) clearInterval(pollingInterval.value);
          if (stepInterval.value) clearInterval(stepInterval.value);
        }
      } catch (e) {
        console.error(e);
      }
    };

    const handleGenerateReport = async () => {
      // [Fix] 권한 체크: 연동 사용자(isLinked) OR 프리미엄 여부
      // 로컬 스토리지에서 b2g_is_linked 확인
      const b2gLinked = localStorage.getItem('b2g_is_linked') === 'true';
      // 진단 패스된 유저는 사실상 프리미엄/연동 유저임 (간접 확인)
      const isAssessed = localStorage.getItem('assessment_completed') === 'true';

      if (!b2gLinked && !isAssessed) {
           alert("유료 사용자 또는 기관 연동 사용자 전용 기능입니다.");
           return;
      }

      if (isGeneratingReport.value) return; // Prevent double click

      isGeneratingReport.value = true;
      reportContent.value = "";

      // Start Step Animation
      let stepIdx = 0;
      loadingStepText.value = loadingSteps[0];

      if (stepInterval.value) clearInterval(stepInterval.value);
      stepInterval.value = setInterval(() => {
        stepIdx = (stepIdx + 1) % loadingSteps.length;
        loadingStepText.value = loadingSteps[stepIdx];
      }, 4000);

      try {
        await diaryAPI.startReportGeneration();

        if (pollingInterval.value) clearInterval(pollingInterval.value);
        pollingInterval.value = setInterval(checkStatus, 3000);
      } catch (e) {
        isGeneratingReport.value = false;
        // 403 Forbidden 등 백엔드 에러 처리
        if (e.response && e.response.status === 403) {
            alert("🔒 접근 제한\n\n보건소 및 병원 사용자\n또는 유료사용자 전용 기능입니다.");
        } else {
            alert("오류: " + e.message);
        }
        if (stepInterval.value) clearInterval(stepInterval.value);
      }
    };

    const checkLongTermStatus = async () => {
      try {
        const res = await diaryAPI.getLongTermReportStatus();
        if (res.status === "completed") {
          isGeneratingLongTerm.value = false;
          longTermReportContent.value = res.insight;
          if (longTermPollingInterval.value) clearInterval(longTermPollingInterval.value);
          if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);
        }
      } catch (e) {}
    };
    // [Modal State]
    const showModal = ref(false);
    const modalMessage = ref("");

    const handleGenerateLongTermReport = async () => {
      if (isGeneratingLongTerm.value) return;

      isGeneratingLongTerm.value = true;
      longTermReportContent.value = "";

      // Start Step Animation
      let stepIdx = 0;
      longTermStepText.value = loadingSteps[0];
      if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);

      longTermStepInterval.value = setInterval(() => {
        stepIdx = (stepIdx + 1) % loadingSteps.length;
        longTermStepText.value = loadingSteps[stepIdx];
      }, 4000);

      try {
        await diaryAPI.startLongTermReportGeneration();

        if (longTermPollingInterval.value) clearInterval(longTermPollingInterval.value);
        longTermPollingInterval.value = setInterval(checkLongTermStatus, 3000);
      } catch (e) {
        isGeneratingLongTerm.value = false;
        if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);
        
        // [UX] Show Modal for Error (e.g. Not Enough Reports)
        if (e.response && e.response.status === 400 && e.response.data && e.response.data.message) {
             modalMessage.value = e.response.data.message;
             showModal.value = true;
        } else {
             modalMessage.value = "분석을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.";
             showModal.value = true;
        }
      }
    };

    const handleRetryLongTermReport = async () => {
        isGeneratingLongTerm.value = true;
        longTermReportContent.value = "";
        
        // Start Step Animation
        let stepIdx = 0;
        longTermStepText.value = loadingSteps[0];
        if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);

        longTermStepInterval.value = setInterval(() => {
            stepIdx = (stepIdx + 1) % loadingSteps.length;
            longTermStepText.value = loadingSteps[stepIdx];
        }, 4000);

        try {
            await diaryAPI.startLongTermReportGeneration();
            if (longTermPollingInterval.value) clearInterval(longTermPollingInterval.value);
            longTermPollingInterval.value = setInterval(checkLongTermStatus, 3000);
        } catch (e) {
            isGeneratingLongTerm.value = false;
            if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);
            alert("오류: " + e.message);
        }
    };

    const formattedReportContent = computed(() => reportContent.value.replace(/\n/g, "<br>"));
    const formattedLongTermContent = computed(() =>
      longTermReportContent.value.replace(/\n/g, "<br>"),
    );

    onUnmounted(() => {
      if (pollingInterval.value) clearInterval(pollingInterval.value);
      if (longTermPollingInterval.value) clearInterval(longTermPollingInterval.value);
      if (stepInterval.value) clearInterval(stepInterval.value);
      if (longTermStepInterval.value) clearInterval(longTermStepInterval.value);
    });

    return {
      loading,
      isLinked,
      currentTab,
      tabs,
      monthlyCharts,
      flowChartData,
      flowChartOptions,
      flowChartWidth,
      moodChartData,
      doughnutOptions,
      moodLegendData,
      weatherChartData,
      weatherBarOptions,
      isGeneratingReport,
      formattedReportContent,
      handleGenerateReport,
      isGeneratingLongTerm,
      formattedLongTermContent,
      handleGenerateLongTermReport,
      handleRetryLongTermReport,
      totalMoodCount,
      loadingStepText,
      longTermStepText,
      showModal,
      modalMessage
    };
  },
};
</script>

<style scoped>
/* Native Scroll Layout for reliability */
.stats-page {
  min-height: 100vh;
  background-color: #fbfbfd;
  display: flex;
  flex-direction: column;
  /* overflow:hidden removed to allow native window scrolling */
  font-family: -apple-system, sans-serif;
}

.stats-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  position: relative;
}

.ios-header {
  padding: 20px 24px 10px;
  background: rgba(251, 251, 253, 0.92); /* Translucent */
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left h2 {
  font-size: 28px;
  font-weight: 800;
  color: #1d1d1f;
  margin: 0;
  letter-spacing: -0.5px;
}
.subtitle {
  font-size: 15px;
  color: #86868b;
  margin-top: 4px;
  font-weight: 500;
}
.close-btn {
  background: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #86868b;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
}

.ios-tabs {
  padding: 10px 24px 20px;
  background: rgba(251, 251, 253, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: sticky;
  top: 94px; /* Adjusted based on header height */
  z-index: 90;
  transition: top 0.2s;
}

.scroll-wrapper {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 5px;
  scrollbar-width: none;
}
.nav-item {
  background: white;
  border: none;
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 15px;
  font-weight: 600;
  color: #86868b;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  cursor: pointer;
  transition: all 0.3s;
}
.nav-item.active {
  background: #0071e3;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
  transform: scale(1.02);
}

.stats-content-area {
  flex: 1;
  /* Removed overflow-y: auto to create single document scroll */
  padding: 0 24px 120px;
}

.chart-card {
  background: white;
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.card-header h3 {
  font-size: 19px;
  font-weight: 700;
  color: #1d1d1f;
  margin: 0;
}
.card-icon {
  font-size: 20px;
}
.main-chart {
  height: 350px;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
}
.sub-chart {
  height: 200px;
}
.chart-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.mood-layout-ios {
  display: flex;
  align-items: center;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 20px;
}
.donut-wrapper {
  position: relative;
  width: 160px;
  height: 160px;
}
.donut-center-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
.total-num {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #1d1d1f;
  line-height: 1;
}
.total-label {
  font-size: 11px;
  color: #86868b;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.mood-legend-ios {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 140px;
}
.legend-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}
.row-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.l-label {
  font-weight: 500;
  color: #1d1d1f;
}
.l-val {
  font-weight: 700;
  color: #86868b;
}

.report-card {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  height: auto;
}
.report-content-ios {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.start-box {
  text-align: center;
  padding: 20px 0;
}
.ios-btn-gradient {
  background: linear-gradient(135deg, #5e5ce6 0%, #0071e3 100%);
  padding: 16px 32px;
  color: white;
  font-weight: 700;
  border-radius: 20px;
  border: none;
  font-size: 16px;
  box-shadow: 0 8px 20px rgba(94, 92, 230, 0.3);
  cursor: pointer;
  transition: transform 0.2s;
}
.ios-btn-gradient:active {
  transform: scale(0.96);
}

.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #86868b;
  min-height: 200px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5ea;
  border-top-color: #0071e3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}
@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}
.result-box {
  background: #fbfbfd;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #f2f2f7;
}
.result-box h4 {
  margin: 0 0 12px;
  color: #1d1d1f;
  font-size: 16px;
}
.r-text {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
}
.long-term-section {
  margin-top: 10px;
}
.ios-btn-green {
  width: 100%;
  padding: 14px;
  background: #34c759;
  color: white;
  font-weight: 600;
  border-radius: 16px;
  border: none;
  font-size: 15px;
  cursor: pointer;
}
.green-box {
  background: #f2fcf5;
  border-color: #dbfbe6;
}
.loading-box-small {
  text-align: center;
  padding: 20px;
  color: #34c759;
  font-weight: 600;
  background: #f2fcf5;
  border-radius: 16px;
  border: 1px dashed #34c759;
}
.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid #dbfbe6;
  border-top-color: #34c759;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}
.retry-text-btn {
  background: none;
  border: none;
  color: #86868b;
  font-size: 13px;
  margin-top: 10px;
  cursor: pointer;
  text-decoration: underline;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.result-box-wrapper {
  width: 100%;
}

@media (max-width: 480px) {
  .ios-tabs,
  .stats-content-area,
  .stats-header {
    padding-left: 16px;
    padding-right: 16px;
  }
}

.ios-btn-outline-blue {
  width: 100%;
  padding: 14px;
  margin-top: 16px;
  background: white;
  border: 1px solid #0071e3;
  color: #0071e3;
  font-weight: 600;
  border-radius: 16px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}
.ios-btn-outline-blue:active {
  background: #f0f8ff;
  transform: scale(0.98);
}

.ios-btn-outline-green {
  width: 100%;
  padding: 14px;
  margin-top: 16px;
  background: white;
  border: 1px solid #34c759;
  color: #34c759;
  font-weight: 600;
  border-radius: 16px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}
.ios-btn-outline-green:active {
  background: #f2fcf5;
  transform: scale(0.98);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: white;
  padding: 24px;
  border-radius: 20px;
  width: 80%;
  max-width: 320px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.modal-icon {
  font-size: 40px;
  margin-bottom: 15px;
}
.modal-content h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 700;
  color: #1d1d1f;
}
.modal-content p {
  margin: 0 0 24px 0;
  font-size: 15px;
  color: #666;
  line-height: 1.5;
}
.modal-btn {
  background: #0071e3;
  color: white;
  border: none;
  padding: 12px 0;
  width: 100%;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.modal-btn:active {
  background: #0077ed;
  transform: scale(0.98);
}
@keyframes popIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
</style>
