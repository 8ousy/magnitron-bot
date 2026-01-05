import os
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Константы для состояний разговора
CHOOSING_LANGUAGE, WAITING_NAME, WAITING_SURNAME, WAITING_PHONE, WAITING_EMAIL, WAITING_ADDRESS = range(6)

# ID владельца бота для уведомлений
OWNER_ID = 215798032

# Файл для сохранения заказов
ORDERS_FILE = 'orders.csv'

# Тексты на разных языках
TEXTS = {
    'ru': {
        'welcome': (
            "Привет! 👋\n\n"
            "Добро пожаловать в *Magnitron Lab*.\n\n"
            "Мы создаём экспериментальные кассетные музыкальные инструменты ручной сборки."
        ),
        'choose_language': "Выберите язык / Choose language:",
        'conditions': (
            "📋 *Условия заказа Magnitron-2:*\n\n"
            "💰 Цена: 1500 EUR + доставка (рассчитывается индивидуально)\n"
            "💳 Предоплата: 50% (750 EUR)\n"
            "🧾 Способы оплаты: RUB / EUR / USD наличными, банковский перевод, PayPal, crypto\n"
            "📦 Производство: 3 месяца (производство запускается после набора 10 заказов, мы проинформируем вас о старте)\n"
            "🌍 Доставка: по всему миру из Екатеринбурга\n\n"
            "Готовы оформить предзаказ?"
        ),
        'agree': "✅ Да, готов оформить",
        'think': "🤔 Нужно подумать",
        'agreed': "Отлично! 🎉\n\nМне нужно собрать несколько данных для оформления заказа.\n\nПожалуйста, укажите ваше *имя*:",
        'thinking': "Конечно, не торопитесь! 🙂\n\nКогда будете готовы, просто напишите /start снова.\n\nЕсли есть вопросы — пишите!",
        'ask_surname': "Спасибо! Теперь укажите вашу *фамилию*:",
        'ask_phone': "Отлично! Укажите ваш *номер телефона* (с кодом страны):",
        'ask_email': "Хорошо! Теперь укажите ваш *email*:",
        'ask_address': "Отлично! И последнее — укажите *полный адрес доставки*\n(страна, город, улица, дом, квартира, индекс):",
        'thank_you': "✅ *Спасибо большое!*\n\nВаша заявка принята. Мы свяжемся с вами в ближайшее время для подтверждения деталей заказа.\n\nЕсли возникнут вопросы — смело пишите!",
        'cancelled': "❌ Заказ отменён.\n\nНапишите /start, когда будете готовы!"
    },
    'en': {
        'welcome': (
            "Hello! 👋\n\n"
            "Welcome to *Magnitron Lab*.\n\n"
            "We create experimental handcrafted cassette-based musical instruments."
        ),
        'choose_language': "Choose language / Выберите язык:",
        'conditions': (
            "📋 *Magnitron-2 Order Terms:*\n\n"
            "💰 Price: 1500 EUR + shipping (calculated individually)\n"
            "💳 Prepayment: 50% (750 EUR)\n"
            "🧾 Payment methods: RUB / EUR / USD cash, bank transfer, PayPal, crypto\n"
            "📦 Production: 3 months (production starts after receiving 10 orders, we will inform you when it begins)\n"
            "🌍 Shipping: worldwide from Yekaterinburg\n\n"
            "Ready to place a pre-order?"
        ),
        'agree': "✅ Yes, ready to order",
        'think': "🤔 Need to think",
        'agreed': "Great! 🎉\n\nI need to collect some information to process your order.\n\nPlease provide your *first name*:",
        'thinking': "Of course, take your time! 🙂\n\nWhen you're ready, just type /start again.\n\nIf you have questions — feel free to ask!",
        'ask_surname': "Thank you! Now please provide your *last name*:",
        'ask_phone': "Perfect! Please provide your *phone number* (with country code):",
        'ask_email': "Good! Now please provide your *email*:",
        'ask_address': "Excellent! And finally — please provide your *full shipping address*\n(country, city, street, building, apartment, postal code):",
        'thank_you': "✅ *Thank you very much!*\n\nYour request has been received. We will contact you shortly to confirm order details.\n\nIf you have any questions — feel free to reach out!",
        'cancelled': "❌ Order cancelled.\n\nType /start when you're ready!"
    }
}

def save_to_csv(data):
    """Сохранение заказа в CSV файл"""
    file_exists = os.path.isfile(ORDERS_FILE)
    
    with open(ORDERS_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'language', 'username', 'user_id', 'name', 'surname', 'phone', 'email', 'address', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    username = user.username if user.username else "Не указан"
    
    # Сохраняем username в контексте
    context.user_data['username'] = username
    context.user_data['user_id'] = user.id
    context.user_data['first_name'] = user.first_name or ""
    context.user_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Уведомляем ТОЛЬКО владельца о новом пользователе
    if user.id != OWNER_ID:
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🔔 *Новый пользователь в боте!*\n\n"
                     f"👤 Username: @{username}\n"
                     f"🆔 User ID: {user.id}\n"
                     f"📝 Имя в TG: {user.first_name}\n"
                     f"⏰ {context.user_data['timestamp']}",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    
    # Показываем выбор языка
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        TEXTS['ru']['choose_language'],
        reply_markup=reply_markup
    )
    
    return CHOOSING_LANGUAGE

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора языка"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]  # 'ru' или 'en'
    context.user_data['language'] = lang
    
    t = TEXTS[lang]
    
    welcome_text = f"{t['welcome']}\n\n{t['conditions']}"
    
    keyboard = [
        [InlineKeyboardButton(t['agree'], callback_data='agree')],
        [InlineKeyboardButton(t['think'], callback_data='think')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('language', 'ru')
    t = TEXTS[lang]
    
    if query.data == 'agree':
        await query.edit_message_text(t['agreed'], parse_mode='Markdown')
        return WAITING_NAME
    
    elif query.data == 'think':
        await query.edit_message_text(t['thinking'])
        return ConversationHandler.END

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени"""
    context.user_data['name'] = update.message.text
    lang = context.user_data.get('language', 'ru')
    await update.message.reply_text(TEXTS[lang]['ask_surname'], parse_mode='Markdown')
    return WAITING_SURNAME

async def receive_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фамилии"""
    context.user_data['surname'] = update.message.text
    lang = context.user_data.get('language', 'ru')
    await update.message.reply_text(TEXTS[lang]['ask_phone'], parse_mode='Markdown')
    return WAITING_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение телефона"""
    context.user_data['phone'] = update.message.text
    lang = context.user_data.get('language', 'ru')
    await update.message.reply_text(TEXTS[lang]['ask_email'], parse_mode='Markdown')
    return WAITING_EMAIL

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email"""
    context.user_data['email'] = update.message.text
    lang = context.user_data.get('language', 'ru')
    await update.message.reply_text(TEXTS[lang]['ask_address'], parse_mode='Markdown')
    return WAITING_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение адреса и завершение"""
    context.user_data['address'] = update.message.text
    lang = context.user_data.get('language', 'ru')
    
    # Подготовка данных для сохранения
    order_data = {
        'timestamp': context.user_data['timestamp'],
        'language': lang,
        'username': context.user_data['username'],
        'user_id': context.user_data['user_id'],
        'name': context.user_data['name'],
        'surname': context.user_data['surname'],
        'phone': context.user_data['phone'],
        'email': context.user_data['email'],
        'address': context.user_data['address'],
        'status': 'Новый'
    }
    
    # Сохраняем в CSV
    try:
        save_to_csv(order_data)
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")
    
    # Уведомляем ТОЛЬКО владельца
    if update.effective_user.id != OWNER_ID:
        try:
            notification = (
                f"🎯 *НОВЫЙ ЗАКАЗ MAGNITRON-2!*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 Язык: {'Русский' if lang == 'ru' else 'English'}\n\n"
                f"👤 *Клиент:*\n"
                f"Имя: {context.user_data['name']} {context.user_data['surname']}\n"
                f"Telegram: @{context.user_data['username']}\n\n"
                f"📞 *Контакты:*\n"
                f"Телефон: {context.user_data['phone']}\n"
                f"Email: {context.user_data['email']}\n\n"
                f"📍 *Адрес доставки:*\n"
                f"{context.user_data['address']}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ {context.user_data['timestamp']}\n"
                f"🆔 User ID: {context.user_data['user_id']}"
            )
            await context.bot.send_message(chat_id=OWNER_ID, text=notification, parse_mode='Markdown')
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    
    # Благодарим пользователя
    await update.message.reply_text(TEXTS[lang]['thank_you'], parse_mode='Markdown')
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    lang = context.user_data.get('language', 'ru')
    await update.message.reply_text(TEXTS[lang]['cancelled'], parse_mode='Markdown')
    return ConversationHandler.END

def main():
    """Запуск бота"""
    TOKEN = "8510850950:AAGIPW4lL4rzJpssnJbwY4MR8Lm2AdD3Xp8"
    
    application = Application.builder().token(TOKEN).build()
    
    # Настройка ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(language_selected, pattern='^lang_')],
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_surname)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(button_callback)
        ],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    print("🤖 Бот запущен!")
    print(f"📝 Заказы сохраняются в: {ORDERS_FILE}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
