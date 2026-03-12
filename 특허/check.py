import docx
doc = docx.Document('특허출원명세서_마음온_AI.docx')
for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if text:
        print(f"[{i}] {text[:100]}")
