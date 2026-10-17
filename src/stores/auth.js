import { reactive } from 'vue'
import { chatsStore } from './chats'

/*
 * ВНИМАНИЕ: это заглушка вместо бэкенда. Пользователи и пароли лежат в localStorage
 * в открытом виде — только для разработки интерфейса.
 *
 * Встроенные аккаунты:
 *   admin / admin123   — администратор
 *   user  / user12345  — обычный пользователь
 */
const USERS_KEY = 'sr_users'
const SESSION_KEY = 'sr_session'

const BUILTIN_USERS = [
  { login: 'admin', password: 'admin123', name: 'Администратор', role: 'admin' },
  { login: 'user', password: 'user12345', name: 'Пользователь', role: 'user' },
]

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignore */
  }
}

const state = reactive({
  session: readJSON(SESSION_KEY, null), // { role: 'guest' } | { login, name, role }
})

const ownerOf = (session) => (session.role === 'guest' ? 'guest' : `user:${session.login.toLowerCase()}`)
const registeredUsers = () => readJSON(USERS_KEY, [])
const allUsers = () => [...BUILTIN_USERS, ...registeredUsers()]

function startSession(session) {
  state.session = session
  writeJSON(SESSION_KEY, session)
  chatsStore.setOwner(ownerOf(session))
}

export const auth = {
  state,
  get isAuthenticated() {
    return !!state.session
  },
  get isGuest() {
    return state.session?.role === 'guest'
  },
  get isAdmin() {
    return state.session?.role === 'admin'
  },

  login(login, password) {
    const user = allUsers().find((u) => u.login.toLowerCase() === login.toLowerCase())
    if (!user || user.password !== password) {
      return { ok: false, error: 'Неверный логин или пароль' }
    }
    startSession({ login: user.login, name: user.name, role: user.role })
    return { ok: true }
  },

  loginAsGuest() {
    startSession({ role: 'guest', name: 'Гость' })
  },

  isLoginTaken(login) {
    return allUsers().some((u) => u.login.toLowerCase() === login.toLowerCase())
  },

  register({ name, login, password }) {
    if (auth.isLoginTaken(login)) return { ok: false, error: 'Этот логин уже занят' }
    const user = { login, password, name, role: 'user' }
    writeJSON(USERS_KEY, [...registeredUsers(), user])
    startSession({ login, name, role: 'user' })
    return { ok: true }
  },

  logout() {
    // Гостевой чат живёт только в рамках гостевой сессии.
    if (state.session?.role === 'guest') chatsStore.removeOwnerData('guest')
    state.session = null
    try {
      localStorage.removeItem(SESSION_KEY)
    } catch {
      /* ignore */
    }
    chatsStore.setOwner(null)
  },
}

// Восстанавливаем чаты при перезагрузке страницы.
if (state.session) chatsStore.setOwner(ownerOf(state.session))
