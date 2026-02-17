import random
from datetime import datetime, time, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
import config
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()

    def get_random_publish_time(self) -> datetime:
        """Генерирует рандомное время публикации (9:00-21:00)"""
        today = datetime.now().date()

        # Рандомное время между start и end
        start_hour = config.PUBLISH_TIME_START
        end_hour = config.PUBLISH_TIME_END

        random_hour = random.randint(start_hour, end_hour - 1)
        random_minute = random.randint(0, 59)

        publish_time = datetime.combine(today, time(random_hour, random_minute))

        logger.info(f"Generated random publish time: {publish_time}")

        return publish_time

    async def publish_daily_question(self):
        """Публикация дневного вопроса в канале"""
        try:
            # Получаем случайный неиспользованный вопрос
            question = self.db.get_random_unused_question()

            if not question:
                logger.error("No unused questions available!")
                return

            # Формируем текст для канала
            message_text = f"""
❓ ВОПРОС ДНЯ

📚 Категория: {question['category']}

{question['question_text']}

А) {question['option_a']}
Б) {question['option_b']}
В) {question['option_c']}
Г) {question['option_d']}

💎 Правильный ответ: {config.POINTS_CORRECT} баллов
🏆 Топ-50: +{config.POINTS_TOP50} баллов
⚡️ Скорость (<{config.SPEED_LIMIT} сек): +{config.POINTS_SPEED} балла

Ответить ⬇️
"""

            # Кнопка "Ответить"
            keyboard = [[
                InlineKeyboardButton(
                    "🎯 Ответить",
                    url=f"t.me/{self.bot.username}?start=q{question['question_id']}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Публикуем в канале
            if question.get('image_url'):
                message = await self.bot.send_photo(
                    chat_id=config.CHANNEL_ID,
                    photo=question['image_url'],
                    caption=message_text,
                    reply_markup=reply_markup
                )
            else:
                message = await self.bot.send_message(
                    chat_id=config.CHANNEL_ID,
                    text=message_text,
                    reply_markup=reply_markup
                )

            # Сохраняем в БД
            publish_time = datetime.now()
            daily_question_id = self.db.create_daily_question(
                question_id=question['question_id'],
                publish_time=publish_time,
                channel_message_id=message.message_id
            )

            logger.info(f"Published question #{question['question_id']} at {publish_time}")

        except Exception as e:
            logger.error(f"Error publishing question: {e}")

    async def send_weekly_ratings(self):
        """Отправка еженедельного рейтинга всем пользователям"""
        try:
            # Получаем топ-10
            top_users = self.db.get_rating(limit=config.RATING_TOP_N)

            # Получаем всех активных пользователей
            all_users = self.db.get_all_active_users()

            logger.info(f"Sending weekly ratings to {len(all_users)} users...")

            medals = {1: "🥇", 2: "🥈", 3: "🥉"}

            for user_id in all_users:
                try:
                    # Формируем рейтинг
                    rating_text = f"🏆 РЕЙТИНГ НЕДЕЛИ\n\nТОП-{config.RATING_TOP_N}:\n\n"

                    for i, user in enumerate(top_users, 1):
                        medal = medals.get(i, f"{i}.")
                        name = user['first_name'] or user['username'] or "Аноним"
                        rating_text += f"{medal} {name} — {user['total_points']} баллов\n"

                    # Добавляем информацию о пользователе
                    user_data = self.db.get_user(user_id)
                    user_rank = self.db.get_user_rank(user_id)

                    rating_text += f"\n{'─' * 30}\n"
                    rating_text += f"📍 Ваше место: #{user_rank['rank']}\n"
                    rating_text += f"💎 Ваши баллы: {user_data['total_points']}\n"

                    if user_rank['rank'] > config.RATING_TOP_N:
                        rating_text += f"🎯 До топ-{config.RATING_TOP_N}: {user_rank['points_to_top10']} баллов\n"

                    rating_text += f"\nПродолжайте участвовать!\nСледите за каналом @{config.CHANNEL_USERNAME}"

                    # Отправляем
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=rating_text
                    )

                except Exception as e:
                    logger.warning(f"Failed to send rating to user {user_id}: {e}")
                    continue

            logger.info("Weekly ratings sent successfully!")

        except Exception as e:
            logger.error(f"Error sending weekly ratings: {e}")
