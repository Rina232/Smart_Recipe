<script setup>
import { computed } from 'vue'
import { passwordStrength } from '@/utils/validation'

const props = defineProps({ password: { type: String, default: '' } })

const config = {
  inactive: { filled: 0, label: '' },
  'very-weak': { filled: 3, label: 'Очень слабый пароль', color: 'var(--status-critical)' },
  weak: { filled: 1, label: 'Слабый пароль', color: 'var(--status-danger)' },
  medium: { filled: 2, label: 'Средний пароль', color: 'var(--status-warning)' },
  strong: { filled: 3, label: 'Сильный пароль', color: 'var(--status-success)' },
}

const state = computed(() => passwordStrength(props.password))
const view = computed(() => config[state.value])
</script>

<template>
  <div class="strength">
    <div class="strength__bars" aria-hidden="true">
      <span
        v-for="n in 3"
        :key="n"
        class="strength__bar"
        :style="n <= view.filled ? { background: view.color } : undefined"
      />
    </div>
    <p class="strength__label" :style="{ color: view.color }" aria-live="polite">{{ view.label }}</p>
  </div>
</template>

<style scoped>
.strength {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}
.strength__bars {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.strength__bar {
  height: 0.5rem;
  border-radius: 0.25rem;
  background: var(--surface-highlight);
  transition: background-color 0.2s ease;
}
.strength__label {
  font: var(--text-caption);
  min-height: 1em;
}
</style>
