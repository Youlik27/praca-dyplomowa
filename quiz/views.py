import datetime
import json
import random
from core.models import EnglishWord, UserEnglishVocabulary, Quiz, QuizQuestion, WordDefinition
from django.db import transaction
from django.db.models import F, Case, When, Value, IntegerField
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


def view_quiz_menu(request):
    recent_quizzes = Quiz.objects.filter(user=request.user, is_finished=True).order_by('-created_at')[:5]
    for quiz in recent_quizzes:
        if quiz.total_questions > 0:
            quiz.percentage = round((quiz.correct_count / quiz.total_questions) * 100)
        else:
            quiz.percentage = 0
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
    REVIEW_COUNT = 7
    NEW_COUNT = 3
    user = request.user

    user_vocab = UserEnglishVocabulary.objects.filter(user=user)
    bucket_a = list(user_vocab.filter(success_rate__lt=40).order_by('?')[:4].values_list('word_id', flat=True))
    bucket_b = list(user_vocab.filter(success_rate__gte=40, success_rate__lt=80).order_by('?')[:2].values_list('word_id',flat=True))
    bucket_c = list(user_vocab.filter(success_rate__gte=80).order_by('?')[:1].values_list('word_id', flat=True))
    review_ids = bucket_a + bucket_b + bucket_c
    if len(review_ids) < REVIEW_COUNT:
        needed_review = REVIEW_COUNT - len(review_ids)
        extra_review = list(
            user_vocab.exclude(word_id__in=review_ids)
            .order_by('?')[:needed_review]
            .values_list('word_id', flat=True)
        )
        review_ids.extend(extra_review)

    new_word_ids = list(
        EnglishWord.objects.exclude(id__in=user_vocab.values_list('word_id', flat=True))
        .filter(is_top_4000=True)
        .order_by('?')[:NEW_COUNT]
        .values_list('id', flat=True)
    )
    final_ids = review_ids + new_word_ids

    if len(final_ids) < QUIZ_SIZE:
        needed_total = QUIZ_SIZE - len(final_ids)
        emergency_new = list(
            EnglishWord.objects.exclude(id__in=final_ids)
            .exclude(id__in=user_vocab.values_list('word_id', flat=True))
            .filter(is_top_4000=True)
            .order_by('?')[:needed_total]
            .values_list('id', flat=True)
        )
        final_ids.extend(emergency_new)

    random.shuffle(final_ids)

    with transaction.atomic():
        quiz = Quiz.objects.create(
            user=user,
            mode='REPEAT_AND_LEARN',
            total_questions=len(final_ids),
        )
        questions = [
            QuizQuestion(quiz=quiz, word_id=word_id, source='user')
            for word_id in final_ids
        ]
        QuizQuestion.objects.bulk_create(questions)
    print(f"Bucket A (Hard): {len(bucket_a)}")
    print(f"Bucket B (Medium): {len(bucket_b)}")
    print(f"Bucket C (Easy): {len(bucket_c)}")
    print(f"New words added: {len(new_word_ids)}")
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
        return JsonResponse({'error': 'Question already answered', 'is_correct': current_question.is_correct},
                            status=400)
    main_word = current_question.word
    selected_def = WordDefinition.objects.filter(id=selected_answer_id).first()
    is_correct = False
    if selected_def and selected_def.english_word == main_word:
        is_correct = True
    is_new = False
    if request.user.is_authenticated:
        vocab_word = UserEnglishVocabulary.objects.filter(
            user=request.user,
            word=main_word
        ).first()
        if vocab_word:
            if is_correct:
                vocab_word.correct_count += 1
            else:
                vocab_word.wrong_count += 1
            vocab_word.last_reviewed_at = timezone.now()
            total = vocab_word.correct_count + vocab_word.wrong_count
            if total < 3:
                vocab_word.success_rate = 0
            else:
                vocab_word.success_rate = (vocab_word.correct_count / total) * 100
            vocab_word.save()
        else:
            is_new = True

    if is_correct:
        messages = ["Prawda!", "Brawo!", "Świetnie!", "Genialnie!"]
        text_color, icon = "text-success", "🎉"
    else:
        messages = ["Nieprawda!", "Niestety...", "Pudło!", "Źle!"]
        text_color, icon = "text-danger", "😔"

    quiz_questions.filter(id=current_question.id).update(
        is_correct=is_correct,
        user_answer=selected_answer_id,
        answered_at=timezone.now()
    )
    random_message = random.choice(messages)
    return JsonResponse({
        'is_correct': is_correct,
        'message': random_message,
        'text_class': text_color,
        'icon': icon,
        'is_new': is_new,
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
