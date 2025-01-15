from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
# from config import TOKEN
import sqlite3
import os

TOKEN = os.environ['TOKEN']

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AddExpenseState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()

ALLOWED_USERS = {660558578, 432192596}

@dp.message(Command("new"))
async def start_new_expense(message: Message, state: FSMContext):

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    await state.clear()  # Сбрасываем текущее состояние пользователя
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
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Добавляем запись в базу данных
    cursor.execute('''
        INSERT INTO expenses (user_id, username, amount, category, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (callback.from_user.id, callback.from_user.full_name, amount, date_str, category,))

    conn.commit()
    conn.close()

    await callback.message.answer(f"Запись успешно добавлена!")
    await state.clear()  # Завершаем состояние


@dp.message(Command("history"))
async def show_history(message: Message, state: FSMContext):

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    await state.clear()  # Завершаем состояние

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, amount, category, date FROM expenses
        ORDER BY id
    ''')
    rows = cursor.fetchall()
    
    if rows:
        history = "\n".join([f"{row[0]} | {row[1]} | {row[2]} € | {row[3]} | {row[4]}" for row in rows])
        await message.answer(f"История расходов:\n\n{history}")
    else:
        await message.answer("За этот период нет данных.")
    
    conn.close()
    await state.clear()  # Завершаем состояние


@dp.message(Command("balance"))
async def calculate_balance(message: Message, state: FSMContext):

    if message.from_user.id not in ALLOWED_USERS:
        await message.answer("У вас нет доступа к этому боту.")
        return

    await state.clear()  # Сбрасываем текущее состояние пользователя

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    # Запрос для получения сумм всех пользователей
    cursor.execute('''
        SELECT user_id, SUM(amount) as total_amount
        FROM expenses
        GROUP BY user_id
    ''')
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

    conn.close()
    await state.clear()  # Завершаем состояние


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    dp.run_polling(bot)