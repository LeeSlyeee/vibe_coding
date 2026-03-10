import os
import re

def has_emoji(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA70-\U0001FAFF"  # more symbols
        u"\u2600-\u26FF"          # misc symbols
        u"\u2700-\u27BF"          # dingbats
        "]+", flags=re.UNICODE)
    return emoji_pattern.search(text) is not None

def extract_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA70-\U0001FAFF"
        u"\u2600-\u26FF"
        u"\u2700-\u27BF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.findall(text)

source_dir = 'ios_app'
for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file.endswith('.swift'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    emojis = extract_emojis(content)
                    if emojis:
                        unique_emojis = list(set(emojis))
                        print(f"{path}: {' '.join(unique_emojis)}")
            except Exception as e:
                pass
