<template>
  <div class="chat-diary-container">
    <!-- Header -->
    <header class="chat-header">
      <button @click="goBack" class="back-btn">
        <span class="material-icons">arrow_back</span>
      </button>
      <h1>{{ formattedDate }}의 대화</h1>
      <button @click="resetChat" class="reset-btn" title="다시 시작">
        <span class="material-icons">refresh</span>
      </button>
    </header>

    <!-- AI Loading Modal (Overlay) -->
    <div v-if="isTyping" class="modal-overlay-nobg">
        <div class="processing-modal">
            <span class="processing-icon pulse">🟣</span>
            <p>AI가 답변을 생각하고 있어요...</p>
        </div>
    </div>

    <!-- Chat Area -->
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(msg, index) in messages" 
        :key="msg.id" 
        class="message-row"
        :class="msg.sender"
      >
        <!-- Bot Profile -->
        <div v-if="msg.sender === 'bot'" class="profile-icon">🤖</div>
        
        <!-- Bubble -->
        <div 
          class="message-bubble" 
          :class="{ 'typing': msg.isTyping }"
          @click="msg.sender === 'user' ? editMessage(index) : null"
        >
          <span v-if="!msg.isTyping" v-html="formatMessage(msg.text)"></span>
          <div v-else class="typing-indicators">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
      <div ref="scrollAnchor"></div>
    </div>

    <!-- Input Area -->
    <div class="input-area" v-if="!isCompleted">
      <!-- Option Selection (Weather/Mood) -->
      <!-- Option Selection (Select One) -->
      <div v-if="currentQuestion.inputType === 'select'" class="options-container">
        <button 
          v-for="opt in currentQuestion.options" 
          :key="opt.value"
          @click="handleSelect(opt.value, opt.label)"
          class="option-btn"
          :class="{ selected: currentInput === opt.value }"
        >
          {{ opt.label }}
        </button>
      </div>

      <!-- Checklist (Select Multiple) -->
      <div v-else-if="currentQuestion.inputType === 'checklist'" class="checklist-container">
          <div class="checklist-options">
            <button 
                v-for="opt in currentQuestion.options" 
                :key="opt.value" 
                @click="toggleChecklist(opt.value)"
                class="option-btn checklist-btn"
                :class="{ selected: selectedOptions.includes(opt.value) }"
            >
                {{ opt.label }}
            </button>
          </div>
          <button @click="submitChecklist" class="submit-action-btn" :disabled="selectedOptions.length === 0">
              선택 완료
          </button>
      </div>

      <!-- Slider (1-10) -->
      <div v-else-if="currentQuestion.inputType === 'slider'" class="slider-wrapper">
          <div class="slider-display">
              <span class="slider-val">{{ sliderValue }}</span>
              <span class="slider-label">점</span>
          </div>
          <input 
            type="range" 
            :min="currentQuestion.min" 
            :max="currentQuestion.max" 
            v-model.number="sliderValue" 
            class="range-input"
          >
          <div class="slider-labels">
              <span>약함</span>
              <span>강함</span>
          </div>
          <button @click="submitSlider" class="submit-action-btn">
              입력
          </button>
      </div>

       <!-- Mood Slider/Buttons -->
      <div v-else-if="currentQuestion.inputType === 'mood'" class="mood-container">
        <div class="mood-buttons">
            <button 
                v-for="level in 5" 
                :key="level"
                @click="handleMoodSelect(level)"
                class="mood-btn"
            >
                <span class="mood-emoji">{{ getMoodEmoji(level) }}</span>
                <span class="mood-label">{{ getMoodLabel(level) }}</span>
            </button>
        </div>
      </div>

      <!-- Text Input -->
      <div v-else class="text-input-wrapper">
        <textarea
          ref="textareaRef"
          v-model="currentInput"
          placeholder="여기에 답을 적어주세요..."
          @input="autoResize"
          @keydown.enter.prevent="handleSend"
          rows="1"
        ></textarea>
        <button 
            @click="handleSend" 
            class="send-btn" 
            :disabled="!currentInput.trim()"
        >
          <span class="material-icons">send</span>
        </button>
      </div>
    </div>
    <!-- Restore Draft Modal -->
    <div v-if="showRestoreModal" class="modal-overlay">
        <div class="modal-content">
            <h3>대화 이어하기</h3>
            <p>이전에 작성 중 멈춘 대화가 있습니다.<br>계속 이어서 하시겠습니까?</p>
            <div class="modal-actions">
                <button @click="discardDraft" class="cancel-btn">새로 시작</button>
                <button @click="restoreDraft" class="confirm-btn">이어하기</button>
            </div>
        </div>
    </div>

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="modal-overlay">
        <div class="modal-content">
            <h3>다시 시작</h3>
            <p>현재 대화 내용이 모두 삭제됩니다.<br>정말 처음부터 다시 시작하시겠습니까?</p>
            <div class="modal-actions">
                <button @click="showResetModal = false" class="cancel-btn">취소</button>
                <button @click="confirmReset" class="confirm-btn" style="background-color: #ff3b30;">다시 시작</button>
            </div>
        </div>
    </div>

    <!-- Exit Confirmation Modal -->
    <div v-if="showExitModal" class="modal-overlay">
        <div class="modal-content">
            <h3>대화 종료</h3>
            <p>대화를 종료하고 나가시겠습니까?<br>작성 중인 내용은 임시 저장됩니다.</p>
            <div class="modal-actions">
                <button @click="showExitModal = false" class="cancel-btn">취소</button>
                <button @click="confirmExit" class="confirm-btn">나가기</button>
            </div>
        </div>
    </div>

    <!-- Completion Modal -->
    <div v-if="showCompletionModal" class="completion-overlay">
        <div class="completion-card">
            <div class="completion-icon">🎉</div>
            <h2>기록 완료!</h2>
            <p>오늘의 마음이 안전하게 저장되었습니다.</p>
            
            <div class="streak-badge" v-if="streakCount > 0">
                <span class="fire-icon">🔥</span>
                <span class="streak-text">{{ streakCount }}일 연속 작성 중!</span>
            </div>
            
            <button @click="$router.push('/calendar')" class="complete-btn">
                캘린더로 이동
            </button>
        </div>
    </div>
  </div>
</template>

<script setup lang="js">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

// --- State ---
// --- State ---
const messages = ref([]);
const answers = ref({});
const currentStep = ref(0);
const currentInput = ref('');
const isTyping = ref(false);
const isCompleted = ref(false);
const isSending = ref(false);
const textareaRef = ref(null);
const messagesContainer = ref(null);
const scrollAnchor = ref(null);
const lastSubmitTime = ref(0);
const retryCount = ref(0); 
const showRestoreModal = ref(false); // New
const showResetModal = ref(false); // New
const showExitModal = ref(false); // New
const savedDraft = ref(null); // New: Store draft temporarily

const targetDate = route.params.date || new Date().toISOString().split('T')[0];

const formattedDate = computed(() => {
  const [y, m, d] = targetDate.split('-');
  return `${y}년 ${m}월 ${d}일`;
});

// --- Questions Scenario ---
const questions = ref([]);

const SCRIPT_GREEN = [
  {
    field: 'sleep_desc',
    text: "안녕하세요! 어젯밤 잠은 푹 주무셨나요? 오늘 컨디션이 어떤지 궁금해요. 😴",
    inputType: 'text'
  },
  {
    field: 'event',
    text: "오늘 하루 중 가장 기억에 남는 사건이나 일은 무엇이었나요?",
    inputType: 'text'
  },
  {
    field: 'emotion_desc',
    text: "그 일이 있었을 때, 기분이 어떠셨나요? 자세한 감정을 들려주세요.",
    inputType: 'text'
  },
  {
    field: 'emotion_meaning',
    text: "왜 그런 감정이 들었을까요? 그 감정이 본인에게 어떤 의미가 있었나요? 🤔",
    inputType: 'text'
  },
  {
    field: 'self_talk',
    text: "오늘 하루 누구보다 고생한 자신에게 해주고 싶은 말이 있다면 적어주세요. 💌",
    inputType: 'text'
  },
  {
    field: 'medication_taken',
    text: "혹시 챙겨 드셔야 할 영양제나 약은 잘 챙겨 드셨나요? 💊",
    inputType: 'select',
    options: [
      { value: true, label: '네, 먹었어요' },
      { value: false, label: '아니요/까먹었어요' },
      { value: null, label: '해당 없음' }
    ]
  },
  {
    field: 'weather',
    text: "오늘의 날씨는 어땠나요?",
    inputType: 'select',
    options: [
      { value: '맑음', label: '☀️ 맑음' },
      { value: '흐림', label: '☁️ 흐림' },
      { value: '비', label: '☔️ 비' },
      { value: '눈', label: '❄️ 눈' },
      { value: '구름조금', label: '⛅️ 구름조금' }
    ]
  },
  {
    field: 'mood_level',
    text: "마지막으로, 오늘 전반적인 기분을 점수로 표현한다면요?",
    inputType: 'mood'
  }
];

const SCRIPT_RED = [
  {
      field: 'sleep_desc',
      text: "안녕하세요. 지난 밤 잠은 푹 주무셨나요? 중간에 깨거나 어렵지는 않으셨는지요.",
      inputType: 'text'
  },
  {
      field: 'symptoms',
      text: "혹시 몸이 불편한 곳은 없나요? 해당되는 증상이 있다면 모두 알려주세요.",
      inputType: 'checklist',
      options: [
          { value: 'headache', label: '두통/어지러움' },
          { value: 'digestion', label: '소화불량/속쓰림' },
          { value: 'palpitation', label: '가슴 두근거림' },
          { value: 'insomnia', label: '불면/과수면' },
          { value: 'fatigue', label: '만성 피로' },
          { value: 'none', label: '증상 없음' }
      ]
  },
  {
      field: 'mood_intensity',
      text: "지금 느끼시는 우울이나 불안의 강도는 어느 정도인가요? (1: 약함 ~ 10: 매우 강함)",
      inputType: 'slider',
      min: 1,
      max: 10
  },
  {
      field: 'emotion_desc',
      text: "지금 마음속에 있는 생각이나 감정을 있는 그대로 털어놓아 보세요. 제가 듣고 있습니다.",
      inputType: 'text'
  },
  {
      field: 'safety_check',
      text: "혹시 스스로를 해치고 싶다는 생각이 들거나, 매우 힘든 상태라면 꼭 알려주세요.",
      inputType: 'select',
      options: [
          { value: 'safe', label: '괜찮습니다.' },
          { value: 'need_help', label: '도움이 필요해요.' },
      ]
  },
  {
    field: 'medication_taken',
    text: "오늘 처방받으신 약은 챙겨 드셨나요? 규칙적인 복용이 중요합니다. 💊",
    inputType: 'select',
    options: [
      { value: true, label: '네, 복용했습니다' },
      { value: false, label: '아니요/깜빡했습니다' },
      { value: null, label: '약 없음' }
    ]
  },
  {
    field: 'weather',
    text: "오늘 창밖의 날씨는 어땠나요?",
    inputType: 'select',
    options: [
      { value: '맑음', label: '☀️ 맑음' },
      { value: '흐림', label: '☁️ 흐림' },
      { value: '비', label: '☔️ 비' },
      { value: '눈', label: '❄️ 눈' },
      { value: '구름조금', label: '⛅️ 구름조금' }
    ]
  },
  {
    field: 'mood_level',
    text: "오늘 하루, 전체적인 기분은 어떠셨나요?",
    inputType: 'mood'
  }
];

const currentQuestion = computed(() => questions.value[currentStep.value] || {});
const sliderValue = ref(5);
const selectedOptions = ref([]);

// --- Lifecycle & Methods ---

// --- Lifecycle & Methods ---

// Helper: Start New Chat
const startNewChat = () => {
    localStorage.removeItem('chat_diary_draft');
    messages.value = [];
    answers.value = {};
    currentStep.value = 0;
    addBotMessage(questions.value[0].text);
};

// Helper: Restore Draft
const restoreDraft = () => {
    if (savedDraft.value) {
        answers.value = savedDraft.value.answers;
        currentStep.value = savedDraft.value.step;
        messages.value = savedDraft.value.messages;
        scrollToBottom();
    }
    showRestoreModal.value = false;
};

// Helper: Discard Draft
const discardDraft = () => {
    startNewChat();
    showRestoreModal.value = false;
};

onMounted(() => {
  // Determine Script based on Risk Level
  const riskLevel = parseInt(localStorage.getItem('risk_level') || '0');
  if (riskLevel >= 5) {
      questions.value = SCRIPT_RED;
      console.log("🚨 High Risk Mode Activated (Chat)");
  } else {
      questions.value = SCRIPT_GREEN;
      console.log("🌿 Green Mode Activated (Chat)");
  }

  // Check Follow-up Context (Priority 1)
  const followupContext = localStorage.getItem('followup_context');
  if (followupContext) {
      try {
          const ctx = JSON.parse(followupContext);
          if (ctx.question) {
              console.log("🚨 Follow-up Mode Activated");
              messages.value = []; // Clear
              addBotMessage(ctx.question); // Start with Follow-up Question
              
              // We should probably adapt the script or flow here.
              // For MVP, we insert this question at the start, then proceed with normal flow?
              // Or maybe just pure chat mode? 
              // The user requirement is "follow-up question".
              // Let's prepend it as a special interaction or just replace the first question.
              
              // Since this is a "Deep Dive", maybe we skip the standard script?
              // But we need to save the data somewhere.
              // Let's treat this as an "extra" conversation that appends to the diary later?
              // For now: Just let the user answer this, then proceed to standard flow? 
              // Or: This REPLACES the first greeting.
              
              // Actually, if we are here, the diary is ALREADY saved.
              // We are just adding more info.
              // So this chat should probably be "Free Chat" mode or update the existing diary.
              // But 'ChatDiaryPage' saves a NEW diary by default.
              
              // Key Fix: If followup, we should probably load the existing diary data into 'answers' 
              // to prevent overwriting or creating duplicate?
              // But ChatDiaryPage logic is designed to CREATE.
              
              // Simplified Approach for now:
              // Just ask the question. Usage of 'ChatDiaryPage' implies creating/updating.
              // We will treat this as a "Continued Conversation".
              
              localStorage.removeItem('followup_context');
              return; // Skip normal start
          }
      } catch (e) {
          console.error("Followup Parse Error", e);
      }
  }

  // Check Draft (Priority 2)
  if (localStorage.getItem('chat_diary_draft')) {
    const draft = JSON.parse(localStorage.getItem('chat_diary_draft'));
    // 날짜가 같으면 모달 표시
    if (draft.date === targetDate) {
        // [Fix] Auto-Sync for Completed Drafts
        if (draft.step >= questions.value.length) {
            console.log("🔄 Auto-syncing unsaved completed draft...");
            answers.value = draft.answers;
            savedDraft.value = null; // Clear modal trigger
            submitDiary(); // Auto Submit
            return;
        }

        savedDraft.value = draft;
        showRestoreModal.value = true;
        return;
    }
  }
  
  // No draft -> Start new immediately
  startNewChat();
});

// Auto-save
watch([answers, currentStep, messages], () => {
  if (!isCompleted.value) {
    localStorage.setItem('chat_diary_draft', JSON.stringify({
        date: targetDate,
        answers: answers.value,
        step: currentStep.value,
        messages: messages.value
    }));
  }
}, { deep: true });

function formatMessage(text) {
    return text.replace(/\n/g, '<br>');
}

function scrollToBottom() {
  nextTick(() => {
    scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' });
  });
}

function autoResize() {
  const el = textareaRef.value;
  if (el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'; // Max height 120px
  }
}

async function addBotMessage(text) {
  isTyping.value = true;
  const typingId = Date.now() + '_typing';
  // Typing simulation
  messages.value.push({ id: typingId, text: '', sender: 'bot', isTyping: true });
  scrollToBottom();

  const delay = Math.min(1000, text.length * 50); // Dynamic delay
  await new Promise(r => setTimeout(r, delay));

  // Safe remove by ID
  messages.value = messages.value.filter(m => m.id !== typingId);
  
  messages.value.push({ id: Date.now(), text, sender: 'bot' });
  scrollToBottom();
  isTyping.value = false;
}

async function handleSend(event) {
  // Debounce: 1초 내 재전송 방지
  const now = Date.now();
  if (now - lastSubmitTime.value < 1000) return;
  lastSubmitTime.value = now;

  if (isSending.value) return;
  if (event && event.isComposing) return;
  if (!currentInput.value.trim()) return;
  
  isSending.value = true;
  try {
    const answerText = currentInput.value.trim();
    const field = currentQuestion.value.field;

    // 1. Add User Message
    messages.value.push({ id: Date.now() + Math.random(), text: answerText, sender: 'user' });
    answers.value[field] = answerText;
    currentInput.value = '';
    if(textareaRef.value) textareaRef.value.style.height = 'auto';

    // 2. AI Reaction (Empathy or Follow-up Question) - Only for text inputs
    if (questions.value[currentStep.value].inputType === 'text') {
        const token = localStorage.getItem('authToken');
        
        // Detect Short Answer (< 10 chars)
        const isShort = answerText.length < 10;
        let mode = 'reaction';
        
        // If short and first attempt, ask follow-up question
        if (isShort && retryCount.value === 0) {
            mode = 'question';
            retryCount.value++;
        } else {
            retryCount.value = 0; // Reset for next step
        }
        
        // Show fake typing immediately
        isTyping.value = true;
        let typingId = Date.now() + '_typing_r' + Math.random();
        messages.value.push({ id: typingId, text: '', sender: 'bot', isTyping: true });
        scrollToBottom();

        try {
            // Call API
            const res = await axios.post('/api/chat/reaction', 
                { text: answerText, mode: mode },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            
            // Safer parsing
            let reaction = "";
            let isRisk = false;
            
            if (res && res.data && res.data.reaction) {
                reaction = res.data.reaction;
                // Check for [RISK] flag
                if (reaction.includes('[RISK]')) {
                    isRisk = true;
                    reaction = reaction.replace('[RISK]', '').trim();
                    // Trigger Safety Modal via Event Bus or Prop injection? 
                    // Since this is a page, we can emit an event or used a shared state (Vuex/Pinia) or just standard alert for now 
                    // But we have App.vue's global modal. We can't easily access it without a store.
                    // Option A: Use window event
                    window.dispatchEvent(new CustomEvent('open-safety-modal'));
                }
            }
            
            // Remove typing bubble (Safe Mutation)
            const tIdx = messages.value.findIndex(m => m.id === typingId);
            if (tIdx !== -1) messages.value.splice(tIdx, 1);
            
            // Client-side Fallback
            if (!reaction || reaction.trim() === "") {
                console.log("Empty reaction, using fallback");
                if (mode === 'question') {
                    const qFallbacks = [
                        "저런, 조금 더 자세히 이야기해주실 수 있나요?",
                        "어떤 일이 있었는지 문득 궁금해지네요.",
                        "특별한 이유가 있었나요? 편하게 들려주세요."
                    ];
                    reaction = qFallbacks[Math.floor(Math.random() * qFallbacks.length)];
                } else {
                    const rFallbacks = [
                        "그렇군요. 이야기해주셔서 감사합니다. 😌",
                        "네, 계속해서 들려주세요. 👂",
                        "소중한 이야기 감사합니다."
                    ];
                    reaction = rFallbacks[Math.floor(Math.random() * rFallbacks.length)];
                }
            }

            // Add Reaction Message
            messages.value.push({ id: Date.now() + Math.random(), text: reaction, sender: 'bot' });
            
            // If risk detected, trigger modal after message
            if (isRisk) {
               console.warn("⚠️ Risk detected. Opening safety modal.");
               // A slight delay to let user read the message
               setTimeout(() => {
                   window.dispatchEvent(new CustomEvent('open-safety-modal'));
               }, 1000);
            }
            
            // Force Scroll
            nextTick(scrollToBottom);
            
            // Logic Branch
            if (mode === 'question') {
                isTyping.value = false;
                isSending.value = false;
                return; // Wait for user
            }
            
            await new Promise(r => setTimeout(r, 2000));

        } catch (e) {
            console.error("Reaction Error:", e);
            // Remove typing bubble (Safe Mutation)
            const tIdx = messages.value.findIndex(m => m.id === typingId);
            if (tIdx !== -1) messages.value.splice(tIdx, 1);
            
            // Error Fallback
            const reaction = "그렇군요. 이야기해주셔서 감사합니다. 😌";
            messages.value.push({ id: Date.now() + Math.random(), text: reaction, sender: 'bot' });
            nextTick(scrollToBottom);
            await new Promise(r => setTimeout(r, 2000));
        }
        isTyping.value = false;
    }

    await proceedNext();
  } finally {
    isSending.value = false;
  }
}

function handleSelect(value, label) {
    const field = currentQuestion.value.field;
    messages.value.push({ id: Date.now(), text: label, sender: 'user' });
    answers.value[field] = value;
    proceedNext();
}

function handleMoodSelect(level) {
    const field = currentQuestion.value.field;
    const label = `${getMoodEmoji(level)} ${getMoodLabel(level)}`;
    messages.value.push({ id: Date.now(), text: label, sender: 'user' });
    answers.value[field] = level;
    proceedNext();
}


function toggleChecklist(value) {
    if (value === 'none') {
        selectedOptions.value = ['none'];
        return;
    }
    
    // If 'none' was selected, deselect it
    if (selectedOptions.value.includes('none')) {
        selectedOptions.value = [];
    }
    
    const idx = selectedOptions.value.indexOf(value);
    if (idx === -1) selectedOptions.value.push(value);
    else selectedOptions.value.splice(idx, 1);
}

function submitChecklist() {
    const field = currentQuestion.value.field;
    const labels = selectedOptions.value.map(val => {
        const opt = currentQuestion.value.options.find(o => o.value === val);
        return opt ? opt.label : val;
    });
    
    messages.value.push({ id: Date.now(), text: labels.join(', '), sender: 'user' });
    answers.value[field] = selectedOptions.value;
    selectedOptions.value = []; // Reset
    proceedNext();
}

function submitSlider() {
    const field = currentQuestion.value.field;
    const value = sliderValue.value;
    
    messages.value.push({ id: Date.now(), text: `${value}점`, sender: 'user' });
    answers.value[field] = value;
    sliderValue.value = 5; // Reset
    proceedNext();
}

function getMoodEmoji(level) {
    return ['🤬', '😢', '😐', '🙂', '🥰'][level-1];
}
function getMoodLabel(level) {
    return ['최악', '우울', '보통', '좋음', '최고'][level-1];
}

async function proceedNext() {
  currentStep.value++;
  
  if (currentStep.value < questions.value.length) {
    await addBotMessage(questions.value[currentStep.value].text);
  } else {
    // Finish
    await addBotMessage("기록해주셔서 감사합니다. 소중한 하루를 저장하고 있어요... 💾");
    submitDiary();
  }
}

const showCompletionModal = ref(false);
const streakCount = ref(0);

async function submitDiary() {
    isCompleted.value = true;
    try {
        const payload = {
            ...answers.value,
            created_at: targetDate, 
        };

        const now = new Date();
        const [y, m, d] = targetDate.split('-');
        now.setFullYear(y, m-1, d);
        payload.created_at = now.toISOString();

        await axios.post('/api/diaries', payload, {
            headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
        });

        // --- Streak Logic ---
        const lastDate = localStorage.getItem('last_diary_date');
        let currentStreak = parseInt(localStorage.getItem('current_streak') || '0');
        
        const todayStr = new Date().toISOString().split('T')[0];
        
        // If last diary was yesterday, increment streak
        // Simple verification: Difference in days = 1
        if (lastDate) {
            const last = new Date(lastDate);
            const today = new Date(todayStr);
            const diffTime = Math.abs(today - last);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
            
            if (diffDays === 1) {
                currentStreak++;
            } else if (diffDays > 1) {
                currentStreak = 1; // Reset if missed a day
            }
            // If same day, do nothing (keep streak)
        } else {
            currentStreak = 1; // First time
        }
        
        localStorage.setItem('last_diary_date', todayStr);
        localStorage.setItem('current_streak', currentStreak);
        streakCount.value = currentStreak;
        
        // Show Completion Modal instead of just text
        showCompletionModal.value = true;
        localStorage.removeItem('chat_diary_draft');

        // Delay navigation is handled by Modal 'Close' or 'Go Home'
        
    } catch (error) {
        console.error(error);
        messages.value.push({ id: Date.now(), text: "저장에 실패했습니다. 잠시 후 다시 시도해주세요.", sender: 'bot' });
        isCompleted.value = false;
    }
}

function editMessage(index) {
    // Simple edit: Remove messages after this point and step back
    // Advanced: Inline edit. For now, let's implement backtracking "Rewind"
    if (!confirm("이 답변을 수정하고 다시 대화하시겠습니까? (이후 대화는 사라집니다)")) return;
    
    // Find which step this message corresponds to
    // This is tricky because indices don't map 1:1 to steps due to typing indicators or multiple bot msgs
    
    // Easier approach: Just rewind step by step until we hit the right one?
    // Since this is MVP Advanced, let's just allow clearing from the clicked message
    // We need to know which 'field' this message answered.
    
    // Actually, step index ~ messages / 2 (roughly)
    
    // For safety in this version: Just reset last answer if user clicks last user message.
    if (index === messages.value.length - 1) {
        messages.value.pop(); // Pop user msg
        messages.value.pop(); // Pop bot waiting msg (if any? no, bot msg is before user msg)
         
        // We need to pop user msg, then restore currentStep logic
        // But bot has already asked next question.
        messages.value.pop(); // Pop next question bot msg
        
        currentStep.value--;
        currentInput.value = answers.value[questions.value[currentStep.value].field];
        if (questions.value[currentStep.value].inputType === 'text') {
             nextTick(autoResize);
        }
    } else {
        alert("마지막 답변만 수정할 수 있습니다.");
    }
}

function goBack() {
    showExitModal.value = true;
}

function confirmExit() {
    router.back();
}

function resetChat() {
    showResetModal.value = true;
}

function confirmReset() {
    localStorage.removeItem('chat_diary_draft');
    window.location.reload();
}

</script>

<style scoped>
.ai-status-bar {
  background: #f3e5f5;
  color: #7b1fa2;
  padding: 8px 16px;
  text-align: center;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  animation: fadeIn 0.3s;
  font-weight: 500;
}
.pulse {
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

.chat-diary-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f9fc;
  font-family: 'Inter', sans-serif;
}

.chat-header {
  padding: 16px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  font-weight: bold;
}
.chat-header h1 {
  font-size: 1.1rem;
  margin: 0;
}
.back-btn, .reset-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  color: #666;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  max-width: 80%;
}
.message-row.bot {
  align-self: flex-start;
}
.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.profile-icon {
  width: 36px;
  height: 36px;
  background: #eef2f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 0.95rem;
  line-height: 1.5;
  position: relative;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.message-row.bot .message-bubble {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-row.user .message-bubble {
  background: #4a90e2;
  color: white;
  border-bottom-right-radius: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.message-row.user .message-bubble:hover {
    opacity: 0.9;
}

/* Typing Indicator */
.typing-indicators {
  display: flex;
  gap: 4px;
  padding: 4px 2px;
}
.typing-indicators span {
  width: 6px;
  height: 6px;
  background: #ccc;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicators span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicators span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input Area */
.input-area {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #eee;
  /* iOS Safe Area */
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}

.text-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: #f0f2f5;
  border-radius: 24px;
  padding: 8px 16px;
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  resize: none;
  font-size: 1rem;
  padding: 8px 0;
  max-height: 120px;
  outline: none;
  font-family: inherit;
}

.send-btn {
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.1s;
}
.send-btn:disabled {
  background: #ccc;
  cursor: default;
}
.send-btn:not(:disabled):active {
    transform: scale(0.95);
}

/* Options & Mood */
.options-container {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}
.option-btn {
    padding: 10px 16px;
    border-radius: 20px;
    border: 1px solid #ddd;
    background: white;
    cursor: pointer;
    font-size: 0.95rem;
    transition: all 0.2s;
}
.option-btn:hover { background: #f9f9f9; }
.option-btn:active { background: #eef2f6; }

.mood-buttons {
    display: flex;
    justify-content: space-between;
    width: 100%;
}
.mood-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: none;
    border: none;
    cursor: pointer;
    gap: 4px;
}
.mood-emoji { font-size: 2rem; transition: transform 0.2s; }
.mood-btn:hover .mood-emoji { transform: scale(1.1); }
.mood-label { font-size: 0.75rem; color: #666; }

@media (max-width: 480px) {
    .message-row { max-width: 90%; }
}

/* Checklist Styles */
.checklist-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.checklist-options {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
}
.checklist-btn {
    border: 1px solid #e0e0e0;
    color: #555;
    background: white;
}
.checklist-btn.selected {
    background: #e3f2fd;
    border-color: #2196f3;
    color: #1976d2;
    font-weight: bold;
}

/* Slider Styles */
.slider-wrapper {
    width: 100%;
    padding: 10px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
}
.slider-display {
    text-align: center;
    margin-bottom: 8px;
}
.slider-val {
    font-size: 2rem;
    font-weight: 800;
    color: #2196f3;
}
.slider-label {
    font-size: 1rem;
    color: #666;
    margin-left: 4px;
}
.range-input {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: #e0e0e0;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
}
.range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #2196f3;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.slider-labels {
    width: 100%;
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #999;
}

/* Submit Action Button */
.submit-action-btn {
    width: 100%;
    padding: 14px;
    background: #1d1d1f;
    color: white;
    border: none;
    border-radius: 16px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 8px;
}
.submit-action-btn:disabled {
    background: #e0e0e0;
    color: #999;
    cursor: not-allowed;
}
.submit-action-btn:active {
    transform: scale(0.98);
}

/* Completion Modal */
.completion-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    backdrop-filter: blur(5px);
    animation: fadeIn 0.3s;
}

.completion-card {
    background: white;
    padding: 32px;
    border-radius: 24px;
    width: 85%;
    max-width: 340px;
    text-align: center;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    animation: slideUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.completion-icon {
    font-size: 48px;
    margin-bottom: 16px;
    animation: bounce 1s infinite;
}

.completion-card h2 {
    margin: 0 0 8px 0;
    color: #1d1d1f;
    font-size: 1.5rem;
}

.completion-card p {
    color: #666;
    margin-bottom: 24px;
    font-size: 0.95rem;
}

.streak-badge {
    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
    padding: 12px 20px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 24px;
    border: 1px solid #ffcc80;
    animation: pulse-orange 2s infinite;
}

.fire-icon {
    font-size: 20px;
}

.streak-text {
    color: #ef6c00;
    font-weight: 700;
    font-size: 1rem;
}

.complete-btn {
    width: 100%;
    padding: 14px;
    background: #1d1d1f;
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s;
}

.complete-btn:active {
    transform: scale(0.96);
}

@keyframes pulse-orange {
    0% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(255, 152, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { transform: translateY(30px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

.modal-overlay-nobg {
    position: fixed;
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 100%;
    background: rgba(255, 255, 255, 0.5); /* Slightly visible overlay */
    backdrop-filter: blur(2px);
    display: flex; 
    justify-content: center; 
    align-items: center; 
    z-index: 2000;
}

.processing-modal {
    background: white;
    padding: 24px 40px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    animation: slideUp 0.3s ease-out;
}

.processing-icon {
    font-size: 40px;
}

.processing-modal p {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin: 0;
}
/* Modal Styles (Scoped) */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 3000;
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease-out;
}

.modal-content {
    background: white;
    padding: 24px;
    border-radius: 20px;
    width: 90%;
    max-width: 320px;
    text-align: center;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-content h3 {
    margin: 0 0 12px 0;
    font-size: 1.2rem;
    color: #1d1d1f;
}

.modal-content p {
    color: #86868b;
    margin-bottom: 24px;
    font-size: 0.95rem;
    line-height: 1.5;
}

.modal-actions {
    display: flex;
    gap: 12px;
}

.modal-actions button {
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 12px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s;
}

.modal-actions button:active {
    transform: scale(0.96);
}

.cancel-btn {
    background: #f5f5f7;
    color: #1d1d1f;
}

.confirm-btn {
    background: #007aff;
    color: white;
}
</style>
