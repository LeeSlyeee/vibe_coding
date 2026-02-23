<template>
  <div class="audit-page">
    <div class="page-header fade-in">
      <h1 class="page-title">🛡️ 감사 로그</h1>
      <p class="page-subtitle">관리자 API 접근 기록</p>
    </div>

    <div class="controls fade-in">
      <div class="filter-group">
        <label>조회 기간</label>
        <select v-model="days" @change="fetchLogs" class="select-input">
          <option :value="1">최근 1일</option>
          <option :value="3">최근 3일</option>
          <option :value="7">최근 7일</option>
          <option :value="30">최근 30일</option>
        </select>
      </div>
      <div class="filter-group">
        <label>필터</label>
        <select v-model="actionFilter" class="select-input">
          <option value="">전체</option>
          <option value="VIEW">조회</option>
          <option value="CREATE">생성</option>
          <option value="UPDATE">수정</option>
          <option value="DELETE">삭제</option>
        </select>
      </div>
      <div class="stat-chip">총 {{ filteredLogs.length }}건</div>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="glass-card fade-in table-container">
      <table class="audit-table">
        <thead>
          <tr>
            <th>시각</th>
            <th>사용자</th>
            <th>행위</th>
            <th>대상</th>
            <th>IP 주소</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id" class="audit-row">
            <td class="td-time">{{ formatDate(log.timestamp) }}</td>
            <td class="td-user">{{ log.user }}</td>
            <td>
              <span class="action-badge" :class="'action-' + log.action">
                {{ actionLabel(log.action) }}
              </span>
            </td>
            <td class="td-target">{{ log.target_type }}</td>
            <td class="td-ip">{{ log.ip_address }}</td>
            <td>
              <span class="status-dot" :class="log.detail?.status < 400 ? 'ok' : 'err'"></span>
              {{ log.detail?.status || '-' }}
            </td>
          </tr>
          <tr v-if="filteredLogs.length === 0">
            <td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">
              로그 데이터가 없습니다
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const loading = ref(true)
const logs = ref([])
const days = ref(7)
const actionFilter = ref('')

const filteredLogs = computed(() => {
  if (!actionFilter.value) return logs.value
  return logs.value.filter(l => l.action === actionFilter.value)
})

async function fetchLogs() {
  loading.value = true
  try {
    const res = await api.getAuditLogs(days.value)
    logs.value = res.data.logs || []
  } catch (e) {
    console.error('감사 로그 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

function actionLabel(action) {
  return { VIEW: '조회', CREATE: '생성', UPDATE: '수정', DELETE: '삭제', OTHER: '기타' }[action] || action
}

onMounted(fetchLogs)
</script>

<style scoped>
.audit-page { padding-bottom: 40px; }

.controls {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 11px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.select-input {
  background: var(--glass);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  min-width: 140px;
}
.stat-chip {
  background: rgba(99,102,241,0.15);
  color: var(--accent-blue);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  margin-left: auto;
}

.table-container { overflow-x: auto; }

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.audit-table th {
  text-align: left;
  padding: 14px 16px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--glass-border);
}
.audit-row {
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.15s;
}
.audit-row:hover { background: rgba(255,255,255,0.03); }
.audit-row td { padding: 12px 16px; }

.td-time { font-family: 'SF Mono', monospace; font-size: 12px; color: var(--text-muted); white-space: nowrap; }
.td-user { font-weight: 600; }
.td-target { font-family: 'SF Mono', monospace; font-size: 12px; }
.td-ip { font-family: 'SF Mono', monospace; font-size: 12px; color: var(--text-muted); }

.action-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}
.action-VIEW { background: rgba(59,130,246,0.15); color: #60a5fa; }
.action-CREATE { background: rgba(16,185,129,0.15); color: #34d399; }
.action-UPDATE { background: rgba(245,158,11,0.15); color: #fbbf24; }
.action-DELETE { background: rgba(244,63,94,0.15); color: #fb7185; }
.action-OTHER { background: rgba(156,163,175,0.15); color: #9ca3af; }

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.ok { background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.4); }
.status-dot.err { background: #f43f5e; box-shadow: 0 0 6px rgba(244,63,94,0.4); }
</style>
