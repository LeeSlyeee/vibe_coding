import SwiftUI

struct RelationalMapView: View {
    @State private var mapData: RelationalMapResponse?
    @State private var isLoading = true
    
    @State private var offsets: [String: CGSize] = [:]
    @State private var selectedNode: RelationalNode?
    @State private var appear = false
    
    var body: some View {
        ZStack {
            // Geist Dark: 별자리 컨셉 다크 배경
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hexString: "111111"),
                    Color(hexString: "171717"),
                    Color(hexString: "111111")
                ]),
                startPoint: .top,
                endPoint: .bottom
            )
            .edgesIgnoringSafeArea(.all)
            
            // 배경 반짝이는 작은 별들
            GeometryReader { geo in
                ForEach(0..<30, id: \.self) { i in
                    Circle()
                        .fill(Color.white.opacity(Double.random(in: 0.1...0.4)))
                        .frame(width: CGFloat.random(in: 1...3), height: CGFloat.random(in: 1...3))
                        .position(
                            x: CGFloat.random(in: 0...geo.size.width),
                            y: CGFloat.random(in: 0...geo.size.height)
                        )
                }
            }
            
            if isLoading {
                VStack(spacing: 20) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                    Text("주변 사람들을 떠올려보고 있어요...")
                        .foregroundColor(.white.opacity(0.7))
                }
            } else if let data = mapData, !data.nodes.isEmpty {
                GeometryReader { geometry in
                    let centerX = geometry.size.width / 2
                    let centerY = geometry.size.height * 0.42 // 살짝 위로 (하단 카드 공간 확보)
                    
                    ZStack {
                        // ─── Links ───
                        ForEach(data.links, id: \.target) { link in
                            if let sourceNode = data.nodes.first(where: { $0.id == link.source }),
                               let targetNode = data.nodes.first(where: { $0.id == link.target }) {
                                let center = CGPoint(x: centerX, y: centerY)
                                let sPoint = sourceNode.id == "Me" ? center : getPosition(for: sourceNode.id, centerX: centerX, centerY: centerY, in: geometry)
                                let tPoint = targetNode.id == "Me" ? center : getPosition(for: targetNode.id, centerX: centerX, centerY: centerY, in: geometry)

                                Path { path in
                                    path.move(to: sPoint)
                                    path.addLine(to: tPoint)
                                }
                                .stroke(
                                    LinearGradient(
                                        gradient: Gradient(colors: [
                                            Color(hexString: sourceNode.color).opacity(0.25),
                                            Color(hexString: targetNode.color).opacity(0.25)
                                        ]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    ),
                                    lineWidth: 1.5
                                )
                            }
                        }
                        
                        // ─── Nodes ───
                        ForEach(data.nodes) { node in
                            let isMe = node.id == "Me"
                            let center = CGPoint(x: centerX, y: centerY)
                            let pos = isMe ? center : getPosition(for: node.id, centerX: centerX, centerY: centerY, in: geometry)
                            let baseSize = CGFloat(node.size)
                            let starSize = isMe ? baseSize * 2.5 : baseSize * 1.8
                            let isSelected = selectedNode?.id == node.id
                            
                            VStack(spacing: 8) {
                                ZStack {
                                    // 외곽 글로우
                                    Circle()
                                        .fill(Color(hexString: node.color).opacity(isSelected ? 0.4 : 0.15))
                                        .frame(width: starSize + 40, height: starSize + 40)
                                        .blur(radius: 15)
                                    
                                    // 중간 글로우
                                    Circle()
                                        .fill(Color(hexString: node.color).opacity(isSelected ? 0.5 : 0.3))
                                        .frame(width: starSize + 20, height: starSize + 20)
                                        .blur(radius: 8)
                                    
                                    // 코어 별
                                    Circle()
                                        .fill(
                                            RadialGradient(
                                                gradient: Gradient(colors: [
                                                    .white,
                                                    Color(hexString: node.color),
                                                    Color(hexString: node.color).opacity(0.7)
                                                ]),
                                                center: .center,
                                                startRadius: 0,
                                                endRadius: starSize / 2
                                            )
                                        )
                                        .frame(width: starSize, height: starSize)
                                        .shadow(color: Color(hexString: node.color).opacity(0.7), radius: isSelected ? 25 : 15, x: 0, y: 0)
                                    
                                    // 선택 링
                                    if isSelected {
                                        Circle()
                                            .stroke(Color.white.opacity(0.6), lineWidth: 2)
                                            .frame(width: starSize + 8, height: starSize + 8)
                                    }
                                }
                                .offset(y: offsets[node.id]?.height ?? 0)
                                .onAppear {
                                    withAnimation(.easeInOut(duration: Double.random(in: 2.5...4.5)).repeatForever(autoreverses: true)) {
                                        offsets[node.id] = CGSize(width: 0, height: Double.random(in: -8...8))
                                    }
                                }
                                .scaleEffect(appear ? (isSelected ? 1.15 : 1.0) : 0.0)
                                .animation(
                                    .spring(response: 0.6, dampingFraction: 0.6)
                                        .delay(isMe ? 0 : Double(data.nodes.firstIndex(where: { $0.id == node.id }) ?? 0) * 0.12),
                                    value: appear
                                )
                                .animation(.spring(response: 0.3), value: isSelected)
                                
                                // 이름 라벨
                                Text(isMe ? "나" : node.id)
                                    .font(.system(size: isMe ? 18 : 15, weight: .bold))
                                    .foregroundColor(.white)
                                    .shadow(color: Color(hexString: node.color).opacity(0.8), radius: 5, x: 0, y: 0)
                                    .shadow(color: .black.opacity(0.5), radius: 3, x: 0, y: 1)
                                
                                if isMe {
                                    Text("✨")
                                        .font(.system(size: 12))
                                }
                            }
                            .position(pos)
                            .onTapGesture {
                                withAnimation(.spring()) {
                                    selectedNode = (selectedNode?.id == node.id) ? nil : node
                                }
                            }
                        }
                    }
                }
                .onAppear {
                    withAnimation {
                        appear = true
                    }
                }
                
                // ─── 하단 인물 정보 카드 ───
                VStack {
                    Spacer()
                    
                    if let selected = selectedNode {
                        VStack(alignment: .leading, spacing: 12) {
                            // 상단: 이름 + 색상 인디케이터
                            HStack(spacing: 10) {
                                Circle()
                                    .fill(Color(hexString: selected.color))
                                    .frame(width: 14, height: 14)
                                    .shadow(color: Color(hexString: selected.color), radius: 5)
                                
                                Text(selected.id == "Me" ? "나" : selected.id)
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                
                                Spacer()
                                
                                // 언급 횟수 뱃지
                                if let count = selected.mentionCount, selected.id != "Me" {
                                    HStack(spacing: 4) {
                                        Image(systemName: "text.bubble.fill")
                                            .font(.caption2)
                                        Text("\(count)회 언급")
                                            .font(.caption)
                                            .fontWeight(.medium)
                                    }
                                    .foregroundColor(Color(hexString: selected.color))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 4)
                                    .background(Color(hexString: selected.color).opacity(0.15))
                                    .cornerRadius(12)
                                }
                            }
                            
                            // 고유 요약 메시지
                            if let summary = selected.summary {
                                Text(summary)
                                    .font(.subheadline)
                                    .foregroundColor(.white.opacity(0.85))
                                    .lineSpacing(4)
                            }
                            
                            // 마지막 언급일
                            if let lastSeen = selected.lastSeen, selected.id != "Me" {
                                HStack(spacing: 4) {
                                    Image(systemName: "calendar")
                                        .font(.caption2)
                                    Text("마지막 언급: \(lastSeen)")
                                        .font(.caption)
                                }
                                .foregroundColor(.white.opacity(0.4))
                            }
                        }
                        .padding(20)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(
                            RoundedRectangle(cornerRadius: 20)
                                .fill(Color.white.opacity(0.1))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 20)
                                        .stroke(Color(hexString: selected.color).opacity(0.3), lineWidth: 1)
                                )
                        )
                        .padding(.horizontal, 20)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                    } else {
                        // 미선택 시 안내
                        HStack(spacing: 6) {
                            Image(systemName: "hand.tap.fill")
                                .foregroundColor(.white.opacity(0.4))
                            Text("별을 터치하면 관계 정보를 볼 수 있어요")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.4))
                        }
                    }
                }
                .padding(.bottom, 30)
                .animation(.spring(response: 0.4), value: selectedNode?.id)
                
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 50))
                        .foregroundColor(.white.opacity(0.4))
                    Text("아직 충분한 관계 데이터가 없어요.")
                        .foregroundColor(.white.opacity(0.7))
                    Text("일기에 자주 만난 사람이나 떠오르는 사람을 적어보세요.")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.5))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }
            }
        }
        .onAppear {
            fetchRelationalMap()
        }
    }
    
    // ─── 원형 레이아웃 ───
    private func getPosition(for id: String, centerX: CGFloat, centerY: CGFloat, in geometry: GeometryProxy) -> CGPoint {
        guard let data = mapData else { return .zero }
        let center = CGPoint(x: centerX, y: centerY)
        
        if id == "Me" { return center }
        
        let otherNodes = data.nodes.filter { $0.id != "Me" }
        guard let index = otherNodes.firstIndex(where: { $0.id == id }) else { return center }
        
        let total = otherNodes.count
        let angle = (Double(index) / Double(total)) * 2 * .pi - .pi / 2
        let radius = min(geometry.size.width, geometry.size.height) * 0.34
        
        let x = centerX + CGFloat(cos(angle)) * radius
        let y = centerY + CGFloat(sin(angle)) * radius
        
        return CGPoint(x: x, y: y)
    }
    
    private func fetchRelationalMap() {
        isLoading = true
        APIService.shared.fetchMyRelationalMap { result in
            DispatchQueue.main.async {
                self.isLoading = false
                if let result = result, !result.nodes.isEmpty {
                    self.mapData = result
                } else {
                    self.mapData = nil // 서버 데이터 없음 → 안내 표시
                }
            }
        }
    }
    
    // ─── 데모 데이터 ───
    static let demoMapData = RelationalMapResponse(
        nodes: [
            RelationalNode(id: "Me", group: 0, size: 35, color: "FFD700",
                          mentionCount: nil, lastSeen: nil,
                          summary: "당신은 이 별자리의 중심이에요. 소중한 사람들이 주변을 밝히고 있어요."),
            RelationalNode(id: "엄마", group: 1, size: 26, color: "FF6B9D",
                          mentionCount: 12, lastSeen: "2026-03-04",
                          summary: "이번 달 가장 많이 떠올린 사람이에요. 안부 전화 한 통은 어떨까요? "),
            RelationalNode(id: "민수", group: 1, size: 22, color: "45B7D1",
                          mentionCount: 7, lastSeen: "2026-03-03",
                          summary: "최근 민수와 함께한 시간 이야기가 많았어요. 좋은 에너지를 주는 친구네요."),
            RelationalNode(id: "지현", group: 2, size: 19, color: "96CEB4",
                          mentionCount: 5, lastSeen: "2026-03-01",
                          summary: "주로 고민 상담이나 진지한 대화에서 등장했어요. 마음을 나누는 관계인 것 같아요."),
            RelationalNode(id: "팀장님", group: 3, size: 21, color: "FFEAA7",
                          mentionCount: 9, lastSeen: "2026-03-05",
                          summary: "업무 관련 언급이 많았어요. 이번 주 특히 자주 등장했네요."),
            RelationalNode(id: "수아", group: 2, size: 16, color: "DDA0DD",
                          mentionCount: 3, lastSeen: "2026-02-25",
                          summary: "최근 언급이 줄었어요. 오랜만에 연락해보는 건 어떨까요?"),
            RelationalNode(id: "강아지", group: 1, size: 18, color: "F39C12",
                          mentionCount: 6, lastSeen: "2026-03-05",
                          summary: "매일 함께하는 소중한 존재! 산책 이야기가 기분을 밝게 해주고 있어요."),
        ],
        links: [
            RelationalLink(source: "Me", target: "엄마", value: 12),
            RelationalLink(source: "Me", target: "민수", value: 7),
            RelationalLink(source: "Me", target: "지현", value: 5),
            RelationalLink(source: "Me", target: "팀장님", value: 9),
            RelationalLink(source: "Me", target: "수아", value: 3),
            RelationalLink(source: "Me", target: "강아지", value: 6),
        ]
    )
}
