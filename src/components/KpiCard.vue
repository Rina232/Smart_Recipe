<script setup>
import DeltaBadge from './DeltaBadge.vue'

defineProps({
  title: { type: String, required: true },
  value: { type: String, required: true },
  delta: { type: Object, required: true }, // { dir, text }
  caption: { type: String, default: '' },
})
</script>

<template>
  <article class="kpi">
    <div class="kpi__top">
      <h2 class="kpi__title">{{ title }}</h2>
      <p class="kpi__value">{{ value }}</p>
    </div>
    <div class="kpi__bottom">
      <DeltaBadge :dir="delta.dir" :text="delta.text" />
      <p v-if="caption" class="kpi__caption">{{ caption }}</p>
    </div>
  </article>
</template>

<style scoped>
.kpi {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1rem;
  width: min(100%, 22rem);
  padding: clamp(0.75rem, 2vw, 1rem);
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-md);
}
.kpi__top {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.kpi__title {
  font: var(--text-h2);
  color: var(--text-main);
}
.kpi__value {
  font: var(--text-body-indicator);
  color: var(--text-main);
}
.kpi__bottom {
  display: flex;
  flex-direction: column;
}
.kpi__caption {
  font: var(--text-label-regular);
  color: var(--text-main);
}
</style>
