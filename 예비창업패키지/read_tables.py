import docx
import sys

def read_docx(path):
    try:
        doc = docx.Document(path)
        print("--- Tables ---")
        for i, table in enumerate(doc.tables):
            print(f"Table {i}:")
            for row in table.rows:
                row_text = [cell.text.replace('\n', ' ') for cell in row.cells]
                print(" | ".join(row_text))
            print("-" * 20)
    except Exception as e:
        print(f"Error reading docx: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_docx(sys.argv[1])
