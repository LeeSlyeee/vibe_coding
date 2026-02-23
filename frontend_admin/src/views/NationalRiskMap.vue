<template>
  <div class="risk-map-page">
    <div class="page-header fade-in">
      <h1 class="page-title">🗺️ 전국 위험도 지도</h1>
      <p class="page-subtitle">시·도별 환자 현황 시각화</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else>
      <div class="map-layout">
        <!-- Map Container -->
        <div class="map-container glass-card fade-in">
          <svg :viewBox="VIEW_BOX" preserveAspectRatio="xMidYMid meet" class="korea-map">
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <linearGradient id="oceanGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="rgba(30,58,95,0.15)"/>
                <stop offset="100%" stop-color="rgba(30,58,95,0.05)"/>
              </linearGradient>
            </defs>

            <!-- Ocean hint -->
            <rect x="-100" y="-100" width="800" height="900" fill="url(#oceanGrad)" rx="12"/>

            <!-- Sea labels -->
            <text x="50" y="250" fill="rgba(255,255,255,0.08)" font-size="28" font-weight="900" transform="rotate(-15,50,250)">서 해</text>
            <text x="450" y="200" fill="rgba(255,255,255,0.08)" font-size="28" font-weight="900" transform="rotate(15,450,200)">동 해</text>

            <!-- Render order: large regions first, small cities on top -->
            <g v-for="r in sortedRegions" :key="r.code"
               @click="selectRegion(r)"
               @mouseenter="hovered = r.code"
               @mouseleave="hovered = null"
               style="cursor:pointer;"
               class="map-region-group">
              <path :d="r.path"
                    :fill="getRegionColor(r)"
                    :stroke="hovered === r.code || selected?.code === r.code ? '#fff' : 'rgba(255,255,255,0.2)'"
                    :stroke-width="hovered === r.code || selected?.code === r.code ? 2.5 : 1.2"
                    :stroke-linejoin="'round'"
                    :filter="selected?.code === r.code ? 'url(#glow)' : 'none'"
                    :opacity="selected && selected.code !== r.code ? 0.65 : 1"
                    style="transition:all 0.3s ease;" />
              <text :x="r.labelX" :y="r.labelY" text-anchor="middle" dominant-baseline="central"
                    fill="white" :font-size="r.fontSize || 12" font-weight="600"
                    style="pointer-events:none;text-shadow:0 1px 3px rgba(0,0,0,0.8);">
                {{ r.name }}
              </text>
              <!-- Patient count badge -->
              <g v-if="r.patient_count > 0 && !r.isSmallCity">
                <circle :cx="r.labelX + 16" :cy="r.labelY - 14" r="8"
                        :fill="r.high_risk_count > 2 ? '#f43f5e' : r.high_risk_count > 0 ? '#f59e0b' : '#10b981'"
                        stroke="rgba(0,0,0,0.3)" stroke-width="0.5"/>
                <text :x="r.labelX + 16" :y="r.labelY - 14" text-anchor="middle" dominant-baseline="central"
                      fill="white" font-size="7" font-weight="800" style="pointer-events:none;">
                  {{ r.patient_count }}
                </text>
              </g>
            </g>
          </svg>

          <!-- Legend -->
          <div class="map-legend">
            <div class="legend-item"><div class="legend-dot" style="background:#1e3a5f;"></div>미등록</div>
            <div class="legend-item"><div class="legend-dot" style="background:#10b981;"></div>정상</div>
            <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;"></div>주의</div>
            <div class="legend-item"><div class="legend-dot" style="background:#f43f5e;"></div>위험</div>
          </div>
        </div>

        <!-- Side Panel -->
        <div class="side-panel">
          <div v-if="selected" class="glass-card fade-in info-card">
            <h3 class="info-title">📍 {{ selected.name }}</h3>
            <div class="stat-grid">
              <div class="mini-stat"><div class="mini-label">보건소</div><div class="mini-value emerald">{{ selected.center_count }}</div></div>
              <div class="mini-stat"><div class="mini-label">환자</div><div class="mini-value">{{ selected.patient_count }}</div></div>
              <div class="mini-stat"><div class="mini-label">고위험</div><div class="mini-value rose">{{ selected.high_risk_count }}</div></div>
              <div class="mini-stat"><div class="mini-label">일기</div><div class="mini-value">{{ selected.diary_count }}</div></div>
            </div>
            <button @click="$router.push(`/dashboard/region/${selected.id}`)" class="btn btn-primary detail-btn">
              상세 보기 →
            </button>
          </div>
          <div v-else class="glass-card placeholder-card">
            <div style="font-size:36px;margin-bottom:8px;">👆</div>
            <p>지도에서 시·도를 클릭하세요</p>
          </div>

          <div class="glass-card fade-in ranking-card">
            <h3 class="ranking-title">🏆 환자 수 Top 5</h3>
            <div v-for="(r, i) in topRegions" :key="r.code" class="rank-row" @click="selectRegion(r)">
              <span class="rank-num" :class="'rank-' + i">{{ i + 1 }}</span>
              <span class="rank-name">{{ r.name }}</span>
              <span class="rank-value">{{ r.patient_count }}명</span>
            </div>
            <div v-if="topRegions.length === 0" style="text-align:center;color:var(--text-muted);padding:16px;font-size:13px;">
              환자 데이터 없음
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { KOREA_REGIONS, VIEW_BOX } from '../data/koreaMapData'

const loading = ref(true)
const regions = ref([])
const selected = ref(null)
const hovered = ref(null)

const topRegions = computed(() =>
  [...regions.value].filter(r => r.patient_count > 0).sort((a, b) => b.patient_count - a.patient_count).slice(0, 5)
)

const mapRegions = computed(() => {
  return regions.value.map(r => ({
    ...r,
    ...(KOREA_REGIONS[r.code] || { path: '', labelX: 0, labelY: 0, isSmallCity: false })
  })).filter(r => r.path)
})

// 작은 도시를 마지막에 그려서 클릭 이벤트를 받게 함 (SVG z-index)
const sortedRegions = computed(() => {
  const large = mapRegions.value.filter(r => !r.isSmallCity)
  const small = mapRegions.value.filter(r => r.isSmallCity)
  return [...large, ...small]
})

function getRegionColor(r) {
  if (r.center_count === 0) return '#1e3a5f'
  if (r.high_risk_count > 2) return '#f43f5e'
  if (r.high_risk_count > 0) return '#f59e0b'
  return '#2ecc71'
}

function selectRegion(r) {
  selected.value = selected.value?.code === r.code ? null : r
}

onMounted(async () => {
  try {
    const res = await api.getNationalSummary()
    regions.value = res.data.regions
  } catch (e) {
    console.error('지도 데이터 로드 실패:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.risk-map-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
}

.map-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.map-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 16px;
  min-height: calc(100vh - 180px);
}

.korea-map {
  width: 100%;
  height: calc(100vh - 220px);
  filter: drop-shadow(0 0 15px rgba(0,0,0,0.5));
}

.map-region-group:hover path {
  fill-opacity: 0.9;
}

/* Legend */
.map-legend {
  position: absolute;
  bottom: 24px;
  left: 24px;
  display: flex;
  gap: 16px;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(10px);
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 13px;
  color: rgba(255,255,255,0.9);
  border: 1px solid rgba(255,255,255,0.1);
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 14px; height: 14px; border-radius: 4px; }

/* Side Panel */
.side-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  max-height: calc(100vh - 180px);
}

.info-card { padding: 24px; }
.info-title { font-size: 18px; font-weight: 800; margin-bottom: 16px; }

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.mini-stat {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  transition: all 0.2s;
}
.mini-stat:hover { background: rgba(255,255,255,0.06); transform: translateY(-2px); }
.mini-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; font-weight: 600; }
.mini-value { font-size: 24px; font-weight: 800; }
.mini-value.emerald { color: var(--accent-emerald); filter: drop-shadow(0 0 8px rgba(16,185,129,0.3)); }
.mini-value.rose { color: var(--accent-rose); filter: drop-shadow(0 0 8px rgba(244,63,94,0.3)); }

.detail-btn { width: 100%; justify-content: center; margin-top: 16px; padding: 12px; font-size: 15px; font-weight: 700; border-radius: 10px; }

.placeholder-card { text-align: center; padding: 60px 24px; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 250px; }

/* Ranking */
.ranking-card { padding: 20px; }
.ranking-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
.rank-row { display: flex; align-items: center; gap: 12px; padding: 12px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); cursor: pointer; border-radius: 8px; transition: background 0.2s; }
.rank-row:hover { background: rgba(255,255,255,0.06); }
.rank-row:last-child { border-bottom: none; }
.rank-num { font-size: 16px; font-weight: 900; width: 28px; text-align: center; color: var(--text-muted); text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.rank-0 { color: #fbbf24; }
.rank-1 { color: #9ca3af; }
.rank-2 { color: #b45309; }
.rank-name { flex: 1; font-size: 14px; font-weight: 600; }
.rank-value { font-size: 15px; font-weight: 800; }

@media (max-width: 1000px) {
  .map-layout { grid-template-columns: 1fr; }
  .korea-map { max-height: 500px; }
  .side-panel { max-height: none; }
}
</style>
