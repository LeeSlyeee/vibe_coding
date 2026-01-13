<template>
  <div class="emoji-selector">
    <p class="emoji-label">{{ label }}</p>
    <div class="emoji-options">
      <button
        v-for="emoji in emojis"
        :key="emoji.value"
        class="emoji-option"
        :class="{ selected: modelValue === emoji.value }"
        @click="selectEmoji(emoji.value)"
        type="button"
      >
        <span class="emoji-icon">{{ emoji.icon }}</span>
        <span class="emoji-name">{{ emoji.name }}</span>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EmojiSelector',
  props: {
    modelValue: {
      type: String,
      default: null
    },
    label: {
      type: String,
      default: '오늘 뭐한 이모지였나요?'
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const emojis = [
      { value: 'happy', icon: '😊', name: '행복해' },
      { value: 'calm', icon: '😌', name: '편안해' },
      { value: 'neutral', icon: '😐', name: '그저그래' },
      { value: 'sad', icon: '😢', name: '우울해' },
      { value: 'angry', icon: '😡', name: '화나' }
    ]

    const selectEmoji = (value) => {
      emit('update:modelValue', value)
    }

    return {
      emojis,
      selectEmoji
    }
  }
}
</script>

<style scoped>
.emoji-selector {
  margin-bottom: var(--spacing-lg);
}

.emoji-label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: var(--spacing-md);
  color: var(--color-text);
}

.emoji-options {
  display: flex;
  gap: var(--spacing-md);
  justify-content: space-around;
  flex-wrap: wrap;
}

.emoji-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background-color: var(--bg-card);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 70px;
}

.emoji-option:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-placeholder);
}

.emoji-option.selected {
  border-color: var(--color-primary);
  background-color: rgba(0, 0, 0, 0.03);
  transform: scale(1.05);
}

.emoji-icon {
  font-size: 32px;
  line-height: 1;
}

.emoji-name {
  font-size: 12px;
  color: var(--color-text-light);
  font-weight: 500;
}

.emoji-option.selected .emoji-name {
  color: var(--color-primary);
  font-weight: 600;
}

@media (max-width: 640px) {
  .emoji-options {
    gap: var(--spacing-sm);
  }
  
  .emoji-option {
    min-width: 60px;
    padding: var(--spacing-sm);
  }
  
  .emoji-icon {
    font-size: 28px;
  }
}
</style>
