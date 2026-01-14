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
        <img :src="emoji.icon" :alt="emoji.name" class="emoji-img" />
        <span class="emoji-name">{{ emoji.name }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import happyImg from '../assets/01.png'
import calmImg from '../assets/02.png'
import neutralImg from '../assets/03.png'
import sadImg from '../assets/04.png'
import angryImg from '../assets/05.png'

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
      { value: 'happy', icon: happyImg, name: '행복해' },
      { value: 'calm', icon: calmImg, name: '편안해' },
      { value: 'neutral', icon: neutralImg, name: '그저그래' },
      { value: 'sad', icon: sadImg, name: '우울해' },
      { value: 'angry', icon: angryImg, name: '화나' }
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
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--spacing-md);
  margin: 0 auto;
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
  /* Force 3 items per row: 30% * 3 = 90%, leaving space for gaps */
  flex: 0 0 30%;
  max-width: 30%;
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

.emoji-img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  margin-bottom: 4px;
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
