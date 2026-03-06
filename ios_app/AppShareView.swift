
import SwiftUI

struct AppShareView: View {
    @StateObject var shareManager = ShareManager.shared
    @State private var selectedTab = 0 // 0: Connect, 1: Share
    
    // Connect Inputs
    @State private var inputCode = ""
    @State private var isConnecting = false
    @State private var alertMsg = ""
    @State private var showAlert = false
    
    // Share State
    @State private var generatedCode = ""
    
    // [P1-수정4] Alert Share Scope
    @State private var shareMood: Bool = true
    @State private var shareReport: Bool = true
    @State private var shareCrisis: Bool = true
    
    // [Phase 2] 마음 브릿지 리포트 Export
    @State private var showExportView = false
    @State private var showPaywallForExport = false
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Custom Segmented Control
            HStack {
                Button(action: { selectedTab = 0 }) {
                    VStack {
                        Text("연결하기 (보호자)")
                            .fontWeight(selectedTab == 0 ? .bold : .regular)
                            .foregroundColor(selectedTab == 0 ? .blue : .gray)
                        Rectangle()
                            .fill(selectedTab == 0 ? Color.blue : Color.clear)
                            .frame(height: 2)
                    }
                }
                .frame(maxWidth: .infinity)
                
                Button(action: { selectedTab = 1 }) {
                    VStack {
                        Text("공유하기 (내담자)")
                            .fontWeight(selectedTab == 1 ? .bold : .regular)
                            .foregroundColor(selectedTab == 1 ? .blue : .gray)
                        Rectangle()
                            .fill(selectedTab == 1 ? Color.blue : Color.clear)
                            .frame(height: 2)
                    }
                }
                .frame(maxWidth: .infinity)
            }
            .padding(.top)
            .background(Color(.systemBackground))
            
            // Content
            if selectedTab == 0 {
                // Connect Tab
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        
                        // Input Section
                        VStack(alignment: .leading, spacing: 10) {
                            Text("초대 코드 입력")
                                .font(.headline)
                            
                            HStack {
                                TextField("8자리 코드", text: $inputCode)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    #if os(iOS)
                                    .textInputAutocapitalization(.characters)
                                    #endif
                                
                                Button(action: {
                                    isConnecting = true
                                    shareManager.connectWithCode(inputCode) { success, msg in
                                        isConnecting = false
                                        alertMsg = msg
                                        showAlert = true
                                        if success { inputCode = "" }
                                    }
                                }) {
                                    if isConnecting {
                                        ProgressView()
                                    } else {
                                        Text("연결")
                                            .fontWeight(.bold)
                                    }
                                }
                                .disabled(inputCode.isEmpty || isConnecting)
                            }
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(12)
                        
                        // List Section
                        VStack(alignment: .leading) {
                            HStack {
                                Text("연결된 사용자 목록")
                                    .font(.headline)
                                Spacer()
                                Button(action: {
                                    shareManager.fetchList(role: "viewer")
                                }) {
                                    Image(systemName: "arrow.clockwise")
                                        .foregroundColor(.blue)
                                        .padding(8)
                                        .background(Color.blue.opacity(0.1))
                                        .clipShape(Circle())
                                }
                            }
                            .padding(.horizontal)
                            
                            if shareManager.connectedUsers.isEmpty {
                                Text("연결된 사용자가 없습니다.")
                                    .foregroundColor(.gray)
                                    .padding()
                                    .frame(maxWidth: .infinity, alignment: .center)
                            } else {
                                ForEach(shareManager.connectedUsers) { user in
                                    NavigationLink(destination: SharedStatsView(targetId: user.id, targetName: user.name)) {
                                        HStack {
                                            VStack(alignment: .leading) {
                                                Text(user.name)
                                                    .font(.headline)
                                                    .foregroundColor(.primary)
                                                Text("연결됨: \(formatConnDate(user.connectedAt))")
                                                    .font(.caption)
                                                    .foregroundColor(.gray)
                                            }
                                            Spacer()
                                            Image(systemName: "chevron.right")
                                                .foregroundColor(.gray)
                                        }
                                        .padding()
                                        .background(Color(.systemBackground))
                                        .cornerRadius(12)
                                        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
                                    }
                                }
                            }
                        }
                    }
                    .padding()
                }
                .onAppear {
                    shareManager.fetchList()
                }
                
            } else {
                // Share Tab
                ScrollView {
                VStack(spacing: 20) {
                    
                    VStack(spacing: 15) {
                        Text("내 공유 코드")
                            .font(.headline)
                            .foregroundColor(.gray)
                        
                        Text(shareManager.myCode.isEmpty ? "– – – – – – – –" : shareManager.myCode)
                            .font(.system(size: 28, weight: .heavy, design: .monospaced))
                            .foregroundColor(.blue)
                            .tracking(3)
                        
                        if !shareManager.myCode.isEmpty {
                            Text("10분간 유효합니다.")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                    .padding(.vertical, 24)
                    .padding(.horizontal)
                    .background(Color(.systemBackground))
                    .cornerRadius(20)
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    
                    Button(action: {
                        shareManager.generateCode { _ in }
                    }) {
                        Text(shareManager.myCode.isEmpty ? "코드 발급받기" : "코드 재생성")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .cornerRadius(14)
                    }
                    .padding(.horizontal, 40)
                    
                    Text("코드가 입력되면 별도의 승인 없이\n상대방과 즉시 연결됩니다.")
                        .multilineTextAlignment(.center)
                        .font(.caption)
                        .foregroundColor(.gray)
                    
                    // Connected Guardians List
                    VStack(alignment: .leading, spacing: 10) {
                        // Header with Refresh
                        HStack {
                            Text("연결된 보호자")
                                .font(.headline)
                            Spacer()
                            Button(action: {
                                shareManager.fetchList(role: "sharer")
                            }) {
                                Image(systemName: "arrow.clockwise")
                                    .foregroundColor(.blue)
                                    .padding(8)
                                    .background(Color.blue.opacity(0.1))
                                    .clipShape(Circle())
                            }
                        }
                        .padding(.horizontal)
                        
                        if shareManager.myGuardians.isEmpty {
                            VStack {
                                Text("아직 연결된 보호자가 없습니다.")
                                    .font(.subheadline)
                                    .foregroundColor(.gray)
                                    .multilineTextAlignment(.center)
                                    .padding()
                                
                                // [DEBUG UI] to see why list is empty
                                if !shareManager.lastErrorMessage.isEmpty {
                                    Text("⚠️ 에러: \(shareManager.lastErrorMessage)")
                                        .font(.caption)
                                        .foregroundColor(.red)
                                        .padding(.top, 5)
                                }
                                
                                Button(action: {
                                    shareManager.fetchList(role: "sharer")
                                }) {
                                    Text("새로고침 (Retry)")
                                        .font(.caption)
                                        .foregroundColor(.blue)
                                        .padding(8)
                                        .background(Color.blue.opacity(0.1))
                                        .cornerRadius(8)
                                }
                                .padding(.top, 10)
                            }
                            .frame(maxWidth: .infinity, alignment: .center)
                        } else {
                            ForEach(shareManager.myGuardians) { guardian in
                                HStack {
                                    VStack(alignment: .leading) {
                                        Text(guardian.name)
                                            .font(.subheadline)
                                            .fontWeight(.medium)

                                            
                                        Text("연결됨: \(formatConnDate(guardian.connectedAt))")
                                            .font(.caption)
                                            .foregroundColor(.gray)
                                    }
                                    Spacer()
                                    Image(systemName: "person.2.fill")
                                        .foregroundColor(.blue)
                                        .padding(.trailing, 8)
                                    
                                    // [DELETE BUTTON]
                                    Button(action: {
                                        shareManager.disconnect(targetId: guardian.id) { success in
                                            // Handle completion if needed
                                        }
                                    }) {
                                        Image(systemName: "trash")
                                            .foregroundColor(.red)
                                            .padding(8)
                                            .background(Color.red.opacity(0.1))
                                            .clipShape(Circle())
                                    }
                                }
                                .padding()
                                .background(Color(.secondarySystemBackground))
                                .cornerRadius(10)
                                .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
                                .padding(.horizontal)
                            }
                        }
                    }
                    .padding(.top)
                    
                    // [P1-수정4] 보호자 알림 공유 범위 설정
                    if !shareManager.myGuardians.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("🔔 보호자에게 공유할 알림")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            Text("보호자에게 전달되는 정보의 범위를 설정합니다.")
                                .font(.caption)
                                .foregroundColor(.gray)
                                .padding(.horizontal)
                            
                            VStack(spacing: 0) {
                                ShareToggleRow(
                                    icon: "🌡️",
                                    title: "기분 온도 알림",
                                    subtitle: "매일의 감정 온도를 공유합니다",
                                    isOn: $shareMood
                                ) { newValue in
                                    updateAllGuardiansScope(shareMood: newValue)
                                }
                                
                                Divider().padding(.leading, 50)
                                
                                ShareToggleRow(
                                    icon: "📊",
                                    title: "분석 리포트",
                                    subtitle: "주간/월간 감정 분석을 공유합니다",
                                    isOn: $shareReport
                                ) { newValue in
                                    updateAllGuardiansScope(shareReport: newValue)
                                }
                                
                                Divider().padding(.leading, 50)
                                
                                ShareToggleRow(
                                    icon: "🚨",
                                    title: "위기 감지 알림",
                                    subtitle: "위기 신호 감지 시 즉시 알립니다",
                                    isOn: $shareCrisis
                                ) { newValue in
                                    updateAllGuardiansScope(shareCrisis: newValue)
                                }
                            }
                            .background(Color(.systemBackground))
                            .cornerRadius(12)
                            .padding(.horizontal)
                            
                            if !shareCrisis {
                                HStack {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .foregroundColor(.orange)
                                    Text("위기 알림이 꺼져 있으면 위급 상황에서 보호자가 알림을 받지 못합니다.")
                                        .font(.caption)
                                        .foregroundColor(.orange)
                                }
                                .padding(.horizontal)
                            }
                        }
                        .padding(.top, 16)
                    }
                    
                    // [Phase 2] 마음 브릿지 리포트 공유 카드
                    VStack(spacing: 12) {
                        Button(action: {
                            let hasAccess = SubscriptionManager.shared.hasMindBridgeAccess
                            if hasAccess {
                                showExportView = true
                            } else {
                                showPaywallForExport = true
                            }
                        }) {
                            HStack(spacing: 15) {
                                ZStack {
                                    Circle()
                                        .fill(
                                            LinearGradient(
                                                colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .frame(width: 44, height: 44)
                                    Image(systemName: "square.and.arrow.up")
                                        .foregroundColor(.white)
                                        .font(.system(size: 18))
                                }
                                
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text("🌉 감정 리포트 공유")
                                            .font(.headline)
                                            .fontWeight(.bold)
                                            .foregroundColor(Color(hexString: "6366f1"))
                                        if !SubscriptionManager.shared.hasMindBridgeAccess {
                                            Text("PRO")
                                                .font(.system(size: 9, weight: .bold))
                                                .foregroundColor(.white)
                                                .padding(.horizontal, 6)
                                                .padding(.vertical, 2)
                                                .background(Color(hexString: "6366f1"))
                                                .cornerRadius(4)
                                        }
                                    }
                                    Text("카카오톡·메시지로 감정 상태 이미지 전송")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundColor(.gray)
                            }
                            .padding()
                            .background(Color(.systemBackground))
                            .cornerRadius(12)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 16)
                    
                }
                .padding(.vertical)
                }
                .background(Color(.systemGroupedBackground))
                .onAppear {
                    shareManager.fetchList(role: "sharer")
                }
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("공유 및 연결")
        .alert(isPresented: $showAlert) {
            Alert(title: Text("알림"), message: Text(alertMsg), dismissButton: .default(Text("확인")))
        }
        .sheet(isPresented: $showExportView) {
            MindBridgeExportView()
        }
        .sheet(isPresented: $showPaywallForExport) {
            MindBridgePaywallView(isPresented: $showPaywallForExport)
        }
    }
    
    func formatConnDate(_ str: String) -> String {
        return String(str.prefix(10))
    }
    
    // [P1-수정4] 모든 보호자에게 공유 범위 일괄 업데이트
    func updateAllGuardiansScope(shareMood: Bool? = nil, shareReport: Bool? = nil, shareCrisis: Bool? = nil) {
        for guardian in shareManager.myGuardians {
            shareManager.updateShareScope(
                viewerId: guardian.id,
                shareMood: shareMood,
                shareReport: shareReport,
                shareCrisis: shareCrisis
            ) { _ in }
        }
    }
}

// [P1-수정4] 토글 행 서브컴포넌트
struct ShareToggleRow: View {
    let icon: String
    let title: String
    let subtitle: String
    @Binding var isOn: Bool
    let onChange: (Bool) -> Void
    
    var body: some View {
        HStack {
            Text(icon)
                .font(.title2)
                .frame(width: 36)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(subtitle)
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            Spacer()
            Toggle("", isOn: $isOn)
                .labelsHidden()
                .onChange(of: isOn) { newValue in
                    onChange(newValue)
                }
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
    }
}
