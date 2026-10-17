<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '@/stores/auth'
import { chatsStore } from '@/stores/chats'
import BaseIcon from './BaseIcon.vue'
import BaseButton from './BaseButton.vue'
import ChatListItem from './ChatListItem.vue'

const props = defineProps({
  collapsed: Boolean,
  mobile: Boolean, // выдвижное наложение на узких экранах
  open: Boolean,
})
const emit = defineEmits(['toggle', 'request-delete'])

const route = useRoute()
const router = useRouter()

const chats = computed(() => chatsStore.state.chats)
const canCreate = computed(() => !auth.isGuest || chats.value.length === 0)
const toggleLabel = computed(() => {
  if (props.mobile) return 'Закрыть панель чатов'
  return props.collapsed ? 'Развернуть панель чатов' : 'Свернуть панель чатов'
})

function logout() {
  auth.logout()
  router.replace({ name: 'login' })
}
</script>

<template>
  <aside
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-mobile': mobile, 'is-open': open }"
    :inert="mobile && !open ? '' : undefined"
    aria-label="Боковая панель"
  >
    <div class="sidebar__head">
      <h2 v-if="!collapsed" class="sidebar__title">ЧАТЫ</h2>
      <button type="button" class="icon-btn" :aria-label="toggleLabel" :aria-expanded="!collapsed" @click="emit('toggle')">
        <BaseIcon name="sidebar-left" size="1.25rem" />
      </button>
    </div>
    <hr class="sidebar__divider" />

    <template v-if="canCreate">
      <RouterLink :to="{ name: 'new-chat' }" class="sidebar__new" :title="collapsed ? 'Новый чат' : undefined" :aria-label="collapsed ? 'Новый чат' : undefined">
        <BaseIcon name="plus" size="1.5rem" />
        <span v-if="!collapsed">Новый чат</span>
      </RouterLink>
      <hr class="sidebar__divider" />
    </template>

    <nav class="sidebar__list" aria-label="Список чатов">
      <ul class="sidebar__items" :class="{ 'is-collapsed': collapsed }">
        <template v-for="chat in chats" :key="chat.id">
          <li v-if="collapsed" class="sidebar__icon-row">
            <ChatListItem :chat="chat" collapsed :selected="route.params.id === chat.id" />
          </li>
          <ChatListItem
            v-else
            :chat="chat"
            :selected="route.params.id === chat.id"
            :deletable="!auth.isGuest"
            @delete="emit('request-delete', chat)"
          />
        </template>
      </ul>
    </nav>

    <div class="sidebar__bottom">
      <BaseButton
        v-if="auth.isAdmin"
        :to="{ name: 'admin' }"
        block
        class="sidebar__btn"
        :class="{ 'is-compact': collapsed }"
        :title="collapsed ? 'Панель администратора' : undefined"
        :aria-label="collapsed ? 'Панель администратора' : undefined"
      >
        <BaseIcon name="dashboard" size="1rem" />
        <span v-if="!collapsed">Панель администратора</span>
      </BaseButton>

      <BaseButton
        variant="secondary"
        block
        class="sidebar__btn"
        :class="{ 'is-compact': collapsed }"
        :title="collapsed ? 'Выйти' : undefined"
        :aria-label="collapsed ? 'Выйти' : undefined"
        @click="logout"
      >
        <BaseIcon name="door" size="1rem" />
        <span v-if="!collapsed">Выйти</span>
      </BaseButton>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  flex: none;
  width: var(--sidebar-w);
  height: 100dvh;
  padding: clamp(1rem, 2vw, 1.5rem);
  background: var(--surface-1);
  border-right: 1px solid var(--border-main);
  overflow: hidden;
  transition: width 0.2s ease, padding 0.2s ease;
}
.sidebar.is-collapsed {
  width: var(--sidebar-w-collapsed);
  padding: 1.5rem 0.75rem;
}

.sidebar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.5rem;
  min-height: 2.25rem;
}
.is-collapsed .sidebar__head {
  justify-content: center;
}
.sidebar__title {
  font: var(--text-h3);
  color: var(--text-main);
}
.icon-btn {
  display: inline-flex;
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  color: var(--text-main);
}
.icon-btn:hover {
  background: var(--surface-highlight);
}

.sidebar__divider {
  width: 100%;
  margin: 0;
  border: 0;
  border-top: 1px solid var(--text-muted);
}

.sidebar__new {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  font: var(--text-body-regular);
  color: var(--text-main);
  text-decoration: none;
  border-radius: var(--radius-sm);
}
.sidebar__new:hover {
  background: var(--surface-highlight);
}
.is-collapsed .sidebar__new {
  justify-content: center;
}

.sidebar__list {
  flex: 1;
  min-height: 0;
  margin-top: 0.75rem;
  overflow-y: auto;
}
.sidebar__items {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.sidebar__items.is-collapsed {
  align-items: center;
  gap: 0.5rem;
}
.sidebar__icon-row {
  display: flex;
}

.sidebar__bottom {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 1rem;
}
.sidebar__btn {
  min-height: 2rem;
}
.sidebar__btn.is-compact {
  width: 2.5rem;
  align-self: center;
  padding: 0.5rem;
}

/* узкие экраны: выдвижная панель поверх контента */
.sidebar.is-mobile {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 40;
  width: min(85vw, 18.25rem);
  transform: translateX(-100%);
  transition: transform 0.2s ease, visibility 0s linear 0.2s;
  visibility: hidden;
  box-shadow: 0 0 2rem rgb(41 37 42 / 0.2);
}
.sidebar.is-mobile.is-open {
  transform: none;
  visibility: visible;
  transition: transform 0.2s ease;
}
</style>
