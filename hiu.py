from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import mysql.connector
import os

TOKEN = os.environ['TOKEN']
USER = os.environ['USER']
PASS = os.environ['PASS']

# from config import TOKEN, USER_DB, PASS_DB

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

db = mysql.connector.connect(
    host="localhost",
    user=USER,
    password=PASS,
    database="expenses"
)

cursor = db.cursor()

class AddExpenseState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()


# ALLOWED_USERS = [432192596, 660558578]

# @dp.message(Command())
# async def handle_command(message: Message):
#     if message.from_user.id not in ALLOWED_USERS:
#         await message.answer("Извините, у вас нет доступа к этому боту.")
#         return


@dp.message(Command("new"))
async def start_new_expense(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем текущее состояние пользователя
    await message.answer("Введите сумму")
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
            ]
        ])

        await message.answer("Выберите категорию", reply_markup=markup)
        await state.set_state(AddExpenseState.waiting_for_category)
    except ValueError:
        await state.clear()  # Завершаем состояние


@dp.callback_query(AddExpenseState.waiting_for_category)
async def process_new_expense_category(callback: CallbackQuery, state: FSMContext):
    # Получаем категорию из callback_data
    category = callback.data.split("_")[1]
    data = await state.get_data()  # Достаём данные (сумма)
    amount = data['amount']

    # Добавляем запись в базу данных
    query = "INSERT INTO expenses (user_id, username, amount, category, date) VALUES (%s, %s, %s, %s, %s)"
    values = (
        callback.from_user.id,
        callback.from_user.full_name,
        amount,
        category,
        datetime.now()
    )
    cursor.execute(query, values)
    db.commit()

    await callback.message.answer(f"Запись успешно добавлена!")
    await state.clear()  # Завершаем состояние


@dp.message(Command("history"))
async def show_history(message: Message, state: FSMContext):
    today = datetime.now()
    start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d 00:00:00')
    end_date = today.strftime('%Y-%m-%d 23:59:59')

    query = """
        SELECT username, amount, category, date
        FROM expenses
        WHERE date BETWEEN %s AND %s
        ORDER BY date DESC
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()

    if rows:
        history = "\n".join([f"{row[0]} | {row[1]} € | {row[2]} | {row[3]}" for row in rows])
        await message.answer(f"История расходов:\n\n{history}")
    else:
        await message.answer("За этот период нет данных.")


@dp.message(Command("balance"))
async def calculate_balance(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем текущее состояние пользователя
    # Запрос для получения сумм всех пользователей
    query = """
        SELECT user_id, SUM(amount) as total_amount
        FROM expenses
        GROUP BY user_id
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # Создаём словарь {user_id: total_amount}
    user_expenses = {row[0]: row[1] for row in rows}
    total_expenses = sum(user_expenses.values())  # Общая сумма всех трат
    num_users = len(user_expenses)  # Количество пользователей

    # Определяем траты текущего пользователя
    current_user_id = message.from_user.id
    current_user_expenses = user_expenses.get(current_user_id, 0)

    # Средние траты всех пользователей
    average_expenses = total_expenses / num_users if num_users > 0 else 0

    # Баланс текущего пользователя
    balance = current_user_expenses - average_expenses

    # Формируем сообщение
    if balance > 0:
        await message.answer(f"Ваш баланс составляет +{balance:.2f} €.")
    elif balance < 0:
        await message.answer(f"Ваш баланс составляет {balance:.2f} €.")
    else:
        await message.answer("Ваш баланс равен 0.00 €.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    dp.run_polling(bot)
