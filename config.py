import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

# Время публикации (9:00 - 21:00)
PUBLISH_TIME_START = 9
PUBLISH_TIME_END = 21

# Баллы
POINTS_CORRECT = 5          # За правильный ответ
POINTS_TOP50 = 5            # Бонус за топ-50
POINTS_SPEED = 2            # Бонус за скорость (<10 сек)
TOP50_LIMIT = 50            # Лимит топ-50
SPEED_LIMIT = 10            # Лимит скорости (секунды)

# База данных
DB_PATH = 'quiz.db'
EXCEL_PATH = 'questions.xlsx'

# Рейтинг
RATING_TOP_N = 10           # Топ-10
RATING_SEND_DAY = 6         # Воскресенье (0=понедельник, 6=воскресенье)
RATING_SEND_TIME = "20:00"  # Время отправки рейтинга
