import os

REPLACEMENTS = {
    'ios_app/AppEmergencyView.swift': [
        ('icon: "🏥",', 'icon: "",'),
        ('icon: "👮",', 'icon: "",'),
        ('Text("🔍")', 'Image(systemName: "magnifyingglass")'),
        ('.navigationTitle("🚨 긴급 도움")', '.navigationTitle("긴급 도움")')
    ],
    'ios_app/AppChatView.swift': [
        ('님! 👋', '님!'),
    ],
    'ios_app/AppStatsView.swift': [
        ('괜찮아요, 편안할 때 한마디 남겨보세요. 🌿', '괜찮아요, 편안할 때 한마디 남겨보세요.'),
        ('장기 분석을 위해 최소 3일 이상의 일기가 필요해요. 꾸준히 기록해주세요! 💪', '장기 분석을 위해 최소 3일 이상의 일기가 필요해요. 꾸준히 기록해주세요!'),
        ('꾸준히 기록하고 계신 것만으로도 정말 대단해요. 계속 응원할게요! 💛', '꾸준히 기록하고 계신 것만으로도 정말 대단해요. 계속 응원할게요!'),
        ('Text("💬 3줄 요약")', 'Text("3줄 요약")'),
        ('Text("🧠 장기 기억 패턴 분석하기")', 'Text("장기 기억 패턴 분석하기")'),
        ('Text("🧠 메타 분석")', 'Text("메타 분석")'),
        ('Text("💡 AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")', 'Text("AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")')
    ],
    'ios_app/PremiumModalView.swift': [
        ('Text("🏥")', 'Image(systemName: "building.2.fill").foregroundColor(.blue)')
    ],
    'ios_app/MindBridgePaywallView.swift': [
        ('Text("🏥")', 'Image(systemName: "building.2.fill").foregroundColor(.blue)')
    ],
    'ios_app/AppSettingsView.swift': [
        ('Text("🌉 마음 브릿지")', 'Text("마음 브릿지")')
    ],
    'ios_app/AppShareView.swift': [
        ('Text("🔔 보호자에게 공유할 알림")', 'Text("보호자에게 공유할 알림")')
    ],
    'ios_app/AppDiaryDetailView.swift': [
        ('Text("🤖 AI 감정 분석")', 'Text("AI 감정 분석")'),
        ('Text("💡 AI 조언")', 'Text("AI 조언")'),
        ('Text("💡 AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")', 'Text("AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")')
    ],
    'ios_app/AppDiaryWriteView.swift': [
        ('0: "맑음 ☀️"', '0: "맑음"'),
        ('1: "대체로 맑음 🌤️"', '1: "대체로 맑음"'),
        ('2: "구름 조금 ⛅"', '2: "구름 조금"'),
        ('3: "흐림 ☁️"', '3: "흐림"'),
        ('4: "안개 🌫️"', '4: "안개"'),
        ('45: "안개 🌫️"', '45: "안개"'),
        ('48: "안개 🌫️"', '48: "안개"'),
        ('51: "이슬비 🌧️"', '51: "이슬비"'),
        ('53: "이슬비 🌧️"', '53: "이슬비"'),
        ('55: "이슬비 🌧️"', '55: "이슬비"'),
        ('61: "비 ☔"', '61: "비"'),
        ('63: "비 ☔"', '63: "비"'),
        ('65: "비 ☔"', '65: "비"'),
        ('80: "소나기 ☔"', '80: "소나기"'),
        ('95: "뇌우 ⚡"', '95: "뇌우"')
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
