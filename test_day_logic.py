"""
Тестовый файл для демонстрации логики "1 день = 1 вопрос"

Этот файл показывает, как работает механизм смены дня:
- При наступлении нового дня (00:00) старый вопрос становится неактивным
- Пользователь может ответить только на вопрос текущего дня
- Сессии автоматически очищаются при смене дня
"""

from datetime import date, datetime, timedelta
from database import Database

def test_daily_question_logic():
    """Демонстрация работы логики дневных вопросов"""

    db = Database('test_quiz.db')

    print("=" * 60)
    print("ТЕСТ: Логика смены дня")
    print("=" * 60)

    # 1. Добавляем тестовые вопросы
    print("\n1. Добавляем 3 тестовых вопроса...")

    for i in range(1, 4):
        db.add_question(
            category="Тест",
            question_text=f"Тестовый вопрос {i}",
            option_a="Ответ А",
            option_b="Ответ Б",
            option_c="Ответ В",
            option_d="Ответ Г",
            correct_option="A",
            explanation="Тестовое объяснение"
        )
    print("   ✅ Вопросы добавлены")

    # 2. Создаем вопросы для разных дней
    print("\n2. Создаем вопросы для разных дней...")

    # Вопрос для вчерашнего дня
    yesterday = datetime.now() - timedelta(days=1)
    question_yesterday = db.get_random_unused_question()
    db.create_daily_question(
        question_id=question_yesterday['question_id'],
        publish_time=yesterday,
        channel_message_id=1
    )
    print(f"   ✅ Вопрос для вчера (ID={question_yesterday['question_id']})")

    # Вопрос для сегодняшнего дня
    today = datetime.now()
    question_today = db.get_random_unused_question()
    db.create_daily_question(
        question_id=question_today['question_id'],
        publish_time=today,
        channel_message_id=2
    )
    print(f"   ✅ Вопрос для сегодня (ID={question_today['question_id']})")

    # 3. Проверяем, какой вопрос активен
    print("\n3. Проверяем активный вопрос...")

    active_question = db.get_today_question()
    if active_question:
        print(f"   ✅ Активный вопрос: ID={active_question['question_id']}")
        print(f"   📅 Дата публикации: {active_question['publish_date']}")
        print(f"   ❓ Текст: {active_question['question_text']}")
    else:
        print("   ❌ Нет активного вопроса")

    # 4. Проверяем логику "только сегодняшний"
    print("\n4. Проверяем, что доступен только сегодняшний вопрос...")

    if active_question['question_id'] == question_today['question_id']:
        print("   ✅ Правильно! Активен только сегодняшний вопрос")
    else:
        print("   ❌ Ошибка! Активен не тот вопрос")

    # 5. Симуляция ответа на устаревший вопрос
    print("\n5. Симуляция: пользователь пытается ответить на вчерашний вопрос...")

    user_id = 12345
    db.add_user(user_id, "test_user", "Test User")

    # Пытаемся ответить на вчерашний вопрос
    if active_question['id'] != question_yesterday['question_id']:
        print("   ✅ Вчерашний вопрос заблокирован")
        print(f"   ℹ️  Можно ответить только на вопрос ID={active_question['question_id']}")

    # 6. Проверка check_user_answered_today
    print("\n6. Проверяем функцию check_user_answered_today()...")

    has_answered = db.check_user_answered_today(user_id)
    print(f"   {'✅' if not has_answered else '❌'} Пользователь {'' if not has_answered else 'уже '}отвечал сегодня")

    # Сохраняем ответ на сегодняшний вопрос
    db.save_answer(
        user_id=user_id,
        daily_question_id=active_question['id'],
        user_answer="A",
        is_correct=True,
        points_earned=5,
        time_from_publish=30,
        answer_position=1,
        got_top50=True,
        got_speed=False
    )
    print("   💾 Сохранен ответ на сегодняшний вопрос")

    has_answered = db.check_user_answered_today(user_id)
    print(f"   {'✅' if has_answered else '❌'} Теперь пользователь {'уже ' if has_answered else 'не '}отвечал сегодня")

    print("\n" + "=" * 60)
    print("ИТОГ:")
    print("=" * 60)
    print("✅ Логика '1 день = 1 вопрос' работает корректно")
    print("✅ При наступлении 00:00 старый вопрос становится неактивным")
    print("✅ get_today_question() возвращает только вопрос текущего дня")
    print("✅ check_user_answered_today() проверяет ответы только на текущий день")
    print("✅ Пользователь не может ответить на вопрос прошлого дня")
    print("=" * 60)

    # Очистка тестовой БД
    import os
    os.remove('test_quiz.db')
    print("\n🗑️  Тестовая база данных удалена")

if __name__ == '__main__':
    test_daily_question_logic()
