export const DEFAULT_CATEGORIES = [
  '🛒 Продукты',
  '🍽 Кафе',
  '🚕 Транспорт',
  '🏠 Дом',
  '💡 Коммуналка',
  '💊 Здоровье',
  '🏋️ Спорт',
  '👕 Одежда',
  '🎉 Развлечения',
  '✈️ Путешествия',
  '🎁 Подарки',
  '📱 Подписки',
  '📦 Другое',
];

export const AMOUNT_PATTERN = /^\d+([.,]\d{1,2})?$/;
export const MONTH_PATTERN = /^(\d{1,2})\/(\d{4})$/;

export const CATEGORY_NAME_MAX_LENGTH = 32;
export const MAX_MESSAGE_LENGTH = 4096;

export const DRAFT_TTL_MS = 10 * 60 * 1000;
export const SUMMARY_DELAY_MS = 1500;
export const BACKUP_INTERVAL_MS = 60 * 60 * 1000;
export const BACKUP_KEEP = 3;
export const STATS_BAR_LENGTH = 10;
export const BACKUP_FILE_PATTERN = /^expenses-.*\.db$/;

export const KIND = {
  expense: 'expense',
  transfer: 'transfer',
} as const;

export const LOAN = {
  lend: 'одолжил',
  repay: 'вернул',
} as const;

export const CALLBACK = {
  category: /^cat:(\d+)$/,
  loan: /^loan:(lend|repay)$/,
  cancel: 'cancel',
  deleteRecord: /^del:(\d+)$/,
  history: /^hist:(\d{4})-(\d{1,2})$/,
  stats: /^stats:(\d{4})-(\d{1,2})$/,
  deleteCategory: /^delcat:(\d+)$/,
  closeMenu: 'close',
};

export const BUTTONS = {
  history: '📊 История',
  stats: '📈 Статистика',
  balance: '⚖️ Баланс',
  undo: '↩️ Отменить последнюю',
  help: '❓ Помощь',
  lend: '🤝 Одолжил',
  repay: '💸 Вернул',
  cancel: '✖️ Отмена',
  delete: '🗑 Удалить',
  close: '✖️ Закрыть',
  prevMonth: '◀️',
  nextMonth: '▶️',
};

export const COMMANDS = [
  { command: 'history', description: 'История за текущий месяц' },
  { command: 'stats', description: 'Траты по категориям за месяц' },
  { command: 'balance', description: 'Баланс между пользователями' },
  { command: 'undo', description: 'Удалить свою последнюю запись' },
  { command: 'del', description: 'Удалить запись по id' },
  { command: 'addcat', description: 'Добавить категорию' },
  { command: 'delcat', description: 'Удалить категорию' },
  { command: 'help', description: 'Справка' },
];

export const PROMPTS = {
  deleteRecord:
    '🗑 Введи id записи, которую нужно удалить (он есть в истории перед суммой):',
  deleteRecordPlaceholder: 'Например: 7',
  addCategory: `🏷 Введи название новой категории, можно с эмодзи (до ${CATEGORY_NAME_MAX_LENGTH} символов):`,
  addCategoryPlaceholder: 'Например: 🐾 Питомцы',
};

export const MESSAGES = {
  help: [
    '➕ Добавить трату',
    'Напиши сумму, а через пробел можно добавить комментарий:',
    '25',
    '12,5 кофе с собой',
    'Потом нажми кнопку с категорией. Трата делится пополам.',
    '',
    '🤝 Займ и возврат долга',
    'Так же напиши сумму, но вместо категории нажми:',
    '🤝 Одолжил — ты дал денег в долг',
    '💸 Вернул — ты отдал долг',
    'Займы идут в баланс полностью, а не пополам.',
    '',
    '📊 Посмотреть траты',
    'Кнопка «История» — текущий месяц, стрелки ◀️ ▶️ листают месяцы.',
    'Или напиши месяц и год: 2/2026',
    'Кнопка «Статистика» — на что ушли деньги по категориям и сравнение с прошлым месяцем.',
    'Кнопка «Баланс» — кто кому сколько должен.',
    '',
    '🗑 Удалить запись',
    '• кнопка 🗑 под сообщением о записи',
    '• «Отменить последнюю» — удалит твою последнюю запись',
    '• /del — удалить по номеру, номер есть в истории перед суммой',
    '',
    '🏷 Категории',
    '/addcat — добавить новую, /delcat — удалить',
  ].join('\n'),
  invalidRequest:
    '🤔 Неверный запрос.\nЧтобы добавить новую запись, отправь сумму и комментарий (опционально) через пробел:\n25\n12,5 кофе',
  noAccess: '⛔ У вас нет доступа к этому боту.',
  internalError: '⚠️ Произошла внутренняя ошибка. Попробуйте ещё раз.',
  chooseCategory: (amount: string, comment: string | null) =>
    `💶 ${amount} €${comment ? `\n💬 ${comment}` : ''}\nВыберите категорию:`,
  draftCancelled: '✖️ Запись отменена.',
  draftExpired: '⌛ Время на выбор категории вышло, запись не сохранена.',
  draftNotFound: '⌛ Черновик устарел, отправь сумму заново.',
  categoryNotFound: '⚠️ Такой категории больше нет.',
  expenseAdded: (id: number, body: string) => `✅ Трата #${id} добавлена\n${body}`,
  expenseNotify: (id: number, username: string, body: string, half: string) =>
    `🔔 Новая трата #${id} — ${username}\n${body}\n👉 Ваша половина: ${half} €`,
  loanAdded: (id: number, body: string) =>
    `🤝 Займ #${id} записан\nВы дали в долг ${body}`,
  loanNotify: (id: number, username: string, body: string) =>
    `🔔 Займ #${id} — ${username}\n🤝 Вам дали в долг ${body}`,
  repayAdded: (id: number, body: string) =>
    `💸 Возврат долга #${id} записан\nВы вернули ${body}`,
  repayNotify: (id: number, username: string, body: string) =>
    `🔔 Возврат долга #${id} — ${username}\n💸 Вам вернули ${body}`,
  recordDeleted: (id: number, body: string) => `🗑 Запись #${id} удалена\n${body}`,
  recordDeletedNotify: (id: number, username: string, body: string) =>
    `🔔 Удалена запись #${id} — ${username}\n🗑 ${body}`,
  recordNotFound: (id: number) => `⚠️ Запись с id ${id} не найдена.`,
  invalidId: '⚠️ id — это целое положительное число. Нажми /del и попробуй ещё раз.',
  nothingToUndo: '🤷 У вас нет записей для отмены.',
  invalidMonth: '⚠️ Месяц должен быть от 1 до 12.',
  historyEmpty: (month: number, year: number) => `📭 За ${month}/${year} записей нет.`,
  historyTitle: (month: number, year: number) =>
    `📊 История расходов за ${month}/${year}:`,
  historyTotals: '🧾 Сумма трат за месяц:',
  statsEmpty: (month: number, year: number) => `📭 За ${month}/${year} трат нет.`,
  statsTitle: (month: number, year: number) =>
    `📈 Траты по категориям за ${month}/${year}:`,
  statsTotal: (total: string) => `💰 Всего: ${total} €`,
  statsCompare: (arrow: string, percent: string, previous: string) =>
    `${arrow} ${percent}% к прошлому месяцу (${previous} €)`,
  balance: (total: string) => `⚖️ Ваш баланс: ${total}`,
  balanceDetails: (expenses: string, loans: string) =>
    `\n  🛍 по общим тратам: ${expenses}\n  🤝 по займам: ${loans}`,
  balanceUnavailable: '⚖️ Баланс можно рассчитать только для двух пользователей.',
  invalidCategoryName: `⚠️ Название должно быть от 1 до ${CATEGORY_NAME_MAX_LENGTH} символов. Нажми /addcat и попробуй ещё раз.`,
  categoryAdded: (name: string) => `✅ Категория «${name}» добавлена.`,
  categoryExists: (name: string) => `⚠️ Категория «${name}» уже есть.`,
  chooseCategoryToDelete: '🏷 Какую категорию удалить? Старые записи с ней останутся.',
  categoryDeleted: (name: string) => `🗑 Категория «${name}» удалена.`,
  lastCategory: '⚠️ Нельзя удалить последнюю категорию.',
  menuClosed: '✖️ Закрыто.',
};
