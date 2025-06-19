import logging
import os  

from telegram import (
    Update,
    LabeledPrice,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
)

# --- НАСТРОЙКИ БОТА ---
# Берём токены из переменных окружения (безопасный способ)
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# Проверка, что токены установлены. Если нет, бот не запустится.
if not BOT_TOKEN or not PAYMENT_PROVIDER_TOKEN:
    raise ValueError(
        "Ошибка: Не найдены BOT_TOKEN и PAYMENT_PROVIDER_TOKEN. "
        "Убедитесь, что вы добавили их в переменные окружения на хостинге."
    )

# Настройка логирования для отладки
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КАТАЛОГ ТОВАРОВ ---
PRODUCTS = {
    "digital": {
        "title": "Цифровые товары 🖼️",
        "items": {
            "pack1": {"name": "Пак стикеров 'Космос'", "price": 10},
            "pack2": {"name": "Обои для телефона 'Природа'", "price": 15},
            "pack3": {"name": "Эксклюзивный аватар", "price": 25},
        },
    },
    "services": {
        "title": "Услуги 🛠️",
        "items": {
            "consult": {"name": "30-минутная консультация", "price": 100},
            "review": {"name": "Аудит вашего канала", "price": 150},
        },
    },
    "guides": {
        "title": "Гайды и инструкции 📚",
        "items": {
            "guide1": {"name": "Гайд по продвижению в Telegram", "price": 50},
            "guide2": {"name": "Инструкция по созданию бота", "price": 75},
        },
    },
    "media": {
        "title": "Медиа-контент 🎵",
        "items": {
            "song": {"name": "Эксклюзивный трек", "price": 30},
            "video": {"name": "Видеоурок по монтажу", "price": 60},
        },
    },
    "access": {
        "title": "Доступы 🔑",
        "items": {
            "chat": {"name": "Доступ в закрытый чат (1 мес)", "price": 200},
            "channel": {"name": "Доступ в VIP-канал (1 мес)", "price": 250},
        },
    },
    "donate": {
        "title": "Поддержать автора ❤️",
        "items": {
            "tip1": {"name": "Маленькая благодарность", "price": 5},
            "tip2": {"name": "Средняя благодарность", "price": 20},
            "tip3": {"name": "Большая благодарность", "price": 50},
        },
    },
}

# --- ФУНКЦИИ БОТА (остальной код без изменений) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    for category_key, category_data in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                category_data["title"], callback_data=f"category:{category_key}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Добро пожаловать! Выберите категорию товаров:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split(":")
    action = data_parts[0]

    if action == "category":
        category_key = data_parts[1]
        await show_category_items(query, category_key)
    elif action == "item":
        category_key = data_parts[1]
        item_key = data_parts[2]
        await show_item_details(query, category_key, item_key)
    elif action == "buy":
        category_key = data_parts[1]
        item_key = data_parts[2]
        await send_invoice(query, context, category_key, item_key)
    elif action == "back_to_menu":
        await show_main_menu(query)
    elif action == "back_to_category":
        category_key = data_parts[1]
        await show_category_items(query, category_key)

async def show_main_menu(query):
    keyboard = []
    for category_key, category_data in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                category_data["title"], callback_data=f"category:{category_key}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Выберите категорию товаров:",
        reply_markup=reply_markup
    )
    
async def show_category_items(query, category_key: str):
    category = PRODUCTS[category_key]
    keyboard = []
    for item_key, item_data in category["items"].items():
        price_in_stars = item_data['price']
        button_text = f"{item_data['name']} ({price_in_stars} ⭐️)"
        keyboard.append([
            InlineKeyboardButton(
                button_text, callback_data=f"item:{category_key}:{item_key}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("« Назад в меню", callback_data="back_to_menu")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Выбрана категория: *{category['title']}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_item_details(query, category_key: str, item_key: str):
    item = PRODUCTS[category_key]["items"][item_key]
    price_in_stars = item['price']
    text = f"Товар: *{item['name']}*\n\nЦена: *{price_in_stars}* Telegram Stars ⭐️"
    keyboard = [
        [InlineKeyboardButton(f"Купить за {price_in_stars} ⭐️", callback_data=f"buy:{category_key}:{item_key}")],
        [InlineKeyboardButton("« Назад к товарам", callback_data=f"back_to_category:{category_key}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def send_invoice(query, context: ContextTypes.DEFAULT_TYPE, category_key: str, item_key: str):
    chat_id = query.message.chat.id
    item = PRODUCTS[category_key]["items"][item_key]
    title = item["name"]
    description = f"Оплата товара '{title}' в Telegram Stars"
    payload = f"payload-{chat_id}-{item_key}-{query.id}"
    currency = "XTR"
    price = item["price"]
    prices = [LabeledPrice(label=title, amount=price)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
    )
    await query.delete_message()

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment_info = update.message.successful_payment
    currency = payment_info.currency
    total_amount = payment_info.total_amount
    logger.info(f"Успешная оплата: {total_amount} {currency}")
    await update.message.reply_text(
        f"Спасибо за покупку! 🎉\n\nВы успешно оплатили {total_amount} {currency}. "
        "Ваш цифровой товар скоро будет доставлен."
    )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
