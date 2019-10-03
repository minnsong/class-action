import random
import minefield.teams as team

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Person
from .models import Question
from .forms import LoginForm

from .teams import rearrange_pairs as rearrange

absent_students = []
present_student = []
teams = {}
current_team = -1
question_list = {}
question_state = {}
f_live_guess = False
penalty = 1


def arrange_teams():
	global present_student
	global teams
	random.shuffle(present_student)
	team_num = 0
	teams[team_num] = []
	for s in present_student:
		if len(teams[team_num]) < 2:
			teams[team_num].append(s)
		else:
			team_num += 1
			teams[team_num] = [s]
	if len(teams[team_num]) == 1:
		teams[0].append(teams[team_num][0])
		teams.pop(team_num)
	print('teams=' + str(teams))


def check_team_eligible(team_num, q_person):
	print('In check_team_eligible()')
	for s in teams.get(team_num):
		print(' s=' + s + ' q_person=' + q_person.name)
		if s == q_person.name:
			return False
	return True


def get_team_num(student_name):
	for t in teams:
		if student_name in teams.get(t):
			return t
	return -1 


def init(request, teacher_name):
	global absent_students
	student_objects = Person.objects.filter(type='student').order_by('name')
	for s in student_objects:
		absent_students.append(s.name)
	context = {
		'student_list': absent_students,
		'teacher_name': teacher_name
	}
	print('In init()..absent_students=' + str(absent_students))
	return render(request, 'minefield/class.html', context)
	# return HttpResponse("This is a list of students in %s's class." % teacher_name)


def set_next_team():
	global teams
	global current_team
	current_team = random.randrange(0, len(teams))
	print('In set_next_team()...current_team=' + str(current_team))
	

def take_attendance(request, teacher_name):
	global absent_students
	global present_student
	global teams
	print('POST=' + str(request.POST))
	if request.method == 'POST':
		present_students = request.POST.dict()
		absent_temp = []
		for s in absent_students:
			if ('s_' + s) in present_students:
				present_student.insert(len(present_student), s)
			else:
				absent_temp.append(s)
		absent_students = absent_temp
	print('absent_students=' + str(absent_students))
	print('present_student=' + str(present_student))
	arrange_teams()
	set_next_team()
	print('teams=' + str(teams))
	# teams = rearrange(teams)
	# print('teams(rearranged)=' + str(teams))
	# rearrange_teams(request)
	teams_items = teams.items()
	context = {
		'teacher_name': teacher_name,
		'team_list': teams_items
	}
	print('teams_items=' + str(teams_items))
	# return HttpResponse('After registering students')
	return render(request, 'minefield/teams.html', context);

def rearrange_teams(request, teacher_name):
	global teams
	teams = team.rearrange_pairs(teams)
	print('teams(rearranged)=' + str(teams))
	teams_items = teams.items()
	context = {
		'teacher_name': teacher_name,
		'team_list': teams_items
	}
	return render(request, 'minefield/teams.html', context)
	

def score(request, hit_landmine):
	if hit_landmine == 'HIT':
		# deduct penalty from team members' score
		# increment penalty
		print('Hit landmine!')
		return render(request, 'minefield/result.html', { 'hit': True })
	elif hit_landmine == 'SAFE':
		# +1 to team members' score
		print('Safe!')
		return render(request, 'minefield/result.html', { 'hit': False })
	else:
		print('ERROR: invalid guess result')
	return HttpResponse('Updated scores here')


def signin(request, person_type):
	if person_type == 'student':
		student_list = [p.name for p in Person.objects.filter(type='student').order_by('name')]
		context = {
			'student_list': student_list
		}
		print('In signin(student)..teams=' + str(teams))
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
	global question_list
	global question_state
	question_list  = Question.objects.order_by('person', 'q_num')
	# add pickling and write to disk : see Notes.app
	# question_list = question_queryset.values()
	print('In questionnaire()..question_list=' + str(question_list))
	for q in question_list:
		# q.update({ 'show_q': True, 'disabled_ans': [] })
		question_state.update({q.id: {'show_q': True, 'disabled_ans': []}})
	context = {
		'question_list': question_list,
		'student_name': student_name
	}
	print('question_state=' + str(question_state))
	return render(request, 'minefield/questionnaire.html', context)


def get_team_name(student_name):
	global teams
	# team_num = -1
	print('teams=' + str(teams))
	print('In get_team_name()..' + student_name)
	for t in teams:
		for s in teams[t]:
			print('s=' + s)
			if s == student_name:
				team_name = ' & '.join(teams[t])
				return team_name
	print('ERROR in retrieving team number')
	return None


def check_guess_valid(q_id, ans_letter):
	global question_list
	global question_state
	print('In check_guess_valid()..q_id=' + str(q_id) + ' ans_letter=' + ans_letter)
	for q in question_list:
		print(' q.id=' + str(q.id) + ' type(q.id)=' + str(type(q.id)) + ' type(q_id)=' + str(type(q_id)))
		if q.id == q_id:
			print('show_q=' + str(question_state[q_id].get('show_q')) + ' disabled_ans=' + str(question_state[q_id].get('disabled_ans')))
			if question_state[q_id].get('show_q') == True and ans_letter not in question_state[q_id].get('disabled_ans'):
				return True 
	return False


def guess(request, student_name):
	global question_list
	global f_live_guess
	try:
		guess = request.POST['choice']
		num_ans = guess.split('_', 1)
		guess_qid = int(num_ans[0])
		guess_letter = num_ans[1]
		q_person = Question.objects.get(pk=guess_qid).person
		question = Question.objects.get(pk=guess_qid)
		if guess_letter == 'a':
			guess = Question.objects.get(pk=guess_qid).ans_a
		elif guess_letter == 'b':
			guess = Question.objects.get(pk=guess_qid).ans_b
		elif guess_letter == 'c':
			guess = Question.objects.get(pk=guess_qid).ans_c
		elif guess_letter == 'd':
			guess = Question.objects.get(pk=guess_qid).ans_d
		else:
			print("An error occurred in reading guessed answer")
	except(KeyError, Question.DoesNotExist):
		question_list = Question.objects.order_by('person', 'q_num')
		return render(request, 'minefield/questionnaire.html', {
			'question_list': question_list
		})
	else:
		# verify team not guessing about own Q
		team_num = get_team_num(student_name)
		if check_team_eligible(team_num, q_person) == False:
			context = {
				'student_name': student_name,
				'msg': 'You cannot choose a question about anyone on your team. Please choose another.'
			}
			return render(request, 'minefield/error.html', context)
		team_name = get_team_name(student_name)
		if check_guess_valid(guess_qid, guess_letter) == True:
			f_live_guess = True
			context = {
				'team': team_name,
				'student_name': student_name,
				'target_person': q_person,
				'question': question,
				'guess': guess,
				'guess_letter': guess_letter.upper()
			}
		else:
			return HttpResponse('Your guess has already been eliminated. Please make another.')
	# return HttpResponse("%s's answer was %s, score = %d" % (student_name, selected_choice, count))
	return render(request, 'minefield/guess.html', context) 


def index(request):
	context = {}
	return render(request, 'minefield/index.html', context)
