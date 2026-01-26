<template>
  <div class="medication-container">
    <header class="header">
      <h1>약물 관리</h1>
      <div class="header-buttons">
        <button class="checkup-btn" @click="$router.push('/assessment')">📋 자가진단</button>
        <!-- 중증(Red) 사용자만 약물 추가 가능 -->
        <button v-if="isSevere" class="add-btn" @click="showAddModal = true">+ 약 추가</button>
        <button v-else class="add-btn locked" @click="showUpgradeAlert">🔒 약 추가</button>
      </div>
    </header>

    <!-- 날짜 네비게이션 -->
    <div class="date-nav">
      <button @click="changeDate(-1)">❮</button>
      <span>{{ formattedDate }}</span>
      <button @click="changeDate(1)">❯</button>
    </div>

    <!-- 복용 현황 (Today's Checklist) -->
    <div class="checklist-section">
      <div v-for="slot in timeSlots" :key="slot.id" class="time-slot">
        <h3>{{ slot.label }}</h3>
        <div v-if="getMedsForSlot(slot.id).length === 0" class="empty-slot">
          복용할 약이 없어요
        </div>
        <div 
          v-for="med in getMedsForSlot(slot.id)" 
          :key="med._id" 
          class="med-item"
          :class="{ taken: isTaken(med._id, slot.id) }"
          @click="toggleTaken(med._id, slot.id)"
        >
          <div class="med-info">
            <span class="med-name" :style="{ borderLeftColor: med.color }">{{ med.name }}</span>
            <span class="med-dosage">{{ med.dosage }}</span>
          </div>
          <div class="check-icon">
            {{ isTaken(med._id, slot.id) ? '✅' : '⬜' }}
          </div>
        </div>
      </div>
    </div>

    <!-- 약물 추가 모달 -->
    <div v-if="showAddModal" class="modal-overlay">
      <div class="modal-content">
        <h2>새 약물 등록</h2>
        <input v-model="newMed.name" placeholder="약 이름 (예: 항우울제)" />
        <input v-model="newMed.dosage" placeholder="용량 (예: 1정)" />
        
        <div class="frequency-select">
          <label>복용 시간 선택:</label>
          <div class="checkbox-group">
            <label v-for="slot in timeSlots" :key="slot.id">
              <input type="checkbox" :value="slot.id" v-model="newMed.frequency">
              {{ slot.label }}
            </label>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showAddModal = false">취소</button>
          <button class="primary" @click="addMedication">등록</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { medicationAPI } from '../services/medication'
import { authAPI } from '../services/api' // Import authAPI

const userRiskLevel = ref(1);
const isSevere = computed(() => userRiskLevel.value >= 3);

const currentDate = ref(new Date())
const medications = ref([])
const logs = ref([])
const showAddModal = ref(false)

const showUpgradeAlert = () => {
    alert("보건소 및 병원 사용자 또는 유료사용자 기능입니다.");
}

const timeSlots = [
  { id: 'morning', label: '아침' },
  { id: 'lunch', label: '점심' },
  { id: 'dinner', label: '저녁' },
  { id: 'bedtime', label: '취침 전' }
]

const newMed = ref({
  name: '',
  dosage: '',
  frequency: [],
  color: '#FF5733'
})

const formattedDate = computed(() => {
  return currentDate.value.toISOString().split('T')[0]
})

// --- API Calls ---

const fetchData = async () => {
  try {
    const [medsRes, logsRes, userRes] = await Promise.all([
      medicationAPI.getMedications(),
      medicationAPI.getMedicationLogs(formattedDate.value),
      authAPI.getUserInfo() // Fetch User Risk Level
    ])
    medications.value = medsRes
    logs.value = logsRes
    if (userRes && userRes.risk_level) {
        userRiskLevel.value = userRes.risk_level;
    }
  } catch (e) {
    console.error("데이터 로딩 실패", e)
  }
}

onMounted(() => {
  fetchData()
})

const changeDate = (days) => {
  const date = new Date(currentDate.value)
  date.setDate(date.getDate() + days)
  currentDate.value = date
  fetchData() // 날짜 변경 시 로그 다시 조회
}

// --- Logic ---

const getMedsForSlot = (slotId) => {
  return medications.value.filter(med => med.frequency.includes(slotId))
}

const isTaken = (medId, slotId) => {
  return logs.value.some(log => 
    log.med_id === medId && 
    log.slot === slotId && 
    log.status === 'taken'
  )
}

const toggleTaken = async (medId, slotId) => {
  const currentStatus = isTaken(medId, slotId)
  const newStatus = currentStatus ? 'skipped' : 'taken' // 토글 로직 (취소 기능 고려)
  
  // 낙관적 업데이트 (UI 먼저 반영)
  if (newStatus === 'taken') {
    logs.value.push({ med_id: medId, slot: slotId, status: 'taken' })
  } else {
    logs.value = logs.value.filter(l => !(l.med_id === medId && l.slot === slotId))
  }

  try {
    await medicationAPI.logMedication(medId, slotId, formattedDate.value, newStatus)
  } catch (e) {
    console.error("기록 저장 실패", e)
    fetchData() // 실패 시 롤백
  }
}

const addMedication = async () => {
  if (!newMed.value.name || newMed.value.frequency.length === 0) {
    alert("약 이름과 복용 시간을 선택해주세요.")
    return
  }
  
  try {
    await medicationAPI.addMedication(newMed.value)
    showAddModal.value = false
    newMed.value = { name: '', dosage: '', frequency: [], color: '#FF5733' }
    fetchData() // 목록 갱신
  } catch (e) {
    alert("등록 실패: " + e.message)
  }
}
</script>

<style scoped>
.medication-container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.date-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  font-size: 1.2rem;
  margin-bottom: 30px;
}

.time-slot {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.time-slot h3 {
  font-size: 1rem;
  color: #666;
  margin-bottom: 10px;
}

.med-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.med-item.taken {
  background: #e3f2fd;
  opacity: 0.7;
}

.med-name {
  font-weight: bold;
  padding-left: 8px;
  border-left: 4px solid #FF5733;
}

.med-dosage {
  font-size: 0.8rem;
  color: #888;
  margin-left: 8px;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.add-btn, .checkup-btn {
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}

.add-btn {
  background: #4caf50;
  color: white;
}

.checkup-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.add-btn:hover, .checkup-btn:hover {
  opacity: 0.9;
}

.add-btn.locked {
    background: #9e9e9e;
    cursor: not-allowed;
    opacity: 0.8;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 25px;
  border-radius: 16px;
  width: 90%;
  max-width: 400px;
}

.modal-content input {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.checkbox-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 10px 0 20px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.modal-actions button {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}

.modal-actions button.primary {
  background: #2196F3;
  color: white;
}
</style>
