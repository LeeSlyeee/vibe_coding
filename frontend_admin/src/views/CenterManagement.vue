<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">🏥 보건소 관리</h1>
      <p class="page-subtitle">전국 보건소 목록 및 관리</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="glass-card fade-in" style="overflow-x:auto;">
      <div v-if="centers.length === 0" style="text-align:center;padding:40px;color:var(--text-muted);">
        등록된 보건소가 없습니다.
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>보건소명</th>
            <th>기관 코드</th>
            <th>소속 시·도</th>
            <th>관할 지역</th>
            <th>환자</th>
            <th>상담사</th>
            <th>수용능력</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in centers" :key="c.id">
            <td style="font-weight:600;">{{ c.name }}</td>
            <td><span class="badge badge-blue">{{ c.code || '-' }}</span></td>
            <td>{{ c.region ? regionName(c.region) : '미배정' }}</td>
            <td>{{ c.region_name || '-' }}</td>
            <td style="font-weight:700;">{{ c.patient_count }}</td>
            <td>{{ c.staff_count }}</td>
            <td>{{ c.capacity }}</td>
            <td>
              <span :class="c.is_active ? 'badge badge-emerald' : 'badge badge-rose'">
                {{ c.is_active ? '활성' : '비활성' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const centers = ref([])
const regions = ref([])
const loading = ref(true)

function regionName(regionId) {
  const r = regions.value.find(r => r.id === regionId)
  return r ? r.name : regionId
}

onMounted(async () => {
  try {
    const [cRes, rRes] = await Promise.all([
      api.getCenters(),
      api.getRegions()
    ])
    centers.value = cRes.data
    regions.value = rRes.data
  } catch (e) {
    console.error('보건소 로드 실패:', e)
  } finally {
    loading.value = false
  }
})
</script>
