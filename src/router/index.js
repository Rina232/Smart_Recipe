import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '@/stores/auth'
import { chatsStore } from '@/stores/chats'

const AppLayout = () => import('@/layouts/AppLayout.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', redirect: { name: 'new-chat' } },
        { path: 'chat/new', name: 'new-chat', component: () => import('@/views/NewChatView.vue') },
        { path: 'chat/:id', name: 'chat', component: () => import('@/views/ChatView.vue') },
        { path: 'admin', name: 'admin', component: () => import('@/views/AdminDashboardView.vue'), meta: { admin: true } },
        { path: 'admin/users/:id', name: 'admin-user', component: () => import('@/views/AdminUserView.vue'), meta: { admin: true } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: { name: 'new-chat' } },
  ],
})

router.beforeEach((to) => {
  if (!auth.isAuthenticated) return to.meta.public ? true : { name: 'login' }

  if (to.meta.public) return { name: 'new-chat' }

  if (to.meta.admin && !auth.isAdmin) return { name: 'new-chat' }

  if (auth.isGuest && to.name === 'new-chat') {
    const existing = chatsStore.state.chats[0]
    if (existing) return { name: 'chat', params: { id: existing.id } }
  }
  if (auth.isGuest && to.name === 'chat' && !chatsStore.get(to.params.id)) {
    return { name: 'new-chat' }
  }
  return true
})

export default router
