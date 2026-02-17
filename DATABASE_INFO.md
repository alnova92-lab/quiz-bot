# База данных quiz.db

## 📊 Общая информация

**Тип:** SQLite
**Файл:** `quiz.db`
**Кодировка:** UTF-8
**Создание:** Автоматически при первом запуске

---

## 🔧 Создание базы данных

База данных создается **автоматически** несколькими способами:

### Способ 1: Явная инициализация (рекомендуется)

```bash
python init_database.py
```

✅ Создает пустую БД с таблицами
✅ Выводит информацию о созданных таблицах

### Способ 2: При импорте вопросов

```bash
python import_questions.py
```

✅ Создает БД, если её нет
✅ Сразу заполняет вопросами из Excel

### Способ 3: При запуске бота

```bash
python bot.py
```

✅ Создает БД при первом запуске
✅ Инициализирует все таблицы

---

## 📋 Структура таблиц

### 1. users (Пользователи)

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

**Назначение:** Хранит информацию о пользователях и их статистику

### 2. questions (Вопросы)

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

**Назначение:** Хранит базу вопросов для квиза

### 3. daily_questions (Дневные вопросы) ⭐

```sql
CREATE TABLE daily_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,                   -- ID вопроса
    publish_date DATE,                     -- ⭐ Дата публикации (без времени!)
    publish_time DATETIME,                 -- Точное время публикации
    channel_message_id INTEGER,            -- ID сообщения в канале
    total_answers INTEGER DEFAULT 0,       -- Всего ответов
    correct_answers INTEGER DEFAULT 0,     -- Правильных ответов
    top50_filled BOOLEAN DEFAULT FALSE,    -- Топ-50 заполнен?
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);
```

**Назначение:** Хранит опубликованные вопросы

**Важно:** `publish_date` — ключевое поле для механизма "1 день = 1 вопрос"!

### 4. answers (Ответы)

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

**Назначение:** Хранит все ответы пользователей с детальной информацией

### 5. weekly_ratings (Еженедельные рейтинги)

```sql
CREATE TABLE weekly_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE,                       -- Начало недели
    week_end DATE,                         -- Конец недели
    sent_date DATETIME,                    -- Когда отправлен
    is_sent BOOLEAN DEFAULT FALSE          -- Отправлен ли
);
```

**Назначение:** История отправок еженедельного рейтинга

---

## 🔑 Ключевые механизмы

### Механизм "1 день = 1 вопрос"

**Как работает:**

1. При публикации вопроса сохраняется `publish_date` (только дата, без времени)
2. Метод `get_today_question()` выполняет запрос:
   ```python
   SELECT * FROM daily_questions
   WHERE publish_date = date('now')
   ```
3. При наступлении **00:00** функция `date('now')` возвращает новую дату
4. SQL автоматически возвращает новый вопрос (или NULL, если не опубликован)

**Результат:** Старый вопрос автоматически становится неактивным!

### Система баллов

```python
points = 5  # Базовые баллы

# Бонус за топ-50
if answer_position <= 50:
    points += 5

# Бонус за скорость
if time_from_publish <= 10:
    points += 2

# Максимум: 12 баллов (5 + 5 + 2)
```

---

## 📊 Примеры запросов

### Получить топ-10 игроков

```sql
SELECT user_id, username, first_name, total_points, correct_answers
FROM users
WHERE is_active = TRUE AND total_points > 0
ORDER BY total_points DESC, correct_answers DESC
LIMIT 10;
```

### Получить статистику по сегодняшнему вопросу

```sql
SELECT
    dq.total_answers,
    dq.correct_answers,
    ROUND(dq.correct_answers * 100.0 / dq.total_answers, 1) as accuracy
FROM daily_questions dq
WHERE dq.publish_date = date('now');
```

### Получить все ответы пользователя

```sql
SELECT
    a.answer_time,
    q.question_text,
    a.user_answer,
    a.is_correct,
    a.points_earned
FROM answers a
JOIN daily_questions dq ON a.daily_question_id = dq.id
JOIN questions q ON dq.question_id = q.question_id
WHERE a.user_id = ?
ORDER BY a.answer_time DESC;
```

### Проверить, отвечал ли пользователь сегодня

```sql
SELECT COUNT(*) FROM answers a
JOIN daily_questions dq ON a.daily_question_id = dq.id
WHERE a.user_id = ? AND dq.publish_date = date('now');
```

---

## 💾 Резервное копирование

### Ручное копирование

```bash
# Windows
copy quiz.db quiz_backup_2024-02-10.db

# Linux/Mac
cp quiz.db quiz_backup_2024-02-10.db
```

### Экспорт в SQL

```bash
sqlite3 quiz.db .dump > quiz_backup.sql
```

### Восстановление

```bash
sqlite3 quiz_new.db < quiz_backup.sql
```

---

## 🔍 Просмотр базы данных

### Через SQLite командную строку

```bash
sqlite3 quiz.db

# Просмотр таблиц
.tables

# Просмотр структуры
.schema users

# Выполнение запроса
SELECT * FROM users LIMIT 5;

# Выход
.quit
```

### Через GUI-программы

- **DB Browser for SQLite** (рекомендуется)
  - Скачать: https://sqlitebrowser.org/
  - Бесплатная, кроссплатформенная

- **DBeaver** (универсальная)
  - Скачать: https://dbeaver.io/
  - Поддержка многих СУБД

- **SQLiteStudio**
  - Скачать: https://sqlitestudio.pl/
  - Легкая и простая

---

## 🛡️ Безопасность

### Защита от SQL-инъекций

Все запросы используют **параметризированные запросы**:

```python
# ✅ Правильно
cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))

# ❌ Неправильно (уязвимо к SQL-инъекциям!)
cursor.execute(f'SELECT * FROM users WHERE user_id = {user_id}')
```

### Права доступа

База данных хранится локально. Права доступа:
- **Чтение:** только бот и администратор системы
- **Запись:** только бот

---

## 📈 Мониторинг

### Размер базы данных

```bash
# Windows
dir quiz.db

# Linux/Mac
ls -lh quiz.db
```

### Количество записей

```python
# analytics.py
import sqlite3

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()

print("Статистика базы данных:")
cursor.execute('SELECT COUNT(*) FROM users')
print(f"Пользователей: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM questions')
print(f"Вопросов: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM answers')
print(f"Ответов: {cursor.fetchone()[0]}")

conn.close()
```

---

## ❓ FAQ

### База данных не создается?

**Решение:**
```bash
python init_database.py
```

### Ошибка "database is locked"?

**Причина:** База данных уже открыта в другом процессе

**Решение:**
1. Закройте все программы, использующие quiz.db
2. Перезапустите бота

### Как очистить базу данных?

**Вариант 1:** Удалить файл
```bash
del quiz.db
python init_database.py
```

**Вариант 2:** Очистить таблицы
```sql
DELETE FROM answers;
DELETE FROM daily_questions;
DELETE FROM users;
UPDATE questions SET is_used = FALSE, usage_date = NULL;
```

### Как перенести базу на другой сервер?

1. Остановите бота
2. Скопируйте `quiz.db` на новый сервер
3. Запустите бота на новом сервере

---

## 📖 Дополнительная информация

- [README.md](README.md) - основная документация
- [DAILY_LOGIC.md](DAILY_LOGIC.md) - механизм "1 день = 1 вопрос"
- [database.py](database.py) - исходный код работы с БД

---

**Важно:** База данных создается автоматически. Не нужно создавать её вручную через SQLite!
