import axios from 'axios'

const API_BASE = import.meta.env.PROD
  ? '/api/v1'
  : '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
})

// JWT 인터셉터
api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/admin/'
    }
    return Promise.reject(err)
  }
)

export default {
  // Auth
  login(username, password) {
    return api.post('/auth/login/', { username, password })
  },

  // Admin Info
  getMe() {
    return api.get('/admin/me/')
  },

  // L4: National
  getNationalSummary() {
    return api.get('/admin/national/summary/')
  },

  // L4: Regions CRUD
  getRegions() {
    return api.get('/admin/regions/')
  },
  getRegionDetail(id) {
    return api.get(`/admin/regions/${id}/`)
  },
  updateRegion(id, data) {
    return api.put(`/admin/regions/${id}/`, data)
  },

  // L3: Region Dashboard
  getRegionDashboard(regionId) {
    return api.get(`/admin/regions/${regionId}/dashboard/`)
  },
  getRegionCenters(regionId) {
    return api.get(`/admin/regions/${regionId}/centers/`)
  },
  getRegionStaff(regionId) {
    return api.get(`/admin/regions/${regionId}/staff/`)
  },

  // PolicyBroadcast
  getBroadcasts(level) {
    const params = level ? { level } : {}
    return api.get('/admin/broadcasts/', { params })
  },
  createBroadcast(data) {
    return api.post('/admin/broadcasts/', data)
  },
  deleteBroadcast(id) {
    return api.delete(`/admin/broadcasts/${id}/`)
  },

  // Export
  exportNationalCSV() {
    return api.get('/admin/export/national/', { responseType: 'blob' })
  },
  exportRegionCSV(regionId) {
    return api.get(`/admin/export/region/${regionId}/`, { responseType: 'blob' })
  },

  // Centers
  getCenters() {
    return api.get('/admin/centers/')
  },

  // Staff
  getStaff() {
    return api.get('/admin/staff/')
  },

  // Alerts (실시간 알림)
  getAlerts() {
    return api.get('/admin/alerts/')
  },
  markAlertRead(alertId) {
    return api.post('/admin/alerts/', { alert_id: alertId })
  },
  markAllAlertsRead() {
    return api.post('/admin/alerts/', { alert_id: 'all' })
  },

  // Audit Logs (감사 로그)
  getAuditLogs(days = 7) {
    return api.get('/admin/audit-logs/', { params: { days } })
  },

  // 2FA
  verify2FA(pin) {
    return api.post('/admin/2fa/', { pin })
  },
  setup2FA(pin) {
    return api.put('/admin/2fa/', { pin })
  },
}
