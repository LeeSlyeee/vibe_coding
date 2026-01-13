<template>
  <div class="question-accordion">
    <button
      class="accordion-header"
      :class="{ open: isOpen }"
      @click="toggle"
      type="button"
    >
      <span class="question-text">
        {{ question }}
        <span v-if="required" class="required-mark">*</span>
      </span>
      <span class="toggle-icon">{{ isOpen ? '▲' : '▼' }}</span>
    </button>
    
    <transition name="slide">
      <div v-if="isOpen" class="accordion-content">
        <textarea
          v-model="inputValue"
          :placeholder="placeholder"
          class="input"
          :rows="rows"
          @input="handleInput"
        ></textarea>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'QuestionAccordion',
  props: {
    question: {
      type: String,
      required: true
    },
    modelValue: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '내용을 입력해주세요...'
    },
    required: {
      type: Boolean,
      default: false
    },
    rows: {
      type: Number,
      default: 4
    },
    defaultOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const isOpen = ref(props.defaultOpen)
    const inputValue = ref(props.modelValue)

    const toggle = () => {
      isOpen.value = !isOpen.value
    }

    const handleInput = () => {
      emit('update:modelValue', inputValue.value)
    }

    watch(() => props.modelValue, (newValue) => {
      inputValue.value = newValue
    })

    return {
      isOpen,
      inputValue,
      toggle,
      handleInput
    }
  }
}
</script>

<style scoped>
.question-accordion {
  margin-bottom: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background-color: var(--bg-card);
}

.accordion-header {
  width: 100%;
  padding: var(--spacing-md);
  background-color: transparent;
  border: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-align: left;
}

.accordion-header:hover {
  background-color: var(--color-hover);
}

.accordion-header.open {
  background-color: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid var(--color-border);
}

.question-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.required-mark {
  color: #FF6B6B;
  margin-left: 4px;
}

.toggle-icon {
  font-size: 12px;
  color: var(--color-text-light);
  transition: transform 0.2s ease;
}

.accordion-content {
  padding: var(--spacing-md);
}

.accordion-content textarea {
  margin: 0;
}

/* 슬라이드 애니메이션 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 300px;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
