import axios from 'axios'

// API 베이스 URL 설정
// API 베이스 URL 설정
// 환경변수가 없으면 현재 브라우저의 호스트명 + 5001 포트 사용 (배포 환경 대응)
const API_BASE_URL = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:5001/api`

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터 - 인증 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 인증 API
export const authAPI = {
  // 로그인
  login: async (username, password) => {
    const response = await api.post('/login', { username, password })
    return response.data
  },

  // 회원가입
  signup: async (username, password) => {
    const response = await api.post('/register', { username, password })
    return response.data
  }
}

// 일기 API
export const diaryAPI = {
  // 모든 일기 가져오기 (월별)
  getDiaries: async (year, month) => {
    const response = await api.get('/diaries', {
      params: { year, month }
    })
    return response.data
  },

  // 특정 일기 가져오기
  getDiary: async (id) => {
    const response = await api.get(`/diaries/${id}`)
    return response.data
  },

  // 날짜별 일기 가져오기
  getDiaryByDate: async (date) => {
    const response = await api.get(`/diaries/date/${date}`)
    return response.data
  },

  // 일기 생성
  createDiary: async (data) => {
    // mood 문자열을 mood_level 숫자로 변환
    const moodToLevel = {
      'angry': 1,
      'sad': 2,
      'neutral': 3,
      'calm': 4,
      'happy': 5
    }
    
    // 프론트엔드 필드 → 백엔드 필드 매핑
    const mappedData = {
      created_at: data.date, // 날짜
      event: data.question1 || '', // 오늘 무슨일이 있었나요?
      emotion_desc: data.question2 || '', // 어떤 감정이 들었나요?
      emotion_meaning: data.question3 || '', // 마지막으로 더 깊게 자신의 감정을 써보세요.
      self_talk: data.question4 || '', // 나에게 따듯한 위로를 보내세요.
      mood_level: moodToLevel[data.mood] || 3 // 감정 이모지 (문자열 → 숫자 변환)
    }
    const response = await api.post('/diaries', mappedData)
    return response.data
  },

  // 일기 수정
  updateDiary: async (id, data) => {
    // mood 문자열을 mood_level 숫자로 변환
    const moodToLevel = {
      'angry': 1,
      'sad': 2,
      'neutral': 3,
      'calm': 4,
      'happy': 5
    }
    
    // 프론트엔드 필드 → 백엔드 필드 매핑
    const mappedData = {
      event: data.question1 || '',
      emotion_desc: data.question2 || '',
      emotion_meaning: data.question3 || '',
      self_talk: data.question4 || '',
      mood_level: moodToLevel[data.mood] || 3 // 감정 이모지 (문자열 → 숫자 변환)
    }
    const response = await api.put(`/diaries/${id}`, mappedData)
    return response.data
  },

  // 일기 삭제
  deleteDiary: async (id) => {
    const response = await api.delete(`/diaries/${id}`)
    return response.data
  },

  // Task 상태 조회
  getTaskStatus: async (taskId) => {
    const response = await api.get(`/tasks/status/${taskId}`)
    return response.data
  }
}

export default api
