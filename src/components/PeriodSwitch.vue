<script setup>
defineProps({
  modelValue: { type: String, required: true },
  options: { type: Array, required: true }, // [{ value, label }]
  label: { type: String, default: 'Период:' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="period">
    <span class="period__label">{{ label }}</span>
    <div class="period__group" role="group" :aria-label="label">
      <button
        v-for="o in options"
        :key="o.value"
        type="button"
        class="period__option"
        :class="{ 'is-active': o.value === modelValue }"
        :aria-pressed="o.value === modelValue"
        @click="$emit('update:modelValue', o.value)"
      >
        {{ o.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.period {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.period__label {
  font: var(--text-label-regular);
  color: var(--text-main);
}
.period__group {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: var(--surface-0);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-sm);
}
.period__option {
  padding: 0 0.375rem;
  border-radius: var(--radius-sm);
  font: var(--text-body-regular);
  color: var(--text-main);
  transition: background-color 0.15s ease;
}
.period__option:hover {
  background: var(--surface-highlight);
}
.period__option.is-active {
  background: var(--surface-highlight);
}
</style>
