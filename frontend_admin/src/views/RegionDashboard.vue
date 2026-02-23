<template>
  <div>
    <!-- Back + Header -->
    <div class="page-header fade-in">
      <button @click="$router.push('/dashboard')" class="btn btn-ghost" style="margin-bottom:12px;">
        ← 전국 현황으로
      </button>
      <h1 class="page-title">📍 {{ regionData?.region?.name || '로딩 중...' }}</h1>
      <p class="page-subtitle">광역 시·도 관리 대시보드</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else-if="regionData">
      <!-- Summary -->
      <div class="grid-4" style="margin-bottom:32px;">
        <div class="glass-card stat-card emerald fade-in fade-in-delay-1">
          <div class="stat-label">관할 보건소</div>
          <div class="stat-value">{{ regionData.summary.total_centers }}</div>
        </div>
        <div class="glass-card stat-card purple fade-in fade-in-delay-2">
          <div class="stat-label">전체 환자</div>
          <div class="stat-value">{{ regionData.summary.total_patients }}</div>
        </div>
        <div class="glass-card stat-card cyan fade-in fade-in-delay-2">
          <div class="stat-label">상담사</div>
          <div class="stat-value">{{ regionData.summary.total_staff }}</div>
        </div>
        <div class="glass-card stat-card rose fade-in fade-in-delay-3">
          <div class="stat-label">고위험군</div>
          <div class="stat-value" style="color:var(--accent-rose);">{{ regionData.summary.total_high_risk }}</div>
        </div>
      </div>

      <!-- Centers Table -->
      <div class="glass-card fade-in fade-in-delay-3" style="margin-bottom:32px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:20px;">🏥 소속 보건소 현황</h2>
        <table class="data-table" v-if="regionData.centers.length">
          <thead>
            <tr>
              <th>보건소명</th>
              <th>관할 지역</th>
              <th>환자 수</th>
              <th>상담사</th>
              <th>일기 수</th>
              <th>고위험</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="center in regionData.centers" :key="center.id">
              <td style="font-weight:600;">{{ center.name }}</td>
              <td style="color:var(--text-secondary);">{{ center.region_name }}</td>
              <td>
                <span style="font-weight:700;font-size:16px;">{{ center.patient_count }}</span>
                <span v-if="center.capacity" style="color:var(--text-muted);font-size:12px;"> / {{ center.capacity }}</span>
              </td>
              <td>{{ center.staff_count }}</td>
              <td>{{ center.diary_count.toLocaleString() }}</td>
              <td>
                <span :class="center.high_risk_count > 0 ? 'badge badge-rose' : 'badge badge-emerald'">
                  {{ center.high_risk_count > 0 ? `⚠️ ${center.high_risk_count}명` : '안전' }}
                </span>
              </td>
              <td>
                <span class="badge badge-emerald">운영 중</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else style="text-align:center;padding:40px;color:var(--text-muted);">
          등록된 보건소가 없습니다.
        </div>
      </div>

      <!-- Chart: Center Comparison -->
      <div class="grid-2" v-if="regionData.centers.length > 1">
        <div class="glass-card fade-in fade-in-delay-4">
          <h3 style="font-size:15px;font-weight:700;margin-bottom:16px;">📊 보건소별 환자 수 비교</h3>
          <div style="padding:8px;">
            <div v-for="center in sortedByPatients" :key="center.id" style="margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span>{{ center.name }}</span>
                <span style="font-weight:700;">{{ center.patient_count }}</span>
              </div>
              <div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                <div :style="barStyle(center.patient_count, maxPatients)" style="height:100%;border-radius:4px;transition:width 1s ease;"></div>
              </div>
            </div>
          </div>
        </div>
        <div class="glass-card fade-in fade-in-delay-4">
          <h3 style="font-size:15px;font-weight:700;margin-bottom:16px;">📝 보건소별 일기 수 비교</h3>
          <div style="padding:8px;">
            <div v-for="center in sortedByDiaries" :key="center.id" style="margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span>{{ center.name }}</span>
                <span style="font-weight:700;">{{ center.diary_count.toLocaleString() }}</span>
              </div>
              <div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                <div :style="barStylePurple(center.diary_count, maxDiaries)" style="height:100%;border-radius:4px;transition:width 1s ease;"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'

const route = useRoute()
const regionData = ref(null)
const loading = ref(true)

const sortedByPatients = computed(() => [...(regionData.value?.centers || [])].sort((a, b) => b.patient_count - a.patient_count))
const sortedByDiaries = computed(() => [...(regionData.value?.centers || [])].sort((a, b) => b.diary_count - a.diary_count))
const maxPatients = computed(() => Math.max(1, ...sortedByPatients.value.map(c => c.patient_count)))
const maxDiaries = computed(() => Math.max(1, ...sortedByDiaries.value.map(c => c.diary_count)))

function barStyle(val, max) {
  return { width: `${(val / max) * 100}%`, background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-cyan))' }
}
function barStylePurple(val, max) {
  return { width: `${(val / max) * 100}%`, background: 'linear-gradient(90deg, var(--accent-purple), var(--accent-rose))' }
}

async function load(id) {
  loading.value = true
  try {
    const res = await api.getRegionDashboard(id)
    regionData.value = res.data
  } catch (e) {
    console.error('광역 대시보드 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => load(route.params.id))
watch(() => route.params.id, (newId) => { if (newId) load(newId) })
</script>
