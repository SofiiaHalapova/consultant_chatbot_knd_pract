import telebot
from telebot import types

TOKEN = "your-bot-token"
bot = telebot.TeleBot(TOKEN)

PRODUCTS = {
    "1": {"name": "MacBook Air M2", "price": 42000},
    "2": {"name": "iPhone 15 Pro", "price": 45000},
    "3": {"name": "AirPods Pro 2", "price": 10000},
}

user_carts = {}


# Декоратор, який вказує боту реагувати на команди /start та /shop
@bot.message_handler(commands=["start", "shop"])
def send_welcome(message: types.Message):
    markup = types.InlineKeyboardMarkup()

    for item_id, item in PRODUCTS.items():
        markup.add(
            types.InlineKeyboardButton(
                f"{item['name']} — {item['price']} грн",
                callback_data=f"add_{item_id}",
            )
        )

    markup.add(
        types.InlineKeyboardButton("Переглянути кошик", callback_data="cart")
    )

    bot.send_message(
        message.chat.id,
        "Вітаю! Оберіть товари для додавання в кошик:",
        reply_markup=markup,
    )


# Декоратор для перехоплення ВСІХ натискань на Inline-кнопки (func=lambda call: True)
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: types.CallbackQuery):
    chat_id = call.message.chat.id

    cart = user_carts.setdefault(chat_id, {})


    if call.data.startswith("add_"):
        item_id = call.data.split("_")[1]

        cart[item_id] = cart.get(item_id, 0) + 1

        bot.answer_callback_query(call.id, text="✅ Додано в кошик!")

    elif call.data == "cart":
        if not cart:
            bot.answer_callback_query(
                call.id, text="Кошик порожній 🛒", show_alert=True
            )
            return

        text = "🛒 **Ваш кошик:**\n\n"
        total = 0

        for item_id, qty in cart.items():
            item = PRODUCTS[item_id]
            cost = item["price"] * qty
            total += cost
            text += f"• {item['name']} x{qty} = `{cost} грн`\n"

        text += f"\n Разом:{total} грн"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "Оформити замовлення", callback_data="checkout"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "Очистити", callback_data="clear_cart"
            )
        )

        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup,
        )

    # Обробка натискання кнопки "Очистити"
    elif call.data == "clear_cart":
        user_carts[chat_id] = {}
        bot.answer_callback_query(call.id, text="Кошик очищено!")
        send_welcome(call.message)

    # Обробка натискання кнопки "Оформити замовлення"
    elif call.data == "checkout":
        msg = bot.send_message(
            chat_id, "Введіть ваше ім'я та телефон для доставки:"
        )
        bot.register_next_step_handler(msg, process_checkout)


# Функція для обробки введених контактних даних (наступний крок після checkout)
def process_checkout(message: types.Message):
    chat_id = message.chat.id
    contact = message.text.strip()

    bot.send_message(
        chat_id,
        f"Дякуємо, замовлення прийнято!\n\nДані для доставки: _{contact}_",
        parse_mode="Markdown",
    )
    user_carts[chat_id] = {}


# Точка входу в програму: перевірка, чи файл запускається безпосередньо
if __name__ == "__main__":
    print("Бот запущений...")
    bot.infinity_polling()