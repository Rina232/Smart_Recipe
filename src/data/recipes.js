// Моковые рецепты. Пока нет бэкенда, «ответы ИИ» подбираются по ключевым словам.

export const recipes = {
  chicken: {
    id: 'spicy-chicken-rice',
    title: 'Пряная курица с овощами и рисом',
    image: 'images/Rice.jpg',
    calories: 540,
    protein: 32,
    fat: 18,
    carbs: 58,
    time: '30 мин.',
    ingredients: [
      { name: 'Куриное филе', amount: '300г' },
      { name: 'Рис сухой', amount: '140г' },
      { name: 'Болгарский перец', amount: '150г' },
      { name: 'Морковь', amount: '100г' },
      { name: 'Репчатый лук', amount: '100г' },
      { name: 'Чеснок', amount: '8г' },
      { name: 'Соевый соус', amount: '30г' },
      { name: 'Растительное масло', amount: '10г' },
      { name: 'Паприка', amount: '4г' },
      { name: 'Соль', amount: '1–2г' },
      { name: 'Черный перец', amount: '1г' },
    ],
    text: 'Рис отварите до готовности. Курицу нарежьте полосками, обжарьте на сильном огне 5–6 минут, добавьте овощи, чеснок и специи, влейте соевый соус и тушите ещё 5 минут. Подавайте горячим поверх риса.',
  },
  bibimbap: {
    id: 'bibimbap',
    title: 'Пибимпап с говядиной и овощами',
    image: null,
    calories: 620,
    protein: 34,
    fat: 21,
    carbs: 70,
    time: '40 мин.',
    ingredients: [
      { name: 'Говяжья вырезка', amount: '200г' },
      { name: 'Рис круглозёрный', amount: '150г' },
      { name: 'Шпинат', amount: '80г' },
      { name: 'Морковь', amount: '80г' },
      { name: 'Цукини', amount: '100г' },
      { name: 'Ростки сои', amount: '60г' },
      { name: 'Яйцо', amount: '1 шт.' },
      { name: 'Соус кочудян', amount: '20г' },
      { name: 'Кунжутное масло', amount: '10г' },
    ],
    text: 'Овощи быстро обжарьте по отдельности с кунжутным маслом, говядину замаринуйте в соевом соусе и обжарьте. Выложите всё секторами на рис, сверху — яйцо и ложка кочудяна. Перед едой перемешайте.',
  },
  tofu: {
    id: 'tofu-stir-fry',
    title: 'Тофу с овощами в соевом соусе',
    image: null,
    calories: 380,
    protein: 24,
    fat: 18,
    carbs: 28,
    time: '25 мин.',
    ingredients: [
      { name: 'Тофу плотный', amount: '250г' },
      { name: 'Брокколи', amount: '150г' },
      { name: 'Болгарский перец', amount: '100г' },
      { name: 'Имбирь', amount: '5г' },
      { name: 'Соевый соус', amount: '25г' },
      { name: 'Кунжут', amount: '5г' },
    ],
    text: 'Тофу обсушите и обжарьте кубиками до золотистой корочки. Добавьте овощи и имбирь, жарьте 4 минуты, влейте соус. Посыпьте кунжутом.',
  },
  oatmeal: {
    id: 'berry-oatmeal',
    title: 'Овсянка с ягодами и греческим йогуртом',
    image: null,
    calories: 340,
    protein: 20,
    fat: 9,
    carbs: 46,
    time: '10 мин.',
    ingredients: [
      { name: 'Овсяные хлопья', amount: '50г' },
      { name: 'Греческий йогурт', amount: '120г' },
      { name: 'Ягоды замороженные', amount: '80г' },
      { name: 'Миндаль', amount: '10г' },
      { name: 'Мёд', amount: '5г' },
    ],
    text: 'Залейте хлопья горячей водой на 5 минут, добавьте йогурт и ягоды, посыпьте измельчённым миндалём и полейте мёдом. Хороший вариант первого приёма пищи при двухразовом питании.',
  },
  lentil: {
    id: 'lentil-soup',
    title: 'Чечевичный суп с морковью',
    image: null,
    calories: 410,
    protein: 22,
    fat: 8,
    carbs: 62,
    time: '35 мин.',
    ingredients: [
      { name: 'Красная чечевица', amount: '120г' },
      { name: 'Морковь', amount: '100г' },
      { name: 'Репчатый лук', amount: '80г' },
      { name: 'Картофель', amount: '150г' },
      { name: 'Оливковое масло', amount: '10г' },
      { name: 'Зира', amount: '2г' },
      { name: 'Соль', amount: '2г' },
    ],
    text: 'Обжарьте лук и морковь со специями, добавьте картофель, чечевицу и 700 мл воды. Варите 20 минут, затем слегка пробейте блендером.',
  },
}

const rules = [
  { re: /корей|кимчи|пибимпап|азиат/i, key: 'bibimbap' },
  { re: /тофу|вегет|веган|постн/i, key: 'tofu' },
  { re: /диет|завтрак|овсян|похуд|кбжу/i, key: 'oatmeal' },
  { re: /суп|чечевиц|борщ/i, key: 'lentil' },
  { re: /кур|рис|ужин|мясо/i, key: 'chicken' },
]

/** Мок «ответа ИИ»: подбирает рецепт по тексту запроса. */
export function buildReply(userText) {
  const hit = rules.find((r) => r.re.test(userText))
  const keys = Object.keys(recipes)
  const key = hit ? hit.key : keys[userText.length % keys.length]
  const recipe = recipes[key]
  return { recipe: { ...recipe, ingredients: [...recipe.ingredients] }, text: recipe.text }
}

let seq = 0
export function uid(prefix = 'id') {
  seq += 1
  return `${prefix}_${Date.now().toString(36)}${seq.toString(36)}${Math.random().toString(36).slice(2, 6)}`
}

/** Демо-чаты для встроенных аккаунтов — чтобы сайдбар выглядел как в макете. */
export function demoChats() {
  const now = Date.now()
  const day = 24 * 3600 * 1000
  const korean = buildReply('Хочу сытное блюдо на ужин, например с курицей и рисом')
  const diet = buildReply('Нужны идеи для двухразовой диеты')
  return [
    {
      id: 'demo-korean',
      title: 'Корейские блюда',
      createdAt: now - 2 * day,
      messages: [
        { id: uid('m'), role: 'user', text: 'Хочу сытное блюдо на ужин, например с курицей и рисом', createdAt: now - 2 * day },
        { id: uid('m'), role: 'assistant', createdAt: now - 2 * day + 4000, ...korean },
      ],
    },
    {
      id: 'demo-diet',
      title: 'Идеи для двухразовой диеты',
      createdAt: now - 5 * day,
      messages: [
        { id: uid('m'), role: 'user', text: 'Нужны идеи для двухразовой диеты', createdAt: now - 5 * day },
        { id: uid('m'), role: 'assistant', createdAt: now - 5 * day + 4000, ...diet },
      ],
    },
  ]
}
