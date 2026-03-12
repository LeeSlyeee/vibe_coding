from bs4 import BeautifulSoup

html_path = '특허명세서_v2_마음온_AI_하이브리드_심리케어시스템.html'
with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

claims_h2 = soup.find('h2', string=lambda t: t and ('특허청구의 범위' in t or '청구범위' in t or '특허청구범위' in t))
curr = claims_h2.find_next_sibling()
while curr and curr.name not in ['h1', 'h2']:
    if curr.name == 'div' and 'claim' in curr.get('class', []):
        claim_text_div = curr.find_next_sibling('div', class_='claim-text')
        print("CLAIMS FOUND:", curr.get_text())
        if claim_text_div:
            # try get_text with separator instead of replace_with
            raw_body = claim_text_div.get_text(separator='\n')
            print("BODY:", repr(raw_body)[:100])
    curr = curr.find_next_sibling()
