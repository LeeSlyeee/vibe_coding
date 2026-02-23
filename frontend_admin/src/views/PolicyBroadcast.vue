<template>
  <div>
    <div class="page-header fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h1 class="page-title">📢 정책·공지 배포</h1>
          <p class="page-subtitle">전국/시도/보건소별 공지사항 관리</p>
        </div>
        <button @click="showForm = true" class="btn btn-primary" v-if="!showForm">
          + 새 공지 등록
        </button>
      </div>
    </div>

    <!-- Create Form -->
    <div v-if="showForm" class="glass-card fade-in" style="margin-bottom:24px;">
      <h3 style="font-size:16px;font-weight:700;margin-bottom:20px;">📝 새 공지 등록</h3>
      <form @submit.prevent="createBroadcast">
        <div class="form-group">
          <label>제목</label>
          <input v-model="form.title" class="form-input" placeholder="공지 제목" required />
        </div>
        <div class="form-group">
          <label>내용</label>
          <textarea v-model="form.content" class="form-input" rows="5" placeholder="공지 내용을 입력하세요" required style="resize:vertical;"></textarea>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div class="form-group">
            <label>배포 범위</label>
            <select v-model="form.broadcast_level" class="form-input">
              <option value="national">전국</option>
              <option value="regional">시·도</option>
              <option value="center">보건소</option>
            </select>
          </div>
          <div class="form-group" v-if="form.broadcast_level === 'regional'">
            <label>대상 시·도</label>
            <select v-model="form.target_region" class="form-input">
              <option :value="null">선택하세요</option>
              <option v-for="r in regionList" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
            <input type="checkbox" v-model="form.is_urgent" style="width:18px;height:18px;" />
            <span>🚨 긴급 공지</span>
          </label>
        </div>
        <div style="display:flex;gap:12px;justify-content:flex-end;">
          <button type="button" @click="showForm = false" class="btn btn-ghost">취소</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '등록 중...' : '등록' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Broadcast List -->
    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="glass-card fade-in">
      <div v-if="broadcasts.length === 0" style="text-align:center;padding:40px;color:var(--text-muted);">
        등록된 공지가 없습니다.
      </div>
      <div v-else>
        <div v-for="b in broadcasts" :key="b.id" class="broadcast-item">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;">
            <div style="flex:1;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span v-if="b.is_urgent" class="badge badge-rose">🚨 긴급</span>
                <span :class="levelBadge(b.broadcast_level)">{{ levelLabel(b.broadcast_level) }}</span>
                <span v-if="b.target_region_name" class="badge badge-blue">📍 {{ b.target_region_name }}</span>
              </div>
              <h3 style="font-size:16px;font-weight:700;margin-bottom:6px;">{{ b.title }}</h3>
              <p style="font-size:13px;color:var(--text-secondary);white-space:pre-wrap;line-height:1.6;">{{ b.content }}</p>
            </div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.04);">
            <span style="font-size:12px;color:var(--text-muted);">{{ b.created_by_name }} · {{ formatDate(b.created_at) }}</span>
            <button @click="deleteBroadcast(b.id)" class="btn btn-ghost" style="padding:4px 10px;font-size:11px;color:var(--accent-rose);">삭제</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const broadcasts = ref([])
const regionList = ref([])
const loading = ref(true)
const showForm = ref(false)
const submitting = ref(false)
const form = ref({ title: '', content: '', broadcast_level: 'national', target_region: null, target_center: null, is_urgent: false })

function levelLabel(l) {
  return { national: '전국', regional: '시·도', center: '보건소' }[l] || l
}
function levelBadge(l) {
  return { national: 'badge badge-purple', regional: 'badge badge-amber', center: 'badge badge-emerald' }[l] || 'badge'
}
function formatDate(d) {
  return new Date(d).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadBroadcasts() {
  try {
    const res = await api.getBroadcasts()
    broadcasts.value = res.data
  } catch (e) {
    console.error('공지 로드 실패:', e)
  } finally {
    loading.value = false
  }
}

async function createBroadcast() {
  submitting.value = true
  try {
    await api.createBroadcast(form.value)
    form.value = { title: '', content: '', broadcast_level: 'national', target_region: null, target_center: null, is_urgent: false }
    showForm.value = false
    loading.value = true
    await loadBroadcasts()
  } catch (e) {
    alert('등록 실패: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

async function deleteBroadcast(id) {
  if (!confirm('이 공지를 삭제하시겠습니까?')) return
  try {
    await api.deleteBroadcast(id)
    broadcasts.value = broadcasts.value.filter(b => b.id !== id)
  } catch (e) {
    alert('삭제 실패')
  }
}

onMounted(async () => {
  await loadBroadcasts()
  try {
    const r = await api.getRegions()
    regionList.value = r.data
  } catch { /* ignore */ }
})
</script>

<style scoped>
.broadcast-item {
  padding: 20px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: background 0.2s;
}
.broadcast-item:hover { background: rgba(255,255,255,0.02); }
.broadcast-item:last-child { border-bottom: none; }
</style>
