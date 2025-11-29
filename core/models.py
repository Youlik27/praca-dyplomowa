from django.contrib.auth.models import User
from django.db import models

class PolishWord(models.Model):
    id_lexentry = models.TextField(unique=True, blank=True, null=True)
    word = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'polish_words'
        verbose_name = 'Polish Word'
        verbose_name_plural = 'Polish Words'

    def __str__(self):
        return self.word or "No word"


class EnglishWord(models.Model):
    word = models.TextField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'english_words'
        verbose_name = 'English Word'
        verbose_name_plural = 'English Words'

    def __str__(self):
        return self.word or "No word"


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
    review_count = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    incorrect_attempts = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'user_english_vocabulary'
        unique_together = (('user', 'word'),)
        verbose_name = 'User English Vocabulary'
        verbose_name_plural = 'User English Vocabularies'


class WordGroup(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_groups')

    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    words = models.ManyToManyField(
        EnglishWord,
        through='WordGroupMembership',
        related_name='contained_in_groups'
    )

    class Meta:
        db_table = 'word_groups'
        verbose_name = 'Word Group'
        verbose_name_plural = 'Word Groups'
        unique_together = ('owner', 'name')

    def __str__(self):
        return f"{self.name} (by {self.owner.username})"


class WordGroupMembership(models.Model):
    word = models.ForeignKey(EnglishWord, on_delete=models.CASCADE)
    group = models.ForeignKey(WordGroup, on_delete=models.CASCADE)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'word_group_membership'
        verbose_name = 'Word Group Membership'
        verbose_name_plural = 'Word Group Memberships'
        unique_together = ('word', 'group')

    def __str__(self):
        return f"{self.word} in {self.group}"