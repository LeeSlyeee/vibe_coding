<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">📊 관할 현황 대시보드</h1>
      <p class="page-subtitle">소속 보건소 통합 모니터링</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else>
      <!-- 통계 카드 -->
      <div class="stat-grid fade-in">
        <div class="glass-card stat-card">
          <div class="label">소속 보건소</div>
          <div class="value" style="color:var(--accent-teal);">{{ data.center_count || 0 }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">총 환자 수</div>
          <div class="value">{{ data.total_patients || 0 }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">고위험군</div>
          <div class="value" style="color:var(--accent-rose);">{{ data.high_risk_count || 0 }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">총 상담사</div>
          <div class="value" style="color:var(--accent-blue);">{{ data.total_staff || 0 }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">누적 일기</div>
          <div class="value" style="color:var(--accent-amber);">{{ data.total_diaries || 0 }}</div>
        </div>
      </div>

      <!-- 보건소별 비교 테이블 -->
      <div class="glass-card fade-in" style="margin-top:24px;">
        <h2 style="font-size:17px;font-weight:800;margin-bottom:16px;">🏥 보건소별 현황</h2>
        <table class="data-table">
          <thead>
            <tr>
              <th>보건소명</th>
              <th>환자 수</th>
              <th>고위험</th>
              <th>일기 수</th>
              <th>상담사</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in centers" :key="c.id">
              <td style="font-weight:700;">{{ c.name }}</td>
              <td>{{ c.patient_count || 0 }}</td>
              <td>
                <span v-if="c.high_risk_count > 0" class="badge badge-rose">{{ c.high_risk_count }}</span>
                <span v-else style="color:var(--text-muted);">0</span>
              </td>
              <td>{{ c.diary_count || 0 }}</td>
              <td>{{ c.staff_count || 0 }}</td>
            </tr>
            <tr v-if="centers.length === 0">
              <td colspan="5" style="text-align:center;padding:40px;color:var(--text-muted);">
                소속 보건소 데이터가 없습니다
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'

const props = defineProps({ regionId: [Number, String] })
const loading = ref(true)
const data = ref({})
const centers = ref([])

async function fetchData(id) {
  if (!id) return
  loading.value = true
  try {
    const res = await api.getRegionDashboard(id)
    data.value = res.data
    centers.value = res.data.centers || []
  } catch (e) {
    console.error('대시보드 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.regionId, (v) => { if (v) fetchData(v) })
onMounted(() => { if (props.regionId) fetchData(props.regionId) })
</script>
