from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from quiz_logic import QuizLogic
import config

db = Database()
quiz = QuizLogic(db)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user

    # Регистрируем пользователя
    db.add_user(user.id, user.username, user.first_name)

    # Проверяем, есть ли параметр (переход из канала)
    if context.args and context.args[0].startswith('q'):
        # Сразу показываем вопрос
        await show_question(update, context)
    else:
        welcome_text = f"""
👋 Добро пожаловать в квиз "Областная газета"!

Привет, {user.first_name}!

Каждый день в случайное время (9:00-21:00) в канале
@{config.CHANNEL_USERNAME} публикуется новый вопрос
о нашем регионе.

🎯 Отвечайте правильно и зарабатывайте баллы!

💎 Система баллов:
• Правильный ответ: {config.POINTS_CORRECT} баллов
• Топ-50 (первые 50 правильных): +{config.POINTS_TOP50} баллов
• Скорость (<{config.SPEED_LIMIT} сек): +{config.POINTS_SPEED} балла

📊 /rating — Посмотреть рейтинг
📈 /stats — Моя статистика
❓ /help — Помощь

Следите за каналом и удачи! 🍀
"""
        await update.message.reply_text(welcome_text)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущий вопрос"""
    user_id = update.effective_user.id

    # Очищаем устаревшие сессии
    quiz.cleanup_expired_sessions()

    result = quiz.start_quiz_for_user(user_id)

    if result['status'] != 'success':
        await update.message.reply_text(result['message'])
        return

    question = result['question']

    # Формируем текст
    question_text = f"""
❓ ВОПРОС ДНЯ

📚 Категория: {question['category']}

{question['question_text']}

Выберите правильный ответ ⬇️
"""

    # Кнопки с вариантами
    keyboard = [
        [
            InlineKeyboardButton(f"А) {question['option_a']}",
                               callback_data=f"answer_A")
        ],
        [
            InlineKeyboardButton(f"Б) {question['option_b']}",
                               callback_data=f"answer_B")
        ],
        [
            InlineKeyboardButton(f"В) {question['option_c']}",
                               callback_data=f"answer_C")
        ],
        [
            InlineKeyboardButton(f"Г) {question['option_d']}",
                               callback_data=f"answer_D")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем вопрос
    if question.get('image_url'):
        await update.message.reply_photo(
            photo=question['image_url'],
            caption=question_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            question_text,
            reply_markup=reply_markup
        )

async def answer_question_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать вопрос (callback от кнопки "Ответить на вопрос")"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Очищаем устаревшие сессии
    quiz.cleanup_expired_sessions()

    result = quiz.start_quiz_for_user(user_id)

    if result['status'] != 'success':
        await query.edit_message_text(result['message'])
        return

    question = result['question']

    question_text = f"""
❓ ВОПРОС ДНЯ

📚 Категория: {question['category']}

{question['question_text']}

Выберите правильный ответ ⬇️
"""

    keyboard = [
        [InlineKeyboardButton(f"А) {question['option_a']}", callback_data="answer_A")],
        [InlineKeyboardButton(f"Б) {question['option_b']}", callback_data="answer_B")],
        [InlineKeyboardButton(f"В) {question['option_c']}", callback_data="answer_C")],
        [InlineKeyboardButton(f"Г) {question['option_d']}", callback_data="answer_D")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        question_text,
        reply_markup=reply_markup
    )

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_answer = query.data.split('_')[1]  # A, B, C, или D

    # Очищаем устаревшие сессии
    quiz.cleanup_expired_sessions()

    result = quiz.check_answer(user_id, user_answer)

    if result['status'] != 'answered':
        if query.message.photo:
            await query.edit_message_caption(result['message'])
        else:
            await query.edit_message_text(result['message'])
        return

    # Формируем ответ
    if result['is_correct']:
        response = f"""
✅ ПРАВИЛЬНО!

{result['explanation']}

💎 Вы заработали: {result['points_earned']} баллов

"""
        for bonus in result['bonus_text']:
            response += f"{bonus}\n"

        response += f"""
📊 Ваша статистика:
• Всего баллов: {result['user_stats']['total_points']}
• Правильных ответов: {result['user_stats']['correct_answers']}
• Ваше место: #{result['user_rank']['rank']}
"""

        if result['user_rank']['rank'] > config.RATING_TOP_N:
            response += f"• До топ-{config.RATING_TOP_N}: {result['user_rank']['points_to_top10']} баллов"

    else:
        response = f"""
❌ НЕПРАВИЛЬНО

Правильный ответ: {result['correct_answer']}

{result['explanation']}

📊 Ваша статистика:
• Всего баллов: {result['user_stats']['total_points']}
• Правильных ответов: {result['user_stats']['correct_answers']}
• Ваше место: #{result['user_rank']['rank']}

Не расстраивайтесь! Следующий вопрос — завтра.
Следите за каналом @{config.CHANNEL_USERNAME}
"""

    if query.message.photo:
        await query.edit_message_caption(response)
    else:
        await query.edit_message_text(response)

async def rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /rating"""
    user_id = update.effective_user.id

    # Получаем топ-10
    top_users = db.get_rating(limit=config.RATING_TOP_N)

    # Получаем позицию пользователя
    user_rank = db.get_user_rank(user_id)
    user_data = db.get_user(user_id)

    rating_text = f"🏆 РЕЙТИНГ ЗНАТОКОВ\n\nТОП-{config.RATING_TOP_N}:\n\n"

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for i, user in enumerate(top_users, 1):
        medal = medals.get(i, f"{i}.")
        name = user['first_name'] or user['username'] or "Аноним"
        rating_text += f"{medal} {name} — {user['total_points']} баллов\n"

    rating_text += f"\n{'─' * 30}\n"
    rating_text += f"📍 Ваше место: #{user_rank['rank']}\n"
    rating_text += f"💎 Ваши баллы: {user_data['total_points']}\n"

    if user_rank['rank'] > config.RATING_TOP_N:
        rating_text += f"🎯 До топ-{config.RATING_TOP_N}: {user_rank['points_to_top10']} баллов\n"

    await update.message.reply_text(rating_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        await update.message.reply_text(
            "❌ Вы ещё не зарегистрированы. Используйте /start"
        )
        return

    accuracy = 0
    if user_data['total_answers'] > 0:
        accuracy = round(
            user_data['correct_answers'] / user_data['total_answers'] * 100, 1
        )

    user_rank = db.get_user_rank(user_id)

    stats_text = f"""
📈 ВАША СТАТИСТИКА

👤 Имя: {user_data['first_name']}
🗓 Зарегистрирован: {user_data['registration_date'][:10]}

💎 Всего баллов: {user_data['total_points']}
✅ Правильных ответов: {user_data['correct_answers']}
📊 Всего ответов: {user_data['total_answers']}
🎯 Точность: {accuracy}%

📍 Место в рейтинге: #{user_rank['rank']}
"""

    if user_rank['rank'] > config.RATING_TOP_N:
        stats_text += f"🎯 До топ-{config.RATING_TOP_N}: {user_rank['points_to_top10']} баллов"

    await update.message.reply_text(stats_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = f"""
❓ ПОМОЩЬ

📌 КАК ИГРАТЬ:
1. Следите за каналом @{config.CHANNEL_USERNAME}
2. Когда появится вопрос — нажмите "Ответить"
3. Выберите правильный вариант ответа
4. Получите баллы!

💎 СИСТЕМА БАЛЛОВ:
• Правильный ответ: {config.POINTS_CORRECT} баллов
• Топ-50 (первые 50 правильных): +{config.POINTS_TOP50} баллов
• Скорость (<{config.SPEED_LIMIT} сек): +{config.POINTS_SPEED} балла

📊 КОМАНДЫ:
/rating — Рейтинг игроков
/stats — Моя статистика
/help — Эта справка

🏆 РЕЙТИНГ:
Каждое воскресенье в 20:00 вы получите сообщение
с текущим рейтингом и вашей позицией.

Удачи в игре! 🍀
"""
    await update.message.reply_text(help_text)
