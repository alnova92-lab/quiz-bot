# Логика "1 день = 1 вопрос"

## Как это работает

### Основной принцип

Бот обеспечивает, что:
- **В каждый день активен только ОДИН вопрос**
- **При наступлении 00:00 старый вопрос автоматически становится неактивным**
- **Новый вопрос становится активным после публикации**

---

## Реализация

### 1. База данных (database.py)

#### Таблица `daily_questions`
```sql
CREATE TABLE daily_questions (
    id INTEGER PRIMARY KEY,
    question_id INTEGER,
    publish_date DATE,           -- ← Ключевое поле!
    publish_time DATETIME,
    ...
)
```

- `publish_date` — дата публикации (только дата, без времени)
- При поиске активного вопроса используется `WHERE publish_date = CURRENT_DATE`

#### Метод `get_today_question()`
```python
def get_today_question(self):
    today = date.today()  # Получаем текущую дату
    cursor.execute('''
        SELECT * FROM daily_questions
        WHERE publish_date = ?
    ''', (today,))
```

**Как это работает:**
- В 23:59 → `date.today()` = 2024-02-10 → возвращает вопрос от 10 февраля
- В 00:00 → `date.today()` = 2024-02-11 → возвращает вопрос от 11 февраля (или None, если не опубликован)

#### Метод `check_user_answered_today()`
```python
def check_user_answered_today(self, user_id):
    today = date.today()
    cursor.execute('''
        SELECT COUNT(*) FROM answers
        JOIN daily_questions ON ...
        WHERE user_id = ? AND publish_date = ?
    ''', (user_id, today))
```

**Что проверяет:**
- Отвечал ли пользователь на вопрос **сегодняшнего дня**
- Ответы на вопросы прошлых дней не учитываются

---

### 2. Логика квиза (quiz_logic.py)

#### Метод `start_quiz_for_user()`

```python
def start_quiz_for_user(self, user_id):
    # 1. Получаем СЕГОДНЯШНИЙ вопрос
    question = self.db.get_today_question()

    if not question:
        return "Вопрос ещё не опубликован"

    # 2. Проверяем, не отвечал ли уже СЕГОДНЯ
    if self.db.check_user_answered_today(user_id):
        return "Вы уже ответили на сегодняшний вопрос"

    # 3. Очищаем старую сессию (если была)
    if user_id in self.active_sessions:
        if self.active_sessions[user_id] != question['id']:
            del self.active_sessions[user_id]

    # 4. Создаем новую сессию
    self.active_sessions[user_id] = question['id']

    return {"status": "success", "question": question}
```

#### Метод `check_answer()`

```python
def check_answer(self, user_id, user_answer):
    # 1. Получаем ID вопроса из сессии
    daily_question_id = self.active_sessions[user_id]

    # 2. Получаем СЕГОДНЯШНИЙ вопрос
    question = self.db.get_today_question()

    # 3. ВАЖНО: Проверяем, что сохраненный вопрос = сегодняшнему
    if question['id'] != daily_question_id:
        del self.active_sessions[user_id]
        return "Этот вопрос уже неактивен!"

    # 4. Обрабатываем ответ...
```

**Защита от краевых случаев:**
- Пользователь открыл вопрос в 23:59
- Ответил в 00:01 следующего дня
- Бот проверит, что `question['id'] != daily_question_id`
- Ответ будет отклонен с сообщением "Вопрос неактивен"

#### Метод `cleanup_expired_sessions()`

```python
def cleanup_expired_sessions(self):
    """Очистить устаревшие сессии при смене дня"""
    today_question = self.db.get_today_question()

    if not today_question:
        self.active_sessions.clear()
        return

    today_question_id = today_question['id']

    # Удаляем сессии вчерашнего дня
    expired_users = [
        user_id for user_id, question_id in self.active_sessions.items()
        if question_id != today_question_id
    ]

    for user_id in expired_users:
        del self.active_sessions[user_id]
```

**Вызывается:**
- Перед каждым `start_quiz_for_user()`
- Перед каждым `check_answer()`

---

### 3. Обработчики (handlers.py)

```python
async def show_question(update, context):
    # Очищаем устаревшие сессии
    quiz.cleanup_expired_sessions()

    result = quiz.start_quiz_for_user(user_id)
    ...

async def answer_callback(update, context):
    # Очищаем устаревшие сессии
    quiz.cleanup_expired_sessions()

    result = quiz.check_answer(user_id, answer)
    ...
```

---

## Сценарии работы

### Сценарий 1: Обычный день

```
09:00 - Бот публикует вопрос №1
        publish_date = 2024-02-10

10:00 - Пользователь A открывает вопрос
        ✅ get_today_question() → вопрос №1

10:05 - Пользователь A отвечает
        ✅ Ответ сохранен, начислены баллы

15:00 - Пользователь B открывает вопрос
        ✅ get_today_question() → вопрос №1

15:10 - Пользователь B отвечает
        ✅ Ответ сохранен, начислены баллы

23:59 - Пользователь C открывает вопрос
        ✅ get_today_question() → вопрос №1
```

### Сценарий 2: Смена дня (00:00)

```
23:59 (10 февраля)
      - Пользователь C открывает вопрос №1
      - active_sessions[C] = 1
      - ✅ Вопрос отображается

00:00 (11 февраля) → СМЕНА ДНЯ
      - date.today() изменилась на 2024-02-11

00:01 - Пользователь C нажимает "Ответ А"
      - check_answer() вызывает get_today_question()
      - get_today_question() → None (новый вопрос не опубликован)
      - ❌ "Произошла ошибка"

      ИЛИ (если новый вопрос уже опубликован):
      - get_today_question() → вопрос №2 (ID=2)
      - active_sessions[C] = 1 (старый вопрос)
      - question['id'] (2) != daily_question_id (1)
      - ❌ "Этот вопрос уже неактивен!"

09:00 - Бот публикует вопрос №2 (11 февраля)
        publish_date = 2024-02-11

09:05 - Пользователь A открывает вопрос
        ✅ get_today_question() → вопрос №2
```

### Сценарий 3: Попытка ответить дважды

```
10:00 - Пользователь A отвечает на вопрос №1
        ✅ Ответ сохранен

11:00 - Пользователь A открывает бота снова
        - check_user_answered_today(A) → True
        - ❌ "Вы уже ответили на сегодняшний вопрос!"

00:00 - СМЕНА ДНЯ

09:00 - Новый вопрос №2 опубликован

09:05 - Пользователь A открывает бота
        - check_user_answered_today(A) → False (новый день!)
        - ✅ Показывается вопрос №2
```

---

## Тестирование

Запустите тестовый скрипт:

```bash
python test_day_logic.py
```

Этот скрипт:
1. Создает вопросы для вчерашнего и сегодняшнего дня
2. Проверяет, что активен только сегодняшний вопрос
3. Проверяет блокировку попыток ответить на старый вопрос
4. Проверяет функцию `check_user_answered_today()`
5. Выводит детальный отчет

---

## Выводы

✅ **Логика "1 день = 1 вопрос" полностью реализована**

- `get_today_question()` использует `date.today()` для фильтрации
- При наступлении 00:00 автоматически меняется активный вопрос
- Защита от ответов на устаревшие вопросы
- Очистка устаревших сессий
- Блокировка повторных ответов в текущий день

✅ **Нет необходимости в cron-задачах для деактивации старых вопросов**

- Деактивация происходит автоматически через SQL-запросы с `WHERE publish_date = today`
- Нет риска "забыть деактивировать"
- Все работает через стандартную функцию `date.today()`

✅ **Все краевые случаи обработаны**

- Пользователь открыл вопрос до 00:00, ответил после 00:00
- Пользователь пытается ответить на вопрос прошлого дня
- Пользователь пытается ответить дважды в один день
- Смена дня при отсутствии нового вопроса
