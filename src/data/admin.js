// Моковые данные админ-панели (247 пользователей, как в макете).
import { TIME } from '@/utils/format'

const { HOUR, DAY } = TIME
const NOW = Date.now()

function mulberry32(seed) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rnd = mulberry32(247)
const randInt = (min, max) => Math.floor(rnd() * (max - min + 1)) + min

/** Сообщения за период; значение за 7 дней задаёт основной ориентир. */
function periodMessages(m7, total) {
  return {
    '1d': Math.min(total, Math.round(m7 * 0.25)),
    '3d': Math.min(total, Math.round(m7 * 0.55)),
    '7d': Math.min(total, m7),
    '1m': Math.min(total, Math.round(m7 * 3.2)),
  }
}

// Первые пять строк повторяют макет.
const fixedUsers = [
  { id: 'u1', name: 'user_1', role: 'user', totalChats: 31, activeChats: 4, totalMessages: 123, m7: 16, lastActive: NOW - 2 * HOUR, joinedAt: NOW - 210 * DAY },
  { id: 'u2', name: 'Aertna', role: 'user', totalChats: 8, activeChats: 1, totalMessages: 97, m7: 9, lastActive: NOW - 45 * DAY, joinedAt: NOW - 300 * DAY },
  { id: 'u3', name: 'CoolBoi', role: 'user', totalChats: 47, activeChats: 9, totalMessages: 58, m7: 2, lastActive: NOW - 23 * DAY, joinedAt: NOW - 120 * DAY },
  { id: 'u4', name: 'Дария', role: 'user', totalChats: 2, activeChats: 2, totalMessages: 19, m7: 4, lastActive: NOW - 562 * DAY, joinedAt: NOW - 600 * DAY },
  { id: 'u5', name: 'かめりあ', role: 'admin', totalChats: 20, activeChats: 13, totalMessages: 173, m7: 34, lastActive: NOW - 3 * DAY, joinedAt: NOW - 41 * DAY },
]

const namePool = [
  'Anna', 'Max', 'Olga', 'Ivan', 'Katya', 'Dima', 'Sveta', 'Nikita', 'Lena', 'Pasha',
  'Masha', 'Artem', 'Vika', 'Egor', 'Alina', 'Sasha', 'Roman', 'Julia', 'Timur', 'Nastya',
  'ChefMax', 'TastyBoy', 'Vkusno', 'KuhnyaPro', 'Борщеед', 'Кулинар', 'Пельмень', 'Сырник',
]

function generateUser(index) {
  const base = namePool[randInt(0, namePool.length - 1)]
  const name = rnd() > 0.4 ? `${base}_${randInt(1, 99)}` : `${base}${randInt(100, 999)}`
  const totalChats = randInt(1, 40)
  const activeChats = Math.min(totalChats, randInt(0, 12))
  const totalMessages = totalChats * randInt(2, 6)
  const m7 = Math.min(totalMessages, randInt(0, 30))
  const idleDays = rnd() < 0.7 ? rnd() * 60 : rnd() * 420
  return {
    id: `u${index}`,
    name,
    role: 'user',
    totalChats,
    activeChats,
    totalMessages,
    m7,
    lastActive: NOW - Math.round(idleDays * DAY),
    joinedAt: NOW - Math.round((idleDays + randInt(5, 200)) * DAY),
  }
}

export const adminUsers = [...fixedUsers]
for (let i = fixedUsers.length + 1; i <= 247; i++) adminUsers.push(generateUser(i))
for (const u of adminUsers) u.messagesByPeriod = periodMessages(u.m7, u.totalMessages)

export const getAdminUser = (id) => adminUsers.find((u) => u.id === id)

/* ---------- KPI ---------- */

export const usersKpi = { total: adminUsers.length, delta: 3.2, caption: 'Рост за 7 дней' }

export const kpiByPeriod = {
  '1d': { active: [21, 1.4], chats: [48, -2.0], messages: [212, 0.8] },
  '3d': { active: [38, -0.9], chats: [121, 3.3], messages: [604, 1.2] },
  '7d': { active: [64, -4.7], chats: [312, 5.1], messages: [1315, 0.0] },
  '1m': { active: [142, 6.8], chats: [1204, 9.4], messages: [5890, -1.1] },
}

export const periodOptions = [
  { value: '1d', label: '1д' },
  { value: '3d', label: '3д' },
  { value: '7d', label: '7д' },
  { value: '1m', label: '1м' },
]

export const messagePeriodOptions = [
  { value: '1d', label: '1 день' },
  { value: '3d', label: '3 дня' },
  { value: '7d', label: '7 дней' },
  { value: '1m', label: '1 месяц' },
]

/* ---------- Чаты и активность пользователя ---------- */

const chatTitles = [
  'Идея для ужина', 'Высокопротеиновая диета', 'Блюда из тофу', 'Японская еда',
  'Завтраки без глютена', 'Что приготовить из курицы', 'Быстрые обеды в офис',
  'Десерты без сахара', 'Постное меню на неделю', 'Рецепты на мангале',
  'Супы на осень', 'Паста с морепродуктами', 'Закуски на праздник',
  'Меню для спортсмена', 'Диета на 1800 ккал', 'Блюда в мультиварке',
  'Веганский ужин', 'Домашняя выпечка', 'Салаты с авокадо', 'Корейская кухня',
]

const chatsCache = new Map()

export function getUserChats(user) {
  if (chatsCache.has(user.id)) return chatsCache.get(user.id)

  const rand = mulberry32(user.id.split('').reduce((s, ch) => s + ch.charCodeAt(0), 0) * 31)
  const n = user.totalChats
  const baseAgo = (NOW - user.lastActive) / DAY

  // Статусы: у первой пользовательницы-админа первые три чата заданы макетом.
  const preset = user.id === 'u5' ? [false, true, true, true] : []
  const presetMsgs = user.id === 'u5' ? [19, 78, 7, 12] : []
  const presetActive = preset.filter(Boolean).length
  const restActive = Math.max(0, user.activeChats - presetActive)
  const restCount = n - preset.length
  const restMsgs = Math.max(restCount, user.totalMessages - presetMsgs.reduce((a, b) => a + b, 0))

  const chats = []
  let activeLeft = restActive
  let msgsLeft = restMsgs
  for (let i = 0; i < n; i++) {
    const isPreset = i < preset.length
    let active
    let messages
    if (isPreset) {
      active = preset[i]
      messages = presetMsgs[i]
    } else {
      const slotsLeft = n - i
      active = activeLeft > 0 && (activeLeft >= slotsLeft || rand() < activeLeft / slotsLeft)
      if (active) activeLeft -= 1
      messages = slotsLeft === 1 ? Math.max(1, msgsLeft) : Math.max(1, Math.round((msgsLeft / slotsLeft) * (0.6 + rand() * 0.8)))
      msgsLeft = Math.max(0, msgsLeft - messages)
    }
    const lastAgo = baseAgo + i * (1 + Math.floor(rand() * 6))
    const createdAgo = lastAgo + Math.floor(rand() * 30) + (i === 0 ? 1 : 0)
    const lastTs = NOW - lastAgo * DAY
    chats.push({
      id: `${user.id}-c${i + 1}`,
      title: i < chatTitles.length ? chatTitles[i] : `${chatTitles[i % chatTitles.length]} ${Math.floor(i / chatTitles.length) + 1}`,
      createdAt: NOW - createdAgo * DAY,
      lastActive: Math.min(lastTs, NOW - 5 * 60 * 1000),
      messages,
      active,
    })
  }
  chatsCache.set(user.id, chats)
  return chats
}

export function getUserActivity(user) {
  const chats = getUserChats(user)
  const deleted = chats.find((c) => !c.active) ?? chats[chats.length - 1]
  const created = chats[Math.min(3, chats.length - 1)]
  return [
    `Создал чат «${created.title}»`,
    `Отправил сообщение в «${chats[0].title}»`,
    `Удалил чат «${deleted.title}»`,
    'Выполнил вход',
  ]
}
