<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import BaseButton from './BaseButton.vue'

const props = defineProps({
  open: Boolean,
  title: { type: String, required: true },
  text: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Подтвердить' },
  cancelLabel: { type: String, default: 'Отмена' },
})
const emit = defineEmits(['confirm', 'cancel'])

const cancelBtn = ref(null)
let previouslyFocused = null

function onKey(e) {
  if (e.key === 'Escape') emit('cancel')
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previouslyFocused = document.activeElement
      window.addEventListener('keydown', onKey)
      await nextTick()
      cancelBtn.value?.$el?.focus()
    } else {
      window.removeEventListener('keydown', onKey)
      previouslyFocused?.focus?.()
    }
  },
)
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="dialog" @mousedown.self="emit('cancel')">
      <div class="dialog__panel" role="alertdialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-text">
        <h2 id="dialog-title" class="dialog__title">{{ title }}</h2>
        <p v-if="text" id="dialog-text" class="dialog__text">{{ text }}</p>
        <div class="dialog__actions">
          <BaseButton ref="cancelBtn" variant="secondary" @click="emit('cancel')">{{ cancelLabel }}</BaseButton>
          <BaseButton @click="emit('confirm')">{{ confirmLabel }}</BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgb(41 37 42 / 0.4);
}
.dialog__panel {
  width: min(100%, 24rem);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-lg);
  box-shadow: 0 1rem 2.5rem rgb(41 37 42 / 0.18);
}
.dialog__title {
  font: var(--text-h2);
  overflow-wrap: anywhere;
}
.dialog__text {
  color: var(--text-muted);
}
.dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
</style>
