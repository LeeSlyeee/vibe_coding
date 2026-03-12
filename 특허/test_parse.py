import docx
from bs4 import BeautifulSoup
import re

html_path = '특허명세서_v2_마음온_AI_하이브리드_심리케어시스템.html'

with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

def get_text_for_heading(heading_text):
    heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and heading_text in tag.get_text())
    if not heading:
        return ["NOT FOUND"]
    print("Found heading:", heading)
    texts = []
    curr = heading.find_next_sibling()
    while curr and curr.name not in ['h1', 'h2', 'h3']:
        if curr.name in ['p', 'ul', 'ol', 'div']:
            text = curr.get_text(separator=' ', strip=True)
            if text:
                texts.append(text)
        curr = curr.find_next_sibling()
    return texts

print("과제:", get_text_for_heading('해결하고자 하는 과제'))
print("수단:", get_text_for_heading('과제의 해결 수단'))
print("효과:", get_text_for_heading('발명의 효과'))

# For Claims:
claims = []
claims_h2 = soup.find('h2', string=re.compile(r'특허청구의 범위|청구범위|청구 범위'))
print("Claims H2:", claims_h2)

