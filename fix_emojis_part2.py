import os

REPLACEMENTS = {
    'ios_app/MoodCalendarView.swift': [
        ('Text("🌉")', 'Image(systemName: "bridge").foregroundColor(.blue)'),
        ('잠시만 기다려주세요! 🚚 (약 5초)', '잠시만 기다려주세요! (약 5초)'),
        ('["", "😠", "😢", "😐", "😌", "😊"]', '["", "매우나쁨", "나쁨", "보통", "좋음", "매우좋음"]'),
        ('// [New] 약물 복용 표시 💊', '// [New] 약물 복용 표시')
    ],
    'ios_app/AppStatsView.swift': [
        ('["", "🤬", "😢", "😐", "😌", "🥰"]', '["", "매우나쁨", "나쁨", "보통", "좋음", "매우좋음"]')
    ],
    'ios_app/AppDiaryWriteView.swift': [
        ('["", "😠", "😢", "😐", "😌", "😊"]', '["", "매우나쁨", "나쁨", "보통", "좋음", "매우좋음"]'),
        ('.overlay(Text("🧘‍♀️").font(.largeTitle))', '.overlay(Image(systemName: "figure.mind.and.body").font(.largeTitle).foregroundColor(.blue))')
    ],
    'ios_app/SharedStatsView.swift': [
        ('case 1: return "🤬"', 'case 1: return "최악"'),
        ('case 2: return "😢"', 'case 2: return "나쁨"'),
        ('case 3: return "😐"', 'case 3: return "보통"'),
        ('case 4: return "😌"', 'case 4: return "좋음"'),
        ('case 5: return "🥰"', 'case 5: return "최고"')
    ],
    'ios_app/MindBridgeExportView.swift': [
        ('icon: "😊",', 'icon: "감정",'),
        ('icon: "🌡️",', 'icon: "온도",'),
        ('self.todayEmoji = (latest["emoji"] as? String) ?? "😊"', 'self.todayEmoji = (latest["mood_label"] as? String) ?? "보통"'),
        ('@Published var todayEmoji: String = "😊"', '@Published var todayEmoji: String = "보통"'),
        ('Text(viewModel.todayEmoji)\n                            .font(.system(size: 48))', 'Text(viewModel.todayEmoji)\n                            .font(.system(size: 32, weight: .bold))\n                            .foregroundColor(Color(hexString: "6366f1"))')
    ],
    'ios_app/WeeklyLetterView.swift': [
        ('안녕하세요, 마음온 AI에요 💌', '안녕하세요, 마음온 AI에요'),
        ('☕🎵', ''),
        ('👏', ''),
        ('🌿', '')
    ],
    'ios_app/AppChatView.swift': [
        ('Text("👋")', 'Image(systemName: "hand.wave.fill").foregroundColor(.yellow)'),
        ('오늘 하루 중 기억에 남는 순간이 있었나요? 🌡️', '오늘 하루 중 기억에 남는 순간이 있었나요?'),
        ('☁️ 서버 AI', '서버 AI'),
        ('📱 로컬 AI', '로컬 AI'),
        ('AI가 마음의 준비를 하고 있어요... 🌿', 'AI가 마음의 준비를 하고 있어요...'),
        ('거의 다 되었습니다! 잠시만요... 🏃', '거의 다 되었습니다! 잠시만요...'),
        ('Text("🏥 가까운 정신건강복지센터 찾기")', 'HStack { Image(systemName: "cross.case.fill"); Text("가까운 정신건강복지센터 찾기") }')
    ],
    'ios_app/AppMainTabView.swift': [
        ('Text("🎂")', 'Image(systemName: "birthday.cake.fill").foregroundColor(.pink)'),
        ('오늘 하루 세상에서 가장 행복한 사람이 되길 바랄게! 🎉', '오늘 하루 세상에서 가장 행복한 사람이 되길 바랄게!'),
        ('고마워! 😍', '고마워!'),
        ('Text("🎉")', 'Image(systemName: "party.popper.fill").foregroundColor(.orange)'),
        ('Text("오늘 생일! 🎂")', 'HStack { Image(systemName: "birthday.cake.fill"); Text("오늘 생일!") }'),
        ('Text("확인했어요! 💌")', 'Text("확인했어요!")')
    ],
    'ios_app/RelationalMapView.swift': [
        ('소중한 사람들이 주변을 밝히고 있어요 💛', '소중한 사람들이 주변을 밝히고 있어요.'),
        ('좋은 에너지를 주는 친구네요 🙌', '좋은 에너지를 주는 친구네요.'),
        ('마음을 나누는 관계인 것 같아요 🌿', '마음을 나누는 관계인 것 같아요.'),
        ('이번 주 특히 자주 등장했네요 💼', '이번 주 특히 자주 등장했네요.'),
        ('오랜만에 연락해보는 건 어떨까요? 💜', '오랜만에 연락해보는 건 어떨까요?'),
        ('산책 이야기가 기분을 밝게 해주고 있어요 🐾', '산책 이야기가 기분을 밝게 해주고 있어요.')
    ]
}

for path, replaces in REPLACEMENTS.items():
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for old, new in replaces:
            content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")
