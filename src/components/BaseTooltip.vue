<script setup>
defineProps({ variant: { type: String, default: 'default' } }) // default | danger
</script>

<template>
  <span class="tooltip" :class="`tooltip--${variant}`" role="tooltip"><slot /></span>
</template>

<style scoped>
.tooltip {
  display: inline-block;
  padding: 0.375rem 0.5rem;
  border-radius: var(--radius-md);
  font: var(--text-caption);
  text-align: center;
  white-space: nowrap;
  pointer-events: none;
}
.tooltip--default {
  background: var(--surface-highlight);
  border: 1px solid var(--border-main);
  color: var(--text-main);
}
.tooltip--danger {
  background: var(--status-danger);
  color: var(--text-inverse);
}
</style>
