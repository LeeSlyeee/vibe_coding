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
          'selected': selectedDate === date.dateString,
          'future-date': date.isFuture
        }"
        @click="handleDateClick(date)"
        :disabled="!date.isCurrentMonth || date.isFuture"
        type="button"
      >
        <span class="date-number">{{ date.day }}</span>
        <img v-if="date.emoji" :src="date.emoji" class="date-emoji" alt="mood" />
        <span v-if="date.aiPrediction" class="date-ai-prediction">{{ date.aiPrediction }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import happyImg from '../assets/01.png'
import calmImg from '../assets/02.png'
import neutralImg from '../assets/03.png'
import sadImg from '../assets/04.png'
import angryImg from '../assets/05.png'

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
      'happy': happyImg,
      'calm': calmImg,
      'neutral': neutralImg,
      'sad': sadImg,
      'angry': angryImg
    }

    const dates = computed(() => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)

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
          dateString: null,
          isFuture: false // Previous month dates visible in current view are always past relative to current view, but checked via disabled anyway
        })
      }
      
      // 현재 달 날짜
      for (let day = 1; day <= lastDate; day++) {
        const dateString = `${props.year}-${String(props.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        const diary = props.diaries.find(d => d.date === dateString)
        const isToday = 
          today.getFullYear() === props.year &&
          today.getMonth() + 1 === props.month &&
          today.getDate() === day
        
        const currentDataDate = new Date(props.year, props.month - 1, day)
        const isFuture = currentDataDate > today

        // [Parsing AI Prediction]
        // "AI가 예측한 당신의 감정은 '행복해 (95%)'입니다." -> "행복해 (95%)"
        let shortPrediction = null
        if (diary?.ai_prediction) {
          try {
             // Match content inside single quotes, allowing for parentheses and numbers
             const match = diary.ai_prediction.match(/'([^']+)'/)
             if (match && match[1]) {
               // match[1] will rely include "행복해 (95%)"
               shortPrediction = `AI 예측: ${match[1]}`
             } else {
               // Fallback
               shortPrediction = diary.ai_prediction.length > 15
                 ? diary.ai_prediction.slice(0, 12) + '...' 
                 : diary.ai_prediction
             }
          } catch (e) {
            shortPrediction = 'AI 분석값 오류'
          }
        }

        result.push({
          key: `current-${day}`,
          day,
          isCurrentMonth: true,
          isToday,
          hasDiary: !!diary,
          emoji: diary ? emojiMap[diary.mood] : null,
          aiPrediction: shortPrediction,
          dateString,
          isFuture
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.weekday-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: var(--spacing-sm);
  flex-shrink: 0; /* Header shouldn't shrink */
}

/* ... */

.dates-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: 1fr;
  gap: 4px; /* Reduce gap */
  /* flex: 1; Remove flex: 1 to prevent stretching to fill height */
}

.date-cell {
  /* Remove aspect-ratio, use min-height for better content fit */
  min-height: 80px; 
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--bg-card);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center; /* Center content vertically */
  gap: 4px;
  transition: all 0.2s ease;
  position: relative;
  padding: 4px;
  overflow: hidden;
}

.date-cell:hover:not(:disabled):not(.other-month) {
  background-color: var(--color-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
  z-index: 1;
}

.date-cell.other-month {
  opacity: 0.3;
  cursor: not-allowed;
  background-color: transparent;
}

.date-cell.today {
  border-color: var(--color-primary);
  border-width: 2px;
}

.date-cell.today .date-number {
  color: var(--color-primary);
  font-weight: 800;
}

.date-cell.selected {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: var(--color-primary);
}

.date-cell.has-diary {
  background-color: rgba(255, 217, 61, 0.08);
}

.date-emoji {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70%;  /* Fill most of the cell */
  height: 70%;
  object-fit: contain;
  opacity: 0.25; /* Subtle background */
  z-index: 0;
  pointer-events: none;
}

.date-ai-prediction {
  position: relative;
  z-index: 1; /* Above emoji */
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text); /* Darker for readability */
  text-align: center;
  line-height: 1.3;
  width: 100%;
  padding: 0 4px;
  /* margin-top: auto; Remove push to bottom */
  /* margin-bottom: 4px; */
  margin: 0; 
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%; /* Take full height to center properly if needed, or let flex parent handle it */
  white-space: normal;
  word-break: keep-all; /* Prefer breaking at spaces */
  overflow: visible;
  /* text-overflow: ellipsis; Remove ellipsis */
  text-shadow: 0 1px 2px rgba(255,255,255,0.8); /* readable against bg */
}

.date-number {
  align-self: flex-start;
  position: absolute;
  top: 4px;
  left: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1;
  z-index: 1; /* Above emoji */
}

@media (max-width: 768px) {
  .dates-grid {
    gap: 4px;
  }
  
  .date-number {
    font-size: 11px;
    top: 4px;
    left: 4px;
  }
  
  .date-emoji {
    font-size: 22px;
    margin-top: 8px;
  }
  
  .date-ai-prediction {
    font-size: 9px;
  }
}
</style>
