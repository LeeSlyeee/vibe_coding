import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('region_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('region_token')
      window.location.href = '/region/'
    }
    return Promise.reject(err)
  }
)

export default {
  login(username, password) {
    return api.post('/auth/login/', { username, password })
  },
  getMe() {
    return api.get('/admin/me/')
  },
  getRegionDashboard(regionId) {
    return api.get(`/admin/regions/${regionId}/dashboard/`)
  },
  getRegionCenters(regionId) {
    return api.get(`/admin/regions/${regionId}/centers/`)
  },
  getRegionStaff(regionId) {
    return api.get(`/admin/regions/${regionId}/staff/`)
  },
  exportRegionCSV(regionId) {
    return api.get(`/admin/export/region/${regionId}/`, { responseType: 'blob' })
  },
  reassignStaff(staffId, targetCenterId) {
    return api.post('/admin/staff/reassign/', { staff_id: staffId, target_center_id: targetCenterId })
  },
}
