<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAdminUser, getUserActivity, getUserChats } from '@/data/admin'
import { formatDay, formatLastActive, formatLongDate, formatRelative, formatShortDate } from '@/utils/format'
import BaseIcon from '@/components/BaseIcon.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TableFooter from '@/components/TableFooter.vue'

const PAGE_SIZE = 3

const route = useRoute()
const router = useRouter()

const user = computed(() => getAdminUser(route.params.id))
const page = ref(1)

watch(
  user,
  (u) => {
    if (!u) router.replace({ name: 'admin' })
  },
  { immediate: true },
)
watch(() => route.params.id, () => (page.value = 1))

const chats = computed(() => (user.value ? getUserChats(user.value) : []))
const activity = computed(() => (user.value ? getUserActivity(user.value) : []))
const pageRows = computed(() => chats.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

const stats = computed(() => [
  { label: 'Всего чатов', value: user.value.totalChats },
  { label: 'Активные чаты', value: user.value.activeChats },
  { label: 'Всего сообщений', value: user.value.totalMessages },
  { label: 'Сообщения — 7 дней', value: user.value.messagesByPeriod['7d'] },
])

const titleFor = (ts) => (formatRelative(ts) ? formatShortDate(ts) : undefined)
</script>

<template>
  <div v-if="user" class="profile">
    <button type="button" class="back" @click="router.push({ name: 'admin' })">
      <BaseIcon name="right-arrow" size="1.25rem" class="back__icon" />
      Назад
    </button>

    <header class="head">
      <div class="head__title">
        <h1 class="head__name">{{ user.name }}</h1>
        <span v-if="user.role === 'admin'" class="role">Администратор</span>
      </div>
      <p class="head__meta">
        <span>Присоединился {{ formatLongDate(user.joinedAt) }}</span>
        <span class="head__dot" aria-hidden="true">•</span>
        <span>Последний раз в сети {{ formatLastActive(user.lastActive) }}</span>
      </p>
    </header>

    <dl class="stats">
      <div v-for="s in stats" :key="s.label" class="stats__cell">
        <dt>{{ s.label }}</dt>
        <dd>{{ s.value }}</dd>
      </div>
    </dl>

    <div class="cols">
      <section class="cols__chats" aria-labelledby="chats-title">
        <h2 id="chats-title" class="section-title section-title--short">Чаты</h2>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th scope="col" class="is-center">Название</th>
                <th scope="col" class="is-right">Дата создания</th>
                <th scope="col" class="is-right">Последняя активность</th>
                <th scope="col" class="is-right">Сообщения</th>
                <th scope="col" class="is-right">Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in pageRows" :key="c.id">
                <td class="is-center is-name">{{ c.title }}</td>
                <td class="is-right" :title="titleFor(c.createdAt)">{{ formatDay(c.createdAt) }}</td>
                <td class="is-right" :title="titleFor(c.lastActive)">{{ formatLastActive(c.lastActive) }}</td>
                <td class="is-right">{{ c.messages }}</td>
                <td class="is-right"><StatusBadge :active="c.active" /></td>
              </tr>
              <tr v-if="!pageRows.length">
                <td colspan="5" class="table__empty">Чатов пока нет</td>
              </tr>
            </tbody>
          </table>
        </div>

        <TableFooter v-model:page="page" :page-size="PAGE_SIZE" :total="chats.length" />
      </section>

      <aside class="cols__activity" aria-labelledby="activity-title">
        <h2 id="activity-title" class="section-title">Последняя активность</h2>
        <ul class="activity">
          <li v-for="(a, i) in activity" :key="i">{{ a }}</li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: clamp(1rem, 2vw, 1.5rem);
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  align-self: flex-start;
  margin-bottom: -0.5rem;
  font: var(--text-label-strong);
  border-radius: var(--radius-sm);
}
.back:hover {
  color: var(--primary);
}
.back__icon {
  transform: scaleX(-1);
}

.head {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.head__title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
.head__name {
  font: var(--text-h1);
  overflow-wrap: anywhere;
}
.role {
  padding: 0.125rem 0.5rem;
  background: var(--primary);
  color: var(--text-inverse);
  border-radius: var(--radius-sm);
  font: var(--text-caption);
}
.head__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.75rem;
  font: 600 0.875rem/1.4 var(--font-paragraph);
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0;
  background: var(--surface-1);
  border: 1px solid var(--border-main);
  border-radius: var(--radius-md);
}
.stats__cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.125rem;
  padding: 0.75rem 1rem;
  text-align: right;
}
.stats__cell + .stats__cell {
  border-left: 1px dotted var(--text-muted);
}
.stats dt {
  font: var(--text-body-regular);
}
.stats dd {
  margin: 0;
  font: var(--text-body-strong);
}

.cols {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(14rem, 18.5rem);
  gap: 1.5rem;
}
.cols__chats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
}
.cols__activity {
  padding-left: 1.5rem;
  border-left: 1px dotted var(--text-muted);
}
.section-title {
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--line-strong);
  font: var(--text-h2);
}
.section-title--short {
  align-self: flex-start;
  padding-right: 1.25rem;
}
.activity {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
  font: var(--text-body-regular);
}

.table-wrap {
  overflow-x: auto;
}
.table {
  width: 100%;
  min-width: 36rem;
  border-collapse: collapse;
}
.table th {
  padding: 0.75rem;
  border-bottom: 1px solid var(--line-strong);
  font: var(--text-label-strong);
  white-space: nowrap;
}
.table td {
  padding: 1.5rem 0.75rem;
  border-bottom: 1px solid var(--line-soft);
  font: var(--text-body-regular);
}
.is-name {
  font: var(--text-label-strong);
}
.is-center {
  text-align: center;
}
.is-right {
  text-align: right;
}
.table__empty {
  text-align: center;
  color: var(--text-muted);
}

@media (max-width: 960px) {
  .cols {
    grid-template-columns: minmax(0, 1fr);
  }
  .cols__activity {
    padding-left: 0;
    border-left: 0;
    padding-top: 1.5rem;
    border-top: 1px dotted var(--text-muted);
  }
}
@media (max-width: 640px) {
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .stats__cell:nth-child(3) {
    border-left: 0;
  }
  .stats__cell:nth-child(n + 3) {
    border-top: 1px dotted var(--text-muted);
  }
}
</style>
