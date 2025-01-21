from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ['TOKEN']

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = web.Application()

class AddExpenseState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_id = State()

ALLOWED_USERS = {660558578, 432192596}

@dp.message(Command("new"))
async def start_new_expense(message: Message, state: FSMContext):

    await state.clear()  # Сбрасываем текущее состояние пользователя

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    await message.answer("Введите сумму (используя точку если нужно)")
    await state.set_state(AddExpenseState.waiting_for_amount)


@dp.message(AddExpenseState.waiting_for_amount)
async def process_new_expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)  # Проверяем, что введено число
        await state.update_data(amount=amount)  # Сохраняем сумму во временное хранилище

        # Отправляем кнопки с категориями
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                {"text": "Продукты", "callback_data": "category_Продукты"},
                {"text": "Онлайн-покупки", "callback_data": "category_Онлайн-покупки"}
            ],
            [
                {"text": "Аптека", "callback_data": "category_Аптека"},
                {"text": "Заведения", "callback_data": "category_Заведения"}
            ],
            [
                {"text": "Развлечения", "callback_data": "category_Развлечения"},
                {"text": "Подписки", "callback_data": "category_Подписки"}
            ],
            [
                {"text": "Другое", "callback_data": "category_Другое"}
            ]])

        await message.answer("Выберите категорию", reply_markup=markup)
        await state.set_state(AddExpenseState.waiting_for_category)
    except ValueError:
        await message.answer("Произошла ошибка, повторите команду")
        await state.clear()  # Завершаем состояние


@dp.callback_query(AddExpenseState.waiting_for_category)
async def process_new_expense_category(callback: CallbackQuery, state: FSMContext):
    # Получаем категорию из callback_data
    category = callback.data.split("_")[1]
    data = await state.get_data()  # Достаём данные (сумма)
    amount = data['amount']
    date = datetime.now().date()

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Добавляем запись в базу данных
    cursor.execute('''
        INSERT INTO expenses (user_id, username, amount, category, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (callback.from_user.id, callback.from_user.full_name, amount, category, date))

    conn.commit()
    conn.close()

    await callback.message.answer(f"Запись успешно добавлена!")
    await state.clear()  # Завершаем состояние


@dp.message(Command("history"))
async def show_history(message: Message, state: FSMContext):

    await state.clear()  # Сбрасываем текущее состояние пользователя

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    try:
        # Отправляем кнопки с категориями
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Неделя", callback_data="time_history_week"),
                InlineKeyboardButton(text="Месяц", callback_data="time_history_month"),
                InlineKeyboardButton(text="Все время", callback_data="time_history_all"),
            ]])
        await message.answer("Выберите период для просмотра истории", reply_markup=markup)
    except ValueError:
        await message.answer("Произошла ошибка, повторите команду.")
        await state.clear()  # Завершаем состояние

@dp.callback_query(lambda callback: callback.data in ["time_history_week", "time_history_month", "time_history_all"])
async def process_time_history(callback: CallbackQuery):

    today = datetime.now()

    if callback.data == "time_history_week":
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')  # 7 дней назад
        end_date = today.strftime('%Y-%m-%d')
        query = '''
            SELECT id, username, amount, category, date 
            FROM expenses 
            WHERE date BETWEEN ? AND ?
            ORDER BY id
        '''
        params = (start_date, end_date)

    elif callback.data == "time_history_month":
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        query = '''
            SELECT id, username, amount, category, date 
            FROM expenses 
            WHERE date BETWEEN ? AND ?
            ORDER BY id
        '''
        params = (start_date, end_date)

    elif callback.data == "time_history_all":
        query = '''
            SELECT id, username, amount, category, date 
            FROM expenses 
            ORDER BY id
        '''
        params = ()
    
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    if rows:
        user_totals = {}
        for row in rows:
            user = row[1]  # Имя пользователя
            amount = row[2]  # Сумма траты
            user_totals[user] = round(user_totals.get(user, 0) + amount, 2)
        history = "\n".join([f"{row[0]}. {row[1]} | {row[2]} € | {row[3]} | {row[4]}" for row in rows])
        totals_text = "\n".join([f"{user}: {total} €" for user, total in user_totals.items()])
        await callback.message.answer(f"История расходов:\n\n{history}\n\nСумма трат за период:\n{totals_text}")
    else:
        await callback.message.answer("За этот период нет данных.")
    
    conn.close()
    await callback.answer()

@dp.message(Command("balance"))
async def calculate_balance(message: Message, state: FSMContext):

    await state.clear()  # Сбрасываем текущее состояние пользователя

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Запрос для получения сумм всех пользователей
    cursor.execute('''
        SELECT user_id, SUM(amount) as total_amount
        FROM expenses
        GROUP BY user_id
    ''')
    rows = cursor.fetchall()
    conn.close()

    # Создаём словарь {user_id: total_amount}
    user_expenses = {row[0]: row[1] for row in rows}

    # Проверяем, что ровно два пользователя участвуют
    if len(user_expenses) != 2:
        await message.answer("Ошибка: Баланс можно рассчитать только для двух пользователей.")
        await state.clear()
        return

    # Получаем ID текущего пользователя и второго пользователя
    current_user_id = message.from_user.id
    other_user_id = next(uid for uid in user_expenses.keys() if uid != current_user_id)

    # Получаем траты обоих пользователей
    current_user_expenses = user_expenses.get(current_user_id, 0)
    other_user_expenses = user_expenses.get(other_user_id, 0)

    # Общая сумма всех расходов
    total_expenses = current_user_expenses + other_user_expenses

    # Доля каждого пользователя
    each_share = total_expenses / 2

    # Расчет баланса для текущего пользователя
    current_user_balance = current_user_expenses - each_share

    # Формируем сообщение
    if current_user_balance > 0:
        await message.answer(f"Ваш баланс составляет +{current_user_balance:.2f} €.")
    elif current_user_balance < 0:
        await message.answer(f"Ваш баланс составляет {current_user_balance:.2f} €.")
    else:
        await message.answer("Ваш баланс составляет 0 €.")

    await state.clear()  # Завершаем состояние


@dp.message(Command("delete"))
async def delete_expense_start(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем текущее состояние пользователя

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    await message.answer("Введите ID записи, которую хотите удалить")
    await state.set_state(AddExpenseState.waiting_for_id)


@dp.message(AddExpenseState.waiting_for_id)
async def process_delete_expense(message: Message, state: FSMContext):
    try:
        # Проверяем, что введено число
        id = int(message.text)
    except ValueError:
        await message.answer("ID должен быть числом. Попробуйте снова.")
        await state.clear()  # Завершаем состояние
        return

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Проверяем, существует ли запись с таким ID
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (id,))
    record = cursor.fetchone()

    if record is None:
        await message.answer(f"Запись с ID {id} не найдена.")
    else:
        # Удаляем запись
        cursor.execute("DELETE FROM expenses WHERE id = ?", (id,))
        conn.commit()
        await message.answer(f"Запись с ID №{id} успешно удалена.")

    conn.close()
    await state.clear()  # Завершаем состояние


async def on_startup(app):
    webhook_url = f"https://sheetavod.onrender.com/webhook"
    logger.info(f"Установка вебхука: {webhook_url}")
    await bot.set_webhook(webhook_url)


async def on_shutdown(app):
    logger.info("Удаление вебхука")
    await bot.delete_webhook()


async def log_requests(request, handler):
    logger.info(f"Получен запрос: {request.method} {request.path}")
    response = await handler(request)
    logger.info(f"Ответ: {response.status}")
    return response


async def handle_head(request):
    return web.Response(status=200, text="OK")


SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
app.router.add_route('HEAD', f'/webhook', handle_head)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)


if __name__ == "__main__":
    try:
        web.run_app(app, port=int(os.getenv("PORT", 5000)))
    except Exception as e:
        logging.error(f"Ошибка: {e}")