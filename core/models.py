from django.contrib.auth.models import User
from django.db import models

class PolishWord(models.Model):
    id_lexentry = models.TextField(unique=True, blank=True, null=True)
    word = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'polish_words'
        verbose_name = 'Polish Word'
        verbose_name_plural = 'Polish Words'


class EnglishWord(models.Model):
    word = models.TextField(unique=True, blank=True, null=True)

    is_top_4000 = models.BooleanField(default=False, verbose_name="Top 4000 Common Word")

    class Meta:
        db_table = 'english_words'
        verbose_name = 'English Word'
        verbose_name_plural = 'English Words'



class WordDefinition(models.Model):
    polish_word = models.ForeignKey(PolishWord, on_delete=models.CASCADE)
    english_word = models.ForeignKey(EnglishWord, on_delete=models.CASCADE)
    definition = models.TextField(blank=True, null=True)
    part_of_speech = models.TextField(blank=True, null=True)
    min_sense_num = models.IntegerField(blank=True, null=True)
    importance = models.FloatField(blank=True, null=True)
    translation_score = models.FloatField(blank=True, null=True)
    class Meta:
        db_table = 'word_definitions'
        verbose_name = 'Word Definition'
        verbose_name_plural = 'Word Definitions'

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
    correct_count = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'user_english_vocabulary'
        unique_together = (('user', 'word'),)
        verbose_name = 'User English Vocabulary'
        verbose_name_plural = 'User English Vocabularies'


class WordList(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_lists')
    created_at = models.DateTimeField(auto_now_add=True)

    words = models.ManyToManyField(
        EnglishWord,
        through='WordListMembership',
        related_name='contained_in_lists'
    )

    class Meta:
        db_table = 'word_lists'
        verbose_name = 'Word List'
        verbose_name_plural = 'Word Lists'


class WordListMembership(models.Model):
    word = models.ForeignKey(EnglishWord, on_delete=models.CASCADE, db_column='word_id')
    word_list = models.ForeignKey(WordList, on_delete=models.CASCADE, db_column='list_id')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'word_lists_membership'
        unique_together = ('word', 'word_list')


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING,db_column='user_id' )
    mode = models.CharField(max_length=20, blank=True, null=True)
    total_questions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)
    correct_count = models.IntegerField(default=0)
    total_time_spent_seconds = models.IntegerField(default=0)

    class Meta:
        db_table = 'quizzes'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.DO_NOTHING,db_column='quiz_id' )
    word = models.ForeignKey(EnglishWord,on_delete=models.CASCADE, db_column='word_id')
    source = models.CharField(max_length=20)
    user_answer = models.CharField(max_length=255, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'quiz_questions'
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'