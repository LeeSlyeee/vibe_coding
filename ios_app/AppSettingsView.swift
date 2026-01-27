import SwiftUI

struct AppSettingsView: View {
    @StateObject private var b2gManager = B2GManager.shared
    @State private var inputCode = ""
    @State private var showAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            List {
                // Section 1: 프로필
                Section(header: Text("내 정보")) {
                    HStack {
                        Image(systemName: "person.circle.fill")
                            .font(.largeTitle)
                            .foregroundColor(.gray)
                        VStack(alignment: .leading) {
                            Text("로컬 프로필")
                                .font(.headline)
                            Text("On-Device Mode")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 8)
                }
                
                // Section 2: B2G 연동 (핵심 기능)
                Section(header: Text("기관 연동 (B2G)")) {
                    if b2gManager.isLinked {
                        // 연동 된 상태
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                Text("보건소 연동됨")
                                    .font(.headline)
                                    .foregroundColor(.green)
                            }
                            
                            Text("현재 담당 선생님과 연결되어 있습니다.")
                                .font(.subheadline)
                            
                            HStack {
                                Text("연동 코드:")
                                    .foregroundColor(.gray)
                                Text(b2gManager.centerCode)
                                    .font(.system(.body, design: .monospaced))
                                    .fontWeight(.bold)
                            }
                            
                            if b2gManager.lastSyncDate > 0 {
                                Text("마지막 전송: \(Date(timeIntervalSince1970: b2gManager.lastSyncDate).formatted())")
                                    .font(.caption2)
                                    .foregroundColor(.gray)
                            }
                            
                            Button(action: {
                                b2gManager.disconnect()
                            }) {
                                Text("연동 해제")
                                    .foregroundColor(.red)
                                    .font(.caption)
                            }
                            .padding(.top, 4)
                        }
                        .padding(.vertical, 8)
                        
                    } else {
                        // 연동 안 된 상태
                        VStack(alignment: .leading, spacing: 10) {
                            Text("보건소/상담센터 연결하기")
                                .font(.headline)
                            Text("담당 선생님께 전달받은 코드를 입력하세요.")
                                .font(.caption)
                                .foregroundColor(.gray)
                            
                            HStack {
                                TextField("예: SEOUL-001", text: $inputCode)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    #if os(iOS)
                                    .textInputAutocapitalization(.characters)
                                    #endif
                                
                                Button(action: {
                                    b2gManager.connect(code: inputCode) { success, message in
                                        alertMessage = message
                                        showAlert = true
                                    }
                                }) {
                                    if b2gManager.isSyncing {
                                        ProgressView()
                                    } else {
                                        Text("연결")
                                            .fontWeight(.bold)
                                    }
                                }
                                .disabled(inputCode.isEmpty || b2gManager.isSyncing)
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }
                
                // Section 3: 앱 정보
                Section(header: Text("앱 정보")) {
                    HStack {
                        Text("버전")
                        Spacer()
                        Text("1.0.0 (On-Device Al)")
                            .foregroundColor(.gray)
                    }
                    HStack {
                        Text("개발자")
                        Spacer()
                        Text("Maum-on Team")
                            .foregroundColor(.gray)
                    }
                    
                    // [Hidden Feature] 개발자용 데이터 생성 버튼
                    Button(action: {
                        seedData()
                    }) {
                        Text("[개발자용] 테스트 데이터 생성 (Demo)")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
            }
            .navigationTitle("설정")
            .alert(isPresented: $showAlert) {
                Alert(title: Text("알림"), message: Text(alertMessage), dismissButton: .default(Text("확인")))
            }
        }
    }
    
    // 이스터에그 함수
    func seedData() {
        DataSeeder.shared.seedDummyData { count in
            alertMessage = "테스트용 일기 \(count)개가 생성되었습니다.\n캘린더와 통계 탭을 확인해보세요."
            showAlert = true
        }
    }
}
