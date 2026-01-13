<template>
  <div class="calendar-grid">
    <!-- 요일 헤더 -->
    <div class="weekday-header">
      <div v-for="day in weekdays" :key="day" class="weekday">
        {{ day }}
      </div>
    </div>

    <!-- 날짜 그리드 -->
    <div class="dates-grid">
      <button
        v-for="date in dates"
        :key="date.key"
        class="date-cell"
        :class="{
          'other-month': !date.isCurrentMonth,
          'today': date.isToday,
          'has-diary': date.hasDiary,
          'selected': selectedDate === date.dateString
        }"
        @click="handleDateClick(date)"
        :disabled="!date.isCurrentMonth"
        type="button"
      >
        <span class="date-number">{{ date.day }}</span>
        <span v-if="date.emoji" class="date-emoji">{{ date.emoji }}</span>
        <span v-if="date.aiPrediction" class="date-ai-prediction">{{ date.aiPrediction }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'CalendarGrid',
  props: {
    year: {
      type: Number,
      required: true
    },
    month: {
      type: Number,
      required: true
    },
    diaries: {
      type: Array,
      default: () => []
    },
    selectedDate: {
      type: String,
      default: null
    }
  },
  emits: ['date-click'],
  setup(props, { emit }) {
    const weekdays = ['일', '월', '화', '수', '목', '금', '토']

    const emojiMap = {
      'happy': '😊',
      'calm': '😌',
      'neutral': '😐',
      'sad': '😢',
      'angry': '😡'
    }

    const dates = computed(() => {
      const result = []
      const firstDay = new Date(props.year, props.month - 1, 1)
      const lastDay = new Date(props.year, props.month, 0)
      const prevLastDay = new Date(props.year, props.month - 1, 0)
      
      const firstDayOfWeek = firstDay.getDay()
      const lastDate = lastDay.getDate()
      
      // 이전 달 날짜
      for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = prevLastDay.getDate() - i
        result.push({
          key: `prev-${day}`,
          day,
          isCurrentMonth: false,
          isToday: false,
          hasDiary: false,
          emoji: null,
          dateString: null
        })
      }
      
      // 현재 달 날짜
      const today = new Date()
      for (let day = 1; day <= lastDate; day++) {
        const dateString = `${props.year}-${String(props.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        const diary = props.diaries.find(d => d.date === dateString)
        const isToday = 
          today.getFullYear() === props.year &&
          today.getMonth() + 1 === props.month &&
          today.getDate() === day
        
        result.push({
          key: `current-${day}`,
          day,
          isCurrentMonth: true,
          isToday,
          hasDiary: !!diary,
          emoji: diary ? emojiMap[diary.mood] : null,
          aiPrediction: diary?.ai_prediction || null,
          dateString
        })
      }
      
      // 다음 달 날짜 (42칸 채우기 - 6주)
      const remainingCells = 42 - result.length
      for (let day = 1; day <= remainingCells; day++) {
        result.push({
          key: `next-${day}`,
          day,
          isCurrentMonth: false,
          isToday: false,
          hasDiary: false,
          emoji: null,
          dateString: null
        })
      }
      
      return result
    })

    const handleDateClick = (date) => {
      if (date.isCurrentMonth) {
        emit('date-click', date)
      }
    }

    return {
      weekdays,
      dates,
      handleDateClick
    }
  }
}
</script>

<style scoped>
.calendar-grid {
  width: 100%;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: var(--spacing-sm);
}

.weekday {
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  padding: var(--spacing-sm);
}

.weekday:first-child {
  color: #FF6B6B;
}

.weekday:last-child {
  color: #4A90E2;
}

.dates-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.date-cell {
  aspect-ratio: 1;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--bg-card);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s ease;
  position: relative;
  padding: var(--spacing-sm);
}

.date-cell:hover:not(:disabled):not(.other-month) {
  background-color: var(--color-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.date-cell.other-month {
  opacity: 0.3;
  cursor: not-allowed;
  background-color: transparent;
}

.date-cell.today {
  border-color: var(--color-primary);
  border-width: 2px;
  font-weight: 600;
}

.date-cell.selected {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: var(--color-primary);
}

.date-cell.has-diary {
  background-color: rgba(255, 217, 61, 0.1);
}

.date-number {
  font-size: 14px;
  color: var(--color-text);
}

.date-emoji {
  font-size: 24px;
  line-height: 1;
}

.date-ai-prediction {
  font-size: 10px;
  color: var(--color-text-light);
  text-align: center;
  line-height: 1.2;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .dates-grid {
    gap: 4px;
  }
  
  .date-number {
    font-size: 12px;
  }
  
  .date-emoji {
    font-size: 20px;
  }
  
  .date-ai-prediction {
    font-size: 9px;
  }
}
</style>
