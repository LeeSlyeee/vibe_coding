import SwiftUI

// MARK: - Phase 3/4: 마음 브릿지 메인 화면
// 수신자 관리 + 공유 깊이 커스텀 + 가족 Export + 상담사 대시보드 연결

struct MindBridgeMainView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var bridgeManager = MindBridgeManager.shared
    
    // 시트
    @State private var showAddRecipient = false
    @State private var showExportView = false
    @State private var selectedRecipient: BridgeRecipient?
    @State private var showDepthSettings = false
    @State private var showShareHistory = false
    
    // 공유 실행 상태
    @State private var shareTargetRecipient: BridgeRecipient?
    @State private var showShareConfirm = false
    @State private var shareResultMessage = ""
    @State private var showShareResult = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    
                    // MARK: - 헤더
                    headerSection
                    
                    // MARK: - 가족/보호자 섹션
                    recipientSection(
                        title: "👨‍👩‍👧 가족 / 보호자",
                        type: .family,
                        recipients: bridgeManager.familyRecipients
                    )
                    
                    // MARK: - 상담사/의료진 섹션
                    recipientSection(
                        title: "🩺 상담사 / 의료진",
                        type: .counselor,
                        recipients: bridgeManager.counselorRecipients
                    )
                    
                    // MARK: - 수신자 추가
                    addRecipientButton
                    
                    // MARK: - 공유 이력 (Phase 5)
                    shareHistoryButton
                    
                    // MARK: - 프라이버시 안내
                    privacyBadge
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("🌉 마음 브릿지")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("닫기") { dismiss() }
                }
            }
            .sheet(isPresented: $showAddRecipient) {
                AddRecipientSheet(bridgeManager: bridgeManager)
            }
            .sheet(isPresented: $showExportView) {
                MindBridgeExportView()
            }
            .sheet(item: $selectedRecipient) { recipient in
                RecipientDepthSettingsView(recipient: recipient, bridgeManager: bridgeManager)
            }
            .sheet(isPresented: $showShareHistory) {
                ShareHistoryView(bridgeManager: bridgeManager)
            }
            .alert("지금 공유할까요?", isPresented: $showShareConfirm) {
                Button("공유", role: .none) {
                    if let recipient = shareTargetRecipient {
                        bridgeManager.shareToRecipient(recipient) { success, error in
                            if success {
                                shareResultMessage = "\(recipient.name)에게 공유가 완료되었습니다"
                            } else {
                                shareResultMessage = error ?? "공유에 실패했습니다"
                            }
                            showShareResult = true
                        }
                    }
                }
                Button("취소", role: .cancel) {}
            } message: {
                if let r = shareTargetRecipient {
                    let depth = bridgeManager.getDepthSettings(for: r.id)
                    Text("\(r.name)에게 설정된 \(depth.enabledCount)개 항목을 서버로 공유합니다.")
                }
            }
            .alert(shareResultMessage, isPresented: $showShareResult) {
                Button("확인", role: .cancel) {}
            }
        }
    }
    
    // MARK: - 헤더
    var headerSection: some View {
        VStack(spacing: 8) {
            Text("내 마음을 소중한 사람에게")
                .font(.title3)
                .fontWeight(.bold)
            Text("안전하게 전해보세요")
                .font(.title3)
                .fontWeight(.bold)
                .foregroundColor(Color(hexString: "6366f1"))
            Text("일기 원문은 절대 공유되지 않습니다")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 8)
    }
    
    // MARK: - 수신자 섹션
    func recipientSection(title: String, type: RecipientType, recipients: [BridgeRecipient]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
            
            if recipients.isEmpty {
                emptyRecipientCard(type: type)
            } else {
                ForEach(recipients) { recipient in
                    recipientCard(recipient)
                }
            }
        }
    }
    
    func emptyRecipientCard(type: RecipientType) -> some View {
        HStack {
            Image(systemName: type == .family ? "person.2.fill" : "stethoscope")
                .foregroundColor(.secondary)
                .frame(width: 32)
            VStack(alignment: .leading, spacing: 2) {
                Text(type == .family ? "가족을 추가해보세요" : "상담사를 연결해보세요")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                Text(type == .family ? "감정 리포트를 안전하게 공유합니다" : "AI 분석 결과를 대시보드로 전달합니다")
                    .font(.caption2)
                    .foregroundColor(.secondary.opacity(0.7))
            }
            Spacer()
            Button(action: { showAddRecipient = true }) {
                Text("추가")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(Color(hexString: "6366f1"))
                    .cornerRadius(8)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
    }
    
    func recipientCard(_ recipient: BridgeRecipient) -> some View {
        HStack {
            // 아바타
            Circle()
                .fill(
                    LinearGradient(
                        colors: recipient.type == .family
                            ? [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")]
                            : [Color(hexString: "10b981"), Color(hexString: "059669")],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 40, height: 40)
                .overlay(
                    Text(String(recipient.name.prefix(1)))
                        .font(.headline)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                )
            
            VStack(alignment: .leading, spacing: 2) {
                Text(recipient.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                HStack(spacing: 4) {
                    Circle()
                        .fill(recipient.isActive ? .green : .orange)
                        .frame(width: 6, height: 6)
                    Text(recipient.isActive ? "공유 중" : "일시 중지")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    if let schedule = recipient.shareSchedule {
                        Text("· \(schedule.displayName)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            // 관리 버튼
            Button(action: { selectedRecipient = recipient }) {
                Text("관리")
                    .font(.caption)
                    .foregroundColor(Color(hexString: "6366f1"))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color(hexString: "6366f1").opacity(0.1))
                    .cornerRadius(8)
            }
            
            // 공유 실행 버튼
            Button(action: {
                shareTargetRecipient = recipient
                showShareConfirm = true
            }) {
                Image(systemName: "paperplane.fill")
                    .font(.caption)
                    .foregroundColor(.white)
                    .padding(8)
                    .background(
                        LinearGradient(
                            colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .clipShape(Circle())
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
    }
    
    // MARK: - 수신자 추가 버튼
    var addRecipientButton: some View {
        Button(action: { showAddRecipient = true }) {
            HStack {
                Image(systemName: "plus.circle.fill")
                    .foregroundColor(Color(hexString: "6366f1"))
                Text("새 수신자 추가")
                    .fontWeight(.medium)
                    .foregroundColor(Color(hexString: "6366f1"))
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .strokeBorder(Color(hexString: "6366f1").opacity(0.3), style: StrokeStyle(lineWidth: 1.5, dash: [6]))
            )
        }
    }
    
    // MARK: - 공유 이력 (Phase 5)
    var shareHistoryButton: some View {
        Button(action: { showShareHistory = true }) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(.secondary)
                Text("공유 이력 보기")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
        }
    }
    
    // MARK: - 프라이버시 배지
    var privacyBadge: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "lock.shield.fill")
                .foregroundColor(.green)
            VStack(alignment: .leading, spacing: 4) {
                Text("프라이버시 보호")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.green)
                Text("모든 공유 항목은 기본 OFF입니다.\n사용자가 직접 켜야만 공유됩니다.\n일기 원문은 어떤 경로로도 절대 공유되지 않습니다.")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - 수신자 추가 시트
struct AddRecipientSheet: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var bridgeManager: MindBridgeManager
    
    @State private var recipientName = ""
    @State private var recipientType: RecipientType = .family
    @State private var shareSchedule: ShareSchedule = .weekly
    @State private var pinCode = ""    // 상담사용 PIN
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("수신자 정보")) {
                    TextField("이름 (예: 엄마, 김OO 상담사)", text: $recipientName)
                    
                    Picker("유형", selection: $recipientType) {
                        Text("👨‍👩‍👧 가족 / 보호자").tag(RecipientType.family)
                        Text("🩺 상담사 / 의료진").tag(RecipientType.counselor)
                    }
                }
                
                if recipientType == .family {
                    Section(header: Text("공유 주기")) {
                        Picker("주기", selection: $shareSchedule) {
                            ForEach(ShareSchedule.allCases, id: \.self) { schedule in
                                Text(schedule.displayName).tag(schedule)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                }
                
                // Phase 5: 상담사 PIN 보안 설정
                if recipientType == .counselor {
                    Section(header: Text("보안 설정"),
                            footer: Text("상담사가 공유 데이터를 열람할 때 이 PIN을 입력해야 합니다.\n4~6자리 숫자를 설정하세요.")) {
                        SecureField("PIN 코드 (4~6자리)", text: $pinCode)
                            .keyboardType(.numberPad)
                    }
                }
                
                Section(header: Text("안내"), footer: Text("모든 공유 항목은 기본 OFF 상태로 시작됩니다.\n수신자별로 공유할 항목을 직접 선택해주세요.")) {
                    HStack {
                        Image(systemName: "checkmark.shield.fill")
                            .foregroundColor(.green)
                        Text("일기 원문은 절대 포함되지 않습니다")
                            .font(.subheadline)
                    }
                }
            }
            .navigationTitle("수신자 추가")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("취소") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("추가") {
                        let pin: String? = (recipientType == .counselor && pinCode.count >= 4) ? pinCode : nil
                        bridgeManager.addRecipient(
                            name: recipientName,
                            type: recipientType,
                            schedule: recipientType == .family ? shareSchedule : nil,
                            pin: pin
                        )
                        dismiss()
                    }
                    .disabled(recipientName.trimmingCharacters(in: .whitespaces).isEmpty || (recipientType == .counselor && pinCode.count >= 1 && pinCode.count < 4))
                    .fontWeight(.bold)
                }
            }
        }
    }
}

// MARK: - Phase 4: 수신자별 공유 깊이 설정
struct RecipientDepthSettingsView: View {
    @Environment(\.dismiss) var dismiss
    let recipient: BridgeRecipient
    @ObservedObject var bridgeManager: MindBridgeManager
    
    // 공유 깊이 토글 (Phase 4 핵심)
    @State private var shareMoodStatus = false    // 주간 감정 상태 (🟢🟡🔴)
    @State private var shareMoodGraph = false     // 감정 변화 그래프
    @State private var shareAISummary = false     // AI 분석 요약 (한 줄)
    @State private var shareDetailedAnalysis = false // 7개 항목 상세 분석
    @State private var shareTriggerKeywords = false  // 감정 트리거 키워드
    
    // 공유 주기 (가족만)
    @State private var shareSchedule: ShareSchedule = .weekly
    
    // 상태
    @State private var isActive = true
    @State private var showPreview = false
    @State private var showDeleteConfirm = false
    @State private var showExportView = false
    
    var body: some View {
        NavigationView {
            Form {
                // MARK: - 수신자 정보
                Section {
                    HStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: recipient.type == .family
                                        ? [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")]
                                        : [Color(hexString: "10b981"), Color(hexString: "059669")],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 48, height: 48)
                            .overlay(
                                Text(String(recipient.name.prefix(1)))
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                            )
                        
                        VStack(alignment: .leading) {
                            Text(recipient.name)
                                .font(.headline)
                            Text(recipient.type == .family ? "가족 / 보호자" : "상담사 / 의료진")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Toggle("", isOn: $isActive)
                            .labelsHidden()
                    }
                }
                
                // MARK: - Phase 4 핵심: 공유할 정보 선택 (기본 전부 OFF)
                Section(header: Text("\(recipient.name)에게 공유할 정보"),
                        footer: Text("기본 OFF — 사용자가 직접 켜야 공유됩니다")) {
                    
                    depthToggle(
                        icon: "🟢",
                        title: "주간 감정 상태",
                        description: "안정/주의/위험 신호등",
                        isOn: $shareMoodStatus
                    )
                    
                    depthToggle(
                        icon: "📊",
                        title: "감정 변화 그래프",
                        description: "7일간 감정 추이 차트",
                        isOn: $shareMoodGraph
                    )
                    
                    depthToggle(
                        icon: "✨",
                        title: "AI 분석 요약 (한 줄)",
                        description: "오늘의 감정을 AI가 요약",
                        isOn: $shareAISummary
                    )
                    
                    depthToggle(
                        icon: "📋",
                        title: "7개 항목 상세 분석",
                        description: "원인, 깊이, 패턴, 신체, 관계, 자각, 전망",
                        isOn: $shareDetailedAnalysis
                    )
                    
                    depthToggle(
                        icon: "🔑",
                        title: "감정 트리거 키워드",
                        description: "감정 변화를 유발한 키워드",
                        isOn: $shareTriggerKeywords
                    )
                }
                
                // MARK: - 공유 주기 (가족만)
                if recipient.type == .family {
                    Section(header: Text("공유 주기")) {
                        Picker("주기", selection: $shareSchedule) {
                            ForEach(ShareSchedule.allCases, id: \.self) { schedule in
                                Text(schedule.displayName).tag(schedule)
                            }
                        }
                        .pickerStyle(.segmented)
                    }
                    
                    // MARK: - 즉시 공유 버튼 (가족)
                    Section {
                        Button(action: {
                            bridgeManager.shareToRecipient(recipient) { success, error in
                                if success {
                                    showExportView = false
                                }
                            }
                        }) {
                            HStack {
                                if bridgeManager.isSharing {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                } else {
                                    Image(systemName: "paperplane.fill")
                                }
                                Text(bridgeManager.isSharing ? "공유 중..." : "지금 바로 서버에 공유")
                                    .fontWeight(.bold)
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                        }
                        .disabled(bridgeManager.isSharing)
                        .listRowBackground(
                            LinearGradient(
                                colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                    }
                }
                
                // MARK: - 미리보기 버튼
                Section {
                    Button(action: { showPreview = true }) {
                        HStack {
                            Image(systemName: "eye.fill")
                                .foregroundColor(Color(hexString: "6366f1"))
                            Text("수신자가 볼 화면 미리보기")
                        }
                    }
                }
                
                // MARK: - 위험 영역
                Section {
                    if recipient.type == .counselor {
                        Button(action: { isActive = false }) {
                            HStack {
                                Image(systemName: "pause.circle")
                                Text("접근 해제 (새 데이터 전송 중단)")
                            }
                            .foregroundColor(.orange)
                        }
                    }
                    
                    Button(action: { showDeleteConfirm = true }) {
                        HStack {
                            Image(systemName: "trash")
                            Text("수신자 삭제")
                        }
                        .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("공유 설정")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("닫기") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("저장") {
                        saveSettings()
                        dismiss()
                    }
                    .fontWeight(.bold)
                }
            }
            .onAppear { loadSettings() }
            .sheet(isPresented: $showExportView) {
                MindBridgeExportView()
            }
            .sheet(isPresented: $showPreview) {
                RecipientPreviewView(
                    recipientName: recipient.name,
                    shareMoodStatus: shareMoodStatus,
                    shareMoodGraph: shareMoodGraph,
                    shareAISummary: shareAISummary,
                    shareDetailedAnalysis: shareDetailedAnalysis,
                    shareTriggerKeywords: shareTriggerKeywords
                )
            }
            .alert("수신자를 삭제할까요?", isPresented: $showDeleteConfirm) {
                Button("삭제", role: .destructive) {
                    bridgeManager.removeRecipient(id: recipient.id)
                    dismiss()
                }
                Button("취소", role: .cancel) {}
            } message: {
                Text("\(recipient.name)에 대한 공유 설정이 모두 삭제됩니다.")
            }
        }
    }
    
    func depthToggle(icon: String, title: String, description: String, isOn: Binding<Bool>) -> some View {
        HStack {
            Text(icon)
                .font(.title2)
                .frame(width: 36)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                Text(description)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            Spacer()
            Toggle("", isOn: isOn)
                .labelsHidden()
        }
    }
    
    func loadSettings() {
        let settings = bridgeManager.getDepthSettings(for: recipient.id)
        shareMoodStatus = settings.moodStatus
        shareMoodGraph = settings.moodGraph
        shareAISummary = settings.aiSummary
        shareDetailedAnalysis = settings.detailedAnalysis
        shareTriggerKeywords = settings.triggerKeywords
        shareSchedule = recipient.shareSchedule ?? .weekly
        isActive = recipient.isActive
    }
    
    func saveSettings() {
        bridgeManager.updateDepthSettings(
            for: recipient.id,
            settings: DepthSettings(
                moodStatus: shareMoodStatus,
                moodGraph: shareMoodGraph,
                aiSummary: shareAISummary,
                detailedAnalysis: shareDetailedAnalysis,
                triggerKeywords: shareTriggerKeywords
            )
        )
        bridgeManager.updateRecipient(id: recipient.id, isActive: isActive, schedule: shareSchedule)
    }
}

// MARK: - Phase 4: 수신자가 볼 화면 미리보기
struct RecipientPreviewView: View {
    @Environment(\.dismiss) var dismiss
    let recipientName: String
    let shareMoodStatus: Bool
    let shareMoodGraph: Bool
    let shareAISummary: Bool
    let shareDetailedAnalysis: Bool
    let shareTriggerKeywords: Bool
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // 헤더
                    VStack(spacing: 8) {
                        Text("🌉 마음온 마음 브릿지")
                            .font(.headline)
                            .foregroundColor(Color(hexString: "6366f1"))
                        
                        let userName = UserDefaults.standard.string(forKey: "userNickname") ?? "사용자"
                        Text("\(userName)님의 오늘 마음 상태")
                            .font(.title3)
                            .fontWeight(.bold)
                        
                        Text(formattedToday)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    
                    let hasAny = shareMoodStatus || shareMoodGraph || shareAISummary || shareDetailedAnalysis || shareTriggerKeywords
                    
                    if !hasAny {
                        VStack(spacing: 12) {
                            Image(systemName: "eye.slash")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                            Text("공유할 항목이 없습니다")
                                .foregroundColor(.secondary)
                            Text("설정에서 하나 이상의 항목을 켜주세요")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(40)
                    }
                    
                    if shareMoodStatus {
                        previewCard(title: "주간 감정 상태") {
                            HStack(spacing: 16) {
                                ForEach(["월","화","수","목","금","토","일"], id: \.self) { day in
                                    VStack(spacing: 4) {
                                        Circle()
                                            .fill(.green)
                                            .frame(width: 24, height: 24)
                                        Text(day)
                                            .font(.system(size: 10))
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }
                    
                    if shareMoodGraph {
                        previewCard(title: "감정 변화 그래프") {
                            HStack(alignment: .bottom, spacing: 8) {
                                ForEach(0..<7, id: \.self) { _ in
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(Color(hexString: "6366f1").opacity(0.6))
                                        .frame(width: 28, height: CGFloat.random(in: 20...60))
                                }
                            }
                            .frame(maxWidth: .infinity)
                        }
                    }
                    
                    if shareAISummary {
                        previewCard(title: "AI 분석 요약") {
                            Text("오늘 전반적으로 안정된 감정 상태가 관찰됩니다.")
                                .font(.subheadline)
                                .foregroundColor(.primary)
                        }
                    }
                    
                    if shareDetailedAnalysis {
                        previewCard(title: "7개 항목 상세 분석") {
                            VStack(alignment: .leading, spacing: 6) {
                                ForEach(["원인 분석", "감정 깊이", "감정 패턴", "신체 반응", "관계 영향", "자기 자각", "미래 전망"], id: \.self) { item in
                                    HStack {
                                        Text("•")
                                            .foregroundColor(Color(hexString: "6366f1"))
                                        Text(item)
                                            .font(.caption)
                                    }
                                }
                            }
                        }
                    }
                    
                    if shareTriggerKeywords {
                        previewCard(title: "감정 트리거 키워드") {
                            HStack(spacing: 6) {
                                ForEach(["업무", "가족", "건강"], id: \.self) { keyword in
                                    Text("#\(keyword)")
                                        .font(.caption)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 4)
                                        .background(Color(hexString: "6366f1").opacity(0.1))
                                        .cornerRadius(12)
                                }
                            }
                        }
                    }
                    
                    // 푸터
                    VStack(spacing: 4) {
                        HStack(spacing: 4) {
                            Image(systemName: "lock.fill")
                                .font(.caption2)
                            Text("마음온에서 안전하게 전달됨")
                                .font(.caption2)
                        }
                        .foregroundColor(.secondary)
                        
                        Text("ⓘ 일기 내용은 포함되지 않습니다")
                            .font(.caption2)
                            .foregroundColor(.secondary.opacity(0.7))
                    }
                    .padding()
                }
            }
            .navigationTitle("미리보기")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("닫기") { dismiss() }
                }
            }
        }
    }
    
    func previewCard<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(.secondary)
            content()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .padding(.horizontal)
    }
    
    var formattedToday: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ko_KR")
        formatter.dateFormat = "yyyy년 M월 d일 (E)"
        return formatter.string(from: Date())
    }
}

// MARK: - Phase 5: 공유 이력 보기
struct ShareHistoryView: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var bridgeManager: MindBridgeManager
    
    var body: some View {
        NavigationView {
            List {
                if bridgeManager.shareHistory.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                        Text("공유 이력이 없습니다")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                    .listRowBackground(Color.clear)
                } else {
                    ForEach(bridgeManager.shareHistory) { entry in
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(entry.recipientName)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                Text(entry.sharedItems)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            VStack(alignment: .trailing, spacing: 4) {
                                Text(entry.formattedDate)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                if entry.wasViewed {
                                    HStack(spacing: 2) {
                                        Image(systemName: "eye.fill")
                                            .font(.system(size: 9))
                                        Text("열람됨")
                                            .font(.system(size: 9))
                                    }
                                    .foregroundColor(.blue)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("공유 이력")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("닫기") { dismiss() }
                }
            }
        }
    }
}
