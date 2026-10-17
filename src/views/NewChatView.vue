<script setup>
import { useRouter } from 'vue-router'
import { chatsStore } from '@/stores/chats'
import ChatComposer from '@/components/ChatComposer.vue'

const router = useRouter()

function start(text) {
  const id = chatsStore.send(null, text)
  if (id) router.push({ name: 'chat', params: { id } })
}
</script>

<template>
  <section class="hero">
    <div class="hero__inner">
      <h1 class="hero__title">Smart Recipe</h1>
      <p class="hero__subtitle">Что бы вы хотели сегодня приготовить?</p>
      <div class="hero__composer">
        <ChatComposer
          dim-when-empty
          placeholder="Напишите, что хотите приготовить или какие продукты у вас есть..."
          @submit="start"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  display: grid;
  place-items: center;
  min-height: 100%;
  padding: 1.5rem;
  background: radial-gradient(ellipse 55% 55% at 50% 50%, rgb(242 230 213 / 0.95) 0%, rgb(242 230 213 / 0.45) 55%, rgb(250 247 240 / 0) 100%),
    var(--surface-0);
}
.hero__inner {
  width: min(100%, 50rem);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.hero__title {
  font: var(--text-h0);
  color: var(--text-muted);
}
.hero__subtitle {
  margin-top: 0.25rem;
  font: var(--text-body-regular);
  color: var(--text-muted);
}
.hero__composer {
  width: 100%;
  margin-top: 2.5rem;
  text-align: left;
}
</style>
