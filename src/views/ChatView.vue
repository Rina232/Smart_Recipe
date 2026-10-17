<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatsStore } from '@/stores/chats'
import ChatComposer from '@/components/ChatComposer.vue'
import RecipeCard from '@/components/RecipeCard.vue'

const route = useRoute()
const router = useRouter()

const chat = computed(() => chatsStore.get(route.params.id))
const pending = computed(() => !!chatsStore.state.pending[route.params.id])
const scroller = ref(null)

// чат удалён или не найден — на экран нового чата
watch(chat, (c) => {
  if (!c) router.replace({ name: 'new-chat' })
}, { immediate: true })

async function scrollToEnd() {
  await nextTick()
  const el = scroller.value
  if (el) el.scrollTop = el.scrollHeight
}

watch(
  () => [route.params.id, chat.value?.messages.length, pending.value],
  scrollToEnd,
  { immediate: true, flush: 'post' },
)

function send(text) {
  chatsStore.send(route.params.id, text)
}
</script>

<template>
  <section v-if="chat" class="chat">
    <div ref="scroller" class="chat__scroll">
      <div class="chat__thread" role="log" aria-live="polite" aria-label="Сообщения чата">
        <template v-for="m in chat.messages" :key="m.id">
          <div v-if="m.role === 'user'" class="chat__row chat__row--user">
            <p class="chat__bubble">{{ m.text }}</p>
          </div>

          <div v-else class="chat__row chat__row--assistant">
            <RecipeCard v-if="m.recipe" :recipe="m.recipe" />
            <p v-if="m.text" class="chat__text">{{ m.text }}</p>
          </div>
        </template>

        <p v-if="pending" class="chat__typing">
          Подбираю рецепт<span class="chat__dots" aria-hidden="true"><i>.</i><i>.</i><i>.</i></span>
        </p>
      </div>
    </div>

    <div class="chat__composer">
      <ChatComposer placeholder="Напишите сообщение" @submit="send" />
    </div>
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.chat__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: clamp(1rem, 2vw, 1.5rem);
}
.chat__thread {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 80rem;
  margin-inline: auto;
}
.chat__row {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.chat__row--user {
  align-items: flex-end;
}
.chat__row--assistant {
  align-items: flex-start;
}
.chat__bubble {
  max-width: min(85%, 28rem);
  padding: 0.5rem 0.75rem;
  background: var(--primary);
  color: var(--text-inverse);
  border-radius: var(--radius-lg);
  font: var(--text-body-regular);
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
.chat__text {
  max-width: 44rem;
  font: var(--text-body-regular);
  color: var(--text-main);
}
.chat__typing {
  font: var(--text-body-regular);
  color: var(--text-muted);
}
.chat__dots i {
  font-style: normal;
  animation: blink 1.2s infinite both;
}
.chat__dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.chat__dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; }
  40% { opacity: 1; }
}
.chat__composer {
  flex: none;
  max-width: 80rem;
  width: 100%;
  margin-inline: auto;
  padding: 0 clamp(1rem, 2vw, 1.5rem) clamp(1rem, 2vw, 1.5rem);
}
</style>
