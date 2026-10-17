<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  variant: { type: String, default: 'primary' }, // primary | secondary
  to: { type: [String, Object], default: undefined },
  block: Boolean,
  type: { type: String, default: 'button' },
})
</script>

<template>
  <component
    :is="to ? RouterLink : 'button'"
    :to="to"
    :type="to ? undefined : type"
    class="btn"
    :class="[`btn--${variant}`, { 'btn--block': block }]"
  >
    <slot />
  </component>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font: var(--text-label-strong);
  line-height: 1.25;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}
.btn--block {
  width: 100%;
}
.btn--primary {
  background: var(--primary);
  color: var(--text-inverse);
}
.btn--primary:hover {
  background: var(--primary-hover);
}
.btn--secondary {
  background: var(--surface-1);
  color: var(--primary);
  border-color: var(--primary);
}
.btn--secondary:hover {
  background: var(--surface-highlight);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
