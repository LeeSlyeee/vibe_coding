from bs4 import BeautifulSoup

html = """
        <div class="claim-text">
          제 1항에 있어서,<br />
          상기 (d) 단계의 하이브리드 라우팅 제어 모듈(150)은, <br />
          상기 응답 텍스트의 민감도 스코어(Ssens)가 기 설정된 민감도 임계치(Tsens) 이상이거나,
          네트워크 접속이 차단된(Offline) 오프라인 상태인 경우,
          상기 입력 텍스트 및 그에 따른 추론 데이터를 외부 서버로 전송하지 않고
          <strong>상기 제1 AI 모델(160)에 의해서만 온디바이스에서 단독 인지 재구성(Cognitive Restructuring) 피드백이 생성되도록</strong>
          강제 라우팅(Forced On-Device Routing)하는 것을 특징으로 하는 제어 방법.
        </div>
"""

soup = BeautifulSoup(html, 'html.parser')
claim_text_div = soup.find('div', class_='claim-text')
for br in claim_text_div.find_all('br'):
    br.replace_with('\n')

raw_body = claim_text_div.get_text()
print("RAW:", repr(raw_body))
