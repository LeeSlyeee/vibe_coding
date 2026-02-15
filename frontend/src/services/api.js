import axios from 'axios'

// [Fix] Point to 217 Backend (Flask) - remove /v1 mismatch
const API_BASE_URL = 'https://217.142.253.35.nip.io/api'

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터 - 인증 토큰 추가
api.interceptors.request.use(
  (config) => {
    // [Fix] User Web uses 'authToken', Admin Web uses 'access_token'. Support both!
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token') || localStorage.getItem('token');
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
    // 401 에러 발생 시 로그아웃 처리 (단, 로그인 요청 자체의 실패는 제외)
    // 또한, 이미 로그인 페이지에 있다면 리다이렉트(새로고침) 하지 않음
    if (error.response?.status === 401 && !error.config.url.includes('/login')) {
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('token'); // 호환성 유지
        window.location.href = '/login';
      }
    }
    return Promise.reject(error)
  }
)

// 인증 API
export const authAPI = {
  // 로그인
  login: async (username, password, centerCode = null) => {
    const response = await api.post('/login', { username, password, center_code: centerCode })
    return response.data
  },

  // 회원가입
  signup: async (username, password) => {
    const response = await api.post('/register', { username, password })
    return response.data
  },

  getUserInfo: async () => {
    const response = await api.get('/user/me')
    return response.data
  },

  // 유료 결제 (모의)
  upgradeAccount: async () => {
    const response = await api.post('/payment/upgrade')
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
      sleep_condition: data.sleep_condition || '', // 잠은 잘 주무셨나요? 
      emotion_desc: data.question2 || '', // 어떤 감정이 들었나요?
      emotion_meaning: data.question3 || '', // 마지막으로 더 깊게 자신의 감정을 써보세요.
      self_talk: data.question4 || '', // 나에게 따듯한 위로를 보내세요.
      mood_level: moodToLevel[data.mood] || 3, // 감정 이모지 (문자열 → 숫자 변환)
      weather: data.weather || null,
      temperature: data.temperature || null,
      
      // New Fields (UI Branching)
      mode: data.mode || 'green',
      mood_intensity: data.mood_intensity || 0,
      symptoms: data.symptoms || [],
      gratitude_note: data.gratitude_note || '',
      safety_flag: data.safety_flag || false
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
      sleep_condition: data.sleep_condition || '',
      emotion_desc: data.question2 || '',
      emotion_meaning: data.question3 || '',
      self_talk: data.question4 || '',
      mood_level: moodToLevel[data.mood] || 3, // 감정 이모지 (문자열 → 숫자 변환)
      weather: data.weather || null,
      temperature: data.temperature || null,
      
      // New Fields (UI Branching)
      mode: data.mode,
      mood_intensity: data.mood_intensity,
      symptoms: data.symptoms,
      gratitude_note: data.gratitude_note,
      gratitude_note: data.gratitude_note,
      safety_flag: data.safety_flag
    }
    // [Fix] Use POST instead of PUT to avoid CORS Preflight/Proxy issues on some networks
    const response = await api.post(`/diaries/${id}`, mappedData)
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
  },

  // 통계 조회
  getStatistics: async () => {
    const response = await api.get('/statistics')
    return response.data
  },

  // 일기 검색
  searchDiaries: async (query) => {
    const response = await api.get('/diaries/search', {
      params: { q: query }
    })
    return response.data
  },

  // 날씨 인사이트
  getWeatherInsight: async (weather, date = null) => {
    const params = { weather }
    if (date) params.date = date
    
    const response = await api.get('/weather-insight', { params })
    return response.data
  },

  // 작성 전 마음가짐 인사이트
  getMindsetInsight: async (date = null, weather = null) => {
    const params = {}
    if (date) params.date = date
    if (weather) params.weather = weather
    
    const response = await api.get('/insight', { params })
    return response.data
  },

  // 심층 리포트 생성 (비동기 시작)
  startReportGeneration: async () => {
    const response = await api.post('/report/start')
    return response.data
  },

  // 심층 리포트 상태 확인 (Polling)
  getReportStatus: async () => {
    const response = await api.get('/report/status')
    return response.data
  },

  // 장기 메타 분석 생성 (비동기 시작)
  startLongTermReportGeneration: async () => {
    const response = await api.post('/report/longterm/start')
    return response.data
  },

  // 장기 메타 분석 상태 확인 (Polling)
  getLongTermReportStatus: async () => {
    const response = await api.get('/report/longterm/status')
    return response.data
  },

  // 음성 받아쓰기 (Voice Diary)
  transcribeVoice: async (formData) => {
    // [Fix] 기본 api 인스턴스는 'Content-Type: application/json'이 강제되므로
    // Multipart 전송을 위해 순수 axios를 사용하여 전송합니다.
    const token = localStorage.getItem('authToken')
    const headers = {}
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    // axios가 FormData를 감지하면 자동으로 Content-Type: multipart/form-data; boundary=... 를 설정합니다.
    const response = await axios.post(`${API_BASE_URL}/voice/transcribe`, formData, {
      headers,
      withCredentials: true
    })
    return response.data
  }
}

export default api
