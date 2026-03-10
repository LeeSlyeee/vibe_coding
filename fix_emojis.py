import os, re
import sys

def remove_emojis_from_string(s):
    # Regex to catch all emojis roughly
    # We will just replace known emojis manually to be 100% safe
    pass

REPLACEMENTS = {
    # AppMainTabView.swift
    '💬 더보기/지원': '더보기/지원',
    '🚀 시작하기': '시작하기',
    '✨ 데이터 가져오기 완료': '데이터 가져오기 완료',
    '❌ 동기화 실패': '동기화 실패',
    '✅ 동기화 완료': '동기화 완료',
    '🎂 [테스트] 친구 데이터 생성됨!': '[테스트] 친구 데이터 생성됨!',
    '🎉 [테스트] 초기 데이터 생성됨!': '[테스트] 초기 데이터 생성됨!',
    '📖 서비스 안내': '서비스 안내',
    '📱 마음온 소개': '마음온 소개',
    '당신의 마음을 기록하고, 🌟': '당신의 마음을 기록하고,',
    '📝 일기 작성하기': '일기 작성하기',
    '🤖 AI 감정 분석 & 코멘트': 'AI 감정 분석 & 코멘트',
    '📊 프라이버시 & 심층 분석': '프라이버시 & 심층 분석',
    '🔒 철통 보안 AI 감정 분석': '철통 보안 AI 감정 분석',
    '🧠 심층 감정 리포트': '심층 감정 리포트',
    '🔬 과거 기록 통합 분석': '과거 기록 통합 분석',
    '🧩 감정 패턴 통계': '감정 패턴 통계',
    '🔍 키워드 검색': '키워드 검색',
    '💌 리뷰': '리뷰',
    '😍 감사해요!': '감사해요!',
    '🚑 신고': '신고',
    '🛑 경고': '경고',
    '잠시 후 다시 시도해주세요. ⏳': '잠시 후 다시 시도해주세요.',
    
    # GuideFeatureCard specific
    'GuideFeatureCard(icon: "🧠"': 'GuideFeatureCard(systemIcon: "brain.head.profile"',
    'GuideFeatureCard(icon: "💬"': 'GuideFeatureCard(systemIcon: "bubble.left.and.bubble.right.fill"',
    'GuideFeatureCard(icon: "🛡️"': 'GuideFeatureCard(systemIcon: "checkmark.shield.fill"',
    'GuideFeatureCard(icon: "📑"': 'GuideFeatureCard(systemIcon: "doc.text.below.ecg.fill"',
    'GuideFeatureCard(icon: "🔭"': 'GuideFeatureCard(systemIcon: "chart.xyaxis.line"',
    'let icon: String': 'let systemIcon: String',
    'Text(icon).font(.system(size: 32))': 'Image(systemName: systemIcon).font(.system(size: 32)).foregroundColor(.blue)',

    # AppStatsView.swift
    '🤬 분노': '분노',
    '💬 분석 중...': '분석 중...',
    '😌 평온': '평온',
    '😢 슬픔': '슬픔',
    '🌿 주간': '주간',
    '💪 상태': '상태',
    '🌱 성취': '성취',
    '😐 보통': '보통',
    '💛 기록된': '기록된',
    '🧠 AI': 'AI',
    '🔄 분석': '분석',
    '💡 인사이트': '인사이트',
    '🥰 기쁨': '기쁨',

    # SharedStatsView.swift
    '🎨 감정': '감정',

    # AppDiaryWriteView.swift
    '🌫 분석': '분석',
    '🛠 AI 분석': 'AI 분석',
    '🌧 부정적': '부정적',
    '�� 위기 감지됨. 즉각적인 도움이 필요할 수 있습니다. 🚨': '위기 감지됨. 즉각적인 도움이 필요할 수 있습니다.',
    '위기 감지됨 🚨': '위기 감지됨',
    '🌤 긍정적': '긍정적',
    '🛡 프라이버시': '프라이버시',
    '📤 [AI]': '[AI]',
    '🧘 평온함': '평온함',
    '🚑 연결된': '연결된',

    # AppChatView.swift
    '🌡 감정': '감정',
    '🏃 응급': '응급',
    '🏥 병원': '병원',
    '🏻': '',
    '👋 안녕': '안녕',

    # AppEmergencyView.swift
    '📞 전화': '전화',
    '👮 112': '112',
    
    # AppDiaryDetailView.swift
    '💡 요약': '요약',
    '🤖 AI 코멘트': 'AI 코멘트',

    # RelationalMapView.swift
    '💼 업무': '업무',
    '🐾 반려동물': '반려동물',
    '💜 관계': '관계',
    '🙌 커뮤니티': '커뮤니티',

    # MindBridgePaywallView.swift & MindBridgeExportView.swift
    '🏥 마음 브릿지': '마음 브릿지',
    '😊 감정': '감정',
    
    # SubscriptionManager.swift / ShareManager.swift / APIService.swift / LLMService.swift / LocalDataManager.swift / B2GManager.swift
    '📊': '',
    '👤': '',
    '🛠': '',
    '📥': '',
    '��': '',
    '🔄': '',
    '📤': '',
    '🏁': '',
    '💾': '',
    '🔓': '',
    '🚑': '',
    '🚫': '',
    '🔑': '',
    '🗑': '',
    '📡': '',
    '📦': '',
    '📝': '',
    '😥': '',
    '📖': '',
    '📏': '',
    '🌍': '',
    '💤': '',
    '📞': '',
    '🔧': '',
    '🧹': '',
    '📋': '',
    '🔗': '',
    '🔐': '',
    '📩': '',
    '��': '',
    '🔥': '',
    '💨': '',
    '🌱': ''
}

for root, _, files in os.walk('ios_app'):
    for f in files:
        if f.endswith('.swift'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            original_content = content
            for k, v in REPLACEMENTS.items():
                content = content.replace(k, v)
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated: {path}")

