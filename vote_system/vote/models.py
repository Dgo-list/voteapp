from __future__ import unicode_literals
from django.db import models

# class User(models.Model):
# 	username=models.CharField(max_length=100)
# 	password=models.CharField(max_length=300)
# 	user_type=models.CharField(max_length=10, default='general')

class Question(models.Model):
	question_text = models.CharField(max_length=300)
	is_published = models.IntegerField(default=0)

class Question_option(models.Model):
	question = models.ForeignKey(Question, on_delete=models.CASCADE)
	option_text = models.CharField(max_length=60)

class Vote(models.Model):
	question = models.ForeignKey(Question)
	username = models.CharField(max_length=100)
	question_option = models.ForeignKey(Question_option)



