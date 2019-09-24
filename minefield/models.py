from django.db import models

# Create your models here.
class PersonManager(models.Manager):
	def get_by_natural_key(self, name):
		return self.get(name=name)


class Person(models.Model):
	name = models.CharField(max_length=32, unique=True)
	type = models.CharField(max_length=16, default="student")
	password = models.CharField(max_length=32, default="")
	objects = PersonManager()

	def __str__(self):
		return self.name

	def natural_key(self):
		return (self.name,)		# must return a tuple


class QuestionManager(models.Manager):
	def get_by_natural_key(self, person, q_num):
		return self.get(person=person, q_num=q_num)


class Question(models.Model):
	person = models.ForeignKey(
		Person,
		on_delete=models.PROTECT,
	)
	q_num = models.IntegerField(default=0)
	q_text = models.CharField(max_length=256)
	component = models.CharField(max_length=64)
	ans_a = models.CharField(max_length=128)
	ans_b = models.CharField(max_length=128)
	ans_c = models.CharField(max_length=128)
	ans_d = models.CharField(max_length=128)
	correct_ans = models.CharField(default="", max_length=8)
	discussion = models.CharField(max_length=1024)

	class Meta:
		unique_together = [['person', 'q_num']]

	def natural_key(self):
		return (self.person, self.q_num)

	def __str__(self):
		return self.q_text


class TiebreakerManager(models.Manager):
	def get_by_natural_key(self, q_num):
		return self.get(q_num=q_num)


class Tiebreaker(models.Model):
	q_num = models.IntegerField(default=0)
	q_text = models.CharField(max_length=256)
	component = models.CharField(max_length=64)
	ans_a = models.CharField(max_length=128)
	ans_b = models.CharField(max_length=128)
	ans_c = models.CharField(max_length=128)
	ans_d = models.CharField(max_length=128)
	correct_ans = models.CharField(max_length=8)
	discussion = models.CharField(max_length=1024)

	def __str__(self):
		return self.q_text
