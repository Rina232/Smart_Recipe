<script setup>
import { computed } from 'vue'
import BaseIcon from './BaseIcon.vue'

const props = defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  total: { type: Number, required: true },
})
const emit = defineEmits(['update:page'])

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const from = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1))
const to = computed(() => Math.min(props.page * props.pageSize, props.total))

const go = (p) => emit('update:page', Math.min(Math.max(1, p), pages.value))
</script>

<template>
  <div class="footer">
    <p class="footer__range">Записи {{ from }}-{{ to }} из {{ total }}</p>
    <p class="footer__page">Страница {{ page }} из {{ pages }}</p>

    <nav class="footer__nav" aria-label="Пагинация">
      <div class="footer__group">
        <button type="button" class="nav-btn nav-btn--flip" :disabled="page <= 1" aria-label="Первая страница" title="Первая страница" @click="go(1)">
          <BaseIcon name="right-arrow-to-bar" />
        </button>
        <button type="button" class="nav-btn nav-btn--flip" :disabled="page <= 1" aria-label="Предыдущая страница" title="Предыдущая страница" @click="go(page - 1)">
          <BaseIcon name="right-arrow" />
        </button>
      </div>
      <div class="footer__group">
        <button type="button" class="nav-btn" :disabled="page >= pages" aria-label="Следующая страница" title="Следующая страница" @click="go(page + 1)">
          <BaseIcon name="right-arrow" />
        </button>
        <button type="button" class="nav-btn" :disabled="page >= pages" aria-label="Последняя страница" title="Последняя страница" @click="go(pages)">
          <BaseIcon name="right-arrow-to-bar" />
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.footer {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 0.75rem 1rem;
  width: 100%;
  min-height: 1.5rem;
  font: var(--text-body-regular);
  color: var(--text-main);
}
.footer__nav {
  display: flex;
  gap: 2rem;
  justify-self: end;
}
.footer__group {
  display: flex;
  gap: 1rem;
}
.nav-btn {
  display: inline-flex;
  color: var(--text-main);
  border-radius: var(--radius-sm);
}
.nav-btn--flip :deep(.icon) {
  transform: scaleX(-1);
}
.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.nav-btn:not(:disabled):hover {
  color: var(--primary);
}

@media (max-width: 640px) {
  .footer {
    grid-template-columns: 1fr;
    justify-items: start;
  }
  .footer__nav {
    justify-self: start;
  }
}
</style>
