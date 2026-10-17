<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '@/stores/auth'
import { validateDisplayName, validateLogin, validatePassword } from '@/utils/validation'
import AuthShell from '@/components/AuthShell.vue'
import TextField from '@/components/TextField.vue'
import BaseButton from '@/components/BaseButton.vue'
import PasswordStrength from '@/components/PasswordStrength.vue'

const router = useRouter()

const form = reactive({ name: '', login: '', password: '' })
const touched = reactive({ name: false, login: false, password: false })
const submitted = ref(false)
const serverLoginError = ref('')

const errors = computed(() => ({
  name: validateDisplayName(form.name),
  login: validateLogin(form.login) || serverLoginError.value,
  password: validatePassword(form.password),
}))

// ошибка показывается после ухода из поля или попытки отправки
const visible = (key) => (touched[key] || submitted.value ? errors.value[key] : '')

function submit() {
  submitted.value = true
  if (errors.value.name || errors.value.login || errors.value.password) return

  const res = auth.register({ name: form.name.trim(), login: form.login.trim(), password: form.password })
  if (!res.ok) {
    serverLoginError.value = res.error
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
    <h1 class="title">Создание аккаунта</h1>

    <form class="form" novalidate @submit.prevent="submit">
      <div class="form__fields">
        <TextField
          v-model="form.name"
          label="Отображаемое имя"
          autocomplete="nickname"
          :error="visible('name')"
          @blur="touched.name = true"
        />
        <TextField
          v-model="form.login"
          label="Логин"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          :error="visible('login')"
          @update:model-value="serverLoginError = ''"
          @blur="touched.login = true"
        />
        <TextField
          v-model="form.password"
          label="Пароль"
          password
          autocomplete="new-password"
          :error="visible('password')"
          @blur="touched.password = true"
        >
          <template #footer>
            <PasswordStrength :password="form.password" />
          </template>
        </TextField>
      </div>

      <div class="form__actions">
        <BaseButton type="submit" block>Зарегистрироваться</BaseButton>
        <BaseButton variant="secondary" block @click="enterAsGuest">Войти как гость</BaseButton>
      </div>
    </form>

    <p class="hint">
      Уже есть аккаунт?
      <RouterLink :to="{ name: 'login' }" class="hint__link">Войти</RouterLink>
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
