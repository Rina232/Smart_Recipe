<script setup>
import DeltaBadge from './DeltaBadge.vue'
import PeriodSwitch from './PeriodSwitch.vue'

defineProps({
  metrics: { type: Array, required: true }, // [{ title, value, delta: { dir, text } }]
  period: { type: String, required: true },
  options: { type: Array, required: true },
})
defineEmits(['update:period'])
</script>

<template>
  <article class="kpi">
    <div class="kpi__metrics">
      <section v-for="m in metrics" :key="m.title" class="metric">
        <h2 class="metric__title">{{ m.title }}</h2>
        <div class="metric__row">
          <p class="metric__value">{{ m.value }}</p>
          <DeltaBadge class="metric__delta" :dir="m.delta.dir" :text="m.delta.text" />
        </div>
      </section>
    </div>

    <div class="kpi__footer">
      <PeriodSwitch :model-value="period" :options="options" @update:model-value="$emit('update:period', $event)" />
    </div>
  </article>
</template>

<style scoped>
.kpi {
  --gap: clamp(1rem, 2vw, 2rem);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1rem;
  width: min(100%, 45.5rem);
  padding: clamp(0.75rem, 2vw, 1rem);
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-md);
}
.kpi__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem var(--gap);
}
.metric {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-width: 0;
}
.metric + .metric {
  padding-left: var(--gap);
  border-left: 0.125rem dotted var(--text-muted);
}
.metric__title {
  font: var(--text-h2);
  color: var(--text-main);
}
.metric__row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}
.metric__value {
  font: var(--text-body-indicator);
  color: var(--text-main);
}
.metric__delta {
  margin-top: 0.25rem;
}
.kpi__footer {
  display: flex;
  justify-content: flex-end;
}
@media (max-width: 640px) {
  .kpi__footer {
    justify-content: flex-start;
  }
  .metric + .metric {
    padding-left: 0;
    border-left: 0;
  }
}
</style>
