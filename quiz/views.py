import datetime
import json
import random
from django.http import JsonResponse
from email._header_value_parser import Word
from urllib import request
from core.models import EnglishWord, UserEnglishVocabulary, Quiz, QuizQuestion, WordDefinition
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


def view_quiz_menu(request):
    return render(request, 'quiz/quiz_menu.html')


def view_quiz(request, quiz_id, question_number=0):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_questions = QuizQuestion.objects.filter(quiz_id=quiz.id).order_by('id')
    if question_number >= len(quiz_questions):
        return redirect('quiz_finished')
    current_question = quiz_questions[question_number]
    main_word = current_question.word
    correct_translation = WordDefinition.objects.filter(
        english_word=main_word
    ).order_by('-translation_score').first()
    other_word_ids = quiz_questions.exclude(id=current_question.id).values_list('word_id', flat=True)
    wrong_defs = []
    other_words = EnglishWord.objects.filter(id__in=other_word_ids)
    for word in other_words:
        top_def = WordDefinition.objects.filter(english_word=word).order_by('-translation_score').first()
        if top_def:
            wrong_defs.append(top_def)

    wrong_defs = random.sample(wrong_defs, min(3, len(wrong_defs)))
    answers = [correct_translation] + wrong_defs
    random.shuffle(answers)
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
    user_words = UserEnglishVocabulary.objects.filter(user_id = request.user)
    user_words_count = user_words.count()
    number_of_needed_words = 10 - user_words_count
    user_word_ids = user_words.values_list('word_id', flat=True)
    if number_of_needed_words > 2:
        random_words = EnglishWord.objects.exclude(id__in=user_word_ids).filter(is_top_4000=True).order_by('?')[
            :number_of_needed_words]
    else:
        random_words = EnglishWord.objects.exclude(id__in=user_word_ids).filter(is_top_4000=True).order_by('?')[:2]
    all_questions = list(user_words.values_list('word_id', flat=True)) + list(random_words.values_list('id', flat=True))
    quiz = Quiz.objects.create(
        user_id = request.user.id,
        mode = 'REPEAT_AND_LEARN',
        total_questions = 10,
    )
    for word_id in all_questions:
        QuizQuestion.objects.create(
            quiz_id=quiz.id,
            word_id=word_id,
            source=request.user
        )

    print(all_questions)
    return redirect('view_quiz', quiz_id=quiz.id, question_number=0)


def check_answer(request, quiz_id, question_number):
    data = json.loads(request.body)
    selected_answer_id = data.get('answer_id')

    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_questions = QuizQuestion.objects.filter(quiz_id=quiz.id).order_by('id')

    if question_number >= len(quiz_questions):
        return JsonResponse({'error': 'Invalid question number'}, status=400)

    current_question = quiz_questions[question_number]
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
        quiz_questions.filter(id = current_question.id).update(is_correct=is_correct, user_answer=selected_answer_id, answered_at=timezone.now())
    else:
        messages = [
            "Nieprawda! To błąd.",
            "Niestety, spróbuj zapamiętać.",
            "Pudło! Następnym razem się uda.",
            "Źle! Poprawna odpowiedź była inna."
        ]
        text_color = "text-danger"

    random_message = random.choice(messages)
    return JsonResponse({
        'is_correct': is_correct,
        'message': random_message,
        'text_class': text_color
    })


def quiz_finished(quiz_id):
    quiz_id = get_object_or_404(Quiz, id=quiz_id)
    correct_count = QuizQuestion.objects.filter(quiz_id=quiz_id, is_correct=True).count()
