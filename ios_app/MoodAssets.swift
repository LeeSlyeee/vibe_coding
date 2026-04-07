
import SwiftUI

struct MoodAsset {
    let level: Int
    let image: String
    let title: String
    let color: Color
}

func getMoodAsset(level: Int) -> MoodAsset {
    switch level {
    case 1: return MoodAsset(level: 1, image: "mood_angry", title: "화나요", color: .mood1)       // 더스티 로즈
    case 2: return MoodAsset(level: 2, image: "mood_sad", title: "우울해요", color: .mood2)       // 뮤트 블루
    case 3: return MoodAsset(level: 3, image: "mood_soso", title: "그저 그래요", color: .mood3)   // 샌드
    case 4: return MoodAsset(level: 4, image: "mood_calm", title: "편안해요", color: .mood4)      // 세이지 그린
    case 5: return MoodAsset(level: 5, image: "mood_happy", title: "행복해요", color: .mood5)     // 피치 코랄
    default: return MoodAsset(level: 3, image: "mood_soso", title: "그저 그래요", color: .mood3)  // 샌드
    }
}

