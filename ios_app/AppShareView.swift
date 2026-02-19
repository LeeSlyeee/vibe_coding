
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
                                TextField("6자리 코드", text: $inputCode)
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
                VStack(spacing: 30) {
                    Spacer()
                    
                    VStack(spacing: 15) {
                        Text("내 공유 코드")
                            .font(.headline)
                            .foregroundColor(.gray)
                        
                        Text(shareManager.myCode.isEmpty ? "------" : shareManager.myCode)
                            .font(.system(size: 40, weight: .heavy, design: .monospaced))
                            .foregroundColor(.blue)
                            .tracking(5)
                        
                        if !shareManager.myCode.isEmpty {
                            Text("10분간 유효합니다.")
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                    .padding(40)
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
                                        // [DEBUG] Show ID to distinguish
                                        Text(guardian.id)
                                            .font(.caption2)
                                            .foregroundColor(.gray.opacity(0.5))
                                            
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
                    
                    Spacer()
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
    }
    
    func formatConnDate(_ str: String) -> String {
        return String(str.prefix(10))
    }
}
