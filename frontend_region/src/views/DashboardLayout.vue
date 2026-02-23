<template>
  <div style="display:flex;">
    <aside class="sidebar">
      <div style="margin-bottom:32px;">
        <div style="font-size:24px;margin-bottom:4px;">🏢</div>
        <div style="font-size:15px;font-weight:800;letter-spacing:-0.5px;">{{ regionName }}</div>
        <div style="font-size:11px;color:var(--text-muted);">광역 정신건강 관제</div>
      </div>

      <nav style="flex:1;">
        <router-link to="/dashboard" class="nav-item" :class="{ active: $route.name === 'RegionHome' }">
          <span>📊</span> 현황 대시보드
        </router-link>
        <router-link to="/dashboard/centers" class="nav-item" :class="{ active: $route.name === 'Centers' }">
          <span>🏥</span> 보건소 관리
        </router-link>
        <router-link to="/dashboard/staff" class="nav-item" :class="{ active: $route.name === 'Staff' }">
          <span>👥</span> 인력 현황
        </router-link>

        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--glass-border);">
          <div style="font-size:11px;color:var(--text-muted);padding:0 16px 8px;text-transform:uppercase;letter-spacing:1px;">내보내기</div>
          <a @click.prevent="exportCSV" href="#" class="nav-item">
            <span>📥</span> 관할 보고서 (CSV)
          </a>
        </div>
      </nav>

      <div style="padding:16px;background:var(--glass);border-radius:12px;">
        <div style="font-size:13px;font-weight:600;">{{ user?.username }}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">광역 관리자</div>
        <button @click="logout" class="btn btn-ghost" style="width:100%;justify-content:center;margin-top:12px;padding:8px;font-size:12px;">
          로그아웃
        </button>
      </div>
    </aside>

    <main class="main-content">
      <router-view :region-id="regionId" />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const user = ref(null)
const regionId = ref(null)
const regionName = computed(() => user.value?.managed_region?.name || '광역 관리')

onMounted(async () => {
  try {
    const cached = localStorage.getItem('region_user')
    if (cached) user.value = JSON.parse(cached)
    const res = await api.getMe()
    user.value = res.data
    regionId.value = res.data.managed_region?.id
    localStorage.setItem('region_user', JSON.stringify(res.data))
  } catch {
    router.push('/')
  }
})

function logout() {
  localStorage.removeItem('region_token')
  localStorage.removeItem('region_refresh')
  localStorage.removeItem('region_user')
  router.push('/')
}

async function exportCSV() {
  if (!regionId.value) return
  try {
    const res = await api.exportRegionCSV(regionId.value)
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8-sig;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `region_report_${regionId.value}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert('내보내기 실패: ' + e.message)
  }
}
</script>
