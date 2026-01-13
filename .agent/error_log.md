# 감정일기 프로젝트 개발 오류 로그

이 문서는 프로젝트 개발 과정에서 발생한 주요 오류들과 그 해결 과정을 기록합니다.

## 1. 프론트엔드 설정 파일 누락 (Frontend Configuration Missing)

- **증상**: `npm run dev` 실행 시 `npm error code ENOENT`, `Could not read package.json` 오류 발생.
- **원인**: `frontend` 폴더 내에 `package.json`, `vite.config.ts`, `index.html` 등의 필수 설정 파일들이 존재하지 않음.
- **해결**:
  - `package.json` 생성 (Vue + TypeScript + Pinia + Axios + Tailwind).
  - `vite.config.ts` 생성 및 프록시 설정.
  - `index.html`, `tsconfig.json` 파일 등 생성.
  - `npm install`로 의존성 설치.

## 2. 모듈 의존성 및 CSS 설정 오류

- **증상**:
  - `Failed to resolve import "lucide-vue-next"` 로 인한 빌드 에러.
  - `style.css`에서 `Unknown word "use strict"` (PostCSS 오류).
- **원인**:
  - `lucide-vue-next` 패키지 미설치.
  - `style.css`에서 `@import "tailwindcss";` 구문 사용 시 특정 환경에서 PostCSS 파싱 오류 발생.
- **해결**:
  - `npm install lucide-vue-next` 실행.
  - `style.css`를 `@tailwind base; @tailwind components; @tailwind utilities;` 형식으로 변경.

## 3. 로그인 API 404 및 CORS 오류

- **증상**: 로그인 시도 시 콘솔에 CORS 관련 오류 또는 404 Not Found 발생.
- **원인**: 백엔드(`app.py`)에 `/api/login` 라우트가 구현되어 있지 않음.
- **해결**: `app.py`에 `/api/login` 엔드포인트를 추가하고 간단한 모의(Mock) 인증 로직 구현 (`testuser`/`password123`).

## 4. 백엔드 연결 로그 누락 (Localhost vs 127.0.0.1)

- **증상**: 프론트엔드에서 API 요청을 보냈으나, 백엔드(`python app.py`) 터미널에 아무런 로그가 찍히지 않음 (연결 실패).
- **원인**:
  - Node.js(Vite)는 `localhost`를 IPv6 `::1`로 해석하여 요청.
  - Flask는 IPv4 `127.0.0.1`에서만 수신 대기.
  - 이로 인해 네트워크 연결이 성립되지 않음.
- **해결**: `vite.config.ts`의 `server.proxy` 타겟을 `http://localhost:5000`에서 `http://127.0.0.1:5000`으로 명시적 변경.

## 5. Tailwind CSS PostCSS 플러그인 호환성 오류

- **증상**: Vite 실행 시 `[postcss] It looks like you're trying to use tailwindcss directly as a PostCSS plugin...` 오류 발생.
- **원인**: 최신 Tailwind CSS(v4 또는 특정 v3 버전)는 PostCSS와 통합될 때 `tailwindcss` 대신 `@tailwindcss/postcss` 패키지를 사용해야 함.
- **해결**:
  - `npm install @tailwindcss/postcss` 설치.
  - `postcss.config.js`의 plugins 항목을 `tailwindcss` -> `@tailwindcss/postcss`로 변경.

## 6. Pinia 초기화 누락 (화면 백지 현상)

- **증상**: 브라우저 화면이 하얗게 나오며 아무것도 렌더링되지 않음. 콘솔에 `[Vue warn]: Unhandled error during execution of setup function` 경고 발생.
- **원인**: `App.vue`에서 `useAuthStore()`를 호출하여 Pinia 스토어를 사용하려 했으나, `main.ts`에서 `app.use(createPinia())`가 호출되지 않아 Pinia 인스턴스가 없는 상태였음.
- **해결**: `main.ts`에 `createPinia`를 import하고 `app.use()`로 플러그인을 등록하여 해결.
