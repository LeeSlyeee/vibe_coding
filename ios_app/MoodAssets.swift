
import SwiftUI

struct MoodAsset {
    let image: String
    let title: String
    let color: Color
}

func getMoodAsset(level: Int) -> MoodAsset {
    switch level {
    case 1: return MoodAsset(image: "mood_angry", title: "화나요", color: .red)
    case 2: return MoodAsset(image: "mood_sad", title: "우울해요", color: .blue)
    case 3: return MoodAsset(image: "mood_soso", title: "그저 그래요", color: .gray)
    case 4: return MoodAsset(image: "mood_calm", title: "편안해요", color: .green)
    case 5: return MoodAsset(image: "mood_happy", title: "행복해요", color: .yellow)
    default: return MoodAsset(image: "mood_soso", title: "그저 그래요", color: .gray)
    }
}
