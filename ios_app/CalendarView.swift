
import SwiftUI

struct CalendarView: View {
    @State private var currentDate = Date()
    @State private var diaries: [String: Diary] = [:] // "YYYY-MM-DD" : Diary Object
    @State private var isLoading = false
    
    // Navigation State
    @State private var selectedDiary: Diary?
    @State private var showDetail = false
    
    // Write Modal State
    @State private var selectedDateForWrite: Date?
    @State private var showWriteSheet = false
    
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
                        ForEach(calendarDays(), id: \.self) { date in
                            if let date = date {
                                let dateStr = dateString(date)
                                let diary = diaries[dateStr]
                                
                                Button(action: { handleDateTap(date, diary: diary) }) {
                                    VStack {
                                        Text("\(Calendar.current.component(.day, from: date))")
                                            .font(.caption)
                                            .foregroundColor(Calendar.current.isDateInToday(date) ? .blue : .primary)
                                            .fontWeight(diary != nil ? .bold : .regular)
                                        
                                        if let d = diary {
                                            Text(moodEmoji(d.mood_level)).font(.system(size: 20))
                                        } else {
                                            Text("").font(.system(size: 20))
                                        }
                                    }
                                    .frame(height: 60)
                                    .frame(maxWidth: .infinity)
                                    .background(
                                        RoundedRectangle(cornerRadius: 10)
                                            .fill(diary != nil ? moodColor(diary!.mood_level).opacity(0.15) : Color.clear)
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
                    destination: selectedDiary != nil ? DiaryDetailView(diary: selectedDiary!, onDelete: { fetchDiaries() }) : nil,
                    isActive: $showDetail
                ) { EmptyView() }
            }
            .navigationBarHidden(true)
            .onAppear(perform: fetchDiaries)
            .onChange(of: currentDate) { _ in fetchDiaries() }
            .sheet(isPresented: $showWriteSheet) {
                if let d = selectedDateForWrite {
                    DiaryWriteView(isPresented: $showWriteSheet, date: d, onSave: fetchDiaries)
                }
            }
        }
    }
    
    // MARK: - Logic
    func handleDateTap(_ date: Date, diary: Diary?) {
        if let diary = diary {
            // 이미 일기가 있으면 상세 보기
            self.selectedDiary = diary
            self.showDetail = true
        } else {
            // 일기가 없으면 작성 모달
            self.selectedDateForWrite = date
            self.showWriteSheet = true
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
    func calendarDays() -> [Date?] {
        let cal = Calendar.current
        let components = cal.dateComponents([.year, .month], from: currentDate)
        let firstDay = cal.date(from: components)!
        let range = cal.range(of: .day, in: .month, for: firstDay)!
        let firstWeekday = cal.component(.weekday, from: firstDay) - 1
        var days: [Date?] = Array(repeating: nil, count: firstWeekday)
        for day in 1...range.count { days.append(cal.date(byAdding: .day, value: day-1, to: firstDay)) }
        return days
    }
    func monthYearString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "YYYY년 M월"; return f.string(from: d) }
    func dateString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: d) }
    func moodEmoji(_ l: Int) -> String { ["", "😠", "😢", "😐", "😌", "😊"][l] }
    func moodColor(_ l: Int) -> Color { [Color.clear, .red, .blue, .gray, .green, .yellow][l] }
}
