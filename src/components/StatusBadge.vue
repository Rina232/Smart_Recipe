<script setup>
defineProps({ active: { type: Boolean, required: true } })
</script>

<template>
  <span class="badge" :class="active ? 'badge--active' : 'badge--deleted'">
    {{ active ? 'Активен' : 'Удален' }}
  </span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-md);
  font: var(--text-caption);
  color: var(--text-inverse);
  white-space: nowrap;
}
.badge--active {
  background: var(--status-success);
}
.badge--deleted {
  background: var(--status-danger);
}
</style>
