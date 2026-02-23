<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">🏥 관할 보건소</h1>
      <p class="page-subtitle">소속 정신건강복지센터 현황</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="glass-card fade-in">
      <div style="font-size:13px;color:var(--text-muted);margin-bottom:16px;">
        총 <strong style="color:var(--accent-teal);">{{ centers.length }}</strong>개 센터
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>센터 코드</th>
            <th>센터명</th>
            <th>활성 상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in centers" :key="c.id">
            <td style="font-family:monospace;font-size:12px;color:var(--text-muted);">{{ c.code }}</td>
            <td style="font-weight:700;">{{ c.name }}</td>
            <td>
              <span v-if="c.is_active" class="badge badge-emerald">활성</span>
              <span v-else class="badge badge-rose">비활성</span>
            </td>
          </tr>
          <tr v-if="centers.length === 0">
            <td colspan="3" style="text-align:center;padding:40px;color:var(--text-muted);">데이터 없음</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'

const props = defineProps({ regionId: [Number, String] })
const loading = ref(true)
const centers = ref([])

async function fetchCenters(id) {
  if (!id) return
  loading.value = true
  try {
    const res = await api.getRegionCenters(id)
    centers.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(() => props.regionId, (v) => { if (v) fetchCenters(v) })
onMounted(() => { if (props.regionId) fetchCenters(props.regionId) })
</script>
