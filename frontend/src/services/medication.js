import api from './api'

export const medicationAPI = {
  // 약물 등록
  addMedication: async (data) => {
    // data: { name, dosage, frequency: [], alarm_time: {}, memo, color }
    const response = await api.post('/medications', data)
    return response.data
  },

  // 약물 목록 조회
  getMedications: async () => {
    const response = await api.get('/medications')
    return response.data
  },

  // 약물 삭제 (Soft Delete)
  deleteMedication: async (medId) => {
    const response = await api.delete(`/medications/${medId}`)
    return response.data
  },

  // 복용 기록 (Check-in)
  logMedication: async (medId, slot, date, status = 'taken') => {
    // slot: morning, lunch, dinner, bedtime
    const response = await api.post('/medications/log', {
      med_id: medId,
      slot,
      date,
      status
    })
    return response.data
  },

  // 복용 기록 조회
  getMedicationLogs: async (date = null) => {
    const params = {}
    if (date) params.date = date
    
    const response = await api.get('/medications/logs', { params })
    return response.data
  },

  // 자가진단 (Assessment) 제출
  submitAssessment: async (data) => {
    // data structure: { type, score, answers } or direct object
    const payload = data.type ? data : { type: 'PHQ-9', ...data }
    const response = await api.post('/assessment', payload)
    return response // return full response to access status etc
  },

  // 사용자 프로필 (위험도 포함) 조회
  getProfile: async () => {
    const response = await api.get('/user/profile')
    return response.data
  }
}
