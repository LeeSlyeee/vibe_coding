
import SwiftUI
import Speech
import AVFoundation
import Combine

class VoiceRecorder: ObservableObject {
    @Published var isRecording = false
    @Published var transcribedText = ""
    @Published var permissionGranted = false
    
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "ko-KR"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    init() {
        requestPermission()
    }
    
    func requestPermission() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            DispatchQueue.main.async {
                self.permissionGranted = authStatus == .authorized
            }
        }
    }
    
    func startRecording() {
        guard permissionGranted else { return }
        
        // 1. 기존 녹음 강제 정리 (Reset)
        stopRecording()
        
        // 잠시 대기 (AudioEngine 리셋 시간 확보)
        // 실제로는 비동기 처리 없이 바로 해도 되지만, 안전을 위해 로직 분리
        
        #if os(iOS)
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Audio Session Error: \(error)")
            return
        }
        #endif
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        let inputNode = audioEngine.inputNode
        // ⚠️ 중요: 기존 Tap이 남아있다면 제거 (방어 코드)
        inputNode.removeTap(onBus: 0)
        
        guard let recognitionRequest = recognitionRequest else { return }
        
        recognitionRequest.shouldReportPartialResults = true
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { result, error in
            var isFinal = false
            
            if let result = result {
                self.transcribedText = result.bestTranscription.formattedString
                isFinal = result.isFinal
            }
            
            if error != nil || isFinal {
                // 종료 시 Cleanup
                self.audioEngine.stop()
                inputNode.removeTap(onBus: 0)
                
                self.recognitionRequest = nil
                self.recognitionTask = nil
                self.isRecording = false
            }
        }
        
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        do {
            try audioEngine.start()
            isRecording = true
        } catch {
            print("Audio Engine Error: \(error)")
        }
    }
    
    func stopRecording() {
        if audioEngine.isRunning {
            audioEngine.stop()
            recognitionRequest?.endAudio()
            // 안전하게 Tap 제거
            audioEngine.inputNode.removeTap(onBus: 0) 
            isRecording = false
        }
    }
}
