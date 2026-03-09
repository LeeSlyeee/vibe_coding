# ☁️ Oracle Cloud (Ubuntu 24.04 ARM) 배포 가이드

오라클 클라우드(Always Free) ARM 인스턴스에 프로젝트를 배포하는 단계별 가이드입니다.

---

## 1. 서버 기본 설정 (SSH 접속 후)

가장 먼저 패키지 목록을 업데이트하고 필요한 필수 프로그램을 설치합니다.

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. 필수 패키지 설치 (Python, pip, venv, git, nginx, mariadb, ffmpeg)
sudo apt install -y python3-pip python3-venv git nginx mariadb-server libmysqlclient-dev pkg-config ffmpeg

# 3. Timezone 한국으로 변경 (선택)
sudo timedatectl set-timezone Asia/Seoul
```

---

## 2. 프로젝트 코드 가져오기

GitHub를 통해 코드를 가져오거나, 로컬에서 `scp`로 파일을 전송할 수 있습니다. 여기서는 GitHub 권장 방식을 사용합니다.

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 클론 (본인의 레포지토리 주소로 변경)
git clone https://github.com/LeeSlyeee/vibe_coding.git

# 폴더명 변경 (편의상 project로 통칭)
mv vibe_coding project
cd project
```

---

## 3. 백엔드 설정 (Backend)

### 3-1. 가상환경 생성 및 패키지 설치

```bash
cd ~/project/backend

# 가상환경 생성 (.venv)
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치 (requirements.txt 필요)
# * ARM 서버에서는 설치 시간이 좀 걸릴 수 있습니다.
pip install -r requirements.txt
```

### 3-2. 데이터베이스 설정

```bash
# MariaDB 접속 (root 권한)
sudo mariadb

# --- DB SQL 실행 시작 ---
CREATE DATABASE mood_diary CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'slyeee'@'localhost' IDENTIFIED BY '비밀번호입력';
GRANT ALL PRIVILEGES ON mood_diary.* TO 'slyeee'@'localhost';
FLUSH PRIVILEGES;
EXIT;
# --- DB SQL 실행 끝 ---
```

### 3-3. 환경 변수 설정

`config.py`가 환경변수를 읽도록 설정되어 있으므로 `.env` 파일을 생성하거나 직접 수정합니다.

```bash
# backend/config.py 수정 (또는 export 사용)
# DB 주소를 위에서 만든 계정으로 변경:
# mysql+pymysql://slyeee:비밀번호입력@localhost/mood_diary
```

### 3-4. 초기 DB 생성

```bash
# 테이블 생성 명령 실행
python create_db.py
# 또는
flask db upgrade
```

---

## 4. 프론트엔드 설정 (Frontend)

Ubuntu 기본 Node.js는 버전이 낮을 수 있으므로 NVM(Node Version Manager)을 설치해 최신 버전을 씁니다.

### 4-1. Node.js 설치 (v20 LTS 권장)

```bash
# NVM 설치
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 터미널 재시작 없이 적용
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Node.js 설치
nvm install 20
node -v  # 버전 확인
```

### 4-2. 빌드 (Build)

```bash
cd ~/project/frontend

# 의존성 설치
npm install

# 프로덕션 빌드 (결과물은 dist 폴더에 생김)
npm run build
```

---

## 5. 배포 연결 (Nginx)

Nginx를 이용해 인터넷 요청을 처리합니다.

- `/` 요청은 → 프론트엔드(`dist/index.html`) 보여주기
- `/api` 요청은 → 백엔드(`localhost:5000`)로 토스하기

### 5-1. 설정 파일 작성

```bash
sudo nano /etc/nginx/sites-available/mood_diary
```

**[편집기 내용 붙여넣기]**

```nginx
server {
    listen 80;
    server_name _;  # 나중에 도메인이 생기면 도메인 입력

    # 1. 프론트엔드 (정적 파일)
    location / {
        root /home/ubuntu/project/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 2. 백엔드 API (프록시)
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

_(주의: `/home/ubuntu` 부분은 오라클 기본 계정명입니다. 본인 계정이 `opc`라면 경로를 수정하세요)_

### 5-2. 활성화 및 재시작

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/mood_diary /etc/nginx/sites-enabled/

# 기본 설정 끄기 (충돌 방지)
sudo rm /etc/nginx/sites-enabled/default

# 문법 검사 & 재시작
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. 백그라운드 실행 (Gunicorn / Systemd)

SSH를 꺼도 서버가 죽지 않게 하려면 서비스를 등록해야 합니다.

### 6-1. 서비스 파일 생성

```bash
sudo nano /etc/systemd/system/mood_backend.service
```

**[내용 붙여넣기]**

```ini
[Unit]
Description=Mood Diary Backend
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/project/backend
Environment="PATH=/home/ubuntu/project/backend/.venv/bin"
ExecStart=/home/ubuntu/project/backend/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5001 app:app

[Install]
WantedBy=multi-user.target
```

### 6-2. 서비스 시작

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl start mood_backend
sudo systemctl enable mood_backend

# 상태 확인
sudo systemctl status mood_backend
```

---

## ✅ 설치 완료!

이제 인터넷 창을 켜고 오라클 클라우드 인스턴스의 **공인 IP 주소**로 접속해보세요.
웹사이트가 뜨고 로그인이 된다면 성공입니다.

### 💡 문제 발생 시 체크리스트

1. **오라클 방화벽(Security List)**: 클라우드 콘솔 웹페이지에서 `Ingress Rules`에 **80번 포트(HTTP)**가 열려 있는지 꼭 확인하세요.
2. **우분투 방화벽**: `sudo iptables -F` (임시)로 방화벽을 꺼보고 되면, `netfilter-persistent`로 포트를 열어야 합니다.

---

## 7. 업데이트 방법 (유지보수)

코드를 수정하고 다시 배포해야 할 때 사용하세요.

```bash
# 1. 프로젝트 폴더로 이동
cd ~/project

# 2. 최신 코드 가져오기
git pull

# 3. 프론트엔드 다시 빌드 (화면 수정 시 필수)
cd ~/project/frontend
npm install
npm run build

# 4. 백엔드 재시작 (API 수정 시 필수)
sudo systemctl restart mood_backend
```
