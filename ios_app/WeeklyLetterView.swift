import SwiftUI

struct WeeklyLetterView: View {
    @State private var letters: [WeeklyLetter] = []
    @State private var selectedLetter: WeeklyLetter?
    @State private var showingDetail = false
    @State private var isLoading = true
    
    var body: some View {
        VStack {
            if isLoading {
                ProgressView("편지함을 열고 있어요...")
            } else if letters.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "envelope.open")
                        .font(.system(size: 40))
                        .foregroundColor(.gray)
                    Text("아직 도착한 주간 편지가 없어요.")
                        .foregroundColor(.secondary)
                    Text("일기를 꾸준히 쓰면 1주일마다 마음온 AI가 편지를 보내드려요!")
                        .font(.caption)
                        .foregroundColor(.gray)
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
                                    self.showingDetail = true
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
        isLoading = true
        APIService.shared.fetchMyWeeklyLetters { result in
            DispatchQueue.main.async {
                self.isLoading = false
                if let result = result {
                    self.letters = result
                }
            }
        }
    }
}

struct LetterRowView: View {
    let letter: WeeklyLetter
    
    var body: some View {
        HStack {
            ZStack {
                Circle()
                    .fill(letter.isRead ? Color.gray.opacity(0.2) : Color.blue.opacity(0.1))
                    .frame(width: 50, height: 50)
                Image(systemName: letter.isRead ? "envelope.open.fill" : "envelope.fill")
                    .foregroundColor(letter.isRead ? .gray : .blue)
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
                Color(hexString: "F8F9FE").edgesIgnoringSafeArea(.all)
                
                if isLoading {
                    VStack {
                        Image(systemName: "envelope.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.blue)
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
                                    .foregroundColor(.gray)
                            }
                            
                            Divider()
                            
                            Text(full.content ?? "내용이 없습니다.")
                                .font(.body)
                                .lineSpacing(8)
                                .padding(.vertical, 10)
                                .foregroundColor(Color(hexString: "2C3E50"))
                            
                            Spacer()
                        }
                        .padding(24)
                        .background(Color.white)
                        .cornerRadius(16)
                        .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 5)
                        .padding()
                        // 뜯어지는 애니메이션 (Fade & Slide up)
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
        APIService.shared.fetchWeeklyLetterDetail(letterId: letter.id) { result in
            DispatchQueue.main.async {
                self.isLoading = false
                if let result = result {
                    self.fullLetter = result
                    // Notify parent to update read status
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
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: dateString) else { return dateString }
        
        let outFormatter = DateFormatter()
        outFormatter.dateFormat = "yyyy년 M월 d일 도착"
        return outFormatter.string(from: date)
    }
}
