<script setup>
import { computed, ref, watch } from 'vue'
import {
  adminUsers,
  kpiByPeriod,
  messagePeriodOptions,
  periodOptions,
  usersKpi,
} from '@/data/admin'
import { formatDelta, formatInt, formatLastActive, formatShortDate, formatRelative } from '@/utils/format'
import KpiCard from '@/components/KpiCard.vue'
import KpiPeriodCard from '@/components/KpiPeriodCard.vue'
import TextField from '@/components/TextField.vue'
import TableFooter from '@/components/TableFooter.vue'
import BaseIcon from '@/components/BaseIcon.vue'

const PAGE_SIZE = 5

const kpiPeriod = ref('7d')
const msgPeriod = ref('7d')
const query = ref('')
const sortKey = ref(null)
const sortDir = ref('asc')
const page = ref(1)

const metrics = computed(() => {
  const k = kpiByPeriod[kpiPeriod.value]
  return [
    { title: 'Активные пользователи', value: formatInt(k.active[0]), delta: formatDelta(k.active[1]) },
    { title: 'Новых чатов', value: formatInt(k.chats[0]), delta: formatDelta(k.chats[1]) },
    { title: 'Сообщений', value: formatInt(k.messages[0]), delta: formatDelta(k.messages[1]) },
  ]
})

const columns = [
  { key: 'name', label: 'Имя', align: 'center' },
  { key: 'totalChats', label: 'Всего чатов', align: 'right' },
  { key: 'activeChats', label: 'Активные чаты', align: 'right' },
  { key: 'totalMessages', label: 'Всего сообщений', align: 'right' },
  { key: 'periodMessages', label: 'Сообщений за период', align: 'right' },
  { key: 'lastActive', label: 'Последняя активность', align: 'right' },
]

const valueOf = (u, key) => (key === 'periodMessages' ? u.messagesByPeriod[msgPeriod.value] : u[key])

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? adminUsers.filter((u) => u.name.toLowerCase().includes(q)) : adminUsers
})

const sorted = computed(() => {
  if (!sortKey.value) return filtered.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  const key = sortKey.value
  return [...filtered.value].sort((a, b) => {
    const av = valueOf(a, key)
    const bv = valueOf(b, key)
    const cmp = typeof av === 'string' ? av.localeCompare(bv, 'ru') : av - bv
    return cmp * dir
  })
})

const pageRows = computed(() => sorted.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

watch(query, () => (page.value = 1))

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  page.value = 1
}

const sortIcon = (key) =>
  sortKey.value !== key ? 'up-down-triagnle' : sortDir.value === 'asc' ? 'up-triangle' : 'down-triangle'

const ariaSort = (key) => (sortKey.value !== key ? 'none' : sortDir.value === 'asc' ? 'ascending' : 'descending')

// относительная дата + абсолютная в подсказке
const activityTitle = (ts) => (formatRelative(ts) ? formatShortDate(ts) : undefined)
</script>

<template>
  <div class="dash">
    <div class="dash__kpis">
      <KpiCard
        title="Всего пользователей"
        :value="formatInt(usersKpi.total)"
        :delta="formatDelta(usersKpi.delta)"
        :caption="usersKpi.caption"
      />
      <KpiPeriodCard v-model:period="kpiPeriod" :metrics="metrics" :options="periodOptions" />
    </div>

    <div class="dash__filters">
      <div class="dash__search">
        <TextField v-model="query" icon="search" placeholder="Найти пользователя" aria-label="Найти пользователя" />
      </div>
      <label class="dash__select">
        <span class="dash__select-label">Сообщения за:</span>
        <span class="select">
          <select v-model="msgPeriod" class="select__control">
            <option v-for="o in messagePeriodOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
          <BaseIcon name="down-triangle" size="1rem" class="select__icon" />
        </span>
      </label>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th v-for="c in columns" :key="c.key" scope="col" :class="`is-${c.align}`" :aria-sort="ariaSort(c.key)">
              <button type="button" class="th-btn" @click="sortBy(c.key)">
                <span>{{ c.label }}</span>
                <BaseIcon :name="sortIcon(c.key)" size="1rem" class="th-btn__icon" />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in pageRows" :key="u.id">
            <td class="is-center">
              <RouterLink :to="{ name: 'admin-user', params: { id: u.id } }" class="user-link">{{ u.name }}</RouterLink>
            </td>
            <td class="is-right">{{ u.totalChats }}</td>
            <td class="is-right">{{ u.activeChats }}</td>
            <td class="is-right">{{ u.totalMessages }}</td>
            <td class="is-right">{{ u.messagesByPeriod[msgPeriod] }}</td>
            <td class="is-right">
              <time :datetime="new Date(u.lastActive).toISOString()" :title="activityTitle(u.lastActive)">
                {{ formatLastActive(u.lastActive) }}
              </time>
            </td>
          </tr>
          <tr v-if="!pageRows.length">
            <td :colspan="columns.length" class="table__empty">Пользователи не найдены</td>
          </tr>
        </tbody>
      </table>
    </div>

    <TableFooter v-model:page="page" :page-size="PAGE_SIZE" :total="sorted.length" />
  </div>
</template>

<style scoped>
.dash {
  container-type: inline-size;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: clamp(1rem, 2vw, 1.5rem);
}

.dash__kpis {
  display: grid;
  grid-template-columns: minmax(0, 22rem) minmax(0, 45.5rem);
  gap: 1rem;
}
@container (max-width: 62rem) {
  .dash__kpis {
    grid-template-columns: minmax(0, 1fr);
  }
}

.dash__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.dash__search {
  flex: 1 1 18rem;
  min-width: 0;
}
.dash__select {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.dash__select-label {
  font: var(--text-label-regular);
}
.select {
  position: relative;
  display: inline-flex;
}
.select__control {
  appearance: none;
  -webkit-appearance: none;
  min-width: 7rem;
  padding: 0.5rem 2.25rem 0.5rem 0.75rem;
  background: var(--surface-1);
  border: 1px solid var(--text-main);
  border-radius: var(--radius-md);
  font: var(--text-body-regular);
  cursor: pointer;
}
.select__control:focus {
  border-color: var(--primary);
  outline: none;
}
.select__icon {
  position: absolute;
  right: 0.625rem;
  top: 50%;
  translate: 0 -50%;
  pointer-events: none;
}

.table-wrap {
  overflow-x: auto;
}
.table {
  width: 100%;
  min-width: 46rem;
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
.is-center {
  text-align: center;
}
.is-right {
  text-align: right;
}
.th-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font: inherit;
}
.th-btn__icon {
  color: var(--primary);
}
.user-link {
  font: var(--text-label-strong);
  text-decoration: none;
}
.user-link:hover {
  color: var(--primary);
  text-decoration: underline;
}
.table__empty {
  text-align: center;
  color: var(--text-muted);
}
</style>
