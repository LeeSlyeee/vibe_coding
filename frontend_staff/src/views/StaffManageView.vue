<template>
  <div class="staff-manage-page">
    <div class="page-header">
      <h1>👥 상담사 관리</h1>
      <p>소속 보건소 상담사 등록·수정·삭제</p>
    </div>

    <!-- 등록 폼 -->
    <div class="card register-card">
      <h2>{{ editMode ? '✏️ 상담사 수정' : '➕ 새 상담사 등록' }}</h2>
      <form @submit.prevent="editMode ? updateStaff() : registerStaff()" class="register-form">
        <div class="form-row">
          <div class="form-group">
            <label>이름 *</label>
            <input v-model="form.first_name" type="text" placeholder="홍길동" required />
          </div>
          <div class="form-group">
            <label>아이디 *</label>
            <input v-model="form.username" type="text" placeholder="counselor01" required :disabled="editMode" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>{{ editMode ? '새 비밀번호 (변경 시만)' : '비밀번호 *' }}</label>
            <input v-model="form.password" type="password" placeholder="6자 이상" :required="!editMode" minlength="6" />
          </div>
          <div class="form-group">
            <label>이메일</label>
            <input v-model="form.email" type="email" placeholder="email@example.com" />
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '처리 중...' : (editMode ? '수정 저장' : '상담사 등록') }}
          </button>
          <button v-if="editMode" type="button" class="btn btn-cancel" @click="cancelEdit">취소</button>
        </div>
        <div v-if="message" class="message" :class="messageType">{{ message }}</div>
      </form>
    </div>

    <!-- 목록 -->
    <div class="card">
      <h2>📋 소속 상담사 목록 <span class="count">({{ staffList.length }}명)</span></h2>
      <div v-if="loading" class="loading">로딩 중...</div>
      <table v-else-if="staffList.length > 0" class="staff-table">
        <thead>
          <tr>
            <th>이름</th>
            <th>아이디</th>
            <th>이메일</th>
            <th>등급</th>
            <th>등록일</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in staffList" :key="s.id">
            <td class="name">{{ s.first_name || '-' }}</td>
            <td>{{ s.username }}</td>
            <td>{{ s.email || '-' }}</td>
            <td><span class="badge">{{ levelLabel(s.admin_level) }}</span></td>
            <td class="date">{{ formatDate(s.date_joined) }}</td>
            <td class="actions">
              <button class="btn-sm btn-edit" @click="startEdit(s)">수정</button>
              <button class="btn-sm btn-delete" @click="deleteStaff(s)">삭제</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">등록된 상담사가 없습니다.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/index'

const staffList = ref([])
const loading = ref(true)
const submitting = ref(false)
const message = ref('')
const messageType = ref('success')
const editMode = ref(false)
const editTargetId = ref(null)

const form = ref({ first_name: '', username: '', password: '', email: '' })

async function fetchStaff() {
  try {
    const res = await api.get('/auth/staff/manage/')
    staffList.value = res.data
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function registerStaff() {
  submitting.value = true; message.value = ''
  try {
    const res = await api.post('/auth/staff/manage/', form.value)
    message.value = res.data.message || '등록 완료'
    messageType.value = 'success'
    form.value = { first_name: '', username: '', password: '', email: '' }
    await fetchStaff()
  } catch (e) {
    message.value = e.response?.data?.error || '등록 실패'
    messageType.value = 'error'
  } finally { submitting.value = false }
}

function startEdit(s) {
  editMode.value = true
  editTargetId.value = s.id
  form.value = { first_name: s.first_name || '', username: s.username, password: '', email: s.email || '' }
  message.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editMode.value = false
  editTargetId.value = null
  form.value = { first_name: '', username: '', password: '', email: '' }
  message.value = ''
}

async function updateStaff() {
  submitting.value = true; message.value = ''
  try {
    const payload = { staff_id: editTargetId.value, first_name: form.value.first_name, email: form.value.email }
    if (form.value.password) payload.password = form.value.password
    const res = await api.put('/auth/staff/manage/', payload)
    message.value = res.data.message || '수정 완료'
    messageType.value = 'success'
    cancelEdit()
    await fetchStaff()
  } catch (e) {
    message.value = e.response?.data?.error || '수정 실패'
    messageType.value = 'error'
  } finally { submitting.value = false }
}

async function deleteStaff(s) {
  const name = s.first_name || s.username
  if (!confirm(`${name} 상담사를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) return
  try {
    const res = await api.delete('/auth/staff/manage/', { data: { staff_id: s.id } })
    message.value = res.data.message || '삭제 완료'
    messageType.value = 'success'
    await fetchStaff()
  } catch (e) {
    message.value = e.response?.data?.error || '삭제 실패'
    messageType.value = 'error'
  }
}

function levelLabel(l) { return { counselor: '상담사', center_admin: '보건소 관리자' }[l] || l || '상담사' }
function formatDate(d) { return d ? new Date(d).toLocaleDateString('ko-KR') : '-' }

onMounted(fetchStaff)
</script>

<style scoped>
.staff-manage-page { max-width: 900px; margin: 0 auto; padding: 24px 16px; }
.page-header { margin-bottom: 28px; }
.page-header h1 { font-size: 24px; font-weight: 800; margin-bottom: 4px; }
.page-header p { font-size: 14px; color: #888; }
.card { background: #fff; border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card h2 { font-size: 17px; font-weight: 700; margin-bottom: 18px; }
.count { font-size: 14px; font-weight: 400; color: #999; }
.register-form { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 600; color: #555; }
.form-group input { padding: 10px 14px; border: 1.5px solid #e0e0e0; border-radius: 10px; font-size: 14px; transition: border-color 0.2s; }
.form-group input:focus { outline: none; border-color: #6366f1; }
.form-group input:disabled { background: #f5f5f5; color: #999; }
.form-actions { margin-top: 4px; display: flex; gap: 10px; }
.btn-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; border: none; padding: 12px 28px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel { background: #f3f4f6; color: #666; border: none; padding: 12px 28px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; }
.message { padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; margin-top: 8px; }
.message.success { background: #ecfdf5; color: #059669; }
.message.error { background: #fef2f2; color: #dc2626; }
.staff-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.staff-table th { text-align: left; padding: 10px 12px; font-size: 12px; font-weight: 700; color: #888; border-bottom: 2px solid #f0f0f0; }
.staff-table td { padding: 12px; border-bottom: 1px solid #f5f5f5; }
.staff-table tr:hover { background: #fafafa; }
.name { font-weight: 600; }
.date { font-size: 12px; color: #999; }
.badge { display: inline-block; background: #eff6ff; color: #3b82f6; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.actions { display: flex; gap: 6px; }
.btn-sm { padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border: none; }
.btn-edit { background: #eff6ff; color: #3b82f6; }
.btn-edit:hover { background: #dbeafe; }
.btn-delete { background: #fef2f2; color: #ef4444; }
.btn-delete:hover { background: #fee2e2; }
.loading, .empty { text-align: center; padding: 40px; color: #999; font-size: 14px; }
@media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }
</style>
