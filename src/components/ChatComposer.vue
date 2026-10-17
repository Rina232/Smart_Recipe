<script setup>
import { nextTick, onMounted, ref, computed } from 'vue'
import BaseIcon from './BaseIcon.vue'

const props = defineProps({
  placeholder: { type: String, default: 'Напишите сообщение' },
  dimWhenEmpty: Boolean, // кнопка отправки серая, пока поле пустое (экран «Новый чат»)
  disabled: Boolean,
})
const emit = defineEmits(['submit'])

const text = ref('')
const area = ref(null)
const canSend = computed(() => text.value.trim().length > 0 && !props.disabled)

function resize() {
  const el = area.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function submit() {
  if (!canSend.value) return
  emit('submit', text.value.trim())
  text.value = ''
  nextTick(resize)
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submit()
  }
}

onMounted(resize)
defineExpose({ focus: () => area.value?.focus() })
</script>

<template>
  <form class="composer" @submit.prevent="submit">
    <textarea
      ref="area"
      v-model="text"
      class="composer__input"
      rows="1"
      :placeholder="placeholder"
      :aria-label="placeholder"
      @input="resize"
      @keydown="onKeydown"
    />
    <button
      type="submit"
      class="composer__send"
      :class="{ 'composer__send--dim': dimWhenEmpty && !canSend }"
      :disabled="!canSend"
      aria-label="Отправить"
    >
      <BaseIcon name="up-arrow-circle" size="1.5rem" />
    </button>
  </form>
</template>

<style scoped>
.composer {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--surface-1);
  border: 1px solid var(--text-main);
  border-radius: var(--radius-md);
  transition: border-color 0.15s ease;
}
.composer:focus-within {
  border-color: var(--primary);
}
.composer__input {
  flex: 1;
  min-width: 0;
  max-height: 10rem;
  padding: 0;
  border: 0;
  outline: none;
  resize: none;
  background: transparent;
  font: var(--text-body-regular);
  line-height: 1.5rem;
  color: var(--text-main);
}
.composer__input::placeholder {
  color: var(--text-main);
  opacity: 1;
}
.composer__send {
  display: inline-flex;
  flex: none;
  border-radius: 50%;
  color: var(--primary);
  transition: color 0.15s ease, transform 0.15s ease;
}
.composer__send--dim {
  color: var(--text-muted);
}
.composer__send:disabled {
  cursor: default;
}
.composer__send:not(:disabled):hover {
  transform: scale(1.08);
}
</style>
