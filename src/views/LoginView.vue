<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '@/stores/auth'
import AuthShell from '@/components/AuthShell.vue'
import TextField from '@/components/TextField.vue'
import BaseButton from '@/components/BaseButton.vue'

const router = useRouter()

const login = ref('')
const password = ref('')
const loginError = ref('')
const passwordError = ref('')

function submit() {
  loginError.value = login.value.trim() ? '' : 'Введите логин'
  passwordError.value = password.value ? '' : 'Введите пароль'
  if (loginError.value || passwordError.value) return

  const res = auth.login(login.value.trim(), password.value)
  if (!res.ok) {
    passwordError.value = res.error
    return
  }
  router.replace({ name: 'new-chat' })
}

function enterAsGuest() {
  auth.loginAsGuest()
  router.replace({ name: 'new-chat' })
}
</script>

<template>
  <AuthShell>
    <h1 class="title">Добро пожаловать!</h1>

    <form class="form" novalidate @submit.prevent="submit">
      <div class="form__fields">
        <TextField
          v-model="login"
          label="Логин"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          :error="loginError"
          @update:model-value="loginError = ''"
        />
        <TextField
          v-model="password"
          label="Пароль"
          password
          autocomplete="current-password"
          :error="passwordError"
          @update:model-value="passwordError = ''"
        />
      </div>

      <div class="form__actions">
        <BaseButton type="submit" block>Войти</BaseButton>
        <BaseButton variant="secondary" block @click="enterAsGuest">Войти как гость</BaseButton>
      </div>
    </form>

    <p class="hint">
      Ещё нет аккаунта?
      <RouterLink :to="{ name: 'register' }" class="hint__link">Зарегистрироваться</RouterLink>
    </p>
  </AuthShell>
</template>

<style scoped>
.title {
  font: var(--text-h1);
  color: var(--text-main);
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1.5rem;
}
.form__fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.form__actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.hint {
  margin-top: 1.5rem;
  font: var(--text-caption);
  color: var(--text-muted);
}
.hint__link {
  color: var(--primary);
  text-decoration: none;
}
.hint__link:hover {
  text-decoration: underline;
}
</style>
