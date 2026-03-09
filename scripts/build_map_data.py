import urllib.request
import json
import re

url = "https://unpkg.com/@svg-maps/south-korea@1.0.1/index.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    content = response.read().decode('utf-8')

# Extract JSON from "export default {...}"
json_str = re.search(r'export default (\{.*\});?', content, re.DOTALL).group(1)
data = json.loads(json_str)

mapping = {
    "busan": "BUSAN",
    "daegu": "DAEGU",
    "daejeon": "DAEJEON",
    "gangwon": "GANGWON",
    "gwangju": "GWANGJU",
    "gyeonggi": "GYEONGGI",
    "incheon": "INCHEON",
    "jeju": "JEJU",
    "north-chungcheong": "CHUNGBUK",
    "north-gyeongsang": "GYEONGBUK",
    "north-jeolla": "JEONBUK",
    "sejong": "SEJONG",
    "seoul": "SEOUL",
    "south-chungcheong": "CHUNGNAM",
    "south-gyeongsang": "GYEONGNAM",
    "south-jeolla": "JEONNAM",
    "ulsan": "ULSAN"
}

# Calculated approximate center for labels based on viewBox 0 0 524 631
labels = {
    "SEOUL": {"x": 155, "y": 140, "fs": 9},
    "INCHEON": {"x": 115, "y": 145, "fs": 9},
    "GYEONGGI": {"x": 165, "y": 110, "fs": 10},
    "GANGWON": {"x": 280, "y": 90, "fs": 11},
    "CHUNGBUK": {"x": 210, "y": 190, "fs": 10},
    "SEJONG": {"x": 165, "y": 215, "fs": 7},
    "CHUNGNAM": {"x": 120, "y": 220, "fs": 10},
    "DAEJEON": {"x": 180, "y": 250, "fs": 8},
    "JEONBUK": {"x": 150, "y": 320, "fs": 10},
    "GWANGJU": {"x": 130, "y": 410, "fs": 8},
    "JEONNAM": {"x": 110, "y": 450, "fs": 10},
    "GYEONGBUK": {"x": 350, "y": 240, "fs": 11},
    "DAEGU": {"x": 330, "y": 340, "fs": 9},
    "ULSAN": {"x": 420, "y": 360, "fs": 8},
    "GYEONGNAM": {"x": 260, "y": 400, "fs": 11},
    "BUSAN": {"x": 400, "y": 410, "fs": 9},
    "JEJU": {"x": 110, "y": 600, "fs": 10}
}

output = [
    '// 자동 생성된 대한민국 시도 SVG 데이터',
    'export const VIEW_BOX = "0 0 524 631";',
    'export const KOREA_REGIONS = {'
]

for loc in data['locations']:
    code = mapping.get(loc['id'])
    if not code: continue
    
    lbl = labels.get(code, {"x": 0, "y": 0, "fs": 10})
    
    output.append(f'  {code}: {{')
    output.append(f'    name: "{loc["name"]}",')
    output.append(f'    path: "{loc["path"]}",')
    output.append(f'    labelX: {lbl["x"]}, labelY: {lbl["y"]}, fontSize: {lbl["fs"]}')
    output.append('  },')

output.append('};')

with open('frontend_admin/src/data/koreaMapData.js', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Successfully generated koreaMapData.js")
