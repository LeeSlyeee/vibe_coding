<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">👥 인력 현황</h1>
      <p class="page-subtitle">관할 보건소 상담사 배치 · 재배치</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else>
      <div class="stat-grid fade-in" style="grid-template-columns:repeat(3,1fr);">
        <div class="glass-card stat-card">
          <div class="label">전체 상담사</div>
          <div class="value">{{ staff.length }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">배치 완료</div>
          <div class="value" style="color:var(--accent-emerald);">{{ staff.filter(s => s.center_name).length }}</div>
        </div>
        <div class="glass-card stat-card">
          <div class="label">미배치</div>
          <div class="value" style="color:var(--accent-rose);">{{ staff.filter(s => !s.center_name).length }}</div>
        </div>
      </div>

      <!-- 메시지 -->
      <div v-if="message" class="glass-card fade-in" :style="{ borderLeft: messageType === 'success' ? '3px solid var(--accent-emerald)' : '3px solid var(--accent-rose)', marginBottom: '16px' }">
        <div style="font-size:13px;font-weight:600;">{{ message }}</div>
      </div>

      <div class="glass-card fade-in">
        <table class="data-table">
          <thead>
            <tr>
              <th>이름</th>
              <th>아이디</th>
              <th>등급</th>
              <th>소속 센터</th>
              <th>담당 환자</th>
              <th>재배치</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in staff" :key="s.id">
              <td style="font-weight:700;">{{ s.first_name || s.username }}</td>
              <td style="font-family:monospace;font-size:12px;">{{ s.username }}</td>
              <td><span class="badge badge-teal">{{ levelLabel(s.admin_level) }}</span></td>
              <td>{{ s.center_name || '미배치' }}</td>
              <td style="font-weight:700;">{{ s.patient_count || 0 }}</td>
              <td>
                <select @change="reassign(s.id, $event.target.value); $event.target.value = ''" class="reassign-select">
                  <option value="">이동...</option>
                  <option v-for="c in centers" :key="c.id" :value="c.id" :disabled="c.name === s.center_name">
                    {{ c.name }}
                  </option>
                </select>
              </td>
            </tr>
            <tr v-if="staff.length === 0">
              <td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">데이터 없음</td>
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
const staff = ref([])
const centers = ref([])
const message = ref('')
const messageType = ref('success')

function levelLabel(l) {
  return { counselor: '상담사', center_admin: '보건소 관리자', region_admin: '광역 관리자' }[l] || l
}

async function fetchData(id) {
  if (!id) return
  loading.value = true
  try {
    const [staffRes, centersRes] = await Promise.all([
      api.getRegionStaff(id),
      api.getRegionCenters(id),
    ])
    staff.value = staffRes.data
    centers.value = centersRes.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function reassign(staffId, centerId) {
  if (!centerId) return
  const s = staff.value.find(x => x.id === staffId)
  const c = centers.value.find(x => x.id == centerId)
  if (!confirm(`${s?.first_name || s?.username}를 ${c?.name}(으)로 재배치하시겠습니까?`)) return

  message.value = ''
  try {
    const res = await api.reassignStaff(staffId, centerId)
    message.value = res.data.message || '재배치 완료'
    messageType.value = 'success'
    await fetchData(props.regionId)
  } catch (e) {
    message.value = e.response?.data?.error || '재배치 실패'
    messageType.value = 'error'
  }
}

watch(() => props.regionId, (v) => { if (v) fetchData(v) })
onMounted(() => { if (props.regionId) fetchData(props.regionId) })
</script>

<style scoped>
.reassign-select {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  min-width: 120px;
}
.reassign-select option { background: #1a1a2e; color: #fff; }
</style>
