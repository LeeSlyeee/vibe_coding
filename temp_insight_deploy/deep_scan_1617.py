import ast
import os

def run():
    log_path = '/home/ubuntu/InsightMind/request_log.txt'
    if not os.path.exists(log_path): return

    lines = open(log_path).readlines()
    
    print("--- DEEP SCAN for Jan 16 & 17 (All Versions) ---")
    
    unique_contents = set()

    for line in lines:
        if 'mood_metrics' in line:
            try:
                # Naive parse to find date
                if "'date': '2026-01-16'" in line or "'date': '2026-01-17'" in line:
                    start = line.find('{')
                    payload = ast.literal_eval(line[start:].strip())
                    metrics = payload.get('mood_metrics', [])
                    for item in metrics:
                        d = item.get('date')
                        if d in ['2026-01-16', '2026-01-17']:
                            content = item.get('event', '') or item.get('content', '')
                            signature = f"Date: {d} | Content: {content[:30]}..."
                            if signature not in unique_contents:
                                print(f"FOUND: {signature}")
                                print(f"   Full Content: {content}")
                                print(f"   AI Comment: {item.get('ai_comment', '')[:30]}...")
                                print("-" * 20)
                                unique_contents.add(signature)
            except:
                continue

run()
