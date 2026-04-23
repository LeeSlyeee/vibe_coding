import SwiftUI

struct WeeklyLetterView: View {
    @State private var letters: [WeeklyLetter] = WeeklyLetterView.demoLetters
    @State private var selectedLetter: WeeklyLetter?
    @State private var isLoading = false
    @State private var isUsingDemo = true
    var targetLetterId: Int? // [Deep Link] Auto-open Support
    
    var body: some View {
        VStack {
            if isLoading {
                ProgressView("편지함을 열고 있어요...")
            } else if letters.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "envelope.open")
                        .font(.system(size: 40))
                        .foregroundColor(.hintText)
                    Text("아직 도착한 주간 편지가 없어요.")
                        .foregroundColor(.secondary)
                    Text("일기를 꾸준히 쓰면 1주일마다 마음온 AI가 편지를 보내드려요!")
                        .font(.caption)
                        .foregroundColor(.hintText)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            } else {
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(letters) { letter in
                            LetterRowView(letter: letter)
                                .onTapGesture {
                                    self.selectedLetter = letter
                                }
                        }
                    }
                    .padding()
                }
            }
        }
        .onAppear {
            fetchLetters()
        }
        .sheet(item: $selectedLetter) { letter in
            LetterDetailView(letter: letter, onRead: { updatedLetter in
                if let index = letters.firstIndex(where: { $0.id == updatedLetter.id }) {
                    letters[index] = updatedLetter
                }
            })
        }
        .navigationTitle("주간 편지함")
    }
    
    private func fetchLetters() {
        // 데모 데이터는 이미 로드됨. 백그라운드에서 API 시도.
        APIService.shared.fetchMyWeeklyLetters { result in
            DispatchQueue.main.async {
                if let result = result, !result.isEmpty {
                    self.letters = result
                    self.isUsingDemo = false
                    
                    // [Deep Link] Auto-open the specific letter if provided
                    if let targetId = self.targetLetterId,
                       let matchingLetter = result.first(where: { $0.id == targetId }) {
                        self.selectedLetter = matchingLetter
                    }
                } else {
                    // API 실패 시 이미 로드된 데모 데이터 유지
                    if let targetId = self.targetLetterId,
                       let matchingLetter = self.letters.first(where: { $0.id == targetId }) {
                        self.selectedLetter = matchingLetter
                    }
                }
            }
        }
    }
    
    // ─── 데모 데이터 ───
    static let demoLetters: [WeeklyLetter] = [
        WeeklyLetter(
            id: 9001,
            title: "2월 24일 ~ 3월 2일 마음 편지",
            content: """
            안녕하세요, 마음온 AI에요

            이번 한 주, 정말 수고 많으셨어요.

            일기를 읽다 보니 요즘 좀 바쁘고 지치신 것 같아요. 평소보다 문장이 짧아지고, 이전에는 다양한 감정을 섬세하게 표현하셨는데 이번 주에는 조금 단조로웠거든요. 아마 몸과 마음이 모두 쉼을 원하고 있는 것 같아요.

            그래도 매일 일기를 꾸준히 쓰고 계신 모습이 정말 대단해요. 이렇게 자신의 마음을 들여다보는 시간 자체가 치유의 시작이니까요.

            이번 주말에는 좋아하는 음악 한 곡과 따뜻한 차 한 잔으로 자신에게 작은 선물을 해보는 건 어떨까요? 

            다음 주에도 함께할게요.

            마음온 AI 드림 ✉️
            """,
            startDate: "2026-02-24",
            endDate: "2026-03-02",
            isRead: false,
            createdAt: "2026-03-02T23:00:00"
        ),
        WeeklyLetter(
            id: 9002,
            title: "2월 17일 ~ 2월 23일 마음 편지",
            content: """
            안녕하세요, 마음온 AI에요

            지난 한 주 동안 일기를 보니, 직장에서의 이야기가 많았어요. 특히 팀장님과 동료분들 이야기가 자주 등장했는데, 그 속에서 보이는 당신의 노력이 참 멋졌어요.

            어휘도 풍부하고 문장도 길었어요. 할 말이 많았던 한 주였나 봐요. 충분히 표현하고, 충분히 기록한 당신에게 박수를 보내요 

            가까운 사람에게 안부 한 마디 전해보는 건 어때요? 따뜻한 말 한 마디가 당신의 마음에도 온기를 줄 거예요.

            언제나 응원하고 있어요.

            마음온 AI 드림 ✉️
            """,
            startDate: "2026-02-17",
            endDate: "2026-02-23",
            isRead: true,
            createdAt: "2026-02-23T23:00:00"
        ),
        WeeklyLetter(
            id: 9003,
            title: "2월 10일 ~ 2월 16일 마음 편지",
            content: """
            안녕하세요, 마음온 AI에요

            이번 주는 마음이 참 편안했던 한 주 같아요. 일기 속 감정이 다채롭고, 좋아하는 것들에 대한 이야기가 많았거든요.

            특히 주말에 산책하며 느꼈던 봄 기운 이야기가 인상적이었어요. 자연 속에서 에너지를 충전하는 당신만의 방법이 참 좋아요 

            이 좋은 흐름을 기록해두세요. 나중에 힘들 때 꺼내보면 큰 힘이 될 거예요.

            마음온 AI 드림 ✉️
            """,
            startDate: "2026-02-10",
            endDate: "2026-02-16",
            isRead: true,
            createdAt: "2026-02-16T23:00:00"
        )
    ]
}

struct LetterRowView: View {
    let letter: WeeklyLetter
    
    var body: some View {
        HStack {
            ZStack {
                Circle()
                    .fill(letter.isRead ? Color.hintText.opacity(0.2) : Color.accent.opacity(0.1))
                    .frame(width: 50, height: 50)
                Image(systemName: letter.isRead ? "envelope.open.fill" : "envelope.fill")
                    .foregroundColor(letter.isRead ? .hintText : .accent)
                    .font(.title2)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(letter.title)
                    .font(.headline)
                    .foregroundColor(.primary)
                Text(formatDateRange(start: letter.startDate, end: letter.endDate))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.leading, 8)
            
            Spacer()
            
            if !letter.isRead {
                Circle()
                    .fill(Color.red)
                    .frame(width: 8, height: 8)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: 2)
    }
    
    private func formatDateRange(start: String?, end: String?) -> String {
        guard let start = start, let end = end else { return "기간 알 수 없음" }
        return "\(start) ~ \(end)"
    }
}

struct LetterDetailView: View {
    @Environment(\.presentationMode) var presentationMode
    let letter: WeeklyLetter
    var onRead: ((WeeklyLetter) -> Void)?
    
    @State private var fullLetter: WeeklyLetter?
    @State private var isLoading = true
    @State private var envelopeOffset: CGFloat = 0
    @State private var isOpened = false
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.white.edgesIgnoringSafeArea(.all)
                
                if isLoading {
                    VStack {
                        Image(systemName: "envelope.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.accent)
                            .offset(y: envelopeOffset)
                            .onAppear {
                                withAnimation(Animation.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                                    envelopeOffset = -10
                                }
                            }
                        Text("편지를 뜯는 중...")
                            .padding(.top, 16)
                            .foregroundColor(.secondary)
                    }
                } else if let full = fullLetter {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 20) {
                            Text(full.title)
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundColor(.primary)
                            
                            HStack {
                                Text("\(full.startDate ?? "") ~ \(full.endDate ?? "")")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                Spacer()
                                Text(formatDate(full.createdAt) ?? "")
                                    .font(.caption)
                                    .foregroundColor(.hintText)
                            }
                            
                            Divider()
                            
                            Text(full.content ?? "내용이 없습니다.")
                                .font(.body)
                                .lineSpacing(8)
                                .padding(.vertical, 10)
                                .foregroundColor(Color.gray900)
                            
                            Spacer()
                        }
                        .padding(24)
                        .background(Color.white)
                        .cornerRadius(16)
                        .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 5)
                        .padding()
                        .opacity(isOpened ? 1 : 0)
                        .offset(y: isOpened ? 0 : 50)
                    }
                } else {
                    Text("편지를 불러오지 못했습니다.")
                        .foregroundColor(.red)
                }
            }
            .navigationBarItems(trailing: Button("닫기") {
                presentationMode.wrappedValue.dismiss()
            })
            .navigationBarTitleDisplayMode(.inline)
            .onAppear {
                fetchDetail()
            }
        }
    }
    
    private func fetchDetail() {
        // 데모 데이터인 경우 (id가 9000번대) API 호출 없이 바로 표시
        if letter.id >= 9000 {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                self.isLoading = false
                self.fullLetter = letter
                var updatedLetter = self.letter
                updatedLetter.isRead = true
                self.onRead?(updatedLetter)
                withAnimation(.spring(response: 0.6, dampingFraction: 0.8)) {
                    self.isOpened = true
                }
            }
            return
        }
        
        APIService.shared.fetchWeeklyLetterDetail(letterId: letter.id) { result in
            DispatchQueue.main.async {
                self.isLoading = false
                if let result = result {
                    self.fullLetter = result
                    var updatedLetter = self.letter
                    updatedLetter.isRead = true
                    self.onRead?(updatedLetter)
                    
                    withAnimation(.spring(response: 0.6, dampingFraction: 0.8)) {
                        self.isOpened = true
                    }
                }
            }
        }
    }
    
    private func formatDate(_ dateString: String?) -> String? {
        guard let dateString = dateString else { return nil }
        // 데모 데이터의 간단한 날짜 형식 처리
        if dateString.count <= 19 {
            return dateString.prefix(10) + " 도착"
        }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: dateString) else { return dateString }
        
        let outFormatter = DateFormatter()
        outFormatter.dateFormat = "yyyy년 M월 d일 도착"
        return outFormatter.string(from: date)
    }
}
