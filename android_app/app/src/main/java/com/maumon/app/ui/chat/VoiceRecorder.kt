package com.maumon.app.ui.chat

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Android 음성-텍스트 변환 (STT) 래퍼
 * iOS VoiceRecorder.swift 대응
 *
 * Android 내장 SpeechRecognizer 사용 (한국어 ko-KR)
 * - 별도 Whisper 모델 없이 Google STT 엔진 활용
 * - RECORD_AUDIO 권한은 AndroidManifest에 이미 선언됨
 */
class VoiceRecorder(private val context: Context) {

    private var speechRecognizer: SpeechRecognizer? = null

    private val _isRecording = MutableStateFlow(false)
    val isRecording: StateFlow<Boolean> = _isRecording

    private val _transcribedText = MutableStateFlow("")
    val transcribedText: StateFlow<String> = _transcribedText

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    /**
     * 음성 인식 시작
     * 런타임 RECORD_AUDIO 권한이 먼저 부여되어 있어야 함
     */
    fun startRecording() {
        if (_isRecording.value) return

        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            _error.value = "이 기기에서는 음성 인식을 사용할 수 없습니다."
            return
        }

        _error.value = null
        _transcribedText.value = ""

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    _isRecording.value = true
                }

                override fun onBeginningOfSpeech() {}

                override fun onRmsChanged(rmsdB: Float) {}

                override fun onBufferReceived(buffer: ByteArray?) {}

                override fun onEndOfSpeech() {
                    _isRecording.value = false
                }

                override fun onError(errorCode: Int) {
                    _isRecording.value = false
                    _error.value = when (errorCode) {
                        SpeechRecognizer.ERROR_NO_MATCH -> "음성을 인식하지 못했습니다. 다시 시도해 주세요."
                        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "음성 입력 시간이 초과되었습니다."
                        SpeechRecognizer.ERROR_AUDIO -> "오디오 녹음 오류가 발생했습니다."
                        SpeechRecognizer.ERROR_NETWORK,
                        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "네트워크 오류가 발생했습니다."
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "마이크 권한이 필요합니다."
                        else -> "음성 인식 오류가 발생했습니다. (코드: $errorCode)"
                    }
                }

                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        _transcribedText.value = matches[0]
                    }
                    _isRecording.value = false
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        _transcribedText.value = matches[0]
                    }
                }

                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
        }

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ko-KR")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ko-KR")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

        speechRecognizer?.startListening(intent)
    }

    /**
     * 음성 인식 중지
     */
    fun stopRecording() {
        speechRecognizer?.stopListening()
        _isRecording.value = false
    }

    /**
     * 리소스 해제 — Activity/Fragment onDestroy 시 호출
     */
    fun destroy() {
        speechRecognizer?.destroy()
        speechRecognizer = null
        _isRecording.value = false
    }
}
