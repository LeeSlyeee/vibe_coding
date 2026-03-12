import Foundation
import UserNotifications
#if os(iOS)
import UIKit
#endif
#if canImport(MLX) && !targetEnvironment(simulator)
import MLX
import MLXLMCommon
import MLXRandom
import MLXLLM
#endif

extension LLMService {
    // MARK: - Model Loading
    // MARK: - Model Loading (Hybrid)
    func loadModel() async {
        if isModelLoaded { return }
        
        #if canImport(MLX) && !targetEnvironment(simulator)
        await ensureModelDownloaded() // Download model files first
        
        let docURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let repoFolderName = huggingFaceRepoID.replacingOccurrences(of: "/", with: "_")
        let modelDir = docURL.appendingPathComponent(repoFolderName)
        
        // [Migration] 기존 haru-on-model 폴더가 있으면 자동 이전
        let legacyDir = docURL.appendingPathComponent("haru-on-model")
        if FileManager.default.fileExists(atPath: legacyDir.path) && !FileManager.default.fileExists(atPath: modelDir.path) {
            try? FileManager.default.moveItem(at: legacyDir, to: modelDir)
        }
        
        // [Hot-Patch] chat_template 누락 자동 복구 (앱 재설치 없이 수정)
        // 캐시된 tokenizer_config.json에 chat_template이 없으면 번들에서 덮어쓰기
        let cachedTokenizerPath = modelDir.appendingPathComponent("tokenizer_config.json")
        if FileManager.default.fileExists(atPath: cachedTokenizerPath.path) {
            if let data = try? Data(contentsOf: cachedTokenizerPath),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["chat_template"] == nil {
                // chat_template 누락 → 번들에서 올바른 파일 복사
                if let bundleURL = Bundle.main.url(forResource: "tokenizer_config", withExtension: "json") {
                    try? FileManager.default.removeItem(at: cachedTokenizerPath)
                    try? FileManager.default.copyItem(at: bundleURL, to: cachedTokenizerPath)
                } else {
                }
            } else {
            }
        }
        
        do {
            let config = ModelConfiguration(directory: modelDir)
            // Load Engine (API Fix: Use Singleton Factory)
            let container = try await MLXLLM.LLMModelFactory.shared.loadContainer(configuration: config) { progress in
                Task { @MainActor in self.modelLoadingProgress = progress.fractionCompleted }
            }
            let instructions = self.systemPrompt
            // ChatSession을 빈 상태로 초기화하되 System Prompt는 프레임워크 템플릿에 맞춤
            let newSession = ChatSession(container, instructions: instructions)
            
            await MainActor.run { 
                self.modelContainer = container
                self.chatSession = newSession
                self.isModelLoaded = true
            }
            
        } catch {
            // Fallback? No, just fail.
        }
        
        #else
        
        await MainActor.run { self.modelLoadingProgress = 0.1 }
        try? await Task.sleep(nanoseconds: 1 * 1_000_000_000)
        
        await MainActor.run { 
            self.modelLoadingProgress = 1.0 
            self.isModelLoaded = true
        }
        #endif
    }
    
    // MARK: - Downloader (Hugging Face)
    func ensureModelDownloaded() async -> Bool {
        let docURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let repoFolderName = huggingFaceRepoID.replacingOccurrences(of: "/", with: "_")
        let modelDir = docURL.appendingPathComponent(repoFolderName)
        
        // Create Directory if missing
        if !FileManager.default.fileExists(atPath: modelDir.path) {
            try? FileManager.default.createDirectory(at: modelDir, withIntermediateDirectories: true)
        }
        
        let session = URLSession.shared
        let totalFiles = Double(modelFiles.count)
        
        
        for (index, fileName) in modelFiles.enumerated() {
            let fileURL = modelDir.appendingPathComponent(fileName)
            
            // Check existence
            if FileManager.default.fileExists(atPath: fileURL.path) {
                // Simple check: If file size is 0, re-download
                if let attr = try? FileManager.default.attributesOfItem(atPath: fileURL.path),
                   let size = attr[.size] as? UInt64, size > 0 {
                    await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index) / totalFiles * 0.8) }
                    continue
                }
            }
            
            // [Fast Load] Bundle에서 파일 찾기 (앱에 포함된 경우 다운로드 건너뛰기)
            let name = (fileName as NSString).deletingPathExtension
            let ext = (fileName as NSString).pathExtension
            if let bundleURL = Bundle.main.url(forResource: name, withExtension: ext) {
                do {
                    if FileManager.default.fileExists(atPath: fileURL.path) {
                        try FileManager.default.removeItem(at: fileURL)
                    }
                    try FileManager.default.copyItem(at: bundleURL, to: fileURL)
                    await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index+1) / totalFiles * 0.8) }
                    continue
                } catch {
                }
            }
            
            // Download from Hugging Face
            let urlString = "https://huggingface.co/\(huggingFaceRepoID)/resolve/main/\(fileName)"
            guard let downloadURL = URL(string: urlString) else { continue }
            
            
            var request = URLRequest(url: downloadURL)
            if !huggingFaceToken.isEmpty {
                request.addValue("Bearer \(huggingFaceToken)", forHTTPHeaderField: "Authorization")
            }
            
            do {
                let (tempURL, response) = try await session.download(for: request) // Use request for headers
                
                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                    return false
                }
                
                // Remove existing if needed
                if FileManager.default.fileExists(atPath: fileURL.path) {
                    try FileManager.default.removeItem(at: fileURL)
                }
                
                try FileManager.default.moveItem(at: tempURL, to: fileURL)
                
                await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index+1) / totalFiles * 0.8) }
                
            } catch {
                return false
            }
        }
        
        return true
    }
    
    func unloadModel() {
        self.modelContainer = nil
        self.isModelLoaded = false
    }

}
