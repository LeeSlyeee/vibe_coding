import { authAPI } from './api';

const CARD_KEY = "b2g_center_code";
const LINK_STATUS_KEY = "b2g_is_linked";
const LAST_SYNC_KEY = "b2g_last_sync";

export const B2GService = {
  // 상태 확인
  isLinked() {
    return localStorage.getItem(LINK_STATUS_KEY) === "true";
  },

  getCenterCode() {
    return localStorage.getItem(CARD_KEY) || "";
  },

  getLastSyncDate() {
    return localStorage.getItem(LAST_SYNC_KEY);
  },

  // 기관 연결 시도 (Real Server Logic)
  async connect(code) {
    try {
        console.log(`🔗 [B2G] Connecting to server with code: ${code}`);
        
        // 실제 서버 API 호출
        // 백엔드 엔드포인트: /centers/verify-code/
        const response = await authAPI.post('/centers/verify-code/', { 
            center_code: code,
            // 닉네임이 있다면 함께 전송하여 유저 매핑 시도
            user_nickname: localStorage.getItem('user_nickname') || 'Guest'
        });

        const data = response.data;

        if (data.valid) {
             // 연동 성공 저장
             // 화면에 표시할 코드는 입력한 코드 그대로 사용
             localStorage.setItem(CARD_KEY, code.toUpperCase()); 
             localStorage.setItem(LINK_STATUS_KEY, "true");
             
             // 즉시 첫 동기화 실행 (비동기)
             this.syncData();
             
             return {
                 success: true,
                 message: data.message || "연동에 성공했습니다!\n이제 담당 선생님이 상태를 확인할 수 있습니다."
             };
        } else {
            // valid: false인 경우
            throw data.error || "유효하지 않은 코드입니다.";
        }
    } catch (error) {
        console.error("❌ [B2G] Connect Error:", error);
        // 에러 메시지 추출
        let serverMsg = "알 수 없는 오류가 발생했습니다.";
        if (error.response && error.response.data && error.response.data.error) {
            serverMsg = error.response.data.error;
        } else if (typeof error === 'string') {
            serverMsg = error;
        } else if (error.message) {
            serverMsg = error.message;
        }
        
        throw serverMsg; // UI 컴포넌트로 에러 전파
    }
  },

  // 연동 해제
  disconnect() {
    localStorage.removeItem(CARD_KEY);
    localStorage.removeItem(LINK_STATUS_KEY);
    localStorage.removeItem(LAST_SYNC_KEY);
    console.log("🔗 [B2G] 연동 해제 완료");
  },

  // 백그라운드 데이터 동기화 (서버 Push)
  async syncData() {
    if (!this.isLinked()) return;

    console.log("🔄 [B2G] 보건소 서버로 데이터 동기화 시도...");
    
    try {
        const lastSync = this.getLastSyncDate();
        const centerCode = this.getCenterCode();

        // 서버에 동기화 상태 확인 및 데이터 푸시
        const response = await authAPI.get('/centers/sync-data/', {
            params: {
                action: 'check_link',
                center_code: centerCode,
                user_nickname: localStorage.getItem('userNickname') || localStorage.getItem('user_nickname') || 'Guest',
                last_sync: lastSync || ''
            }
        });

        if (response.data?.linked) {
            console.log("✅ [B2G Sync] 서버 연동 확인됨");
        }

        // 동기화 시간 갱신
        const now = new Date().toISOString();
        localStorage.setItem(LAST_SYNC_KEY, now);
        console.log("✅ [B2G Sync] 동기화 완료:", now);
    } catch (e) {
        console.error("❌ [B2G Sync] Error:", e.response?.status, e.message);
    }
  },
};
