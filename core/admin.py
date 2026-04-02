from django.contrib import admin
from .models import (
    PolishWord, EnglishWord, WordDefinition, SearchHistory,
    UserEnglishVocabulary, WordList, WordListMembership,
    Quiz, QuizQuestion, AssistantResponse
)


@admin.register(PolishWord)
class PolishWordAdmin(admin.ModelAdmin):
    list_display = ('id', 'word', 'id_lexentry')
    search_fields = ('word', 'id_lexentry')


@admin.register(EnglishWord)
class EnglishWordAdmin(admin.ModelAdmin):
    list_display = ('id', 'word', 'is_top_4000')
    search_fields = ('word',)
    list_filter = ('is_top_4000',)


@admin.register(WordDefinition)
class WordDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'polish_word', 'english_word',
        'part_of_speech', 'min_sense_num',
        'importance', 'translation_score'
    )
    search_fields = (
        'polish_word__word',
        'english_word__word',
        'definition',
        'part_of_speech'
    )
    list_filter = ('part_of_speech',)
    autocomplete_fields = ('polish_word', 'english_word')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'query', 'created_at')
    search_fields = ('query', 'user__username')
    list_filter = ('created_at',)


@admin.register(UserEnglishVocabulary)
class UserEnglishVocabularyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'word', 'study_status',
        'correct_count', 'wrong_count',
        'success_rate', 'last_reviewed_at', 'added_at',
        'is_learned'
    )
    search_fields = ('user__username', 'word__word', 'study_status')
    list_filter = ('study_status', 'added_at', 'last_reviewed_at')
    autocomplete_fields = ('user', 'word')


@admin.register(WordList)
class WordListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'icon', 'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('created_at',)
    autocomplete_fields = ('owner',)


@admin.register(WordListMembership)
class WordListMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'word', 'word_list', 'added_at')
    search_fields = ('word__word', 'word_list__name')
    list_filter = ('added_at',)
    autocomplete_fields = ('word', 'word_list')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'mode', 'total_questions',
        'correct_count', 'is_finished',
        'total_time_spent_seconds', 'created_at'
    )
    search_fields = ('user__username', 'mode')
    list_filter = ('mode', 'is_finished', 'created_at')
    autocomplete_fields = ('user',)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'quiz', 'word', 'source',
        'user_answer', 'is_correct', 'answered_at'
    )
    search_fields = ('word__word', 'source', 'user_answer')
    list_filter = ('source', 'is_correct', 'answered_at')
    autocomplete_fields = ('quiz', 'word')


@admin.register(AssistantResponse)
class AssistantResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'created_at')
    search_fields = ('user__username', 'name', 'user_input', 'text')
    list_filter = ('created_at',)
    autocomplete_fields = ('user',)