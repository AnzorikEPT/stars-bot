import asyncio
import os
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import (
    init_db, add_participant, get_participants, clear_participants,
    get_total_stars, add_stars, reset_stars, record_win, get_user_stats,
    add_admin_profit, get_admin_profit, get_total_users_count,
    get_goal_stars, set_goal_stars
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # ЗАМЕНИТЬ НА СВОЙ ID!

ENTRY_PRICE = 10      # Цена 1 билета
COMMISSION_PCT = 10   # Комиссия сервиса (10%)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить билет (10 ⭐️)", callback_data="buy_ticket")],
        [
            InlineKeyboardButton(text="📊 Статистика раунда", callback_data="round_stats"),
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")
        ],
        [InlineKeyboardButton(text="📜 Правила игры", callback_data="rules")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚙️ Изменить цель банка", callback_data="admin_set_goal")],
        [InlineKeyboardButton(text="🎯 Принудительный розыгрыш", callback_data="admin_force_win")],
        [InlineKeyboardButton(text="♻️ Сбросить текущий раунд", callback_data="admin_reset_round")],
        [InlineKeyboardButton(text="◀️ Выход в обычное меню", callback_data="main_menu")]
    ])

def get_goal_variants_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="50 ⭐️", callback_data="goal_50"),
            InlineKeyboardButton(text="100 ⭐️", callback_data="goal_100"),
            InlineKeyboardButton(text="250 ⭐️", callback_data="goal_250")
        ],
        [
            InlineKeyboardButton(text="500 ⭐️", callback_data="goal_500"),
            InlineKeyboardButton(text="1000 ⭐️", callback_data="goal_1000")
        ],
        [InlineKeyboardButton(text="◀️ Назад в админку", callback_data="back_to_admin")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    init_db()
    text = (
        "✨ **Добро пожаловать в Звёздный Куш!** ✨\n\n"
        "🔥 Уникальная лотерея в Telegram Stars. Закидывай звёзды, собирай банк и забирай всё одним кликом!\n\n"
        "👇 Выбирай нужный раздел в меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    
    text = (
        "🔐 **Панель Администратора**\n\n"
        "Добро пожаловать, босс! Выберите действие:"
    )
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_admin")
async def cb_back_to_admin(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    text = "🔐 **Панель Администратора**\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    total_bank = get_total_stars()
    goal = get_goal_stars()
    profit = get_admin_profit()
    users_count = get_total_users_count()
    participants = len(get_participants())

    text = (
        f"📈 **Расширенная статистика бота:**\n\n"
        f"👥 Всего пользователей: <code>{users_count}</code>\n"
        f"🎯 Участников в раунде: <code>{participants}</code>\n"
        f"🏆 Цель банка: <code>{goal} ⭐️</code>\n"
        f"💰 Текущий банк: <code>{total_bank} / {goal} ⭐️</code>\n"
        f"🏛 Заработано комиссией: <code>{profit} ⭐️</code>"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_set_goal")
async def cb_admin_set_goal(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    current_goal = get_goal_stars()
    text = (
        f"⚙️ **Установка цели банка**\n\n"
        f"Текущая цель: <b>{current_goal} ⭐️</b>\n\n"
        f"Выберите новую сумму, при достижении которой будет автоматически запускаться розыгрыш:"
    )
    await callback.message.edit_text(text, reply_markup=get_goal_variants_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("goal_"))
async def cb_change_goal(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    new_goal = int(callback.data.split("_")[1])
    set_goal_stars(new_goal)

    await callback.message.edit_text(
        f"✅ **Цель банка успешно изменена!**\n\n"
        f"Теперь розыгрыш будет запускаться при достижении <b>{new_goal} ⭐️</b>.",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer(f"Цель изменена на {new_goal} ⭐️!")

@dp.callback_query(F.data == "admin_force_win")
async def cb_admin_force_win(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    participants = get_participants()
    if not participants:
        await callback.answer("⚠️ В текущем раунде нет участников!", show_alert=True)
        return

    await callback.message.answer("⚡️ **Админ запустил принудительный розыгрыш!**")
    await run_giveaway(callback.message)
    await callback.answer("Розыгрыш проведен!")

@dp.callback_query(F.data == "admin_reset_round")
async def cb_admin_reset_round(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    clear_participants()
    reset_stars()
    
    await callback.message.edit_text(
        "♻️ **Текущий раунд успешно сброшен!** Банк обнулен, участники удалены.",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Раунд сброшен!", show_alert=True)

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    text = "✨ **Главное меню:**\n\n👇 Выбирай интересующий раздел:"
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "round_stats")
async def cb_round_stats(callback: CallbackQuery):
    init_db()
    total = get_total_stars()
    goal = get_goal_stars()
    participants = get_participants()
    stars_left = max(0, goal - total)
    
    text = (
        f"📊 **Статистика текущего раунда:**\n\n"
        f"• Цель раунда: <code>{goal} ⭐️</code>\n"
        f"• Собрано в банке: <code>{total} ⭐️</code>\n"
        f"• Осталось собрать: <code>{stars_left} ⭐️</code>\n"
        f"• Всего участников: <code>{len(participants)}</code>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def cb_my_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    tickets, wins, total_won = get_user_stats(user_id)

    text = (
        f"👤 **Ваш игровой профиль:**\n\n"
        f"🎟 Куплено билетов: <code>{tickets}</code>\n"
        f"🏆 Побед: <code>{wins}</code>\n"
        f"💎 Выиграно звёзд: <code>{total_won} ⭐️</code>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "rules")
async def cb_rules(callback: CallbackQuery):
    goal = get_goal_stars()
    text = (
        "📜 **Правила и механика:**\n\n"
        f"1️⃣ Стоимость билета — <b>{ENTRY_PRICE} ⭐️</b>.\n"
        f"2️⃣ Когда банк достигает целевой суммы в <b>{goal} ⭐️</b>, бот случайно выбирает победителя.\n"
        f"3️⃣ Победитель забирает банк за вычетом комиссии сервиса ({COMMISSION_PCT}%)."
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "buy_ticket")
async def cb_buy_ticket(callback: CallbackQuery):
    await callback.message.answer(
        f"💳 **Покупка билета**\n\n"
        f"Нажмите кнопку ниже для оплаты взноса в размере **{ENTRY_PRICE} ⭐️**.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Оплатить {ENTRY_PRICE} ⭐️", pay=True)],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
        ]),
        parse_mode="Markdown"
    )
    
    await callback.message.answer_invoice(
        title="Билет на розыгрыш",
        description=f"Взнос {ENTRY_PRICE} звёзд в призовой фонд.",
        payload="lottery_ticket",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Билет", amount=ENTRY_PRICE)]
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    add_participant(user_id, username)
    add_stars(ENTRY_PRICE)

    total = get_total_stars()
    goal = get_goal_stars()
    
    await message.answer(
        f"✅ **Оплата прошла успешно!** Вы в игре.\n\n"
        f"📊 Текущий банк: <b>{total} / {goal} ⭐️</b>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    if total >= goal:
        await run_giveaway(message)

async def run_giveaway(message: Message):
    participants = get_participants()
    if not participants:
        return

    total_bank = get_total_stars()
    admin_commission = int(total_bank * COMMISSION_PCT / 100)
    winner_prize = total_bank - admin_commission

    add_admin_profit(admin_commission)

    msg = await message.answer("🎰 **Запускаем генератор случайных чисел...** 🎲")
    await asyncio.sleep(1.5)
    await msg.edit_text("🔄 **Барабан крутится, выбираем счастливчика...** ⏳")
    await asyncio.sleep(1.5)

    winner_tuple = random.choice(participants)
    winner_id = winner_tuple[0]
    winner_name = winner_tuple[1]

    record_win(winner_id, winner_prize)

    formatted_name = f"@{winner_name}" if not winner_name.isdigit() else f"id{winner_id}"

    await msg.edit_text(
        f"🎉 **РОЗЫГРЫШ ЗАВЕРШЕН! УРА ПОБЕДИТЕЛЮ!** 🎉\n\n"
        f"💰 Итоговый банк: <b>{total_bank} ⭐️</b>\n"
        f"🏆 **Приз победителя:** <b>{winner_prize} ⭐️</b>\n\n"
        f"👑 Победитель: <b>{formatted_name}</b> 🥳",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            winner_id,
            f"🏆 **ПОЗДРАВЛЯЕМ! ТЫ ВЫИГРАЛ!** 🥳\n\n"
            f"В этом раунде тебе достался суперприз: **{winner_prize} ⭐️**!",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    clear_participants()
    reset_stars()

async def main():
    init_db()
    print("Готовый премиальный бот со всеми функциями запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
