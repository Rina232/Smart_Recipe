<script setup>
import { computed } from 'vue'
import BaseIcon from './BaseIcon.vue'

const props = defineProps({
  dir: { type: String, required: true }, // up | down | flat
  text: { type: String, required: true },
})

const icon = computed(() => ({ up: 'up-triangle', down: 'down-triangle', flat: 'equals' })[props.dir])
const label = computed(() => ({ up: 'Рост', down: 'Снижение', flat: 'Без изменений' })[props.dir])
</script>

<template>
  <span class="delta" :class="`delta--${dir}`">
    <BaseIcon :name="icon" size="1rem" />
    <span class="sr-only">{{ label }}:</span>
    <span>{{ text }}</span>
  </span>
</template>

<style scoped>
.delta {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
  font: var(--text-label-strong);
}
.delta--up {
  color: var(--status-success);
}
.delta--down {
  color: var(--status-danger);
}
.delta--flat {
  color: var(--text-muted);
}
</style>
