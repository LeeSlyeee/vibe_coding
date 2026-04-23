
import os
import time

class VoiceBrain:
    def __init__(self, model_size="small", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.is_loading = False

    def load_model(self):
        if self.model is None and not self.is_loading:
            self.is_loading = True
            try:
                print(f"🎙️ Loading Faster-Whisper Model ({self.model_size}) on {self.device}...")
                from faster_whisper import WhisperModel
                # model_size can be "tiny", "base", "small", "medium", "large-v3"
                self.model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                print("✅ Faster-Whisper Model Loaded.")
            except Exception as e:
                print(f"❌ Failed to load Whisper: {e}")
                self.model = None
            finally:
                self.is_loading = False

    def transcribe(self, audio_path):
        if self.model is None:
            self.load_model()
            if self.model is None:
                return "음성 인식 모델 로딩 실패"

        try:
            start_time = time.time()
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=5, 
                language="ko",
                vad_filter=True # Filter silence
            )
            
            print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            print(f"🎙️ Transcription took {time.time() - start_time:.2f}s")
            return full_text.strip()
        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            return "음성 인식 오류 발생"

    def structure_diary_text(self, text):
        """
        Uses Local LLM (Gemma 4) to split the transcribed text into diary fields.
        Returns a dict with keys: event, emotion, meaning, comfort.
        """
        import requests
        import json
        import re

        if not text or len(text) < 5:
            return None

        print(f"🧠 [VoiceBrain] Structuring text with Gemma 4...")
        
        try:
            url = "http://localhost:11434/api/generate"
            prompt_text = (
                f"### Role\n"
                f"당신은 사용자의 일기 내용을 분석하여 4가지 항목으로 분류해주는 AI 비서입니다.\n\n"
                f"### Input Text\n"
                f"{text}\n\n"
                f"### Task\n"
                f"위 내용을 다음 4가지 항목으로 적절히 나누거나 요약해서 JSON 형식으로 출력하세요.\n"
                f"1. event: 오늘 있었던 구체적인 사건/사실\n"
                f"2. emotion: 그 사건으로 인해 느낀 감정\n"
                f"3. meaning: 그 감정이 자신에게 주는 의미나 깊은 생각 (없다면 내용을 바탕으로 추론)\n"
                f"4. comfort: 자신에게 해주고 싶은 위로의 말 (없다면 내용을 바탕으로 따뜻하게 작성)\n\n"
                f"### Output Format (Strict JSON)\n"
                f"{{\n"
                f"  \"event\": \"...\",\n"
                f"  \"emotion\": \"...\",\n"
                f"  \"meaning\": \"...\",\n"
                f"  \"comfort\": \"...\"\n"
                f"}}\n"
                f"* 반드시 JSON만 출력하세요. 마크다운이나 잡담 금지."
            )

            payload = {
                "model": "gemma4:2b",
                "prompt": prompt_text,
                "stream": False,
                "format": "json", # Enforce structured mode
                "options": {
                    "temperature": 0.5,
                    "num_predict": 500
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                print(f"❌ LLM Error: {response.text}")
                return None
                
            json_str = response.json().get('response', '')
            print(f"🧠 [VoiceBrain] Raw LLM Response: {json_str[:100]}...")
            
            # Simple Cleaning just in case
            try:
                data = json.loads(json_str)
                return {
                    "question1": data.get("event", ""),
                    "question2": data.get("emotion", ""),
                    "question3": data.get("meaning", ""),
                    "question4": data.get("comfort", "")
                }
            except json.JSONDecodeError:
                print("❌ Failed to parse JSON from LLM")
                return None

        except Exception as e:
            print(f"❌ Structure Error: {e}")
            return None

# Global Instance
voice_brain_instance = VoiceBrain()
