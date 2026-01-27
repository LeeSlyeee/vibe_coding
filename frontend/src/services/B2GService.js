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

  // 기관 연결 시도 (Mock Logic)
  async connect(code) {
    return new Promise((resolve, reject) => {
      // 서버 통신 딜레이 시뮬레이션
      setTimeout(() => {
        const upperCode = code.toUpperCase().trim();

        // 유효성 검사 (시뮬레이션)
        if (!upperCode) {
          reject("코드를 입력해주세요.");
          return;
        }

        // 특정 접두어만 허용 (보안 코스프레)
        // SEOUL, TEST, CENTER로 시작하는 코드만 승인
        const validPrefixes = ["SEOUL", "TEST", "CENTER", "HOSPITAL"];
        const isValid = validPrefixes.some((prefix) => upperCode.startsWith(prefix));

        if (isValid) {
          // 연동 성공 저장
          localStorage.setItem(CARD_KEY, upperCode);
          localStorage.setItem(LINK_STATUS_KEY, "true");

          // 즉시 첫 동기화 실행
          this.syncData();

          resolve({
            success: true,
            message: "연동에 성공했습니다!\n이제 담당 선생님이 상태를 확인할 수 있습니다.",
          });
        } else {
          reject("유효하지 않은 기관 코드입니다.\n코드를 다시 확인해주세요.");
        }
      }, 1000); // 1초 딜레이
    });
  },

  // 연동 해제
  disconnect() {
    localStorage.removeItem(CARD_KEY);
    localStorage.removeItem(LINK_STATUS_KEY);
    localStorage.removeItem(LAST_SYNC_KEY);
    console.log("🔗 [B2G] 연동 해제 완료");
  },

  // 백그라운드 데이터 동기화 시뮬레이션
  syncData() {
    if (!this.isLinked()) return;

    console.log("🔄 [B2G] 보건소 서버로 데이터 전송 시작...");

    // 타임스탬프 갱신
    const now = new Date().toISOString();
    localStorage.setItem(LAST_SYNC_KEY, now);

    // 실제로는 여기서 axios.postWithCrypto(...) 등을 호출
    setTimeout(() => {
      console.log(`✅ [B2G Sync] Data sent to center: ${this.getCenterCode()}`);
    }, 500);
  },
};
