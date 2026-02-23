<template>
  <div>
    <div class="page-header fade-in">
      <h1 class="page-title">👥 인력 관리</h1>
      <p class="page-subtitle">전국 상담사 현황 및 배치</p>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <template v-else>
      <!-- Summary Cards -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;" class="fade-in">
        <div class="glass-card" style="text-align:center;">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">전체 상담사</div>
          <div style="font-size:28px;font-weight:800;">{{ staff.length }}</div>
        </div>
        <div class="glass-card" style="text-align:center;">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">배치 완료</div>
          <div style="font-size:28px;font-weight:800;color:var(--accent-emerald);">{{ staff.filter(s => s.center).length }}</div>
        </div>
        <div class="glass-card" style="text-align:center;">
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">미배치</div>
          <div style="font-size:28px;font-weight:800;color:var(--accent-rose);">{{ staff.filter(s => !s.center).length }}</div>
        </div>
      </div>

      <!-- Staff Table -->
      <div class="glass-card fade-in" style="overflow-x:auto;">
        <div v-if="staff.length === 0" style="text-align:center;padding:40px;color:var(--text-muted);">
          등록된 상담사가 없습니다.
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>이름</th>
              <th>아이디</th>
              <th>등급</th>
              <th>소속 보건소</th>
              <th>담당 환자</th>
              <th>이메일</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in staff" :key="s.id">
              <td style="font-weight:600;">{{ s.first_name || s.username }}</td>
              <td>{{ s.username }}</td>
              <td>
                <span :class="levelBadge(s.admin_level)">{{ levelLabel(s.admin_level) }}</span>
              </td>
              <td>{{ s.center_name || '미배치' }}</td>
              <td style="font-weight:700;">{{ s.patient_count }}</td>
              <td style="color:var(--text-muted);font-size:12px;">{{ s.email || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const staff = ref([])
const loading = ref(true)

function levelLabel(l) {
  return { counselor: '상담사', center_admin: '보건소 관리자', region_admin: '광역 관리자', central_admin: '중앙 관리자' }[l] || l
}
function levelBadge(l) {
  return {
    counselor: 'badge badge-blue',
    center_admin: 'badge badge-emerald',
    region_admin: 'badge badge-amber',
    central_admin: 'badge badge-purple',
  }[l] || 'badge'
}

onMounted(async () => {
  try {
    const res = await api.getStaff()
    staff.value = res.data
  } catch (e) {
    console.error('인력 로드 실패:', e)
  } finally {
    loading.value = false
  }
})
</script>
