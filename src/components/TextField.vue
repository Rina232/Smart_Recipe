<script setup>
import { computed, ref, useId } from 'vue'
import BaseIcon from './BaseIcon.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  password: Boolean,
  icon: { type: String, default: '' },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'blur'])

const uid = useId()
const shown = ref(false)
const inputType = computed(() => (props.password ? (shown.value ? 'text' : 'password') : props.type))
</script>

<template>
  <div class="field" :class="{ 'field--error': !!error }">
    <label v-if="label" class="field__label" :for="uid">{{ label }}</label>

    <div class="field__control">
      <BaseIcon v-if="icon" :name="icon" size="1rem" class="field__lead" />
      <input
        v-bind="$attrs"
        :id="uid"
        class="field__input"
        :type="inputType"
        :value="modelValue"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="error ? `${uid}-error` : undefined"
        @input="emit('update:modelValue', $event.target.value)"
        @blur="emit('blur', $event)"
      />
      <button
        v-if="password"
        type="button"
        class="field__action"
        :aria-label="shown ? 'Скрыть пароль' : 'Показать пароль'"
        :aria-pressed="shown"
        @click="shown = !shown"
      >
        <BaseIcon :name="shown ? 'eye-off' : 'eye-on'" size="1.5rem" />
      </button>
      <BaseIcon v-else-if="error" name="exclamation" size="1.5rem" class="field__status" />
    </div>

    <p v-if="error" :id="`${uid}-error`" class="field__error" role="alert">{{ error }}</p>
    <slot name="footer" />
  </div>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}
.field__label {
  font: var(--text-label-strong);
  color: var(--text-main);
  text-align: left;
}
.field__control {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  background: var(--surface-1);
  border: 1px solid var(--text-main);
  border-radius: var(--radius-md);
  color: var(--text-main);
  transition: border-color 0.15s ease;
}
.field__control:focus-within {
  border-color: var(--primary);
}
.field--error .field__control {
  border-color: var(--status-danger);
}
.field__input {
  flex: 1;
  min-width: 0;
  padding: 0;
  border: 0;
  outline: none;
  background: transparent;
  font: var(--text-body-regular);
  color: var(--text-main);
}
.field__input::placeholder {
  color: var(--text-muted);
}
.field__action {
  display: inline-flex;
  margin: -0.125rem 0;
  border-radius: var(--radius-sm);
  color: var(--text-main);
}
.field__status {
  color: var(--status-danger);
  margin: -0.125rem 0;
}
.field__error {
  font: var(--text-caption);
  color: var(--status-danger);
}
</style>
