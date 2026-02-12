import sys

def check_parentheses(file_path):
    print(f"Checking {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        stack = []
        lines = content.splitlines()
        
        # Line number tracking
        current_line = 1
        current_col = 0
        
        for char in content:
            current_col += 1
            if char == '\n':
                current_line += 1
                current_col = 0
                continue
                
            if char in '{[(':
                stack.append((char, current_line, current_col))
            elif char in '}])':
                if not stack:
                    print(f"Error: Unmatched '{char}' at line {current_line}, col {current_col}")
                    return

                top, line_num, col = stack.pop()
                expected_close = '}' if top == '{' else (']' if top == '[' else ')')
                if char != expected_close:
                    print(f"Error: Mismatched '{char}' at line {current_line}, col {current_col} (expected '{expected_close}' for '{top}' from line {line_num}, col {col})")
                    return

        if stack:
            top, line_num, col = stack[-1]
            print(f"Error: Unclosed '{top}' from line {line_num}, col {col}")
        else:
            print("SUCCESS: Parentheses are balanced.")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_parentheses(sys.argv[1])
    else:
        print("Usage: python3 check_parentheses.py <file_path>")
