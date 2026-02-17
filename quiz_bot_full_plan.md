# ПЛАН РЕАЛИЗАЦИИ БОТА-КВИЗА "ОБЛАСТНАЯ ГАЗЕТА"
## Полное техническое задание и реализация

---

## 📋 ТЕХНИЧЕСКОЕ ЗАДАНИЕ (уточнённое)

### **МЕХАНИКА РАБОТЫ**

**Публикация вопросов:**
- ✅ 1 вопрос в день
- ✅ Рандомное время публикации: 9:00 - 21:00
- ✅ Публикация в Telegram-канале "Областная газета"

**Процесс ответа:**
```
1. Пост появляется в канале
2. Кнопка "Ответить" в посте
3. Переход в бота @oblastnaya_quiz_bot
4. Кнопка "Ответить на вопрос"
5. Появляется вопрос с 4 вариантами (А/Б/В/Г)
6. Пользователь выбирает ответ
7. Бот показывает результат
```

**Система баллов:**
```
Базовые баллы: 5 баллов (за правильный ответ)

Бонусы (стакаются):
• Топ-50 (первые 50 правильных ответов): +5 баллов
• Скорость (<10 сек от появления вопроса): +2 балла

Примеры:
→ Ответил правильно, №23, за 7 сек = 5 + 5 + 2 = 12 баллов ✅
→ Ответил правильно, №23, за 15 сек = 5 + 5 = 10 баллов
→ Ответил правильно, №67, за 8 сек = 5 + 2 = 7 баллов
→ Ответил правильно, №67, за 15 сек = 5 баллов
→ Ответил неправильно = 0 баллов

ВАЖНО: После того как первые 50 человек ответили правильно,
бонус за топ-50 больше не начисляется. Остаётся только:
• 5 баллов за правильный ответ
• +2 за скорость (<10 сек)
```

**Рейтинг:**
- ✅ Топ-10 игроков
- ✅ Отправляется 1 раз в неделю в личку каждому пользователю
- ✅ Формат: Топ-10 + место пользователя + до топ-10

**База вопросов:**
- ✅ Таблица (Excel/Google Sheets)
- ✅ Редактируемая вручную
- ✅ Поля: Категория, Вопрос, Варианты A/Б/В/Г, Правильный ответ, Объяснение
- ✅ Категория отображается в боте

**Хостинг:**
- ✅ Обычный компьютер (Windows/Mac/Linux)
- ✅ Должен быть включён 24/7

---

## 🏗 АРХИТЕКТУРА СИСТЕМЫ

```
┌─────────────────────────────────────────────────────────┐
│                    ВАША СИСТЕМА                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐      ┌─────────────────────┐   │
│  │  questions.xlsx  │─────▶│   Python Script     │   │
│  │  (База вопросов) │      │   (Импорт в БД)     │   │
│  └──────────────────┘      └─────────────────────┘   │
│                                    │                   │
│                                    ▼                   │
│  ┌──────────────────────────────────────────────┐    │
│  │        База данных (SQLite)                  │    │
│  │  • users (пользователи)                      │    │
│  │  • questions (вопросы)                       │    │
│  │  • answers (ответы с временем)               │    │
│  │  • daily_questions (активные вопросы)        │    │
│  └──────────────────────────────────────────────┘    │
│                      ▲          ▲                      │
│                      │          │                      │
│  ┌─────────────────┴──────────┴────────────────┐    │
│  │         Telegram Bot (Python)                 │    │
│  │  • Обработка команд                           │    │
│  │  • Проверка ответов                           │    │
│  │  • Начисление баллов                          │    │
│  │  • Рейтинг                                    │    │
│  └───────────────────────────────────────────────┘    │
│                      ▲                                 │
│                      │                                 │
│  ┌─────────────────┴─────────────────────────────┐   │
│  │       Scheduler (Планировщик)                  │   │
│  │  • Генерирует рандомное время (9-21)           │   │
│  │  • Публикует вопрос в канал                    │   │
│  │  • Еженедельная рассылка рейтинга              │   │
│  └────────────────────────────────────────────────┘   │
│                      │                                 │
└──────────────────────┼─────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Telegram API               │
        │  • Канал "Областная газета"  │
        │  • Бот @oblastnaya_quiz_bot  │
        └──────────────────────────────┘
```

---

## 📊 СТРУКТУРА БАЗЫ ДАННЫХ

### **Таблица 1: users**
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,           -- Telegram ID
    username TEXT,                         -- @username
    first_name TEXT,                       -- Имя
    registration_date DATETIME,            -- Дата регистрации
    total_points INTEGER DEFAULT 0,        -- Всего баллов
    correct_answers INTEGER DEFAULT 0,     -- Правильных ответов
    total_answers INTEGER DEFAULT 0,       -- Всего ответов
    is_active BOOLEAN DEFAULT TRUE         -- Активен ли
);
```

### **Таблица 2: questions**
```sql
CREATE TABLE questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,                -- Категория (История, География...)
    question_text TEXT NOT NULL,           -- Текст вопроса
    option_a TEXT NOT NULL,                -- Вариант А
    option_b TEXT NOT NULL,                -- Вариант Б
    option_c TEXT NOT NULL,                -- Вариант В
    option_d TEXT NOT NULL,                -- Вариант Г
    correct_option TEXT NOT NULL,          -- Правильный (A/B/C/D)
    explanation TEXT,                      -- Объяснение ответа
    image_url TEXT,                        -- Картинка (опционально)
    is_used BOOLEAN DEFAULT FALSE,         -- Уже использовался?
    usage_date DATE                        -- Когда использовался
);
```

### **Таблица 3: daily_questions**
```sql
CREATE TABLE daily_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,                   -- ID вопроса
    publish_date DATE,                     -- Дата публикации
    publish_time DATETIME,                 -- Точное время публикации
    channel_message_id INTEGER,            -- ID сообщения в канале
    total_answers INTEGER DEFAULT 0,       -- Всего ответов
    correct_answers INTEGER DEFAULT 0,     -- Правильных ответов
    top50_filled BOOLEAN DEFAULT FALSE,    -- Топ-50 заполнен?
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);
```

### **Таблица 4: answers**
```sql
CREATE TABLE answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,                       -- ID пользователя
    daily_question_id INTEGER,             -- ID дневного вопроса
    user_answer TEXT,                      -- Ответ (A/B/C/D)
    is_correct BOOLEAN,                    -- Правильно?
    points_earned INTEGER,                 -- Заработано баллов
    answer_time DATETIME,                  -- Время ответа
    time_from_publish INTEGER,             -- Секунд от публикации
    answer_position INTEGER,               -- Позиция ответа (1,2,3...)
    got_top50_bonus BOOLEAN DEFAULT FALSE, -- Получил бонус топ-50?
    got_speed_bonus BOOLEAN DEFAULT FALSE, -- Получил бонус скорости?
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (daily_question_id) REFERENCES daily_questions(id)
);
```

### **Таблица 5: weekly_ratings**
```sql
CREATE TABLE weekly_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE,                       -- Начало недели
    week_end DATE,                         -- Конец недели
    sent_date DATETIME,                    -- Когда отправлен
    is_sent BOOLEAN DEFAULT FALSE          -- Отправлен ли
);
```

---

## 🗂 СТРУКТУРА EXCEL-ТАБЛИЦЫ

**Файл: `questions.xlsx`**

| Категория | Вопрос | Вариант А | Вариант Б | Вариант В | Вариант Г | Правильный | Объяснение | Картинка (URL) |
|-----------|--------|-----------|-----------|-----------|-----------|------------|------------|----------------|
| История | В каком году основан Иркутск? | 1651 | 1661 | 1671 | 1681 | Б | Иркутский острог основан в 1661 году | https://... |
| География | Какова глубина Байкала? | 1187 м | 1442 м | 1642 м | 1867 м | В | Максимальная глубина — 1642 метра | |
| Культура | Кто написал "Прощание с Матёрой"? | Астафьев | Распутин | Шукшин | Белов | Б | Валентин Распутин — иркутский писатель | |

**Скрипт импорта:**
```python
# import_questions.py
import pandas as pd
from database import Database

db = Database('quiz.db')

# Читаем Excel
df = pd.read_excel('questions.xlsx')

# Импортируем в БД
for _, row in df.iterrows():
    db.add_question(
        category=row['Категория'],
        question_text=row['Вопрос'],
        option_a=row['Вариант А'],
        option_b=row['Вариант Б'],
        option_c=row['Вариант В'],
        option_d=row['Вариант Г'],
        correct_option=row['Правильный'],
        explanation=row['Объяснение'],
        image_url=row.get('Картинка (URL)', None)
    )

print(f"Импортировано {len(df)} вопросов!")
```

---

## 💻 КОД БОТА

### **Структура проекта:**
```
oblastnaya_quiz_bot/
├── bot.py                  # Главный файл
├── database.py             # Работа с БД
├── scheduler.py            # Планировщик
├── config.py               # Настройки
├── handlers.py             # Обработчики команд
├── quiz_logic.py           # Логика квиза
├── import_questions.py     # Импорт из Excel
├── questions.xlsx          # База вопросов
├── quiz.db                 # SQLite база
├── requirements.txt        # Зависимости
└── .env                    # Секретные ключи
```

---

### **1. requirements.txt**
```txt
python-telegram-bot==21.9
APScheduler==3.10.4
python-dotenv==1.0.0
pandas==2.2.0
openpyxl==3.1.2
```

---

### **2. .env**
```env
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
CHANNEL_ID=@oblastnaya  # или -100xxxxxxxxxx
CHANNEL_USERNAME=oblastnaya
```

---

### **3. config.py**
```python
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
```

---

### **4. database.py**
```python
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
```

---

### **5. quiz_logic.py**
```python
from datetime import datetime
from database import Database
import config

class QuizLogic:
    def __init__(self, db: Database):
        self.db = db
        self.active_sessions = {}  # {user_id: daily_question_id}
    
    def start_quiz_for_user(self, user_id: int) -> dict:
        """Начать квиз для пользователя"""
        # Проверяем, не отвечал ли уже
        if self.db.check_user_answered_today(user_id):
            return {
                'status': 'already_answered',
                'message': '✅ Вы уже ответили на сегодняшний вопрос!\n\nСледующий вопрос появится завтра.'
            }
        
        # Получаем сегодняшний вопрос
        question = self.db.get_today_question()
        
        if not question:
            return {
                'status': 'no_question',
                'message': '😔 Сегодняшний вопрос ещё не опубликован.\n\nСледите за каналом @' + config.CHANNEL_USERNAME
            }
        
        # Сохраняем сессию
        self.active_sessions[user_id] = question['id']
        
        return {
            'status': 'success',
            'question': question
        }
    
    def check_answer(self, user_id: int, user_answer: str) -> dict:
        """Проверка ответа"""
        if user_id not in self.active_sessions:
            return {
                'status': 'no_session',
                'message': '❌ Сначала нажмите "Ответить на вопрос"'
            }
        
        daily_question_id = self.active_sessions[user_id]
        question = self.db.get_today_question()
        
        if not question:
            return {
                'status': 'error',
                'message': '❌ Произошла ошибка. Попробуйте позже.'
            }
        
        # Проверяем правильность
        is_correct = (user_answer.upper() == question['correct_option'].upper())
        
        # Считаем время от публикации
        publish_time = datetime.fromisoformat(question['publish_time'])
        time_diff = int((datetime.now() - publish_time).total_seconds())
        
        # Считаем баллы
        points = 0
        got_top50 = False
        got_speed = False
        answer_position = 0
        bonus_text = []
        
        if is_correct:
            points = config.POINTS_CORRECT
            bonus_text.append(f"✅ Правильно: +{config.POINTS_CORRECT} баллов")
            
            # Позиция ответа
            answer_position = self.db.get_correct_answers_count(daily_question_id) + 1
            
            # Бонус за топ-50
            if answer_position <= config.TOP50_LIMIT:
                points += config.POINTS_TOP50
                got_top50 = True
                bonus_text.append(f"🏆 Топ-50 (#{answer_position}): +{config.POINTS_TOP50} баллов")
            
            # Бонус за скорость
            if time_diff <= config.SPEED_LIMIT:
                points += config.POINTS_SPEED
                got_speed = True
                bonus_text.append(f"⚡️ Скорость ({time_diff} сек): +{config.POINTS_SPEED} балла")
        
        # Сохраняем ответ
        self.db.save_answer(
            user_id=user_id,
            daily_question_id=daily_question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            points_earned=points,
            time_from_publish=time_diff,
            answer_position=answer_position,
            got_top50=got_top50,
            got_speed=got_speed
        )
        
        # Удаляем сессию
        del self.active_sessions[user_id]
        
        # Получаем обновлённые данные пользователя
        user_data = self.db.get_user(user_id)
        user_rank = self.db.get_user_rank(user_id)
        
        return {
            'status': 'answered',
            'is_correct': is_correct,
            'points_earned': points,
            'bonus_text': bonus_text,
            'explanation': question.get('explanation', ''),
            'correct_answer': question['correct_option'],
            'user_stats': user_data,
            'user_rank': user_rank
        }
```

---

### **6. handlers.py**
```python
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
    
    result = quiz.check_answer(user_id, user_answer)
    
    if result['status'] != 'answered':
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
```

---

# ПЛАН РЕАЛИЗАЦИИ БОТА-КВИЗА (ПРОДОЛЖЕНИЕ)

## 💻 КОД БОТА (продолжение)

### **7. scheduler.py** (Планировщик публикаций)
```python
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
```

---

### **8. bot.py** (Главный файл)
```python
import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
```

---

### **9. import_questions.py** (Импорт из Excel)
```python
import pandas as pd
from database import Database

def import_questions_from_excel(filepath: str):
    """Импорт вопросов из Excel в БД"""
    
    db = Database()
    
    # Читаем Excel
    df = pd.read_excel(filepath)
    
    print(f"Найдено {len(df)} вопросов в файле {filepath}")
    
    # Проверяем наличие необходимых колонок
    required_columns = [
        'Категория', 'Вопрос', 'Вариант А', 'Вариант Б', 
        'Вариант В', 'Вариант Г', 'Правильный', 'Объяснение'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Ошибка: отсутствуют колонки: {missing_columns}")
        return
    
    # Импортируем в БД
    imported = 0
    for index, row in df.iterrows():
        try:
            db.add_question(
                category=str(row['Категория']),
                question_text=str(row['Вопрос']),
                option_a=str(row['Вариант А']),
                option_b=str(row['Вариант Б']),
                option_c=str(row['Вариант В']),
                option_d=str(row['Вариант Г']),
                correct_option=str(row['Правильный']).upper(),
                explanation=str(row['Объяснение']) if pd.notna(row['Объяснение']) else None,
                image_url=str(row['Картинка (URL)']) if 'Картинка (URL)' in df.columns and pd.notna(row['Картинка (URL)']) else None
            )
            imported += 1
        except Exception as e:
            print(f"❌ Ошибка в строке {index + 2}: {e}")
            continue
    
    print(f"✅ Успешно импортировано {imported} из {len(df)} вопросов!")

if __name__ == '__main__':
    import_questions_from_excel('questions.xlsx')
```

---

## 🚀 ИНСТРУКЦИЯ ПО ЗАПУСКУ

### **ШАГ 1: Установка Python**

**Windows:**
1. Скачайте Python 3.10+ с [python.org](https://www.python.org/downloads/)
2. При установке поставьте галочку "Add Python to PATH"
3. Проверьте установку: откройте CMD и введите `python --version`

**Mac:**
```bash
# Установка через Homebrew
brew install python@3.10
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3-pip
```

---

### **ШАГ 2: Создание бота в Telegram**

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Введите название: `Областная Квиз`
4. Введите username: `oblastnaya_quiz_bot` (или другой доступный)
5. Скопируйте полученный **Token**

**Получение ID канала:**
```
Вариант 1: Если канал публичный
→ CHANNEL_ID = @oblastnaya

Вариант 2: Если канал приватный
1. Добавьте бота в канал как администратора
2. Отправьте любое сообщение в канал
3. Откройте: https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
4. Найдите "chat":{"id":-100xxxxxxxxx}
5. CHANNEL_ID = -100xxxxxxxxx
```

---

### **ШАГ 3: Подготовка проекта**

1. Создайте папку для проекта:
```bash
mkdir oblastnaya_quiz_bot
cd oblastnaya_quiz_bot
```

2. Скопируйте все файлы из моего плана в эту папку:
```
oblastnaya_quiz_bot/
├── bot.py
├── database.py
├── scheduler.py
├── config.py
├── handlers.py
├── quiz_logic.py
├── import_questions.py
├── requirements.txt
└── .env (создайте)
```

3. Создайте файл `.env`:
```env
BOT_TOKEN=YOUR_TOKEN_HERE
CHANNEL_ID=@oblastnaya
CHANNEL_USERNAME=oblastnaya
```

---

### **ШАГ 4: Установка зависимостей**

Откройте терминал/командную строку в папке проекта:

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

---

### **ШАГ 5: Подготовка вопросов**

1. Создайте файл `questions.xlsx` в Excel/Google Sheets
2. Заполните по шаблону (см. выше)
3. Сохраните в папку проекта

4. Импортируйте вопросы в БД:
```bash
python import_questions.py
```

Должно появиться:
```
Найдено 50 вопросов в файле questions.xlsx
✅ Успешно импортировано 50 из 50 вопросов!
```

---

### **ШАГ 6: Настройка бота в канале**

1. Добавьте бота в канал как **администратора**
2. Дайте права:
   - ✅ Публикация сообщений
   - ✅ Редактирование сообщений
3. Проверьте, что бот может писать в канал

---

### **ШАГ 7: Запуск бота**

```bash
python bot.py
```

Должно появиться:
```
2025-02-10 15:30:00 - __main__ - INFO - Starting bot...
2025-02-10 15:30:01 - __main__ - INFO - Bot started successfully!
2025-02-10 15:30:01 - scheduler - INFO - Next question scheduled for 2025-02-10 18:23:00
```

**Бот запущен!** 🎉

---

### **ШАГ 8: Тестирование**

1. Откройте бота в Telegram: `@oblastnaya_quiz_bot`
2. Отправьте `/start`
3. Проверьте, что бот отвечает
4. Отправьте `/help`
5. Дождитесь публикации вопроса в канале (или запустите вручную для теста)

**Ручной запуск вопроса для теста:**
```python
# test_publish.py
import asyncio
from telegram import Bot
from scheduler import Scheduler
from config import BOT_TOKEN

async def test():
    bot = Bot(token=BOT_TOKEN)
    scheduler = Scheduler(bot)
    await scheduler.publish_daily_question()
    print("Тестовый вопрос опубликован!")

asyncio.run(test())
```

```bash
python test_publish.py
```

---

## 🔧 НАСТРОЙКА АВТОЗАПУСКА

Чтобы бот работал постоянно, настройте автозапуск:

### **Windows (Task Scheduler)**

1. Откройте "Планировщик заданий"
2. Создать задачу → Общие:
   - Имя: `Oblastnaya Quiz Bot`
   - Выполнять вне зависимости от регистрации
3. Триггеры → Новый:
   - При запуске компьютера
4. Действия → Новый:
   - Программа: `C:\путь\к\venv\Scripts\python.exe`
   - Аргументы: `bot.py`
   - Рабочая папка: `C:\путь\к\oblastnaya_quiz_bot`
5. Условия:
   - Снять "Запускать только при питании от электросети"
6. ОК

### **Mac (launchd)**

Создайте файл `~/Library/LaunchAgents/com.oblastnaya.quizbot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oblastnaya.quizbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/путь/к/venv/bin/python</string>
        <string>/путь/к/bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/путь/к/oblastnaya_quiz_bot</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Загрузите:
```bash
launchctl load ~/Library/LaunchAgents/com.oblastnaya.quizbot.plist
```

### **Linux (systemd)**

Создайте файл `/etc/systemd/system/quizbot.service`:

```ini
[Unit]
Description=Oblastnaya Quiz Bot
After=network.target

[Service]
Type=simple
User=ваш_username
WorkingDirectory=/home/ваш_username/oblastnaya_quiz_bot
ExecStart=/home/ваш_username/oblastnaya_quiz_bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запустите:
```bash
sudo systemctl daemon-reload
sudo systemctl enable quizbot
sudo systemctl start quizbot
```

---

## 📊 МОНИТОРИНГ И ЛОГИ

### **Просмотр логов**

Логи выводятся в консоль. Для сохранения в файл:

```bash
# Запуск с логированием в файл
python bot.py > bot.log 2>&1
```

### **Проверка статуса**

```bash
# Linux
sudo systemctl status quizbot

# Логи
tail -f bot.log
```

---

## 🔄 ОБНОВЛЕНИЕ ВОПРОСОВ

Когда нужно добавить новые вопросы:

1. Откройте `questions.xlsx`
2. Добавьте новые строки
3. Сохраните
4. Импортируйте:
```bash
python import_questions.py
```

**Вопросы добавятся в базу, не удаляя старые!**

---

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### **Бот не запускается**
```bash
# Проверьте токен
python -c "from config import BOT_TOKEN; print(BOT_TOKEN)"

# Проверьте зависимости
pip install -r requirements.txt --upgrade
```

### **Вопросы не публикуются**
```bash
# Проверьте, что бот админ в канале
# Проверьте CHANNEL_ID в .env
# Посмотрите логи на ошибки
```

### **Рейтинг не отправляется**
```bash
# Проверьте день и время в config.py
# RATING_SEND_DAY = 6 (воскресенье)
# RATING_SEND_TIME = "20:00"
```

---

## 📈 МЕТРИКИ ДЛЯ ОТСЛЕЖИВАНИЯ

**Ежедневно:**
- Сколько человек ответило на вопрос
- Процент правильных ответов
- Средняя скорость ответа

**Еженедельно:**
- Прирост пользователей
- Вовлечённость (retention)
- Топ-10 игроков

**SQL-запросы для статистики:**

```python
# analytics.py
import sqlite3

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()

# Статистика по последнему вопросу
cursor.execute('''
    SELECT 
        total_answers,
        correct_answers,
        ROUND(correct_answers * 100.0 / total_answers, 1) as accuracy
    FROM daily_questions
    ORDER BY publish_date DESC
    LIMIT 1
''')

stats = cursor.fetchone()
print(f"Всего ответов: {stats[0]}")
print(f"Правильных: {stats[1]}")
print(f"Точность: {stats[2]}%")

conn.close()
```

---

## ✅ ИТОГОВЫЙ ЧЕКЛИСТ

- [ ] Python 3.10+ установлен
- [ ] Создан бот через @BotFather
- [ ] Получен токен и ID канала
- [ ] Создана папка проекта
- [ ] Скопированы все файлы
- [ ] Создан .env с токеном
- [ ] Установлены зависимости (pip install -r requirements.txt)
- [ ] Создан questions.xlsx
- [ ] Импортированы вопросы (python import_questions.py)
- [ ] Бот добавлен в канал как админ
- [ ] Бот запущен (python bot.py)
- [ ] Протестирован (отправлены команды)
- [ ] Настроен автозапуск
- [ ] Создан backup-план (копии БД)

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

**Через 1 неделю:**
- 100-200 участников
- 5-7 опубликованных вопросов
- Первый рейтинг отправлен

**Через 1 месяц:**
- 500-1000 участников
- 30 вопросов опубликовано
- Стабильная активность

**Через 3 месяца:**
- 2000+ участников
- 90 вопросов
- Сформированное комьюнити

---

## 💰 ЗАТРАТЫ

**Минимальные (ваш компьютер):**
- 0₽ в месяц (электричество ~50-100₽)

**При переносе на VPS:**
- 249-500₽/месяц

---

## 🚀 ГОТОВО К ЗАПУСКУ!

Теперь у вас есть:
1. ✅ Полный код бота
2. ✅ Структура БД
3. ✅ Система импорта вопросов
4. ✅ Планировщик публикаций
5. ✅ Рейтинговая система
6. ✅ Инструкция по запуску

**Начинайте с малого:**
- 50-100 вопросов для старта
- Тестовый период 1-2 недели
- Соберите обратную связь
- Масштабируйте!

Удачи! 🍀
