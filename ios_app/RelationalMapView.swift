import SwiftUI

struct RelationalMapView: View {
    @State private var mapData: RelationalMapResponse?
    @State private var isLoading = true
    
    // GeometryReader variables
    @State private var offsets: [String: CGSize] = [:]
    
    var body: some View {
        ZStack {
            Color.bgMain.edgesIgnoringSafeArea(.all)
            
            if isLoading {
                VStack(spacing: 20) {
                    ProgressView()
                    Text("주변 사람들을 떠올려보고 있어요...")
                        .foregroundColor(.gray)
                }
            } else if let data = mapData, !data.nodes.isEmpty {
                GeometryReader { geometry in
                    ZStack {
                        // 1. Links
                        ForEach(data.links, id: \.target) { link in
                            if let sourceNode = data.nodes.first(where: { $0.id == link.source }),
                               let targetNode = data.nodes.first(where: { $0.id == link.target }) {
                                Path { path in
                                    let isSourceMe = sourceNode.id == "Me"
                                    let center = CGPoint(x: geometry.size.width / 2, y: geometry.size.height / 2)
                                    
                                    // Me is always center
                                    let sPoint = isSourceMe ? center : getPosition(for: sourceNode.id, in: geometry)
                                    let tPoint = targetNode.id == "Me" ? center : getPosition(for: targetNode.id, in: geometry)
                                    
                                    path.move(to: sPoint)
                                    path.addLine(to: tPoint)
                                }
                                .stroke(Color.gray.opacity(0.3), lineWidth: 2)
                            }
                        }
                        
                        // 2. Nodes
                        ForEach(data.nodes) { node in
                            let isMe = node.id == "Me"
                            let pos = isMe ? CGPoint(x: geometry.size.width / 2, y: geometry.size.height / 2) : getPosition(for: node.id, in: geometry)
                            
                            VStack(spacing: 4) {
                                Circle()
                                    .fill(Color(hexString: node.color) ?? .gray)
                                    .frame(width: CGFloat(node.size * 2), height: CGFloat(node.size * 2))
                                    .shadow(color: Color(hexString: node.color)?.opacity(0.5) ?? .clear, radius: 10, x: 0, y: 0)
                                    // Float Animation
                                    .offset(y: offsets[node.id]?.height ?? 0)
                                    .onAppear {
                                        if !isMe {
                                            withAnimation(.easeInOut(duration: Double.random(in: 2.0...4.0)).repeatForever(autoreverses: true)) {
                                                offsets[node.id] = CGSize(width: 0, height: Double.random(in: -10...10))
                                            }
                                        }
                                    }
                                
                                Text(isMe ? "나" : node.id)
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundColor(.primary)
                            }
                            .position(pos)
                        }
                    }
                }
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "person.2.slash")
                        .font(.system(size: 40))
                        .foregroundColor(.gray)
                    Text("아직 충분한 관계 데이터가 없어요.")
                        .foregroundColor(.secondary)
                    Text("일기에 자주 만난 사람이나 떠오르는 사람을 적어보세요.")
                        .font(.caption)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                }
            }
        }
        .onAppear {
            fetchRelationalMap()
        }
        .navigationTitle("나의 마음 별자리")
    }
    
    // Simple force-directed layout approximation (static circular layout)
    private func getPosition(for id: String, in geometry: GeometryProxy) -> CGPoint {
        guard let data = mapData else { return .zero }
        let center = CGPoint(x: geometry.size.width / 2, y: geometry.size.height / 2)
        
        if id == "Me" { return center }
        
        let otherNodes = data.nodes.filter { $0.id != "Me" }
        guard let index = otherNodes.firstIndex(where: { $0.id == id }) else { return center }
        
        let total = otherNodes.count
        let angle = (Double(index) / Double(total)) * 2 * .pi
        let radius = min(geometry.size.width, geometry.size.height) * 0.35
        
        let x = center.x + CGFloat(cos(angle)) * radius
        let y = center.y + CGFloat(sin(angle)) * radius
        
        return CGPoint(x: x, y: y)
    }
    
    private func fetchRelationalMap() {
        isLoading = true
        APIService.shared.fetchMyRelationalMap { result in
            DispatchQueue.main.async {
                self.isLoading = false
                if let result = result {
                    self.mapData = result
                }
            }
        }
    }
}
