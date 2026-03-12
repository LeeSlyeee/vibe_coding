from bs4 import BeautifulSoup
import re

html_path = '특허명세서_v2_마음온_AI_하이브리드_심리케어시스템.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace all <br> variations with newline characters before parsing to avoid DOM destruction
html = re.sub(r'<br\s*/?>', '\n', html)
soup = BeautifulSoup(html, 'html.parser')

claims_h2 = soup.find('h2', string=re.compile(r'특허청구의 범위|청구범위|특허청구범위'))
curr = claims_h2.find_next_sibling()
while curr and curr.name not in ['h1', 'h2']:
    if curr.name == 'div' and 'claim' in curr.get('class', []):
        claim_text_div = curr.find_next_sibling('div', class_='claim-text')
        print("CLAIMS FOUND:", curr.get_text())
        if claim_text_div:
            # simply get text, newlines are already in text nodes!
            raw_body = claim_text_div.get_text()
            body_lines = [line.strip() for line in raw_body.split('\n') if line.strip()]
            for b in body_lines:
                print("  - [", b, "]")
    curr = curr.find_next_sibling()
