<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">🏢 시·도 관리</h1>
      <p class="page-subtitle">전국 17개 시·도 조직 관리</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="glass-card fade-in" style="overflow-x:auto;">
      <table class="data-table">
        <thead>
          <tr>
            <th>코드</th>
            <th>시·도명</th>
            <th>유형</th>
            <th>보건소</th>
            <th>환자</th>
            <th>상담사</th>
            <th>상태</th>
            <th>액션</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="region in regions" :key="region.id">
            <td><span class="badge badge-blue">{{ region.code }}</span></td>
            <td style="font-weight:600;">{{ region.name }}</td>
            <td>
              <span :class="typeClass(region.region_type)">{{ typeLabel(region.region_type) }}</span>
            </td>
            <td style="font-weight:700;">{{ region.center_count }}</td>
            <td style="font-weight:700;">{{ region.total_patients }}</td>
            <td>{{ region.total_staff }}</td>
            <td>
              <span :class="region.is_active ? 'badge badge-emerald' : 'badge badge-rose'">
                {{ region.is_active ? '활성' : '비활성' }}
              </span>
            </td>
            <td>
              <button class="btn btn-ghost" style="padding:6px 12px;font-size:12px;" @click="$router.push(`/dashboard/region/${region.id}`)">
                상세 →
              </button>
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

const regions = ref([])
const loading = ref(true)

function typeLabel(t) {
  return { metropolitan: '특별시/광역시', province: '도', special: '특별자치' }[t] || t
}
function typeClass(t) {
  return { metropolitan: 'badge badge-purple', province: 'badge badge-amber', special: 'badge badge-blue' }[t] || 'badge'
}

onMounted(async () => {
  try {
    const res = await api.getRegions()
    regions.value = res.data
  } catch (e) {
    console.error('시·도 목록 로드 실패:', e)
  } finally {
    loading.value = false
  }
})
</script>
