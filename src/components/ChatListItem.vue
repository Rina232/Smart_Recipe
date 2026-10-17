<script setup>
import BaseIcon from './BaseIcon.vue'
import BaseTooltip from './BaseTooltip.vue'

defineProps({
  chat: { type: Object, required: true },
  selected: Boolean,
  collapsed: Boolean,
  deletable: { type: Boolean, default: true },
})
defineEmits(['delete'])
</script>

<template>
  <!-- свёрнутый сайдбар: только иконка чата -->
  <RouterLink
    v-if="collapsed"
    :to="{ name: 'chat', params: { id: chat.id } }"
    class="chat-icon"
    :class="{ 'is-selected': selected }"
    :title="chat.title"
    :aria-label="chat.title"
    :aria-current="selected ? 'page' : undefined"
  >
    <BaseIcon name="chat" size="1.5rem" />
  </RouterLink>

  <!-- развёрнутый сайдбар -->
  <li v-else class="chat-item" :class="{ 'is-selected': selected }">
    <RouterLink
      :to="{ name: 'chat', params: { id: chat.id } }"
      class="chat-item__link"
      :aria-current="selected ? 'page' : undefined"
    >
      {{ chat.title }}
    </RouterLink>
    <template v-if="deletable">
      <button type="button" class="chat-item__delete" :aria-label="`Удалить чат «${chat.title}»`" @click="$emit('delete')">
        <BaseIcon name="bin" size="1.25rem" />
      </button>
      <BaseTooltip variant="danger" class="chat-item__tip">Удалить чат</BaseTooltip>
    </template>
  </li>
</template>

<style scoped>
.chat-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding-right: 0.5rem;
  border-radius: var(--radius-md);
}
.chat-item:hover,
.chat-item:focus-within,
.chat-item.is-selected {
  background: var(--surface-highlight);
}
.chat-item__link {
  flex: 1;
  min-width: 0;
  padding: 0.5rem 0 0.5rem 0.5rem;
  font: var(--text-body-regular);
  color: var(--text-main);
  text-decoration: none;
  overflow-wrap: anywhere;
}
.chat-item__delete {
  display: none;
  flex: none;
  margin-top: 0.5rem;
  color: var(--text-main);
  border-radius: var(--radius-sm);
}
.chat-item:hover .chat-item__delete,
.chat-item:focus-within .chat-item__delete {
  display: inline-flex;
}
@media (hover: none) {
  .chat-item__delete {
    display: inline-flex;
  }
}
.chat-item__tip {
  position: absolute;
  right: -0.375rem;
  bottom: calc(100% + 0.25rem);
  opacity: 0;
  transition: opacity 0.12s ease;
  z-index: 5;
}
.chat-item__delete:hover + .chat-item__tip,
.chat-item__delete:focus-visible + .chat-item__tip {
  opacity: 1;
}

.chat-icon {
  display: inline-flex;
  align-self: center;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  color: var(--text-main);
}
.chat-icon:hover,
.chat-icon.is-selected {
  background: var(--surface-highlight);
}
</style>
