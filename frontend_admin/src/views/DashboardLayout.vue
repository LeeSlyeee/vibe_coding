<template>
  <div style="display:flex;">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div style="margin-bottom:32px;">
        <div style="font-size:24px;margin-bottom:4px;">🏛️</div>
        <div style="font-size:16px;font-weight:800;letter-spacing:-0.5px;">마음온 관리</div>
        <div style="font-size:11px;color:var(--text-muted);">National Admin System</div>
      </div>

      <!-- Nav -->
      <nav style="flex:1;">
        <router-link to="/dashboard" class="nav-item" :class="{ active: $route.name === 'National' }">
          <span>📊</span> 전국 현황
        </router-link>
        <router-link to="/dashboard/map" class="nav-item" :class="{ active: $route.name === 'RiskMap' }">
          <span>🗺️</span> 위험도 지도
        </router-link>
        <router-link to="/dashboard/regions" class="nav-item" :class="{ active: $route.name === 'RegionManagement' }">
          <span>🏢</span> 시·도 관리
        </router-link>
        <router-link to="/dashboard/broadcasts" class="nav-item" :class="{ active: $route.name === 'PolicyBroadcast' }">
          <span>📢</span> 정책 배포
        </router-link>
        <router-link to="/dashboard/centers" class="nav-item" :class="{ active: $route.name === 'CenterManagement' }">
          <span>🏥</span> 보건소 관리
        </router-link>
        <router-link to="/dashboard/staff" class="nav-item" :class="{ active: $route.name === 'StaffManagement' }">
          <span>👥</span> 인력 관리
        </router-link>

        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--glass-border);">
          <div style="font-size:11px;color:var(--text-muted);padding:0 16px 8px;text-transform:uppercase;letter-spacing:1px;">감사·보안</div>
          <router-link to="/dashboard/audit" class="nav-item" :class="{ active: $route.name === 'AuditLog' }">
            <span>🛡️</span> 감사 로그
          </router-link>
        </div>

        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--glass-border);">
          <div style="font-size:11px;color:var(--text-muted);padding:0 16px 8px;text-transform:uppercase;letter-spacing:1px;">내보내기</div>
          <a @click.prevent="exportCSV" href="#" class="nav-item">
            <span>📥</span> 전국 보고서 (CSV)
          </a>
        </div>

        <!-- 광역 관리자: 자기 관할 바로가기 -->
        <div v-if="user?.managed_region" style="margin-top:16px;padding-top:16px;border-top:1px solid var(--glass-border);">
          <div style="font-size:11px;color:var(--text-muted);padding:0 16px 8px;text-transform:uppercase;letter-spacing:1px;">내 관할</div>
          <router-link :to="`/dashboard/region/${user.managed_region.id}`" class="nav-item" :class="{ active: $route.params.id == user.managed_region.id }">
            <span>📍</span> {{ user.managed_region.name }}
          </router-link>
        </div>
      </nav>

      <!-- User Info -->
      <div style="padding:16px;background:var(--glass);border-radius:12px;">
        <div style="font-size:13px;font-weight:600;">{{ user?.username }}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{{ user?.admin_level_display }}</div>
        <button @click="logout" class="btn btn-ghost" style="width:100%;justify-content:center;margin-top:12px;padding:8px;font-size:12px;">
          로그아웃
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="main-content">
      <!-- Top Bar with Notification Bell -->
      <div class="top-bar">
        <div></div>
        <div class="top-bar-actions">
          <div class="notification-wrapper" @click="toggleNotifications">
            <div class="bell-icon">🔔</div>
            <div v-if="unreadCount > 0" class="badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</div>
          </div>
        </div>
      </div>

      <!-- Notification Panel -->
      <transition name="slide">
        <div v-if="showNotifications" class="notification-panel glass-card">
          <div class="noti-header">
            <h3>🔔 알림</h3>
            <button v-if="alerts.length > 0" @click="markAllRead" class="noti-mark-all">모두 읽음</button>
          </div>
          <div v-if="alerts.length === 0" class="noti-empty">새로운 알림이 없습니다</div>
          <div v-for="a in alerts" :key="a.id" class="noti-item" @click="markRead(a.id)">
            <div class="noti-type" :class="'type-' + a.type">
              {{ a.type === 'HIGH_RISK' ? '🔴' : a.type === 'CRISIS' ? '🆘' : a.type === 'NEW_PATIENT' ? '🟢' : '⚙️' }}
            </div>
            <div class="noti-content">
              <div class="noti-title">{{ a.title }}</div>
              <div class="noti-msg">{{ a.message }}</div>
              <div class="noti-time">{{ formatTime(a.created_at) }}</div>
            </div>
          </div>
        </div>
      </transition>

      <router-view v-if="!show2FA" />

      <!-- 2FA PIN Modal -->
      <div v-if="show2FA" class="tfa-overlay">
        <div class="tfa-modal glass-card fade-in">
          <div style="text-align:center;margin-bottom:24px;">
            <div style="font-size:48px;">🔐</div>
            <h2 style="font-size:20px;font-weight:900;margin-top:12px;">2차 인증</h2>
            <p style="font-size:13px;color:var(--text-muted);margin-top:6px;">{{ pinSetupMode ? '새 PIN을 설정해주세요 (4~8자리 숫자)' : '관리자 PIN을 입력해주세요' }}</p>
          </div>
          <form @submit.prevent="handlePinSubmit">
            <input v-model="pinInput" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="8"
              class="tfa-input" placeholder="● ● ● ●" autofocus />
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;font-size:15px;margin-top:12px;">
              {{ pinSetupMode ? 'PIN 설정' : '인증' }}
            </button>
            <div v-if="pinError" style="text-align:center;color:var(--accent-rose);font-size:13px;font-weight:600;margin-top:12px;">{{ pinError }}</div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const user = ref(null)
const alerts = ref([])
const unreadCount = ref(0)
const showNotifications = ref(false)
const show2FA = ref(false)
const pinInput = ref('')
const pinError = ref('')
const pinSetupMode = ref(false)
let pollTimer = null

onMounted(async () => {
  try {
    const cached = localStorage.getItem('admin_user')
    if (cached) user.value = JSON.parse(cached)
    const res = await api.getMe()
    user.value = res.data
    localStorage.setItem('admin_user', JSON.stringify(res.data))

    // L4 중앙 관리자 → 2FA 체크
    if (res.data.admin_level === 'central_admin') {
      try {
        await api.verify2FA('__check__')  // 2FA 상태 확인
      } catch (e) {
        if (e.response?.data?.requires_2fa || e.response?.data?.needs_setup) {
          show2FA.value = true
          pinSetupMode.value = !!e.response?.data?.needs_setup
        }
      }
    }
  } catch {
    router.push('/')
  }

  fetchAlerts()
  pollTimer = setInterval(fetchAlerts, 30000) // 30초마다 폴링
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function fetchAlerts() {
  try {
    const res = await api.getAlerts()
    alerts.value = res.data.alerts || []
    unreadCount.value = res.data.unread_count || 0
  } catch {}
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
}

async function markRead(id) {
  try {
    await api.markAlertRead(id)
    alerts.value = alerts.value.filter(a => a.id !== id)
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch {}
}

async function markAllRead() {
  try {
    await api.markAllAlertsRead()
    alerts.value = []
    unreadCount.value = 0
  } catch {}
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return '방금 전'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  return `${Math.floor(diff / 86400)}일 전`
}

async function handlePinSubmit() {
  pinError.value = ''
  if (!pinInput.value || pinInput.value.length < 4) {
    pinError.value = '4자리 이상 숫자를 입력해주세요'
    return
  }
  try {
    if (pinSetupMode.value) {
      await api.setup2FA(pinInput.value)
      await api.verify2FA(pinInput.value)
    } else {
      await api.verify2FA(pinInput.value)
    }
    show2FA.value = false
    pinInput.value = ''
  } catch (e) {
    pinError.value = e.response?.data?.error || '인증 실패'
  }
}

function logout() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_refresh')
  localStorage.removeItem('admin_user')
  router.push('/')
}

async function exportCSV() {
  try {
    const res = await api.exportNationalCSV()
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8-sig;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'national_report.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert('내보내기 실패: ' + e.message)
  }
}
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0 16px;
  margin-bottom: 4px;
}
.top-bar-actions { display: flex; align-items: center; gap: 12px; }

.notification-wrapper {
  position: relative;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  transition: all 0.2s;
}
.notification-wrapper:hover { background: rgba(255,255,255,0.08); transform: scale(1.05); }
.bell-icon { font-size: 18px; }
.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--accent-rose);
  color: white;
  font-size: 10px;
  font-weight: 800;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  box-shadow: 0 2px 8px rgba(244,63,94,0.4);
  animation: pulse-badge 2s infinite;
}
@keyframes pulse-badge {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.notification-panel {
  position: absolute;
  top: 60px;
  right: 24px;
  width: 380px;
  max-height: 480px;
  overflow-y: auto;
  z-index: 1000;
  padding: 0;
  border: 1px solid var(--glass-border);
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.noti-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--glass-border);
}
.noti-header h3 { font-size: 15px; font-weight: 700; margin: 0; }
.noti-mark-all {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 12px;
  cursor: pointer;
  font-weight: 600;
}
.noti-empty {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}
.noti-item {
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  cursor: pointer;
  transition: background 0.2s;
}
.noti-item:hover { background: rgba(255,255,255,0.04); }
.noti-type { font-size: 20px; flex-shrink: 0; }
.noti-title { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
.noti-msg { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
.noti-time { font-size: 11px; color: var(--text-muted); margin-top: 4px; opacity: 0.7; }

.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* 2FA Modal */
.tfa-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.tfa-modal {
  width: 380px;
  padding: 40px;
}
.tfa-input {
  width: 100%;
  background: rgba(255,255,255,0.05);
  border: 2px solid var(--glass-border);
  color: var(--text-primary);
  padding: 16px;
  border-radius: 14px;
  font-size: 24px;
  text-align: center;
  letter-spacing: 8px;
  font-weight: 800;
  transition: border-color 0.2s;
}
.tfa-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}
</style>
