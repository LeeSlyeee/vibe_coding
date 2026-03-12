from bs4 import BeautifulSoup
import re

html_path = '특허명세서_v2_마음온_AI_하이브리드_심리케어시스템.html'

with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

claims = []
claims_h2 = soup.find('h2', string=re.compile(r'특허청구의 범위|청구범위|특허청구범위'))
if claims_h2:
    curr = claims_h2.find_next_sibling()
    while curr and curr.name not in ['h1', 'h2']:
        if curr.name == 'div' and 'claim' in curr.get('class', []):
            claim_text_div = curr.find_next_sibling('div', class_='claim-text')
            if claim_text_div:
                claim_num = curr.get_text(separator=' ', strip=True)
                for br in claim_text_div.find_all('br'):
                    br.replace_with('\n')
                raw_body = claim_text_div.get_text()
                body_lines = [line.strip() for line in raw_body.split('\n') if line.strip()]
                claims.append((claim_num, body_lines))
        curr = curr.find_next_sibling()

for c_num, lines in claims:
    print(f"--- {c_num} ---")
    for i, l in enumerate(lines):
        print(f"L{i}: {l}")

