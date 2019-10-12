import random
import minefield.teams as team

from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.forms import Form

from .models import Person
from .models import Question
from .forms import AddDropForm
from .forms import LoginForm

from .teams import rearrange_pairs as rearrange

students = []
student_names = []
teams = {}
current_team = -1
question_list = {}
questionnaire_state = {}
f_live_guess = False
penalty = 1


def arrange_teams():
	global students
	global teams
	random.shuffle(students)
	team_num = 0
	teams[team_num] = []
	for s in students:
		if s['present'] == True:
			if len(teams[team_num]) < 2:
				teams[team_num].append(s['name'])
			else:
				team_num += 1
				# teams[team_num] = [s]
				teams[team_num] = [s['name']]
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


def disable_answer(q_id, ans_letter):
	global questionnaire_state
	for a in questionnaire_state[q_id]['disabled_ans']:
		if a == ans_letter:
			return			# letter already present, don't add again
	questionnaire_state[q_id]['disabled_ans'].append(ans_letter)


def disable_question(q_id):
	global questionnaire_state
	if len(questionnaire_state[q_id]['disabled_ans'] >= 3):
		questionnaire_state[q_id]['show_q'] = False

		
def get_team_num(student_name):
	for t in teams:
		if student_name in teams.get(t):
			return t
	return -1 


def init_questionnaire():
	global question_list
	global questionnaire_state
	question_list = Question.objects.order_by('person', 'q_num')
	# add pickling and write to disk : see Notes.app
	# question_list = question_queryset.values()
	# print('In questionnaire()..question_list=' + str(question_list))
	for q in question_list:
		# q.update({ 'show_q': True, 'disabled_ans': [] })
		questionnaire_state.update({q.id: {'show_q': True, 'disabled_ans': []}})
	
	
def init_class(request, teacher_name):
	global students
	global student_names
	student_objects = Person.objects.filter(type='student').order_by('name')
	for s in student_objects:
		students.append({'name': s.name, 'present': False, 'score': 0})
		student_names.append(s.name)
	context = {
		'student_names': student_names,
		'teacher_name': teacher_name
	}
	# print('In init_class()..students=' + str(students))
	return render(request, 'minefield/class.html', context)
	# return HttpResponse("This is a list of students in %s's class." % teacher_name)


def set_next_team():
	global teams
	global current_team
	current_team = random.randrange(0, len(teams))
	print('In set_next_team()...current_team=' + str(current_team))
	

def take_attendance(request, teacher_name):
	global students
	global teams
	print('POST=' + str(request.POST))
	if request.method == 'POST':
		# students = request.POST.dict()
		present_students = request.POST.dict()
		# absent_temp = []
		for s in students:
			if ('s_' + s['name']) in present_students:
				s['present'] = True
			else:
				print(s['name'] + ' is absent')
		# absent_students = absent_temp
	print('students=' + str(students))
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
	init_questionnaire()
	# return HttpResponse('After registering students')
	# return render(request, 'minefield/teams.html', context);
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))


def show_students(request, teacher_name):
	global student_names
	absent = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == False]] 
	present = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == True]]
	present_tuples = []
	for p in present:
		present_tuples.append((p, p))
	form = AddDropForm()
	form.fields['chosen_student'].choices = present_tuples
	context = {
		'teacher_name': teacher_name,
		'absent': absent,
		# 'present': present,
		'students': present_tuples,
		'form': form
	}
	# return HttpResponse('Add/drop students here')
	return render(request, 'minefield/update_class.html', context)


def add_student(request, teacher_name):
	global students
	global teams
	if request.method == 'POST' and 'add' in request.POST:
		print('request.body=' + str(request.body))
		form = Form(request.POST)
		if form.is_valid():
			# added = request.POST['add']
			added = form.cleaned_data['add']
			for s in students:
				if s['name'] == added:
					s['present'] = True
					teams = team.add_student(teams, s['name'])
	# return HttpResponse('Added students. Redirect to teams listing.')
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))


def drop_student(request, teacher_name):
	global students
	global teams
	dropped = ''
	if request.method == 'POST':
		present = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == True]]
		present_tuples = []
		for p in present:
			present_tuples.append((p, p))
		print('request.POST=' + str(request.POST))
		form = AddDropForm(request.POST)
		form.fields['chosen_student'].choices = present_tuples
		# form = AddDropForm()
		# print('POST successful. form.is_bound()=' + str(form.is_bound))
		# print('form=' + str(form))
		# print('form.errors=' + str(form.errors))
		if form.is_valid():
			dropped = form.cleaned_data['chosen_student']
			print('dropped=' + dropped)
			for s in students:
				if s['name'] == dropped:
					s['present'] = False
					# teams = team.drop_student(teams, s['name'])[0]	
					team.drop_student(teams, s['name'])
					print('teams(after drop)=' + str(teams))
					return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	return HttpResponse('Dropped ' + str(dropped) + '. Redirect to teams listing.')


def show_teams(request, teacher_name):
	global teams
	teams_items = teams.items()
	context = {
		'teacher_name': teacher_name,
		'team_list': teams_items
	}
	return render(request, 'minefield/teams.html', context)


def rearrange_teams(request, teacher_name):
	global teams
	teams = team.rearrange_pairs(teams)
	print('teams(rearranged)=' + str(teams))
	# teams_items = teams.items()
	# context = {
		# 'teacher_name': teacher_name,
		# 'team_list': teams_items
	# }
	# return render(request, 'minefield/teams.html', context)
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	

def score(request, hit_landmine):
	global f_live_guess
	f_live_guess = False
	student_name = request.POST['student_name']
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
				return HttpResponseRedirect(reverse('minefield:init_class', args=(teacher_name,)))
	else:
		form = LoginForm()
	return render(request, 'minefield/signin_teacher.html', {'form': form})


def show_questionnaire(request, student_name):
	global question_list
	global questionnaire_state
	# question_list  = Question.objects.order_by('person', 'q_num')
	# add pickling and write to disk : see Notes.app
	# question_list = question_queryset.values()
	# print('In questionnaire()..question_list=' + str(question_list))
	# for q in question_list:
		# q.update({ 'show_q': True, 'disabled_ans': [] })
		# questionnaire_state.update({q.id: {'show_q': True, 'disabled_ans': []}})
	context = {
		'question_list': question_list,
		'student_name': student_name
	}
	# print('questionnaire_state=' + str(questionnaire_state))
	return render(request, 'minefield/questionnaire.html', context)


def show_questionnaire_class(request):
	global question_list
	global questionnaire_state
	context = {
		'question_list': question_list,
		'questionnaire_state': questionnaire_state
	}
	return render(request, 'minefield/questionnaire.html', context)


def get_team_name(student_name):
	global teams
	# team_num = -1
	print('teams=' + str(teams))
	print('In get_team_name()..' + student_name)
	for t in teams:
		for s in teams[t]:
			if s == student_name:
				team_name = ' & '.join(teams[t])
				return team_name
	print('ERROR in retrieving team number')
	return None


def check_guess_valid(q_id, ans_letter):
	global question_list
	global questionnaire_state
	print('In check_guess_valid()..q_id=' + str(q_id) + ' ans_letter=' + ans_letter)
	for q in question_list:
		print(' q.id=' + str(q.id) + ' type(q.id)=' + str(type(q.id)) + ' type(q_id)=' + str(type(q_id)))
		if q.id == q_id:
			print('show_q=' + str(questionnaire_state[q_id].get('show_q')) + ' disabled_ans=' + str(questionnaire_state[q_id].get('disabled_ans')))
			if questionnaire_state[q_id].get('show_q') == True and ans_letter not in questionnaire_state[q_id].get('disabled_ans'):
				return True 
	return False


def show_guess(request, new_context={}):
	# return HttpResponse('Display student guess here')
	context = {}
	context.update(new_context)
	return render(request, 'minefield/guess.html', context=context) 


def submit_guess(request, student_name):
	global question_list
	global f_live_guess
	context = {}
	try:
		choice = request.POST['choice']
		for_type = request.POST['for_type']
		if for_type == 'c':
			student_name = request.POST['student_name']
		num_ans = choice.split('_', 1)
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
			# update questionnaire state
			# questionnaire_state[guess_qid]['disabled_ans'].append(guess_letter)
			disable_answer(guess_qid, guess_letter)
			print('disabled_ans=' + str(questionnaire_state[guess_qid].get('disabled_ans')))
			f_live_guess = True
			context = {
				'for_type': for_type,
				'team': team_name,
				'student_name': student_name,
				'target_person': q_person,
				'question': question,
				'guess': guess,
				'guess_letter': guess_letter.upper()
			}
		else:
			# return HttpResponse('Your guess has already been eliminated. Please make another.')
			context = {
				'student_name': student_name,
				'msg': 'Your guess has already been eliminated. Please make another.'
			}
			return render(request, 'minefield/error.html', context)
	# return HttpResponse("%s's answer was %s, score = %d" % (student_name, selected_choice, count))
	# return render(request, 'minefield/guess.html', context) 
	# return HttpResponseRedirect(reverse('minefield:show_guess', args=(student_name, context,)))
	# return redirect('minefield:show_guess', args=(student_name,), kwargs={'context': context})
	response = show_guess(request, context)
	return response


def index(request):
	context = {}
	return render(request, 'minefield/index.html', context)
