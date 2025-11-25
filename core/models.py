from django.contrib.auth.models import User
from django.db import models

class EnglishWord(models.Model):
    word = models.TextField(blank=True, null=True)
    frequency = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'english_words'
        verbose_name = 'English Word'
        verbose_name_plural = 'English Words'

class PolishWord(models.Model):
    word = models.TextField(blank=True, null=True)
    frequency = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'polish_words'
        verbose_name = 'Polish Word'
        verbose_name_plural = 'Polish Words'

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='searches', blank=True, null=True)
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'

class UserEnglishVocabulary(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    word = models.ForeignKey(EnglishWord, on_delete=models.CASCADE)
    study_status = models.CharField(max_length=20, default='new')
    last_reviewed_at = models.DateTimeField(blank=True, null=True)
    review_count = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    incorrect_attempts = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'user_english_vocabulary'
        unique_together = (('user', 'word'),)
        verbose_name = 'User English Vocabulary'
        verbose_name_plural = 'User English Vocabularies'

class WordDefinition(models.Model):
    # id bigint присутствует в создании таблицы, но не помечен как PK явно в дампе,
    # но Django требует PK. Предполагаем, что id существует и уникален.
    polish_word = models.ForeignKey(PolishWord, on_delete=models.DO_NOTHING, blank=True, null=True)
    english_word = models.ForeignKey(EnglishWord, on_delete=models.DO_NOTHING, blank=True, null=True)
    lang_code = models.CharField(max_length=10, blank=True, null=True)
    pos = models.CharField(max_length=50, blank=True, null=True)
    sense_index = models.SmallIntegerField(blank=True, null=True)
    translation_index = models.SmallIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    raw_gloss = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    ipa = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'word_definitions'
        verbose_name = 'Word Definition'
        verbose_name_plural = 'Word Definitions'

