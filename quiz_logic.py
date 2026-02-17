from datetime import datetime
from database import Database
import config

class QuizLogic:
    def __init__(self, db: Database):
        self.db = db
        self.active_sessions = {}  # {user_id: {'question_id': id, 'start_time': datetime}}

    def cleanup_expired_sessions(self):
        """Очистить устаревшие сессии при смене дня"""
        today_question = self.db.get_today_question()
        if not today_question:
            # Если нет сегодняшнего вопроса, очищаем все сессии
            self.active_sessions.clear()
            return

        today_question_id = today_question['id']
        # Удаляем сессии, которые относятся к вопросам не сегодняшнего дня
        expired_users = [
            user_id for user_id, session in self.active_sessions.items()
            if session['question_id'] != today_question_id
        ]
        for user_id in expired_users:
            del self.active_sessions[user_id]

    def start_quiz_for_user(self, user_id: int) -> dict:
        """Начать квиз для пользователя"""
        # Получаем сегодняшний вопрос
        question = self.db.get_today_question()

        if not question:
            return {
                'status': 'no_question',
                'message': '😔 Сегодняшний вопрос ещё не опубликован.\n\nСледите за каналом @' + config.CHANNEL_USERNAME
            }

        # Проверяем, не отвечал ли уже на СЕГОДНЯШНИЙ вопрос
        if self.db.check_user_answered_today(user_id):
            return {
                'status': 'already_answered',
                'message': '✅ Вы уже ответили на сегодняшний вопрос!\n\nСледующий вопрос появится завтра.'
            }

        # Очищаем старую сессию, если есть (на случай смены дня)
        if user_id in self.active_sessions:
            if self.active_sessions[user_id]['question_id'] != question['id']:
                del self.active_sessions[user_id]

        # Сохраняем сессию с временем нажатия кнопки "Ответить"
        self.active_sessions[user_id] = {
            'question_id': question['id'],
            'start_time': datetime.now()
        }

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

        session = self.active_sessions[user_id]
        daily_question_id = session['question_id']
        start_time = session['start_time']
        question = self.db.get_today_question()

        if not question:
            return {
                'status': 'error',
                'message': '❌ Произошла ошибка. Попробуйте позже.'
            }

        # Проверяем, что сохраненный вопрос соответствует сегодняшнему
        if question['id'] != daily_question_id:
            # Удаляем устаревшую сессию
            del self.active_sessions[user_id]
            return {
                'status': 'expired',
                'message': '⏰ Этот вопрос уже неактивен!\n\nНаступил новый день. Следите за каналом @' + config.CHANNEL_USERNAME + ' - скоро появится новый вопрос!'
            }

        # Проверяем правильность
        is_correct = (user_answer.upper() == question['correct_option'].upper())

        # Считаем время от нажатия кнопки "Ответить"
        time_diff = int((datetime.now() - start_time).total_seconds())

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
