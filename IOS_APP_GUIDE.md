# 📱 iOS 앱 개발/배포 가이드 (Capacitor)

이 가이드는 현재 웹 프로젝트를 iPhone 앱으로 변환하여 실행하는 방법을 설명합니다.

---

## 1. 사전 준비 (Mac 필수)

1.  **Xcode 설치**: App Store에서 Xcode를 최신 버전으로 설치해야 합니다.
2.  **CocoaPods 설치**: iOS 라이브러리 관리 도구입니다.
    ```bash
    sudo gem install cocoapods
    ```

---

## 2. API 주소 설정 (중요!) ⚠️

앱은 `localhost`가 아닌 **실제 서버 주소**를 바라봐야 합니다.
OCI 서버의 공인 IP가 필요합니다.

1.  `frontend/.env.production` 파일을 생성합니다.
2.  아래 내용을 입력하세요. (IP는 본인의 OCI 공인 IP로 변경)

    ```ini
    VITE_API_URL=http://<OCI_SERVER_IP>
    ```

    _(예: `VITE_API_URL=http://123.45.67.89`)_

3.  앱을 위해 다시 빌드합니다.
    ```bash
    cd frontend
    npm run build
    npx cap sync
    ```

---

## 3. iOS 프로젝트 실행하기

터미널에서 아래 명령어를 입력하여 Xcode를 실행합니다.

```bash
cd frontend
npx cap open ios
```

- 만약 `npx cap open ios`가 에러가 난다면, Finder에서 `frontend/ios/App/App.xcworkspace` (흰색 아이콘) 파일을 더블클릭해서 여세요.
  - _주의: `.xcworkspace` 파일이 없다면 `frontend/ios/App` 폴더 안에서 `pod install` 명령어를 실행해야 할 수도 있습니다._

---

## 4. Xcode에서 실행

1.  Xcode 좌측 상단에서 **App > iPhone 16 Pro** (또는 원하는 시뮬레이터)를 선택합니다.
2.  **▶ (Play 버튼)**을 누르세요.
3.  시뮬레이터가 켜지고 앱이 실행됩니다!

---

## 5. 자주 발생하는 에러

### Q. 화면이 하얗게 나오거나 데이터가 안 떠요.

- **API 주소** 문제입니다. 위 '2. API 주소 설정'을 다시 확인하세요.
- `frontend/src/services/api.js` 파일에서 `const API_BASE_URL`이 `/api`로 고정되어 있다면 앱에서는 작동하지 않습니다. 이 부분을 환경변수를 쓰도록 수정해야 합니다. (이미 수정되어 있다면 패스)

### Q. 'pod install' 에러가 나요.

- 터미널에서 `cd frontend/ios/App` 이동 후 `pod install`을 직접 입력해보세요.
- CocoaPods가 설치되어 있지 않다면 `sudo gem install cocoapods`를 실행하세요.

---

## 6. 앱 수정 팁

Vue 코드를 수정하고 앱에 반영하려면?

```bash
# 1. Vue 코드 수정
# 2. 빌드
cd frontend
npm run build

# 3. 앱으로 복사 (Sync)
npx cap sync
```

이후 Xcode에서 다시 실행(Cmd + R)하면 됩니다.
