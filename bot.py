import logging
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from database import Database
from scheduler import Scheduler
from handlers import (
    start,
    answer_question_callback,
    answer_callback,
    rating_command,
    stats_command,
    help_command
)
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация БД
db = Database()

async def schedule_daily_question(context: ContextTypes.DEFAULT_TYPE):
    """Планирование дневного вопроса"""
    scheduler = Scheduler(context.bot)

    # Генерируем рандомное время на следующий день
    random_time = scheduler.get_random_publish_time()

    # Планируем публикацию
    context.job_queue.run_once(
        publish_question_job,
        when=random_time,
        name='daily_question'
    )

    logger.info(f"Next question scheduled for {random_time}")

async def publish_question_job(context: ContextTypes.DEFAULT_TYPE):
    """Job для публикации вопроса"""
    scheduler = Scheduler(context.bot)
    await scheduler.publish_daily_question()

    # Планируем следующий вопрос на следующий день
    await schedule_daily_question(context)

async def send_weekly_ratings_job(context: ContextTypes.DEFAULT_TYPE):
    """Job для отправки рейтинга"""
    scheduler = Scheduler(context.bot)
    await scheduler.send_weekly_ratings()

def main():
    """Запуск бота"""
    logger.info("Starting bot...")

    # Создаём приложение
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rating", rating_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчики callback-кнопок
    application.add_handler(CallbackQueryHandler(
        answer_question_callback,
        pattern="^show_question$"
    ))
    application.add_handler(CallbackQueryHandler(
        answer_callback,
        pattern="^answer_"
    ))

    # Планировщик заданий
    job_queue = application.job_queue

    # Запланировать первый вопрос на сегодня (или завтра, если уже поздно)
    now = datetime.now()
    if now.hour < config.PUBLISH_TIME_END:
        # Сегодня ещё можно опубликовать
        job_queue.run_once(
            schedule_daily_question,
            when=1  # Через 1 секунду после запуска
        )
    else:
        # Уже поздно, планируем на завтра
        tomorrow = now.replace(hour=9, minute=0, second=0) + timedelta(days=1)
        job_queue.run_once(
            schedule_daily_question,
            when=tomorrow
        )

    # Еженедельная рассылка рейтинга (каждое воскресенье в 20:00)
    rating_time = time(hour=20, minute=0)
    job_queue.run_daily(
        send_weekly_ratings_job,
        time=rating_time,
        days=(config.RATING_SEND_DAY,)  # 6 = воскресенье
    )

    logger.info("Bot started successfully!")

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
