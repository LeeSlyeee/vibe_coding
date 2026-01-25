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

    <!-- AI Status Indicator -->
    <div v-if="isTyping" class="ai-status-bar">
        <span class="pulse">🟣</span> AI가 답변을 생각하고 있어요...
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
  </div>
</template>

<script setup lang="js">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();

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
const retryCount = ref(0); // Fix: Missing ref caused crash

const targetDate = route.params.date || new Date().toISOString().split('T')[0];

const formattedDate = computed(() => {
  const [y, m, d] = targetDate.split('-');
  return `${y}년 ${m}월 ${d}일`;
});

// --- Questions Scenario ---
const questions = [
  {
    field: 'sleep_desc',
    text: "안녕하세요! 어젯밤 잠은 푹 주무셨나요? 오늘 컨디션이 어떤지 궁금해요. 😴",
    inputType: 'text'
  },
  {
    field: 'event',
    text: "그렇군요. 오늘 하루 중 가장 기억에 남는 사건이나 일은 무엇이었나요?",
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

const currentQuestion = computed(() => questions[currentStep.value] || {});

// --- Lifecycle & Methods ---

onMounted(() => {
  if (localStorage.getItem('chat_diary_draft')) {
    const draft = JSON.parse(localStorage.getItem('chat_diary_draft'));
    // 날짜가 같으면 복원
    if (draft.date === targetDate) {
        if (confirm("작성 중인 대화가 있습니다. 이어하시겠습니까?")) {
            answers.value = draft.answers;
            currentStep.value = draft.step;
            messages.value = draft.messages;
            scrollToBottom();
            return;
        }
    }
  }
  // Start new
  localStorage.removeItem('chat_diary_draft');
  addBotMessage(questions[0].text);
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
    if (questions[currentStep.value].inputType === 'text') {
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
            if (res && res.data && res.data.reaction) {
                reaction = res.data.reaction;
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

function getMoodEmoji(level) {
    return ['🤬', '😢', '😐', '🙂', '🥰'][level-1];
}
function getMoodLabel(level) {
    return ['최악', '우울', '보통', '좋음', '최고'][level-1];
}

async function proceedNext() {
  currentStep.value++;
  
  if (currentStep.value < questions.length) {
    await addBotMessage(questions[currentStep.value].text);
  } else {
    // Finish
    await addBotMessage("기록해주셔서 감사합니다. 소중한 하루를 저장하고 있어요... 💾");
    submitDiary();
  }
}

async function submitDiary() {
    isCompleted.value = true;
    try {
        const payload = {
            ...answers.value,
            created_at: targetDate, // Or handled by backend? backend uses created_at param
            // backend 'created_at' expects ISO string or date part? 
            // implementation_plan says /api/diaries POST.
            // Let's ensure format. backend expects 'YYYY-MM-DD' or ISO?
            // backend: created_at = datetime.fromisoformat(created_at_str)
        };

        // Ensure date format compatible with backend
        // If we only send date, backend might set time to current time or 00:00
        // Best to send ISO string with current time but target date
        const now = new Date();
        const [y, m, d] = targetDate.split('-');
        now.setFullYear(y, m-1, d);
        payload.created_at = now.toISOString();

        await axios.post('/api/diaries', payload, {
            headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
        });

        localStorage.removeItem('chat_diary_draft');
        await addBotMessage("저장이 완료되었습니다! 캘린더로 이동합니다. 👋");
        setTimeout(() => {
            router.push('/calendar');
        }, 1500);

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
        currentInput.value = answers.value[questions[currentStep.value].field];
        if (questions[currentStep.value].inputType === 'text') {
             nextTick(autoResize);
        }
    } else {
        alert("마지막 답변만 수정할 수 있습니다.");
    }
}

function goBack() {
    if(confirm("대화를 종료하고 나가시겠습니까?")) {
        router.back();
    }
}

function resetChat() {
    if(confirm("대화를 처음부터 다시 시작하시겠습니까?")) {
        localStorage.removeItem('chat_diary_draft');
        window.location.reload();
    }
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
</style>
