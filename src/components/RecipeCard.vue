<script setup>
import { computed, ref } from 'vue'
import BaseIcon from './BaseIcon.vue'

const props = defineProps({ recipe: { type: Object, required: true } })

const failed = ref(false)
const src = computed(() => (props.recipe.image ? `${import.meta.env.BASE_URL}${props.recipe.image}` : ''))

const nutrition = computed(() => [
  `${props.recipe.calories} ккал`,
  `${props.recipe.protein}г белка`,
  `${props.recipe.fat}г жиров`,
  `${props.recipe.carbs}г углеводов`,
])
</script>

<template>
  <article class="recipe">
    <img v-if="src && !failed" class="recipe__image" :src="src" :alt="recipe.title" @error="failed = true" />
    <div v-else class="recipe__image recipe__image--empty" role="img" :aria-label="`Фото блюда «${recipe.title}» пока нет`">
      <BaseIcon name="deco/bowl-noodles" size="2.5rem" />
    </div>

    <div class="recipe__body">
      <h2 class="recipe__title">{{ recipe.title }}</h2>

      <ul class="recipe__nutrition">
        <li v-for="item in nutrition" :key="item">{{ item }}</li>
      </ul>

      <p class="recipe__time">
        <span class="recipe__time-label">Время приготовления:</span>
        <span>{{ recipe.time }}</span>
      </p>

      <div class="recipe__ingredients">
        <h3 class="recipe__ingredients-title">Ингредиенты:</h3>
        <ul class="recipe__list">
          <li v-for="item in recipe.ingredients" :key="item.name">{{ item.name }} — {{ item.amount }}</li>
        </ul>
      </div>
    </div>
  </article>
</template>

<style scoped>
.recipe {
  width: min(100%, 28rem);
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.recipe__image {
  display: block;
  width: 100%;
  aspect-ratio: 3.4 / 1;
  object-fit: cover;
  border-bottom: 1px solid var(--border-main);
}
.recipe__image--empty {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--surface-highlight), var(--surface-0));
  color: var(--text-muted);
}
.recipe__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: clamp(1rem, 3vw, 1.5rem);
}
.recipe__title {
  font: var(--text-h2);
  color: var(--text-main);
}
.recipe__nutrition {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.5rem;
  font: var(--text-body-regular);
}
.recipe__nutrition li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.recipe__nutrition li + li::before {
  content: '';
  width: 0.25rem;
  height: 0.25rem;
  border-radius: 50%;
  background: currentColor;
}
.recipe__time {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  font: var(--text-body-regular);
}
.recipe__time-label {
  font: var(--text-body-strong);
}
.recipe__ingredients {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.recipe__ingredients-title {
  font: var(--text-body-strong);
}
.recipe__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-left: 1rem;
  font: var(--text-body-regular);
}
.recipe__list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.recipe__list li::before {
  content: '';
  flex: none;
  width: 0.25rem;
  height: 0.25rem;
  border-radius: 50%;
  background: currentColor;
}
</style>
