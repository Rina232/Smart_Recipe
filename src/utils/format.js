const MIN = 60 * 1000
const HOUR = 60 * MIN
const DAY = 24 * HOUR

const MONTHS_GEN = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]
const MONTHS_SHORT = [
  'Янв.', 'Февр.', 'Март', 'Апр.', 'Мая', 'Июн.',
  'Июл.', 'Авг.', 'Сент.', 'Окт.', 'Нояб.', 'Дек.',
]

/** Склонение: plural(5, ['день', 'дня', 'дней']) */
export function plural(n, [one, few, many]) {
  const m10 = n % 10
  const m100 = n % 100
  if (m10 === 1 && m100 !== 11) return one
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few
  return many
}

/** «2 часа назад», «1 месяц назад». Возвращает null, если прошло больше года. */
export function formatRelative(ts, now = Date.now()) {
  const diff = Math.max(0, now - ts)
  const min = Math.floor(diff / MIN)
  if (min < 1) return 'только что'
  if (min < 60) return `${min} ${plural(min, ['минуту', 'минуты', 'минут'])} назад`
  const h = Math.floor(diff / HOUR)
  if (h < 24) return `${h} ${plural(h, ['час', 'часа', 'часов'])} назад`
  const d = Math.floor(diff / DAY)
  if (d < 30) return `${d} ${plural(d, ['день', 'дня', 'дней'])} назад`
  const mo = Math.floor(d / 30)
  if (mo < 12) return `${mo} ${plural(mo, ['месяц', 'месяца', 'месяцев'])} назад`
  return null
}

/** «4 Апр. 2025» */
export function formatShortDate(ts) {
  const d = new Date(ts)
  return `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]} ${d.getFullYear()}`
}

/** «7 сентября 2026» */
export function formatLongDate(ts) {
  const d = new Date(ts)
  return `${d.getDate()} ${MONTHS_GEN[d.getMonth()]} ${d.getFullYear()}`
}

/** Последняя активность: относительная дата, а для старых записей — абсолютная. */
export function formatLastActive(ts, now = Date.now()) {
  return formatRelative(ts, now) ?? formatShortDate(ts)
}

/** Дата создания: «Сегодня», «13 дней назад», «3 месяца назад». */
export function formatDay(ts, now = Date.now()) {
  if (now - ts < DAY) return 'Сегодня'
  return formatRelative(ts, now) ?? formatShortDate(ts)
}

/** Целые числа в формате макета: 1,315 */
const intFormatter = new Intl.NumberFormat('en-US')
export function formatInt(n) {
  return intFormatter.format(n)
}

/** Изменение показателя: { dir: 'up' | 'down' | 'flat', text: '4,7%' } */
export function formatDelta(value) {
  const dir = value > 0 ? 'up' : value < 0 ? 'down' : 'flat'
  return { dir, text: `${Math.abs(value).toFixed(1).replace('.', ',')}%` }
}

export const TIME = { MIN, HOUR, DAY }
