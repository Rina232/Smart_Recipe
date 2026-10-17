export function validateDisplayName(value) {
  const v = value.trim()
  if (v.length < 3 || v.length > 30) return 'Имя должно содержать от 3 до 30 символов'
  if (!/^[\p{L}\s'’-]+$/u.test(v)) return 'Имя должно содержать только буквы, пробел, дефис или апостроф'
  return ''
}

export function validateLogin(value) {
  const v = value.trim()
  if (v.length < 3 || v.length > 30) return 'Логин должен содержать от 3 до 30 символов'
  if (!/^[A-Za-z0-9_-]+$/.test(v)) return 'Логин должен содержать только латинские буквы, цифры, дефис или подчёркивание'
  return ''
}

const COMMON_PASSWORDS = [
  '12345678', '123456789', '1234567890', 'qwertyui', 'qwerty123', 'password', 'password1',
  'йцукенгш', '11111111', '00000000', 'abcdefgh', 'admin123', 'iloveyou',
]

function isTrivial(p) {
  if (COMMON_PASSWORDS.includes(p.toLowerCase())) return true
  if (p.length >= 4 && new Set(p).size === 1) return true // aaaaaa
  return false
}

export function passwordStrength(p) {
  if (!p) return 'inactive'
  if (isTrivial(p)) return 'very-weak'
  let score = 0
  if (p.length >= 8) score += 1
  if (p.length >= 12) score += 1
  if (/[a-zа-яё]/.test(p) && /[A-ZА-ЯЁ]/.test(p)) score += 1
  if (/\d/.test(p)) score += 1
  if (/[^\p{L}\d]/u.test(p)) score += 1
  if (score <= 1) return 'weak'
  if (score <= 3) return 'medium'
  return 'strong'
}

export function validatePassword(value) {
  if (!value) return 'Введите пароль'
  if (value.length < 8) return 'Пароль должен содержать не менее 8 символов'
  if (passwordStrength(value) === 'very-weak') return 'Этот пароль слишком простой'
  return ''
}
