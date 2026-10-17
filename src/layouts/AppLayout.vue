<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatsStore } from '@/stores/chats'
import Sidebar from '@/components/Sidebar.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import BaseIcon from '@/components/BaseIcon.vue'

const route = useRoute()
const router = useRouter()

const COLLAPSE_KEY = 'sr_sidebar_collapsed'
const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === '1')

const isMobile = ref(false)
const mobileOpen = ref(false)
let mq = null
const onMq = (e) => {
  isMobile.value = e.matches
  if (!e.matches) mobileOpen.value = false
}

onMounted(() => {
  mq = window.matchMedia('(max-width: 768px)')
  isMobile.value = mq.matches
  mq.addEventListener('change', onMq)
})
onBeforeUnmount(() => mq?.removeEventListener('change', onMq))

watch(() => route.fullPath, () => (mobileOpen.value = false))

function toggleSidebar() {
  if (isMobile.value) {
    mobileOpen.value = !mobileOpen.value
    return
  }
  collapsed.value = !collapsed.value
  try {
    localStorage.setItem(COLLAPSE_KEY, collapsed.value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

const pendingDelete = ref(null)

function confirmDelete() {
  const chat = pendingDelete.value
  pendingDelete.value = null
  if (!chat) return
  const wasCurrent = route.params.id === chat.id
  chatsStore.remove(chat.id)
  if (wasCurrent) router.replace({ name: 'new-chat' })
}
</script>

<template>
  <div class="app">
    <div v-if="isMobile && mobileOpen" class="app__scrim" @click="mobileOpen = false" />

    <Sidebar
      :collapsed="!isMobile && collapsed"
      :mobile="isMobile"
      :open="mobileOpen"
      @toggle="toggleSidebar"
      @request-delete="pendingDelete = $event"
    />

    <main class="app__main">
      <div v-if="isMobile" class="app__topbar">
        <button type="button" class="app__menu" aria-label="Открыть панель чатов" @click="mobileOpen = true">
          <BaseIcon name="sidebar-left" size="1.25rem" />
        </button>
      </div>
      <div class="app__content">
        <RouterView />
      </div>
    </main>

    <ConfirmDialog
      :open="!!pendingDelete"
      title="Удалить чат?"
      :text="pendingDelete ? `Чат «${pendingDelete.title}» будет удалён без возможности восстановления.` : ''"
      confirm-label="Удалить"
      @confirm="confirmDelete"
      @cancel="pendingDelete = null"
    />
  </div>
</template>

<style scoped>
.app {
  display: flex;
  height: 100dvh;
  background: var(--surface-0);
}
.app__main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  height: 100dvh;
}
.app__content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.app__topbar {
  flex: none;
  padding: 0.75rem 1rem 0;
}
.app__menu {
  display: inline-flex;
  padding: 0.375rem;
  border-radius: var(--radius-md);
  background: var(--surface-1);
  border: 1px solid var(--border-main);
}
.app__scrim {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: rgb(41 37 42 / 0.35);
}
</style>
