<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">🇰🇷 전국 현황 대시보드</h1>
      <p class="page-subtitle">마음온 전국 정신건강 관리 시스템 실시간 현황</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else-if="data">
      <!-- Summary Cards -->
      <div class="grid-6" style="margin-bottom:32px;">
        <div class="glass-card stat-card blue fade-in fade-in-delay-1">
          <div class="stat-label">시·도</div>
          <div class="stat-value">{{ data.summary.total_regions }}</div>
        </div>
        <div class="glass-card stat-card emerald fade-in fade-in-delay-1">
          <div class="stat-label">보건소</div>
          <div class="stat-value">{{ data.summary.total_centers }}</div>
        </div>
        <div class="glass-card stat-card purple fade-in fade-in-delay-2">
          <div class="stat-label">전체 환자</div>
          <div class="stat-value">{{ data.summary.total_patients.toLocaleString() }}</div>
        </div>
        <div class="glass-card stat-card cyan fade-in fade-in-delay-2">
          <div class="stat-label">상담사</div>
          <div class="stat-value">{{ data.summary.total_staff }}</div>
        </div>
        <div class="glass-card stat-card rose fade-in fade-in-delay-3">
          <div class="stat-label">고위험군</div>
          <div class="stat-value" style="color:var(--accent-rose);">{{ data.summary.total_high_risk }}</div>
        </div>
        <div class="glass-card stat-card amber fade-in fade-in-delay-3">
          <div class="stat-label">일기 총수</div>
          <div class="stat-value">{{ data.summary.total_diaries.toLocaleString() }}</div>
        </div>
      </div>

      <!-- Region Cards Grid -->
      <div style="margin-bottom:24px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:16px;">📊 시·도별 현황</h2>
      </div>

      <!-- 활성 지역 (데이터 있는) -->
      <div class="grid-3" style="margin-bottom:24px;">
        <div
          v-for="region in activeRegions" :key="region.id"
          class="glass-card region-card fade-in"
          @click="goToRegion(region.id)"
        >
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <span style="font-size:20px;">{{ regionIcon(region.region_type) }}</span>
            <div>
              <div style="font-weight:700;font-size:15px;">{{ region.name }}</div>
              <div style="font-size:11px;color:var(--text-muted);">{{ region.code }}</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
            <div>
              <div style="font-size:11px;color:var(--text-muted);">보건소</div>
              <div style="font-size:18px;font-weight:700;color:var(--accent-emerald);">{{ region.center_count }}</div>
            </div>
            <div>
              <div style="font-size:11px;color:var(--text-muted);">환자</div>
              <div style="font-size:18px;font-weight:700;">{{ region.patient_count }}</div>
            </div>
            <div>
              <div style="font-size:11px;color:var(--text-muted);">고위험</div>
              <div style="font-size:18px;font-weight:700;" :style="{ color: region.high_risk_count > 0 ? 'var(--accent-rose)' : 'var(--text-muted)' }">
                {{ region.high_risk_count }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 비활성 지역 (데이터 없는) -->
      <div v-if="inactiveRegions.length">
        <h3 style="font-size:14px;color:var(--text-muted);margin-bottom:12px;">미등록 시·도 ({{ inactiveRegions.length }})</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          <span v-for="r in inactiveRegions" :key="r.id" class="badge badge-blue" style="cursor:pointer;" @click="goToRegion(r.id)">
            {{ r.name }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const data = ref(null)
const loading = ref(true)

const activeRegions = computed(() =>
  (data.value?.regions || []).filter(r => r.center_count > 0 || r.patient_count > 0).sort((a, b) => b.patient_count - a.patient_count)
)
const inactiveRegions = computed(() =>
  (data.value?.regions || []).filter(r => r.center_count === 0 && r.patient_count === 0)
)

function regionIcon(type) {
  const icons = { metropolitan: '🏙️', province: '🌾', special: '⭐' }
  return icons[type] || '📍'
}

function goToRegion(id) {
  router.push(`/dashboard/region/${id}`)
}

onMounted(async () => {
  try {
    const res = await api.getNationalSummary()
    data.value = res.data
  } catch (e) {
    console.error('전국 현황 로드 실패:', e)
  } finally {
    loading.value = false
  }
})
</script>
