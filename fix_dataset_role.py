import json

def fix_jsonl(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            data = json.loads(line)
            messages = data['messages']
            
            new_messages = []
            system_content = ""
            
            # Extract system message content
            for msg in messages:
                if msg['role'] == 'system':
                    system_content = msg['content']
                elif msg['role'] == 'user':
                    # Prepend system content to the first user message
                    if system_content:
                        new_content = f"{system_content}\n\n사용자: {msg['content']}"
                        new_messages.append({"role": "user", "content": new_content})
                        system_content = "" # Clear after use
                    else:
                        new_messages.append(msg)
                else:
                    new_messages.append(msg)
            
            json.dump({"messages": new_messages}, f_out, ensure_ascii=False)
            f_out.write('\n')

    print(f"Fixed {input_file} -> {output_file}")

if __name__ == "__main__":
    fix_jsonl('data/final_train.jsonl', 'data/final_train_fixed.jsonl')
    fix_jsonl('data/final_valid.jsonl', 'data/final_valid_fixed.jsonl')
