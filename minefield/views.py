import copy
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

# students = []
student_dict = {}
student_names = []
teams = []
current_team = None
question_dict = {}
f_live_guess = False
live_guess = {}
penalty = 1


def check_team_eligible(team_num, q_person):
	global teams
	print('In check_team_eligible()..team_num=' + str(team_num))
	for s in teams[team_num]:
		print(' s=' + s + ' q_person=' + q_person)
		if s == q_person:
			return False
	return True


def disable_answer(q_id, ans_letter):
	global question_dict
	id = int(q_id)
	for a in question_dict[id]['disabled_ans']:
		if a == ans_letter:
			return											# letter already present, do not add again
	question_dict[id]['disabled_ans'].append(ans_letter)
	if len(question_dict[id]['disabled_ans']) >= 3:			# if question complete, show discussion
		question_dict[id]['show_dkn'] = True


def disable_other_answers(q_id, ans_letter):
	global question_dict
	id = int(q_id)
	question_dict[id]['disabled_ans'].clear()
	answer = ['a', 'b', 'c', 'd']
	for a in answer:
		if a != ans_letter:
			question_dict[id]['disabled_ans'].append(a)
	question_dict[id]['show_dkn'] = True					# question completed, show discussion

		
def get_team_num(student_name):
	print('In get_team_num()..student_name=' + student_name)
	idx = 0
	for t in teams:
		if student_name in t:
			return idx
		idx += 1
	return -1 


def init_questionnaire():
	global question_dict
	# person_names = Person.objects.all()
	questions = Question.objects.order_by('person', 'q_num')
	question_list = list(questions.values())		# convert to list to support ops unavailable w QuerySet
	# print('question_list(before edit)=' + str(question_list))
	for q in question_list:
		person = Person.objects.get(pk=q['person_id'])
		person_name = person.name
		id = q['id']
		# del q['id']
		del q['person_id']
		entry = q
		# del q
		question_dict[id] = entry
		question_dict[id].update({ 'person': person_name, 'show_q': True, 'disabled_ans': [], 'show_dkn': False })
		# question_dict[id] = entry
		# question_dict[id]['person'] = person_name
		# question_dict[id]['disabled_ans'] = []
	# print('question_list=' + str(question_list))
	# print('question_dict=' + str(question_dict))
	

def init_class(request, teacher_name):
	global student_dict
	global student_names
	student_objects = Person.objects.filter(type='student').order_by('name')
	for s in student_objects:
		student_dict[s.name] = {'name': s.name, 'present': False, 'score': 0}
		student_names.append(s.name)
	context = {
		'student_names': student_names,
		'teacher_name': teacher_name
	}
	return render(request, 'minefield/class.html', context)


def set_next_current_team():
	global teams
	global current_team
	team_number = (current_team + 1) % (len(teams))
	current_team = team_number
	print('In set_next_current_team()..current_team=' + str(current_team) + '(' + str(teams[current_team]) + ')')
	

def take_attendance(request, teacher_name):
	global student_dict
	global teams
	global current_team
	print('POST=' + str(request.POST))
	students = convert_dict_to_list(student_dict)
	if request.method == 'POST':
		present_students = request.POST.dict()
		for s in students:
			if ('s_' + s['name']) in present_students:
				s['present'] = True
			else:
				print(s['name'] + ' is absent')
	team.arrange_teams(teams, students)
	current_team = random.randrange(0, len(teams))			# randomly select team as current_team
	print('teams=' + str(teams))
	print('current_team=' + str(current_team) + '(' + str(teams[current_team]) + ')')
	context = {
		'teacher_name': teacher_name,
		'teams': teams
	}
	init_questionnaire()
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))


def show_students(request, teacher_name):
	global student_dict
	global student_names
	students = convert_dict_to_list(student_dict)
	absent = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == False]] 
	present = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == True]]
	absent_tuples = []
	present_tuples = []
	for a in absent:
		absent_tuples.append((a, a))
	for p in present:
		present_tuples.append((p, p))
	form1 = AddDropForm()
	form1.fields['chosen_student'].choices = absent_tuples
	form2 = AddDropForm()
	form2.fields['chosen_student'].choices = present_tuples
	context = {
		'for_type': 't',
		'teacher_name': teacher_name,
		# 'absent': absent,
		# 'present': present,
		#'students': present_tuples,
		'form1': form1,
		'form2': form2
	}
	# return HttpResponse('Add/drop students here')
	return render(request, 'minefield/update_class.html', context)


def add_student(request, teacher_name):
	global student_dict
	global teams
	added = ''
	students = convert_dict_to_list(student_dict)
	if request.method == 'POST':
		absent = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == False]] 
		absent_tuples = []
		for a in absent:
			absent_tuples.append((a, a))
		form = AddDropForm(request.POST)
		form.fields['chosen_student'].choices = absent_tuples
		if form.is_valid():
			added = form.cleaned_data['chosen_student']
			for s in students:
				if s['name'] == added:
					s['present'] = True
					team.add_student(teams, added)
					return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	return HttpResponseRedirect(reverse('minefield:show_students', args=(teacher_name,)))	


def drop_student(request, teacher_name):
	global students
	global teams
	global current_team
	dropped = ''
	students = convert_dict_to_list(student_dict)
	if request.method == 'POST':
		present = [i for i in student_names if i in [s['name'] for s in students if s['name'] == i and s['present'] == True]]
		present_tuples = []
		for p in present:
			present_tuples.append((p, p))
		print('request.POST=' + str(request.POST))
		form = AddDropForm(request.POST)
		form.fields['chosen_student'].choices = present_tuples
		if form.is_valid():
			dropped = form.cleaned_data['chosen_student']
			print('dropped=' + dropped)
			for s in students:
				if s['name'] == dropped:
					s['present'] = False
					# teams = team.drop_student(teams, s['name'])[0]	
					team_num = team.drop_student(teams, s['name'])
					if team_num >= 0 and team_num < current_team:
						current_team -= 1				# team removed, and before current team
					else:
						current_team = current_team % len(teams)
					print('teams(after drop)=' + str(teams))
					print('current_team=' + str(current_team))
					return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	return HttpResponse('Dropped ' + str(dropped) + '. Redirect to teams listing.')


def show_teams(request, teacher_name):
	global teams
	# teams_items = teams.items()
	context = {
		'for_type': 't',
		'teacher_name': teacher_name,
		'teams': teams
	}
	return render(request, 'minefield/teams.html', context)


def rearrange_teams(request, teacher_name):
	global teams
	team.rearrange_pairs(teams)
	print('teams(rearranged)=' + str(teams))
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	

def show_game(request, teacher_name):
	global question_dict
	global f_live_guess
	global live_guess
	if f_live_guess == True:
		# return HttpResponse('Display UI for selecting whether guess correct or not')		
		student_name = live_guess['student_name']
		team_members = get_team_members(student_name)
		return render(request, 'minefield/guess.html', {
			'for_type': 't',
			'teacher_name': teacher_name,
			'student_name': student_name,
			'team': team_members,
			'question': live_guess['question'],
			'guess_letter': live_guess['guess_letter']
		})
	return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def build_team_str_from_members(members):
	last = len(members) - 1
	i = 0
	team = ''
	for m in members:
		if i == last:
			team += ' & ' +  m
		elif i == 0:
			team += m
		else:
			team += ', ' + m
		i += 1
	return team	

		
def show_result(request, teacher_name, hit_landmine):
	global f_live_guess
	global current_team
	global penalty
	f_live_guess = False
	hit = False
	student_name = ''
	question_id = -1
	guess_letter = ''
	team_members = []
	team_str = ''
	msg = ''
	print('In show_result()')
	if request.method == 'POST':
		student_name = request.POST['student_name']
		print(' student_name=' + student_name)
		team_members = get_team_members(student_name)
		team_str = build_team_str_from_members(team_members)
		print('In show_result()..team_members=' + str(team_members))
		question_id = request.POST['question_id']
		guess_letter = request.POST['guess_letter']
		if hit_landmine == 'HIT':
			disable_other_answers(question_id, guess_letter)
			for t in team_members:					# deduct penalty from team members' score
				student_dict[t]['score'] -= penalty
			if penalty > 1:
				msg = team_str + ' lose ' + str(penalty) + ' points!'
			else:
				msg = team_str + ' lose ' + str(penalty) + ' point!'
			penalty += 1							# increment penalty
			hit = True
		elif hit_landmine == 'SAFE':
			disable_answer(question_id, guess_letter)
			for t in team_members:					# +1 to team members' score
				student_dict[t]['score'] += 1
			msg = team_str + ' win one point.'
			hit = False
		else:										# if error occurred, enter answer manually
			print('ERROR: invalid guess result')
			print('student_dict=' + str(student_dict))
			return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))
		set_next_current_team()	
		return render(request, 'minefield/result.html', {
			'question_id': question_id,
			'teacher_name': teacher_name,
			'hit': hit,
			'msg': msg
		})
	else:
		print('Error processing post to show_result()')
		return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def show_discussion(request, teacher_name):
	global question_dict
	print('In show_discussion()')
	# print('question_dict=' + str(question_dict))
	if request.method == 'POST':
		id = int(request.POST['question_id'])
		q = question_dict[id]
		if len(q['disabled_ans']) >= 3 and q['show_q'] == True:
			print(' setting show_q false for: ' + str(question_dict[id]))
			question_dict[id]['show_q'] = False						# after leave discussion page, hide this question
			return render(request, 'minefield/discussion.html', {
				'question': q,
				'teacher_name': teacher_name
			})
	return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def show_scoreboard(request, teacher_name):
	global student_dict
	student_list = convert_dict_to_list(student_dict)
	context = {
		'for_type': 't',
		'student_list': student_list,
		'penalty': penalty,
		'teacher_name': teacher_name,
	}
	return render(request, 'minefield/scoreboard.html', context)


def show_master(request, teacher_name):
	return HttpResponse('Show master questionniare')


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
				return HttpResponseRedirect(reverse('minefield:init_class', args=(teacher_name,)))
	else:
		form = LoginForm()
	return render(request, 'minefield/signin_teacher.html', {'form': form})


def convert_dict_to_list(dict):
	new_list = []
	for d in dict:
		new_list.append(copy.deepcopy(dict[d]))		# make copy of data, otherwise points to original data
	return new_list


def show_questions_s(request, student_name):
	global question_dict
	question_list = convert_dict_to_list(question_dict)
	team_members = get_team_members(student_name)
	for q in question_list:
		# if len(q['disabled_ans']) >= 3:
			# q['show_dkn'] = True
		for s in team_members:
			if s == q['person']:				# if question is about one of team, don't display
				q['show_q'] = False
	context = {
		'question_list': question_list,
		'student_name': student_name,
		'for_type': 's'
	}
	return render(request, 'minefield/questionnaire.html', context)


def show_questions_t(request, teacher_name):
	global question_dict
	global student_dict
	print('In show_questions_t()')
	question_list = convert_dict_to_list(question_dict)
	student_list = convert_dict_to_list(student_dict)
	team_members = teams[current_team]
	team_str = build_team_str_from_members(team_members)
	print(' In show_questions_t()..team_members=' + str(team_members))
	print(' before loop')
	print(' question_list[0][person]=' + question_list[0]['person'] + ' [show_q]=' + str(question_list[0]['show_q']))
	print(' question_list[1][person]=' + question_list[1]['person'] + ' [show_q]=' + str(question_list[1]['show_q']))
	print(' question_dict[0][person]=' + question_dict[0]['person'] + ' [show_q]=' + str(question_dict[0]['show_q']))
	print(' question_dict[1][person]=' + question_dict[1]['person'] + ' [show_q]=' + str(question_dict[1]['show_q']))
	for q in question_list:
		# if len(q['disabled_ans']) >= 3:
			# q['show_dkn'] = True
		for s in team_members:
			if s == q['person']:				# if question is about one of team, don't display
				q['show_q'] = False
	msg = 'Current team to guess: ' + team_str
	print(' after loop')
	print(' question_list[0][person]=' + question_list[0]['person'] + ' [show_q]=' + str(question_list[0]['show_q']))
	print(' question_list[1][person]=' + question_list[1]['person'] + ' [show_q]=' + str(question_list[1]['show_q']))
	print(' question_dict[0][person]=' + question_dict[0]['person'] + ' [show_q]=' + str(question_dict[0]['show_q']))
	print(' question_dict[1][person]=' + question_dict[1]['person'] + ' [show_q]=' + str(question_dict[1]['show_q']))
	context = {
		'msg': msg,
		'question_list': question_list,
		'for_type': 't',
		'teacher_name': teacher_name
	}
	return render(request, 'minefield/questionnaire.html', context)


def get_team_members(student_name):
	global teams
	# team_num = -1
	print('teams=' + str(teams))
	print('In get_team_members()..' + student_name)
	for t in teams:
		for s in t:
			if s == student_name:
				# team_name = ' & '.join(teams[t])
				# return team_name
				return t
	return 'Error retrieving team members'


def check_guess_valid(q_id, ans_letter):
	global question_dict
	# print('In check_guess_valid()..q_id=' + str(q_id) + ' ans_letter=' + ans_letter)
	for q in question_dict:
		# print(' q[id]=' + str(q['id']) + ' type(q[id])=' + str(type(q['id']) + ' type(q_id)=' + str(type(q_id))))
		if q == q_id:
			if question_dict[q]['show_q'] == True and ans_letter not in question_dict[q]['disabled_ans']:
				return True 
	return False


def show_guess(request, new_context={}):
	# return HttpResponse('Display student guess here')
	context = {}
	context.update(new_context)
	return render(request, 'minefield/guess.html', context=context) 


def show_error_s(request, new_context={}):
	context = {}
	context.update(new_context)
	return render(request, 'minefield/error.html', context=context)


def process_guess(question_id, guess_letter, for_type, student_name, teacher_name):
	global question_dict
	global f_live_guess
	# global live_guess
	f_live_guess = True							# if flag set, no guesses can be submitted, tjr game UI will show guess
	# disable_answer(question_id, guess_letter)
	team_members = get_team_members(student_name)
	question = question_dict[question_id]
	print('In process_guess()..question=' + str(question))
	context = {
		'for_type': for_type,
		'team': team_members,
		'question': question,
		'guess_letter': guess_letter,
		'student_name': student_name
	}
	if for_type == 't':
		context.update({ 'teacher_name': teacher_name })
	return context


def submit_guess_s(request, student_name):
	global question_dict
	global f_live_guess
	global live_guess
	global teams
	team_num = get_team_num(student_name)
	team_members = teams[team_num]
	question_list = convert_dict_to_list(question_dict)
	if f_live_guess == True or team_num != current_team:		# don't allow guess if one already submitted, or not current team
		return HttpResponseRedirect(reverse('minefield:questions_s', args=(student_name,)))
	if request.method == 'POST':
		choice = request.POST['choice']
		num_ans = choice.split('_', 1)
		question_id = int(num_ans[0])
		guess_letter = num_ans[1]
		if check_team_eligible(team_num, question_dict[question_id]['person']) == False:
			context = {
				'student_name': student_name,
				'msg': 'You cannot choose a question about a member of your team. Please choose another.'
			}
			return render(request, 'minefield/error.html', context)			# need to make into HttpResponseRedirect?
		if check_guess_valid(question_id, guess_letter) == True:
			live_guess = {
				# 'team': team_members,
				'student_name': student_name,
				'question': question_dict[question_id],
				'guess_letter': guess_letter
			}
			context = process_guess(question_id, guess_letter, 's', student_name, None)
			response = show_guess(request, context)
			return response
		else:
			context = {
				'student_name': student_name,
				'msg': 'Your guess has already been eliminated. Please select another.'
			}
			response = show_error_s(request, context)
			return response
	else:
		return HttpResponseRedirect(reverse('minefield:questions_s', args=(student_name,)))


def submit_guess_t(request, teacher_name):
	global live_guess
	student_name = teams[current_team][0]	# use 1st S in team arbitrarily (needed to get all team members for display in process_guess()))
	team_members = teams[current_team]
	if request.method == 'POST':
		choice = request.POST['choice']
		num_ans = choice.split('_', 1)
		question_id = int(num_ans[0])
		guess_letter = num_ans[1]
		# live_guess = {
			# 'team': team_members,
			# 'question': question_dict[question_id],
			# 'guess_letter': guess_letter
		# }
		context = process_guess(question_id, guess_letter, 't', student_name, teacher_name)
		response = show_guess(request, context)
		return response
	else:
		return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def show_master(request, teacher_name):
	global question_dict
	question_list = convert_dict_to_list(question_dict)
	context = {
		'for_type': 't',
		'teacher_name': teacher_name,
		'question_list': question_list
	}
	return render(request, 'minefield/master.html', context)

 
def update_master(request, teacher_name):
	global question_dict
	if request.method == 'POST':
		question_id = request.post['question_id']
		action = request.post['action']
		return HttpResponse('question_id=' + question_id + ' action=' + action)
	else:
		question_list = convert_dict_to_list(question_dict)
		context = {
			'for_type': 't',
			'teacher_name': teacher_name,
			'question_list': question_list
		}
		return render(request, 'minefield/master.html', context)
		


def index(request):
	context = {}
	return render(request, 'minefield/index.html', context)
