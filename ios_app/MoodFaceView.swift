
import SwiftUI

// MARK: - ☕ Warm Journal 스타일 감정 이모지 (벡터 기반)
// 참조 목업 이미지 기반 — 귀여운 미니멀 라인아트 얼굴
// 큰 이목구비 + 굵은 선 + 둥근 비율

struct MoodFaceView: View {
    let level: Int
    var size: CGFloat = 40
    
    private var faceColor: Color {
        getMoodAsset(level: level).color
    }
    
    // Geist Dark Gray #171717
    private let lineColor = Color(red: 23/255, green: 23/255, blue: 23/255)
    
    var body: some View {
        ZStack {
            // 배경 원
            Circle()
                .fill(faceColor)
                .frame(width: size, height: size)
            
            // 얼굴 표정
            Canvas { context, canvasSize in
                let cx = canvasSize.width / 2
                let cy = canvasSize.height / 2
                
                switch level {
                case 1: drawAngry(context: context, cx: cx, cy: cy)
                case 2: drawSad(context: context, cx: cx, cy: cy)
                case 3: drawNeutral(context: context, cx: cx, cy: cy)
                case 4: drawCalm(context: context, cx: cx, cy: cy)
                case 5: drawHappy(context: context, cx: cx, cy: cy)
                default: drawNeutral(context: context, cx: cx, cy: cy)
                }
            }
            .frame(width: size, height: size)
        }
    }
    
    // MARK: - 공통 헬퍼
    
    /// 큰 점 눈 그리기
    private func drawDotEyes(_ context: GraphicsContext, cx: CGFloat, cy: CGFloat, yOffset: CGFloat = 0.02) {
        let eyeR = size * 0.065
        let eyeSpacing = size * 0.17
        let eyeY = cy - size * yOffset
        
        context.fill(
            Path(ellipseIn: CGRect(
                x: cx - eyeSpacing - eyeR,
                y: eyeY - eyeR,
                width: eyeR * 2, height: eyeR * 2
            )),
            with: .color(lineColor)
        )
        context.fill(
            Path(ellipseIn: CGRect(
                x: cx + eyeSpacing - eyeR,
                y: eyeY - eyeR,
                width: eyeR * 2, height: eyeR * 2
            )),
            with: .color(lineColor)
        )
    }
    
    /// ∪ 모양 감은 눈 (편안/행복용)
    private func drawClosedEyes(_ context: GraphicsContext, cx: CGFloat, cy: CGFloat, eyeWidth: CGFloat = 0.10, depth: CGFloat = 0.06) {
        let lw = size * 0.055
        let eyeSpacing = size * 0.17
        let eyeY = cy - size * 0.02
        let hw = size * eyeWidth  // 눈 반 너비
        let d = size * depth      // 곡선 깊이
        
        // 왼쪽 감은 눈 ∪
        var leftEye = Path()
        leftEye.move(to: CGPoint(x: cx - eyeSpacing - hw, y: eyeY))
        leftEye.addQuadCurve(
            to: CGPoint(x: cx - eyeSpacing + hw, y: eyeY),
            control: CGPoint(x: cx - eyeSpacing, y: eyeY + d)
        )
        context.stroke(
            leftEye, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
        
        // 오른쪽 감은 눈 ∪
        var rightEye = Path()
        rightEye.move(to: CGPoint(x: cx + eyeSpacing - hw, y: eyeY))
        rightEye.addQuadCurve(
            to: CGPoint(x: cx + eyeSpacing + hw, y: eyeY),
            control: CGPoint(x: cx + eyeSpacing, y: eyeY + d)
        )
        context.stroke(
            rightEye, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
    
    // MARK: - Level 1: 화남 — 점 눈 + V자 곡선 눈썹 + 아래로 굽은 입
    
    private func drawAngry(context: GraphicsContext, cx: CGFloat, cy: CGFloat) {
        let lw = size * 0.055
        
        // 눈 (큰 점)
        drawDotEyes(context, cx: cx, cy: cy, yOffset: 0.0)
        
        // 눈썹 — 안쪽으로 기울어진 곡선형 V자
        let browLw = size * 0.055
        let eyeSpacing = size * 0.17
        
        // 왼쪽 눈썹: 바깥쪽 위 → 안쪽 아래 (살짝 곡선)
        var leftBrow = Path()
        leftBrow.move(to: CGPoint(x: cx - eyeSpacing - size * 0.10, y: cy - size * 0.14))
        leftBrow.addQuadCurve(
            to: CGPoint(x: cx - eyeSpacing + size * 0.06, y: cy - size * 0.20),
            control: CGPoint(x: cx - eyeSpacing - size * 0.02, y: cy - size * 0.14)
        )
        context.stroke(
            leftBrow, with: .color(lineColor),
            style: StrokeStyle(lineWidth: browLw, lineCap: .round)
        )
        
        // 오른쪽 눈썹: 안쪽 아래 → 바깥쪽 위 (좌우 대칭)
        var rightBrow = Path()
        rightBrow.move(to: CGPoint(x: cx + eyeSpacing + size * 0.10, y: cy - size * 0.14))
        rightBrow.addQuadCurve(
            to: CGPoint(x: cx + eyeSpacing - size * 0.06, y: cy - size * 0.20),
            control: CGPoint(x: cx + eyeSpacing + size * 0.02, y: cy - size * 0.14)
        )
        context.stroke(
            rightBrow, with: .color(lineColor),
            style: StrokeStyle(lineWidth: browLw, lineCap: .round)
        )
        
        // 입 — 아래로 굽은 큰 곡선 (찡그린 입)
        var mouth = Path()
        mouth.move(to: CGPoint(x: cx - size * 0.14, y: cy + size * 0.20))
        mouth.addQuadCurve(
            to: CGPoint(x: cx + size * 0.14, y: cy + size * 0.20),
            control: CGPoint(x: cx, y: cy + size * 0.12)
        )
        context.stroke(
            mouth, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
    
    // MARK: - Level 2: 우울 — 점 눈 + 물결 처진 눈썹 + 작은 입꼬리 처짐
    
    private func drawSad(context: GraphicsContext, cx: CGFloat, cy: CGFloat) {
        let lw = size * 0.055
        
        // 눈 (큰 점)
        drawDotEyes(context, cx: cx, cy: cy, yOffset: 0.0)
        
        // 눈썹 — 안쪽이 올라가고 바깥쪽이 처지는 걱정스러운 곡선(~)
        let browLw = size * 0.05
        let eyeSpacing = size * 0.17
        
        // 왼쪽 눈썹: 안쪽(높음) → 바깥(낮음), 중간이 위로 볼록
        var leftBrow = Path()
        leftBrow.move(to: CGPoint(x: cx - eyeSpacing + size * 0.08, y: cy - size * 0.18))
        leftBrow.addQuadCurve(
            to: CGPoint(x: cx - eyeSpacing - size * 0.10, y: cy - size * 0.12),
            control: CGPoint(x: cx - eyeSpacing - size * 0.02, y: cy - size * 0.22)
        )
        context.stroke(
            leftBrow, with: .color(lineColor),
            style: StrokeStyle(lineWidth: browLw, lineCap: .round)
        )
        
        // 오른쪽 눈썹: 안쪽(높음) → 바깥(낮음), 중간이 위로 볼록 (좌우 대칭)
        var rightBrow = Path()
        rightBrow.move(to: CGPoint(x: cx + eyeSpacing - size * 0.08, y: cy - size * 0.18))
        rightBrow.addQuadCurve(
            to: CGPoint(x: cx + eyeSpacing + size * 0.10, y: cy - size * 0.12),
            control: CGPoint(x: cx + eyeSpacing + size * 0.02, y: cy - size * 0.22)
        )
        context.stroke(
            rightBrow, with: .color(lineColor),
            style: StrokeStyle(lineWidth: browLw, lineCap: .round)
        )
        
        // 입 — 작은 입꼬리 처짐
        var mouth = Path()
        mouth.move(to: CGPoint(x: cx - size * 0.10, y: cy + size * 0.20))
        mouth.addQuadCurve(
            to: CGPoint(x: cx + size * 0.10, y: cy + size * 0.20),
            control: CGPoint(x: cx, y: cy + size * 0.14)
        )
        context.stroke(
            mouth, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
    
    // MARK: - Level 3: 보통 — 굵은 대시(—) 눈 + 일자 입 (눈썹 없음)
    
    private func drawNeutral(context: GraphicsContext, cx: CGFloat, cy: CGFloat) {
        let lw = size * 0.055
        let eyeSpacing = size * 0.17
        let eyeY = cy - size * 0.02
        let dashW = size * 0.08
        
        // 왼쪽 대시 눈
        var leftEye = Path()
        leftEye.move(to: CGPoint(x: cx - eyeSpacing - dashW, y: eyeY))
        leftEye.addLine(to: CGPoint(x: cx - eyeSpacing + dashW, y: eyeY))
        context.stroke(
            leftEye, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
        
        // 오른쪽 대시 눈
        var rightEye = Path()
        rightEye.move(to: CGPoint(x: cx + eyeSpacing - dashW, y: eyeY))
        rightEye.addLine(to: CGPoint(x: cx + eyeSpacing + dashW, y: eyeY))
        context.stroke(
            rightEye, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
        
        // 일자 입
        var mouth = Path()
        mouth.move(to: CGPoint(x: cx - size * 0.10, y: cy + size * 0.18))
        mouth.addLine(to: CGPoint(x: cx + size * 0.10, y: cy + size * 0.18))
        context.stroke(
            mouth, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
    
    // MARK: - Level 4: 편안 — ∪ 감은 눈 + 살짝 미소 (눈썹 없음)
    
    private func drawCalm(context: GraphicsContext, cx: CGFloat, cy: CGFloat) {
        let lw = size * 0.055
        
        // 감은 눈 ∪ (작은 곡선)
        drawClosedEyes(context, cx: cx, cy: cy, eyeWidth: 0.09, depth: 0.06)
        
        // 살짝 미소
        var mouth = Path()
        mouth.move(to: CGPoint(x: cx - size * 0.10, y: cy + size * 0.16))
        mouth.addQuadCurve(
            to: CGPoint(x: cx + size * 0.10, y: cy + size * 0.16),
            control: CGPoint(x: cx, y: cy + size * 0.24)
        )
        context.stroke(
            mouth, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
    
    // MARK: - Level 5: 행복 — ∪ 감은 눈 + 큰 미소 (눈썹 없음)
    
    private func drawHappy(context: GraphicsContext, cx: CGFloat, cy: CGFloat) {
        let lw = size * 0.055
        
        // 감은 눈 ∪ (큰 곡선)
        drawClosedEyes(context, cx: cx, cy: cy, eyeWidth: 0.11, depth: 0.07)
        
        // 큰 미소
        var mouth = Path()
        mouth.move(to: CGPoint(x: cx - size * 0.14, y: cy + size * 0.14))
        mouth.addQuadCurve(
            to: CGPoint(x: cx + size * 0.14, y: cy + size * 0.14),
            control: CGPoint(x: cx, y: cy + size * 0.28)
        )
        context.stroke(
            mouth, with: .color(lineColor),
            style: StrokeStyle(lineWidth: lw, lineCap: .round)
        )
    }
}

// MARK: - Preview

#if DEBUG
struct MoodFaceView_Previews: PreviewProvider {
    static var previews: some View {
        HStack(spacing: 16) {
            ForEach(1...5, id: \.self) { level in
                VStack {
                    MoodFaceView(level: level, size: 60)
                    Text(getMoodAsset(level: level).title)
                        .font(.caption)
                }
            }
        }
        .padding()
        .previewLayout(.sizeThatFits)
    }
}
#endif
