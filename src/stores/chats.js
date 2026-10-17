import { reactive } from 'vue'
import { buildReply, demoChats, uid } from '@/data/recipes'

const SEEDED_OWNERS = new Set(['user:admin', 'user:user'])
const storageKey = (owner) => `sr_chats:${owner}`

const state = reactive({
  owner: null,
  chats: [],
  pending: {},
})

function read(owner) {
  try {
    const raw = localStorage.getItem(storageKey(owner))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function persist() {
  if (!state.owner) return
  try {
    localStorage.setItem(storageKey(state.owner), JSON.stringify(state.chats))
  } catch {
  }
}

function makeTitle(text) {
  const clean = text.replace(/\s+/g, ' ').trim()
  const cut = clean.length > 40 ? `${clean.slice(0, 40).trimEnd()}…` : clean
  return cut.charAt(0).toUpperCase() + cut.slice(1)
}

function get(id) {
  return state.chats.find((c) => c.id === id)
}

function setOwner(owner) {
  state.owner = owner
  state.pending = {}
  if (!owner) {
    state.chats = []
    return
  }
  let data = read(owner)
  if (data === null && SEEDED_OWNERS.has(owner)) data = demoChats()
  state.chats = data ?? []
  persist()
}

function removeOwnerData(owner) {
  try {
    localStorage.removeItem(storageKey(owner))
  } catch {
  }
}

function send(chatId, rawText) {
  const text = rawText.trim()
  if (!text) return null

  let id = chatId
  if (!id || !get(id)) {
    id = uid('c')
    state.chats.unshift({ id, title: makeTitle(text), createdAt: Date.now(), messages: [] })
  }
  const chat = get(id)
  chat.messages.push({ id: uid('m'), role: 'user', text, createdAt: Date.now() })
  persist()

  state.pending[id] = true
  const delay = 900 + Math.random() * 700
  setTimeout(() => {
    delete state.pending[id]
    const target = get(id)
    if (!target) return
    target.messages.push({ id: uid('m'), role: 'assistant', createdAt: Date.now(), ...buildReply(text) })
    persist()
  }, delay)

  return id
}

function remove(id) {
  const i = state.chats.findIndex((c) => c.id === id)
  if (i === -1) return
  state.chats.splice(i, 1)
  delete state.pending[id]
  persist()
}

export const chatsStore = { state, get, setOwner, removeOwnerData, send, remove }
