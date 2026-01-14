# frontend

이 템플릿은 Vite 환경에서 Vue 3 개발을 시작하는 데 도움이 됩니다.

## 권장 IDE 설정

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (Vetur는 비활성화하세요).

## 권장 브라우저 설정

- Chromium 기반 브라우저 (Chrome, Edge, Brave 등):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Chrome DevTools에서 Custom Object Formatter 켜기](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Firefox DevTools에서 Custom Object Formatters 켜기](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## TS에서 `.vue` 임포트에 대한 타입 지원

TypeScript는 기본적으로 `.vue` 임포트에 대한 타입 정보를 처리할 수 없으므로, 타입 체크를 위해 `tsc` CLI 대신 `vue-tsc`를 사용합니다. 에디터에서는 TypeScript 언어 서비스가 `.vue` 타입을 인식할 수 있도록 [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar)가 필요합니다.

## 설정 사용자 정의

[Vite 설정 참조](https://vite.dev/config/)를 확인하세요.

## 프로젝트 설정

```sh
npm install
```

### 개발을 위한 컴파일 및 Hot-Reload

```sh
npm run dev
```

### 프로덕션을 위한 타입 체크, 컴파일 및 미니파이(Minify)

```sh
npm run build
```

### [Vitest](https://vitest.dev/)를 이용한 유닛 테스트 실행

```sh
npm run test:unit
```

### [Playwright](https://playwright.dev)를 이용한 E2E(End-to-End) 테스트 실행

```sh
# 첫 실행 시 브라우저 설치가 필요합니다
npx playwright install

# CI에서 테스트할 때는 먼저 프로젝트를 빌드해야 합니다
npm run build

# E2E 테스트 실행
npm run test:e2e
# Chromium에서만 테스트 실행
npm run test:e2e -- --project=chromium
# 특정 파일에 대한 테스트 실행
npm run test:e2e -- tests/example.spec.ts
# 디버그 모드로 테스트 실행
npm run test:e2e -- --debug
```

### [ESLint](https://eslint.org/)를 이용한 린트(Lint) 실행

```sh
npm run lint
```
