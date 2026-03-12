import docx
doc = docx.Document('특허출원명세서_마음온_AI.docx')
found = False
for p in doc.paragraphs:
    if '【청구항 5】' in p.text:
        found = True
    if found:
        print(f"-> {p.text}")
    if found and '【청구항 6】' in p.text:
        break
