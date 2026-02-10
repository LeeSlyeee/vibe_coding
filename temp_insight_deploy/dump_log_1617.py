import ast
import os

def run():
    log_path = '/home/ubuntu/InsightMind/request_log.txt'
    if not os.path.exists(log_path): return

    lines = open(log_path).readlines()
    
    print("--- RAW LOG DUMP for Jan 16-17 ---")
    for line in lines:
        if 'mood_metrics' in line:
            try:
                start = line.find('{')
                payload = ast.literal_eval(line[start:].strip())
                metrics = payload.get('mood_metrics', [])
                for item in metrics:
                    d_str = item.get('created_at') or item.get('date')
                    if not d_str: continue
                    if '2026-01-16' in d_str or '2026-01-17' in d_str:
                        print(f"Date: {d_str}")
                        print(f"Keys: {list(item.keys())}")
                        print(f"Values: {item}")
                        print("-" * 20)
            except:
                continue

run()
