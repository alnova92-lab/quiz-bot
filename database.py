import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict
import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registration_date DATETIME,
                total_points INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                total_answers INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Таблица вопросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                explanation TEXT,
                image_url TEXT,
                is_used BOOLEAN DEFAULT FALSE,
                usage_date DATE
            )
        ''')

        # Таблица дневных вопросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                publish_date DATE,
                publish_time DATETIME,
                channel_message_id INTEGER,
                total_answers INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                top50_filled BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (question_id) REFERENCES questions(question_id)
            )
        ''')

        # Таблица ответов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                daily_question_id INTEGER,
                user_answer TEXT,
                is_correct BOOLEAN,
                points_earned INTEGER,
                answer_time DATETIME,
                time_from_publish INTEGER,
                answer_position INTEGER,
                got_top50_bonus BOOLEAN DEFAULT FALSE,
                got_speed_bonus BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (daily_question_id) REFERENCES daily_questions(id)
            )
        ''')

        # Таблица рейтингов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start DATE,
                week_end DATE,
                sent_date DATETIME,
                is_sent BOOLEAN DEFAULT FALSE
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str, first_name: str):
        """Регистрация пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, registration_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now()))

        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def add_question(self, category: str, question_text: str,
                    option_a: str, option_b: str, option_c: str, option_d: str,
                    correct_option: str, explanation: str = None,
                    image_url: str = None):
        """Добавление вопроса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO questions
            (category, question_text, option_a, option_b, option_c, option_d,
             correct_option, explanation, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category, question_text, option_a, option_b, option_c, option_d,
              correct_option, explanation, image_url))

        conn.commit()
        conn.close()

    def get_random_unused_question(self) -> Optional[Dict]:
        """Получить случайный неиспользованный вопрос"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM questions
            WHERE is_used = FALSE
            ORDER BY RANDOM()
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_daily_question(self, question_id: int,
                              publish_time: datetime,
                              channel_message_id: int) -> int:
        """Создать дневной вопрос"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO daily_questions
            (question_id, publish_date, publish_time, channel_message_id)
            VALUES (?, ?, ?, ?)
        ''', (question_id, publish_time.date(), publish_time, channel_message_id))

        daily_question_id = cursor.lastrowid

        # Помечаем вопрос как использованный
        cursor.execute('''
            UPDATE questions
            SET is_used = TRUE, usage_date = ?
            WHERE question_id = ?
        ''', (publish_time.date(), question_id))

        conn.commit()
        conn.close()

        return daily_question_id

    def get_today_question(self) -> Optional[Dict]:
        """Получить сегодняшний вопрос"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        today = date.today()

        cursor.execute('''
            SELECT dq.*, q.*
            FROM daily_questions dq
            JOIN questions q ON dq.question_id = q.question_id
            WHERE dq.publish_date = ?
        ''', (today,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def check_user_answered_today(self, user_id: int) -> bool:
        """Проверить, отвечал ли пользователь сегодня"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = date.today()

        cursor.execute('''
            SELECT COUNT(*) FROM answers a
            JOIN daily_questions dq ON a.daily_question_id = dq.id
            WHERE a.user_id = ? AND dq.publish_date = ?
        ''', (user_id, today))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def save_answer(self, user_id: int, daily_question_id: int,
                   user_answer: str, is_correct: bool, points_earned: int,
                   time_from_publish: int, answer_position: int,
                   got_top50: bool, got_speed: bool):
        """Сохранить ответ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Сохраняем ответ
        cursor.execute('''
            INSERT INTO answers
            (user_id, daily_question_id, user_answer, is_correct,
             points_earned, answer_time, time_from_publish, answer_position,
             got_top50_bonus, got_speed_bonus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, daily_question_id, user_answer, is_correct,
              points_earned, datetime.now(), time_from_publish, answer_position,
              got_top50, got_speed))

        # Обновляем статистику пользователя
        if is_correct:
            cursor.execute('''
                UPDATE users
                SET total_points = total_points + ?,
                    correct_answers = correct_answers + 1,
                    total_answers = total_answers + 1
                WHERE user_id = ?
            ''', (points_earned, user_id))
        else:
            cursor.execute('''
                UPDATE users
                SET total_answers = total_answers + 1
                WHERE user_id = ?
            ''', (user_id,))

        # Обновляем статистику вопроса
        cursor.execute('''
            UPDATE daily_questions
            SET total_answers = total_answers + 1,
                correct_answers = correct_answers + ?
            WHERE id = ?
        ''', (1 if is_correct else 0, daily_question_id))

        conn.commit()
        conn.close()

    def get_correct_answers_count(self, daily_question_id: int) -> int:
        """Получить количество правильных ответов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM answers
            WHERE daily_question_id = ? AND is_correct = TRUE
        ''', (daily_question_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count

    def is_top50_filled(self, daily_question_id: int) -> bool:
        """Заполнен ли топ-50"""
        return self.get_correct_answers_count(daily_question_id) >= config.TOP50_LIMIT

    def get_rating(self, limit: int = config.RATING_TOP_N) -> List[Dict]:
        """Получить рейтинг"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, first_name, total_points,
                   correct_answers
            FROM users
            WHERE is_active = TRUE AND total_points > 0
            ORDER BY total_points DESC, correct_answers DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_user_rank(self, user_id: int) -> Dict:
        """Получить позицию пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Позиция
        cursor.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM users
            WHERE total_points > (
                SELECT total_points FROM users WHERE user_id = ?
            )
        ''', (user_id,))
        rank = cursor.fetchone()[0]

        # Баллы пользователя
        cursor.execute('''
            SELECT total_points FROM users WHERE user_id = ?
        ''', (user_id,))
        user_points = cursor.fetchone()[0]

        # Баллы 10-го места
        cursor.execute('''
            SELECT total_points FROM users
            WHERE total_points > 0
            ORDER BY total_points DESC
            LIMIT 1 OFFSET 9
        ''')
        row = cursor.fetchone()
        top10_points = row[0] if row else 0

        conn.close()

        points_to_top10 = max(0, top10_points - user_points + 1)

        return {
            'rank': rank,
            'points': user_points,
            'points_to_top10': points_to_top10
        }

    def get_all_active_users(self) -> List[int]:
        """Получить всех активных пользователей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id FROM users WHERE is_active = TRUE
        ''')

        user_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return user_ids
