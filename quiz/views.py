import datetime
import json
import random
from core.models import EnglishWord, UserEnglishVocabulary, Quiz, QuizQuestion, WordDefinition
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


def view_quiz_menu(request):
    recent_quizzes = Quiz.objects.filter(user=request.user, is_finished=True).order_by('-created_at')[:5]
    return render(request, 'quiz/quiz_menu.html', {'recent_quizzes': recent_quizzes})


def view_quiz(request, quiz_id, question_number=0):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_questions = QuizQuestion.objects.filter(quiz_id=quiz.id).order_by('id')
    if question_number >= len(quiz_questions):
        return redirect('quiz_finished', quiz_id=quiz.id)
    current_question = quiz_questions[question_number]
    if current_question.answered_at is not None:
        next_unanswered_index = -1
        for index, q in enumerate(quiz_questions):
            if q.answered_at is None:
                next_unanswered_index = index
                break
        if next_unanswered_index != -1:
            return redirect('view_quiz', quiz_id=quiz_id, question_number=next_unanswered_index)
        else:
            return redirect('quiz_finished', quiz_id=quiz.id)
    main_word = current_question.word
    correct_translation = WordDefinition.objects.filter(
        english_word=main_word
    ).order_by('-translation_score').first()
    other_word_ids = quiz_questions.exclude(id=current_question.id).values_list('word_id', flat=True)
    wrong_defs = []
    other_words = EnglishWord.objects.filter(id__in=other_word_ids).order_by('id')
    for word in other_words:
        top_def = WordDefinition.objects.filter(english_word=word).order_by('-translation_score').first()
        if top_def:
            wrong_defs.append(top_def)
    wrong_defs.sort(key=lambda x: x.id)
    rng = random.Random(current_question.id)
    wrong_defs = rng.sample(wrong_defs, min(3, len(wrong_defs)))
    answers = [correct_translation] + wrong_defs
    rng.shuffle(answers)
    context = {
        'quiz': quiz,
        'main_word': main_word,
        'answers': answers,
        'correct_translation': correct_translation,
        'question_number': question_number,
        'total_questions': len(quiz_questions),
    }
    return render(request, 'quiz/view_quiz.html', context)

def create_quiz_repeat_and_learn(request):
    QUIZ_SIZE = 10
    REVIEW_PROPORTION = 7
    user_vocab = UserEnglishVocabulary.objects.filter(user=request.user).order_by(
        '-wrong_count',
        'correct_count',
        'last_reviewed_at'
    )[:REVIEW_PROPORTION]

    review_word_ids = list(user_vocab.values_list('word_id', flat=True))
    needed_new_words = QUIZ_SIZE - len(review_word_ids)

    all_user_word_ids = UserEnglishVocabulary.objects.filter(user=request.user).values_list('word_id', flat=True)
    new_words = EnglishWord.objects.exclude(id__in=all_user_word_ids).filter(is_top_4000=True).order_by('?')[
        :needed_new_words]
    new_word_ids = list(new_words.values_list('id', flat=True))
    all_questions = review_word_ids + new_word_ids

    random.shuffle(all_questions)
    quiz = Quiz.objects.create(
        user=request.user,
        mode='REPEAT_AND_LEARN',
        total_questions=len(all_questions),
    )

    for word_id in all_questions:
        QuizQuestion.objects.create(
            quiz=quiz,
            word_id=word_id,
            source=request.user
        )
    return redirect('view_quiz', quiz_id=quiz.id, question_number=0)
def check_answer(request, quiz_id, question_number):
    if request.method != 'POST':
        return JsonResponse({'error': 'Post request required'}, status=400)
    data = json.loads(request.body)
    selected_answer_id = data.get('answer_id')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_questions = QuizQuestion.objects.filter(quiz_id=quiz.id).order_by('id')

    if question_number >= len(quiz_questions):
        return JsonResponse({'error': 'Invalid question number'}, status=400)

    current_question = quiz_questions[question_number]
    if current_question.answered_at is not None:
        return JsonResponse({ 'error': 'Question already answered', 'is_correct': current_question.is_correct }, status=400)
    main_word = current_question.word

    selected_def = WordDefinition.objects.filter(id=selected_answer_id).first()

    is_correct = False
    if selected_def and selected_def.english_word == main_word:
        is_correct = True

    if is_correct:
        messages = [
            "Prawda! To poprawna odpowiedź.",
            "Brawo! Zgadłeś.",
            "Świetnie! Dokładnie tak.",
            "Genialnie! Lecisz dalej."
        ]
        text_color = "text-success"
        icon = "🎉"
        if request.user.is_authenticated:
            try:
                vocab_word = UserEnglishVocabulary.objects.get(user=request.user, word=main_word)
                vocab_word.correct_count += 1
                vocab_word.last_reviewed_at = timezone.now()
                vocab_word.save()

            except UserEnglishVocabulary.DoesNotExist:
                pass

    else:
        messages = [
            "Nieprawda! To błąd.",
            "Niestety, spróbuj zapamiętać.",
            "Pudło! Następnym razem się uda.",
            "Źle! Poprawna odpowiedź była inna."
        ]
        text_color = "text-danger"
        icon = "😔"
        if request.user.is_authenticated:
            try:
                vocab_word = UserEnglishVocabulary.objects.get(user=request.user, word=main_word)
                vocab_word.wrong_count += 1
                vocab_word.last_reviewed_at = timezone.now()
                vocab_word.save()
            except UserEnglishVocabulary.DoesNotExist:
                pass
    quiz_questions.filter(id = current_question.id).update(is_correct=is_correct, user_answer=selected_answer_id, answered_at=timezone.now())

    random_message = random.choice(messages)
    return JsonResponse({
        'is_correct': is_correct,
        'message': random_message,
        'text_class': text_color,
        'icon': icon
    })


def quiz_finished(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    total_questions = quiz.total_questions
    correct_count = QuizQuestion.objects.filter(quiz_id=quiz, is_correct=True).count()
    if not quiz.is_finished:
        total_time_spent_seconds = (timezone.now() - quiz.created_at).total_seconds()
        quiz.correct_count = correct_count
        quiz.is_finished = True
        quiz.total_time_spent_seconds = total_time_spent_seconds
        quiz.save()
    total_time = quiz.total_time_spent_seconds
    minutes = round(total_time // 60)
    seconds = round(total_time % 60)
    if total_questions > 0:
        percentage = round((correct_count / total_questions) * 100)
    else:
        percentage = 0
    return render(request, 'quiz/view_quiz_finish.html', {'correct_count': correct_count,
                                                          'total_questions': total_questions,
                                                          'percentage': percentage,
                                                          "minutes": minutes,
                                                          "seconds": seconds,
                                                          })
