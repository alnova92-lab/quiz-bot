"""
Скрипт для очистки базы данных после тестирования

ВНИМАНИЕ: Удаляет ВСЕ тестовые данные!
- Все ответы пользователей
- Все опубликованные вопросы
- Всех пользователей
- Сбрасывает статус вопросов (is_used = FALSE)
"""

import sqlite3
import config

def cleanup_database():
    """Очистка базы данных"""
    print("=" * 60)
    print("ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)

    print(f"\n⚠️  ВНИМАНИЕ!")
    print("Будут удалены:")
    print("  • Все ответы пользователей")
    print("  • Все опубликованные вопросы")
    print("  • Все пользователи")
    print("  • Статус вопросов сброшен (можно использовать заново)")

    confirm = input("\n❓ Продолжить? (yes/no): ").lower()

    if confirm != 'yes':
        print("\n❌ Отменено")
        return

    print(f"\n🗄️  База данных: {config.DB_PATH}")

    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    # Подсчитываем перед удалением
    cursor.execute('SELECT COUNT(*) FROM answers')
    answers_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM daily_questions')
    daily_questions_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM questions WHERE is_used = TRUE')
    used_questions_count = cursor.fetchone()[0]

    print(f"\n📊 Найдено:")
    print(f"   • Ответов: {answers_count}")
    print(f"   • Опубликованных вопросов: {daily_questions_count}")
    print(f"   • Пользователей: {users_count}")
    print(f"   • Использованных вопросов: {used_questions_count}")

    # Очистка
    print(f"\n🧹 Очистка...")

    cursor.execute('DELETE FROM answers')
    print("   ✅ Ответы удалены")

    cursor.execute('DELETE FROM daily_questions')
    print("   ✅ Опубликованные вопросы удалены")

    cursor.execute('DELETE FROM users')
    print("   ✅ Пользователи удалены")

    cursor.execute('UPDATE questions SET is_used = FALSE, usage_date = NULL')
    print("   ✅ Статус вопросов сброшен")

    cursor.execute('DELETE FROM weekly_ratings')
    print("   ✅ История рассылок удалена")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ БАЗА ДАННЫХ ОЧИЩЕНА!")
    print("=" * 60)
    print("\nТеперь можно:")
    print("  1. Начать тестирование заново")
    print("  2. Или запустить бота для продакшена")
    print("\n💡 Вопросы остались в базе и готовы к использованию")

if __name__ == '__main__':
    cleanup_database()
