import logging

# Импортируем необходимые классы из библиотеки
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
# Вставьте сюда токен вашего бота, полученный от @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN" 
# Вставьте сюда токен для оплаты, полученный от @BotFather
# Важно: это должен быть токен от провайдера "Telegram Stars"
PAYMENT_PROVIDER_TOKEN = "YOUR_PAYMENT_PROVIDER_TOKEN" 

# Настройка логирования для отладки
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КАТАЛОГ ТОВАРОВ ---
# Структура данных для хранения наших товаров. 
# Цены указаны в целых числах (количество Telegram Stars).
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

# --- ОСНОВНЫЕ ФУНКЦИИ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и показывает главное меню."""
    keyboard = []
    # Создаем кнопки для каждой категории
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
    """Обрабатывает нажатия на inline-кнопки."""
    query = update.callback_query
    await query.answer()
    
    # Разбираем callback_data, например: "category:digital" или "item:digital:pack1"
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
    """Показывает главное меню (категории), редактируя существующее сообщение."""
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
    """Показывает товары в выбранной категории."""
    category = PRODUCTS[category_key]
    keyboard = []
    for item_key, item_data in category["items"].items():
        # Цена в звездах
        price_in_stars = item_data['price']
        button_text = f"{item_data['name']} ({price_in_stars} ⭐️)"
        keyboard.append([
            InlineKeyboardButton(
                button_text, callback_data=f"item:{category_key}:{item_key}"
            )
        ])
    
    # Кнопка "Назад" в главное меню
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
    """Показывает детали товара и кнопку 'Купить'."""
    item = PRODUCTS[category_key]["items"][item_key]
    price_in_stars = item['price']
    
    text = f"Товар: *{item['name']}*\n\n"
    text += f"Цена: *{price_in_stars}* Telegram Stars ⭐️"
    
    keyboard = [
        [InlineKeyboardButton(f"Купить за {price_in_stars} ⭐️", callback_data=f"buy:{category_key}:{item_key}")],
        [InlineKeyboardButton("« Назад к товарам", callback_data=f"back_to_category:{category_key}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def send_invoice(query, context: ContextTypes.DEFAULT_TYPE, category_key: str, item_key: str):
    """Создает и отправляет счет на оплату."""
    chat_id = query.message.chat.id
    item = PRODUCTS[category_key]["items"][item_key]
    
    title = item["name"]
    description = f"Оплата товара '{title}' в Telegram Stars"
    # Уникальный ID для этого платежа
    payload = f"payload-{chat_id}-{item_key}-{query.id}" 
    # Для Telegram Stars используется валюта XTR
    currency = "XTR"
    # Цена должна быть в виде списка LabeledPrice. Количество - это количество звезд.
    price = item["price"]
    prices = [LabeledPrice(label=title, amount=price)]

    # Отправляем инвойс
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
    )
    # Удаляем сообщение с кнопкой "Купить", чтобы избежать повторных нажатий
    await query.delete_message()


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на запрос pre-checkout. Обязательный шаг для оплаты."""
    query = update.pre_checkout_query
    # Здесь можно добавить проверку, доступен ли еще товар
    # Если все в порядке, подтверждаем
    await query.answer(ok=True)
    # Если товар закончился, можно отклонить:
    # await query.answer(ok=False, error_message="Извините, этот товар уже недоступен.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вызывается после успешной оплаты."""
    payment_info = update.message.successful_payment
    currency = payment_info.currency
    total_amount = payment_info.total_amount
    
    logger.info(f"Успешная оплата: {total_amount} {currency}")

    # Здесь вы можете выдать товар: отправить файл, ссылку, инструкцию и т.д.
    await update.message.reply_text(
        f"Спасибо за покупку! 🎉\n\nВы успешно оплатили {total_amount} {currency}. "
        "Ваш цифровой товар скоро будет доставлен."
    )

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()