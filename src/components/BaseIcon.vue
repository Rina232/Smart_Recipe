<script setup>
import { computed } from 'vue'

/*
 * Иконки из public/icons красятся через CSS-маску: цвет берётся из `color` родителя.
 * name: 'bin' → icons/ui/bin.svg, 'deco/fish' → icons/deco/fish.svg
 */
const props = defineProps({
  name: { type: String, required: true },
  size: { type: String, default: '1.5rem' },
})

const base = import.meta.env.BASE_URL

const style = computed(() => {
  const path = props.name.includes('/') ? props.name : `ui/${props.name}`
  const url = `url("${base}icons/${path}.svg")`
  return { width: props.size, height: props.size, maskImage: url, webkitMaskImage: url }
})
</script>

<template>
  <span class="icon" :style="style" aria-hidden="true" />
</template>

<style scoped>
.icon {
  display: inline-block;
  flex: none;
  background-color: currentColor;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}
</style>
