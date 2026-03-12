from bs4 import BeautifulSoup
import re

html_path = '특허명세서_v2_마음온_AI_하이브리드_심리케어시스템.html'

with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

claims_h2 = soup.find('h2', string=re.compile(r'특허청구의 범위|청구범위|특허청구범위'))
if claims_h2:
    curr = claims_h2.find_next_sibling()
    while curr and curr.name not in ['h1', 'h2']:
        if curr.name == 'div':
            print("DIV class:", curr.get('class'))
            if curr.get('class') == ['claim-text']:
                print("RAW TEXT IN claim-text:", repr(curr.encode_contents().decode('utf-8'))[:200])
        curr = curr.find_next_sibling()
