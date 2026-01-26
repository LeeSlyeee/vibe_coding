
import SwiftUI

struct AppAssessmentView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.presentationMode) var presentationMode
    
    // Questions (PHQ-9 or simplified check)
    let questions = [
        "기분이 가라앉거나, 우울하거나, 희망이 없다고 느꼈다.",
        "평소 하던 일에 대한 흥미나 즐거움을 느끼지 못했다.",
        "잠들기 어렵거나 중간에  자주 깼다.",
        "피곤하고 기운이 없다고 느꼈다.",
        "식욕이 줄었거나 반대로 너무 많이 먹었다.",
        "내 자신이 실패자로 느껴지거나 가족을 실망시켰다고 생각했다.",
        "신문을 읽거나 TV를 보는 것과 같은 일상적인 일에 집중하기 어려웠다.",
        "다른 사람들이 눈치 챌 정도로 말이 느려지거나 안절부절못했다.",
        "차라리 죽는 것이 낫겠다고 생각하거나 자해할 생각을 했다."
    ]
    
    @State private var ratings: [Int] = Array(repeating: 0, count: 9) // 0~3점
    @State private var currentStep = 0
    @State private var isSubmitting = false
    
    let baseURL = "https://217.142.253.35.nip.io"
    
    var body: some View {
        NavigationView {
            VStack {
                // Progress
                ProgressView(value: Double(currentStep + 1), total: Double(questions.count))
                    .padding()
                
                Spacer()
                
                // Question Card
                VStack(spacing: 20) {
                    Text("Q\(currentStep + 1).")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    
                    Text(questions[currentStep])
                        .font(.title2)
                        .fontWeight(.medium)
                        .multilineTextAlignment(.center)
                        .padding()
                        .frame(minHeight: 120)
                }
                
                Spacer()
                
                // Options (0: 없음, 1: 며칠, 2: 절반 이상, 3: 거의 매일)
                VStack(spacing: 12) {
                    optionButton(score: 0, label: "전혀 없음")
                    optionButton(score: 1, label: "며칠 동안")
                    optionButton(score: 2, label: "7일 이상")
                    optionButton(score: 3, label: "거의 매일")
                }
                .padding()
                
                Spacer()
            }
            .navigationBarTitle("초기 심리 진단", displayMode: .inline)
            .padding()
        }
    }
    
    func optionButton(score: Int, label: String) -> some View {
        Button(action: {
            handleAnswer(score)
        }) {
            HStack {
                Text(label)
                    .font(.headline)
                Spacer()
                if ratings[currentStep] == score {
                    Image(systemName: "checkmark.circle.fill")
                }
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(Color(UIColor.systemGray6))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.blue.opacity(0.3), lineWidth: 1)
            )
        }
        .foregroundColor(.primary)
    }
    
    func handleAnswer(_ score: Int) {
        ratings[currentStep] = score
        
        if currentStep < questions.count - 1 {
            withAnimation {
                currentStep += 1
            }
        } else {
            submitAssessment()
        }
    }
    
    func submitAssessment() {
        guard let token = authManager.token else { return }
        isSubmitting = true
        
        let totalScore = ratings.reduce(0, +)
        print("📊 Assessment Score: \(totalScore)")
        
        guard let url = URL(string: "\(baseURL)/api/assessment") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "score": totalScore,
            "answers": ratings
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, _, error in
            DispatchQueue.main.async {
                isSubmitting = false
                if error == nil {
                    // Refresh Profile or Estimate Risk
                    // Simple Logic: 0-4 (1), 5-9 (2), 10-14 (3), 15-19 (4), 20+ (5)
                    var newLevel = 1
                    if totalScore >= 20 { newLevel = 5 }
                    else if totalScore >= 15 { newLevel = 4 }
                    else if totalScore >= 10 { newLevel = 3 }
                    else if totalScore >= 5 { newLevel = 2 }
                    
                    authManager.setRiskLevel(newLevel)
                    presentationMode.wrappedValue.dismiss()
                }
            }
        }.resume()
    }
}
