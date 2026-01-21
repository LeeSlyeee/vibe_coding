
import SwiftUI

// MARK: - Safe Data Wrapper
struct WriteTargetDate: Identifiable {
    let id = UUID()
    let date: Date
}

// MARK: - Helper Struct
struct CalendarDay: Identifiable {
    let id = UUID()
    let date: Date?
}

struct MoodCalendarView: View {
    @State private var currentDate = Date()
    @State private var diaries: [String: Diary] = [:] // "YYYY-MM-DD" : Diary Object
    @State private var isLoading = false
    
    // Navigation State
    @State private var selectedDiary: Diary?
    @State private var showDetail = false
    
    // Write Modal State (Identifiable Item for Safe Presentation)
    @State private var writeTarget: WriteTargetDate?
    
    // ✅ Base URL
    let baseURL = "https://217.142.253.35.nip.io"
    
    let columns = Array(repeating: GridItem(.flexible()), count: 7)
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // 상단 헤더
                HStack {
                    Button(action: { changeMonth(by: -1) }) {
                        Image(systemName: "chevron.left").font(.title2).foregroundColor(.black)
                    }
                    Spacer()
                    Text(monthYearString(currentDate)).font(.title2).fontWeight(.bold)
                    Spacer()
                    Button(action: { changeMonth(by: 1) }) {
                        Image(systemName: "chevron.right").font(.title2).foregroundColor(.black)
                    }
                }
                .padding(.horizontal)
                .padding(.top, 20)
                
                // 요일 헤더
                HStack {
                    ForEach(["일", "월", "화", "수", "목", "금", "토"], id: \.self) { day in
                        Text(day).font(.caption).fontWeight(.bold).foregroundColor(.gray).frame(maxWidth: .infinity)
                    }
                }
                
                // 달력 그리드
                if isLoading {
                    Spacer(); ProgressView(); Spacer()
                } else {
                    LazyVGrid(columns: columns, spacing: 15) {
                        ForEach(calendarDays()) { dayItem in
                            if let date = dayItem.date {
                                let dateStr = dateString(date)
                                let diary = diaries[dateStr]
                                
                                Button(action: { handleDateTap(date, diary: diary) }) {
                                    VStack(spacing: 1) { // 간격 최소화
                                        // 1. 날짜
                                        Text("\(Calendar.current.component(.day, from: date))")
                                            .font(.system(size: 10, weight: diary != nil ? .bold : .regular)) // 날짜 크기 축소
                                            .foregroundColor(Calendar.current.isDateInToday(date) ? .blue : .primary)
                                            .padding(.top, 4)
                                        
                                        if let d = diary {
                                            VStack(spacing: 0) {
                                                // 2. 사용자 선택 이모지 (이미지)
                                                let asset = getMoodAsset(level: d.mood_level)
                                                Image(uiImage: UIImage(named: asset.image) ?? UIImage())
                                                    .resizable()
                                                    .scaledToFit()
                                                    .frame(width: 28, height: 28)
                                                    .padding(.bottom, 2)
                                                
                                                // 3 & 4. AI 예측 (감정 + 퍼센트)
                                                let (label, percent) = parseAI(d.ai_prediction)
                                                if !label.isEmpty {
                                                    Text(label)
                                                        .font(.system(size: 8, weight: .bold)) // 텍스트 크기 축소
                                                        .foregroundColor(.primary)
                                                        .lineLimit(1)
                                                        .minimumScaleFactor(0.7)
                                                    
                                                    if !percent.isEmpty {
                                                        Text(percent)
                                                            .font(.system(size: 7))
                                                            .foregroundColor(.secondary)
                                                            .lineLimit(1)
                                                            .minimumScaleFactor(0.7)
                                                    }
                                                }
                                            }
                                        } else {
                                            Spacer()
                                        }
                                        Spacer(minLength: 2)
                                    }
                                    .frame(height: 75) // 셀 높이 약간 증가
                                    .frame(maxWidth: .infinity)
                                    .background(
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(diary != nil ? getMoodAsset(level: diary!.mood_level).color.opacity(0.15) : Color.clear)
                                    )
                                }
                            } else {
                                Text("") // 빈 칸
                            }
                        }
                    }
                    .padding()
                }
                Spacer()
                
                // Hidden Navigation Link for Detail
                NavigationLink(
                    destination: selectedDiary != nil ? AppDiaryDetailView(diary: selectedDiary!, onDelete: { fetchDiaries() }) : nil,
                    isActive: $showDetail
                ) { EmptyView() }
            }
            .navigationBarHidden(true)
            .onAppear(perform: fetchDiaries)
            .onChange(of: currentDate) { _ in fetchDiaries() }
            .sheet(item: $writeTarget) { target in
                 // 바인딩 전달을 위한 래퍼
                 AppDiaryWriteView(
                    isPresented: Binding(
                        get: { writeTarget != nil },
                        set: { if !$0 { writeTarget = nil } }
                    ),
                    date: target.date,
                    onSave: fetchDiaries
                 )
            }
        }
    }
    
    // MARK: - Logic
    func parseAI(_ text: String?) -> (String, String) {
        guard var raw = text, !raw.isEmpty else { return ("", "") }
        
        // 1. Extract from single quotes if present (e.g., 'Happy (80%)')
        if let start = raw.firstIndex(of: "'"), let end = raw.lastIndex(of: "'"), start != end {
            raw = String(raw[raw.index(after: start)..<end])
        }
        
        // 2. Extract Label and Percent
        // Check for format "Label (N%)"
        if raw.hasSuffix(")"), let openParen = raw.lastIndex(of: "(") {
            let label = String(raw[..<openParen]).trimmingCharacters(in: .whitespaces)
            let percent = String(raw[openParen...])
            if percent.contains("%") {
                 return (label, percent)
            }
        }
        
        // Fallback: Return raw string as label if parsing fails
        return (raw, "")
    }

    func handleDateTap(_ date: Date, diary: Diary?) {
        if let diary = diary {
            // 이미 일기가 있으면 상세 보기
            self.selectedDiary = diary
            self.showDetail = true
        } else {
            // 일기가 없으면 작성 모달 (데이터를 먼저 담고 시트 오픈)
            self.writeTarget = WriteTargetDate(date: date)
        }
    }
    
    func fetchDiaries() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/diaries") else { return }
        
        // Fetch all (or current month logic if API supports)
        // For now, fetching limit 100 which is default backend
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        URLSession.shared.dataTask(with: request) { data, _, _ in
            DispatchQueue.main.async { isLoading = false }
            guard let data = data else { return }
            
            do {
                let list = try JSONDecoder().decode([Diary].self, from: data)
                var newMap: [String: Diary] = [:]
                for item in list {
                    // item.date format check. Backend raw `date` might be missing, use `created_at`
                    if let dStr = item.created_at {
                        // Assuming created_at is ISO "YYYY-MM-DDTHH:mm:ss"
                        let dateKey = String(dStr.prefix(10))
                        newMap[dateKey] = item
                    }
                }
                DispatchQueue.main.async { diaries = newMap }
            } catch {
                print("Decode Error: \(error)")
            }
        }.resume()
    }
    
    // Helpers
    func changeMonth(by value: Int) {
        if let newDate = Calendar.current.date(byAdding: .month, value: value, to: currentDate) { currentDate = newDate }
    }
    func calendarDays() -> [CalendarDay] {
        let cal = Calendar.current
        let components = cal.dateComponents([.year, .month], from: currentDate)
        let firstDay = cal.date(from: components)!
        let range = cal.range(of: .day, in: .month, for: firstDay)!
        let firstWeekday = cal.component(.weekday, from: firstDay) - 1
        
        var days: [CalendarDay] = []
        
        // 빈 칸 (이전 달)
        for _ in 0..<firstWeekday {
            days.append(CalendarDay(date: nil))
        }
        
        // 이번 달 날짜들
        for day in 1...range.count {
            if let date = cal.date(byAdding: .day, value: day-1, to: firstDay) {
                days.append(CalendarDay(date: date))
            }
        }
        return days
    }
    func monthYearString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "YYYY년 M월"; return f.string(from: d) }
    func dateString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: d) }
    func moodEmoji(_ l: Int) -> String { ["", "😠", "😢", "😐", "😌", "😊"][l] }
    func moodColor(_ l: Int) -> Color { [Color.clear, .red, .blue, .gray, .green, .yellow][l] }
}
