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

    # Маппинг русских букв в английские
    ru_to_en = {'А': 'A', 'Б': 'B', 'В': 'C', 'Г': 'D'}

    # Импортируем в БД
    imported = 0
    for index, row in df.iterrows():
        try:
            correct_raw = str(row['Правильный']).upper().strip()
            correct_option = ru_to_en.get(correct_raw, correct_raw)
            db.add_question(
                category=str(row['Категория']),
                question_text=str(row['Вопрос']),
                option_a=str(row['Вариант А']),
                option_b=str(row['Вариант Б']),
                option_c=str(row['Вариант В']),
                option_d=str(row['Вариант Г']),
                correct_option=correct_option,
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
