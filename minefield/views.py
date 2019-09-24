import random

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Person
from .models import Question
from .forms import LoginForm

from .teams import rearrange_pairs as rearrange

absent_students = []
team_queue = []
teams = {}


def arrange():
	global team_queue
	global teams
	random.shuffle(team_queue)
	team_num = 0
	teams[team_num] = []
	for s in team_queue:
		if len(teams[team_num]) < 2:
			teams[team_num].append(s)
		else:
			team_num += 1
			teams[team_num] = [s]
	if len(teams[team_num]) == 1:
		teams[0].append(teams[team_num][0])
		teams.pop(team_num)
	print('teams=' + str(teams))


def init(request, username):
	global absent_students
	student_objects = Person.objects.filter(type='student').order_by('name')
	for s in student_objects:
		absent_students.append(s.name)
	context = {
		'student_list': absent_students,
		'teacher_name': username
	}
	print('In init()..absent_students=' + str(absent_students))
	return render(request, 'minefield/attendance.html', context)
	# return HttpResponse("This is a list of students in %s's class." % teacher_name)


def register(request, teacher_name):
	global absent_students
	global team_queue
	global teams
	print('POST=' + str(request.POST))
	if request.method == 'POST':
		present_students = request.POST.dict()
		absent_temp = []
		print('present_students=' + str(present_students))
		print('absent_students=' + str(absent_students))
		for s in absent_students:
			print('s=' + s)
			if ('s_' + s) in present_students:
				print('removed ' + s + ' from absent_students, added to team_queue')
				# absent_students.remove(s)
				team_queue.insert(len(team_queue), s)
			else:
				absent_temp.append(s)
		absent_students = absent_temp
	print('absent_students=' + str(absent_students))
	print('team_queue=' + str(team_queue))
	arrange()
	print('teams=' + str(teams))
	teams = rearrange(teams)
	print('teams(rearranged)=' + str(teams))
	return HttpResponse('After registering students')
	

def signin(request, person_type):
	if person_type == 'student':
		student_list = [p.name for p in Person.objects.filter(type='student').order_by('name')]
		context = {
			'student_list': student_list
		}
		return render(request, 'minefield/signin_student.html', context)
	elif person_type == 'teacher':
		teacher_list = [p.name for p in Person.objects.filter(type='teacher').order_by('name')]
		form = LoginForm()
		context = {
			'form': form
		}
		return render(request, 'minefield/signin_teacher.html', context)
	return HttpResponse('Error processing person type')


def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			teacher_name = form.cleaned_data['username']
			password = form.cleaned_data['password']
			if Person.objects.filter(name=teacher_name, password=password):
				# return HttpResponseRedirect('/minefield/t/' + teacher_name + '/')
				return HttpResponseRedirect(reverse('minefield:init', args=(teacher_name,)))
	else:
		form = LoginForm()
	return render(request, 'minefield/signin_teacher.html', {'form': form})


def questionnaire(request, student_name):
	question_list = Question.objects.order_by('person', 'q_num')
	# output = ', '.join([q.q_text for q in question_list])
	#return HttpResponse(output)
	context = {
		'question_list': question_list,
		'student_name': student_name
	}
	return render(request, 'minefield/questionnaire.html', context)


def guess(request, student_name):
	count = 0
	try:
		selected_answer = request.POST['choice']
		num_ans = selected_answer.split('_', 1)
		q_person = Question.objects.get(pk=num_ans[0]).person
		q_text = Question.objects.get(pk=num_ans[0]).q_text
		if num_ans[1] == 'a':
			q_guess = Question.objects.get(pk=num_ans[0]).ans_a
		elif num_ans[1] == 'b':
			q_guess = Question.objects.get(pk=num_ans[0]).ans_b
		elif num_ans[1] == 'c':
			q_guess = Question.objects.get(pk=num_ans[0]).ans_c
		elif num_ans[1] == 'd':
			q_guess = Question.objects.get(pk=num_ans[0]).ans_d
		else:
			print("An error occurred in reading guessed answer")
	except(KeyError, Question.DoesNotExist):
		question_list = Question.objects.order_by('person', 'q_num')
		return render(request, 'minefield/questionnaire.html', {
			'question_list': question_list
		})
	else:
		count = 1
		context = {
			'count': count,
			'student': student_name,
			'answer': selected_answer,
			'person': q_person,
			'question': q_text,
			'guess': q_guess
		}
	# return HttpResponse("%s's answer was %s, score = %d" % (student_name, selected_choice, count))
	return render(request, 'minefield/guess.html', context) 


def index(request):
	context = {}
	return render(request, 'minefield/index.html', context)
