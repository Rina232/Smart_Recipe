<script setup>
import BaseIcon from './BaseIcon.vue'

const decos = [
  { name: 'fish', color: '#6e9bc5', left: '3%', top: '19%', size: 'clamp(4rem, 8vw, 7rem)', rotate: '-20deg' },
  { name: 'toast', color: '#e7b94e', left: '56%', top: '20%', size: 'clamp(4rem, 7.5vw, 6.5rem)', rotate: '0deg' },
  { name: 'bacon', color: '#c94b3c', right: '9%', top: '32%', size: 'clamp(3.5rem, 6.5vw, 5.5rem)', rotate: '18deg' },
  { name: 'chef-hat', color: 'rgb(41 37 42 / 0.62)', left: '19%', top: '49%', size: 'clamp(4rem, 7.5vw, 6.5rem)', rotate: '-12deg' },
  { name: 'apple', color: '#6f9b62', left: '3%', top: '76%', size: 'clamp(4rem, 7.5vw, 6.5rem)', rotate: '-8deg' },
  { name: 'bowl-noodles', color: 'rgb(41 37 42 / 0.62)', left: '27%', top: '86%', size: 'clamp(4rem, 8vw, 7rem)', rotate: '6deg' },
  { name: 'burger', color: '#b8861b', right: '5%', top: '76%', size: 'clamp(4rem, 8vw, 7rem)', rotate: '-6deg' },
]
</script>

<template>
  <div class="auth">
    <div class="auth__decor" aria-hidden="true">
      <BaseIcon
        v-for="d in decos"
        :key="d.name"
        :name="`deco/${d.name}`"
        :size="d.size"
        class="auth__deco"
        :style="{ left: d.left, right: d.right, top: d.top, color: d.color, transform: `rotate(${d.rotate})` }"
      />
    </div>

    <header class="auth__logo">Smart Recipe</header>

    <main class="auth__main">
      <div class="auth__card"><slot /></div>
    </main>
  </div>
</template>

<style scoped>
.auth {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  overflow: hidden;
  background: linear-gradient(180deg, var(--cream-100) 0%, var(--cream-200) 100%);
}
.auth__decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.auth__deco {
  position: absolute;
  filter: blur(2.5px);
  opacity: 0.85;
}
.auth__logo {
  position: relative;
  padding: clamp(1.25rem, 4vw, 3rem) clamp(1.25rem, 4vw, 4rem) 0;
  font: var(--text-h1);
  color: var(--text-muted);
}
.auth__main {
  position: relative;
  flex: 1;
  display: grid;
  place-items: center;
  padding: 1.5rem 1rem 3rem;
}
.auth__card {
  width: min(100%, 28rem);
  padding: 1.5rem;
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-lg);
}

@media (max-width: 640px) {
  .auth__deco:nth-child(n + 5) {
    display: none;
  }
}
</style>
