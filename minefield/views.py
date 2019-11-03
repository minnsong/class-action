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
from .models import Tiebreaker
from .forms import AddDropForm
from .forms import LoginForm

from .teams import rearrange_pairs as rearrange

student_list = []
student_dict = {}
student_names = []
teams = []
current_index = None
question_dict = {}
f_live_guess = False
live_guess = {}
penalty = 1
scoreboard_msg = ''
f_tiebreak = False
tiebreak_dict = {}
tiebreak_index = 100
tiebreak_index_max = 103
tiebreak_students = []


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

		
def enable_answer(q_id, ans_letter):
	global question_dict
	id = int(q_id)
	for a in question_dict[id]['disabled_ans']:
		if a == ans_letter:
			question_dict[id]['disabled_ans'].remove(a)
	if len(question_dict[id]['disabled_ans']) < 3:			# question not completed, hide discussion
		question_dict[id]['show_dkn'] = False


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
	global tiebreak_dict
	global f_tiebreak
	questions = Question.objects.order_by('person', 'q_num')
	question_list = list(questions.values())		# convert to list to support ops unavailable w QuerySet
	tiebreaks = Tiebreaker.objects.all()
	tiebreak_list = list(tiebreaks.values())
	f_tiebreak = False
	for q in question_list:
		person = Person.objects.get(pk=q['person_id'])
		person_name = person.name
		id = q['id']
		del q['person_id']
		entry = q
		question_dict[id] = entry
		question_dict[id].update({ 'person': person_name, 'show_q': True, 'disabled_ans': [], 'show_dkn': False })
	for t in tiebreak_list:
		print('t=' + str(t))
		id = t['id']
		del t['id']
		entry = copy.deepcopy(t)
		question_dict[id] = entry
		question_dict[id].update({ 'id': id, 'show_q': False, 'disabled_ans': [], 'show_dkn': False })
	question_dict[tiebreak_index]['show_q'] = True		# make 1st tiebreak visible when S runs out of Q, or enter tiebreak
	# print('question_dict=' + str(question_dict))
	# print('tiebreak_dict=' + str(tiebreak_dict))
	

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
	global current_index
	team_number = (current_index + 1) % (len(teams))
	current_index = team_number
	print('In set_next_current_team()..current_index=' + str(current_index) + '(' + str(teams[current_index]) + ')')
	

def take_attendance(request, teacher_name):
	global student_dict
	# global student_list			# need use global student_list b/c call to team.arrange_teams() would otherwise only modify local copy?
	global teams
	global current_index
	print('POST=' + str(request.POST))
	if request.method == 'POST':
		present_students = request.POST.dict()
		for s in student_dict:
			if ('s_' + s) in present_students:
				student_dict[s]['present'] = True
			else:
				print(student_dict[s]['name'] + ' is absent')
	student_list = convert_dict_to_list(student_dict)
	team.arrange_teams(teams, student_list)
	current_index = random.randrange(0, len(teams))			# randomly select team as current_index
	print('teams=' + str(teams))
	print('current_index=' + str(current_index) + '(' + str(teams[current_index]) + ')')
	context = {
		'teacher_name': teacher_name,
		'teams': teams
	}
	init_questionnaire()
	return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))


def show_students(request, teacher_name):
	global student_dict
	global student_names
	student_list = convert_dict_to_list(student_dict)
	absent = [i for i in student_names if i in [s['name'] for s in student_list if s['name'] == i and s['present'] == False]] 
	present = [i for i in student_names if i in [s['name'] for s in student_list if s['name'] == i and s['present'] == True]]
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
		'form1': form1,
		'form2': form2
	}
	return render(request, 'minefield/update_class.html', context)


def add_student(request, teacher_name):
	global student_dict
	global student_names
	global teams
	added = ''
	student_list = convert_dict_to_list(student_dict)
	if request.method == 'POST':
		absent = [i for i in student_names if i in [s['name'] for s in student_list if s['name'] == i and s['present'] == False]] 
		absent_tuples = []
		for a in absent:
			absent_tuples.append((a, a))
		form = AddDropForm(request.POST)
		form.fields['chosen_student'].choices = absent_tuples
		if form.is_valid():
			added = form.cleaned_data['chosen_student']
			for s in student_dict:
				if student_dict[s]['name'] == added:
					student_dict[s]['present'] = True
					team.add_student(teams, added)
					# return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	return HttpResponseRedirect(reverse('minefield:show_students', args=(teacher_name,)))	


def drop_student(request, teacher_name):
	global student_dict
	global student_names
	global teams
	global current_index
	dropped = ''
	student_list = convert_dict_to_list(student_dict)
	if request.method == 'POST':
		present = [i for i in student_names if i in [s['name'] for s in student_list if s['name'] == i and s['present'] == True]]
		present_tuples = []
		for p in present:
			present_tuples.append((p, p))
		form = AddDropForm(request.POST)
		form.fields['chosen_student'].choices = present_tuples
		if form.is_valid():
			dropped = form.cleaned_data['chosen_student']
			for s in student_dict:
				if student_dict[s]['name'] == dropped:
					student_dict[s]['present'] = False
					team_num = team.drop_student(teams, dropped)
					if team_num >= 0 and team_num < current_index:
						current_index -= 1				# team removed, and before current team
					else:
						current_index = current_index % len(teams)	# in case team removed was last team
					# return HttpResponseRedirect(reverse('minefield:show_teams', args=(teacher_name,)))
	return HttpResponseRedirect(reverse('minefield:show_students', args=(teacher_name,)))	


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
	global f_tiebreak
	global f_live_guess
	global live_guess
	if f_live_guess == True:
		# return HttpResponse('Display UI for selecting whether guess correct or not')		
		student_name = live_guess['student_name']
		team_members = get_team_members(student_name)
		print('In show_game()..team_members=' + str(team_members))
		return render(request, 'minefield/guess.html', {
			'f_tiebreak': f_tiebreak,
			'for_type': 't',
			'teacher_name': teacher_name,
			'student_name': student_name,
			'team': team_members,
			'question': live_guess['question'],
			'guess_letter': live_guess['guess_letter']
		})
	return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def build_students_str(members):
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
	global current_index
	global penalty
	global f_tiebreak
	global tiebreak_students
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
		if f_tiebreak == False:
			team_members = get_team_members(student_name)
			team_str = build_students_str(team_members)
			print('In show_result()..team_members=' + str(team_members))
		question_id = request.POST['question_id']
		guess_letter = request.POST['guess_letter']
		if hit_landmine == 'HIT':
			disable_other_answers(question_id, guess_letter)
			if f_tiebreak == False:						# for hit during normal play
				for t in team_members:					# deduct penalty from team members' score
					student_dict[t]['score'] -= penalty
				if penalty > 1:
					msg = team_str + ' lose ' + str(penalty) + ' points!'
				else:
					msg = team_str + ' lose ' + str(penalty) + ' point!'
				penalty += 1							# increment penalty
			else:										# for hit during tiebreak
				tiebreak_students.remove(student_name)	# remove student from tiebreak
				current_index = current_index % len(tiebreak_students)
				msg = student_name + ' is out!!'
			hit = True
		elif hit_landmine == 'SAFE':
			disable_answer(question_id, guess_letter)	# should have already been disabled when submit guess
			if f_tiebreak == False:
				for t in team_members:					# +1 to team members' score
					student_dict[t]['score'] += 1
				msg = team_str + ' win one point.'
			else:
				current_index = (current_index + 1) % len(tiebreak_students)
				msg = student_name + ' is still in!'
			hit = False
		else:										# if error occurred, enter answer manually
			print('ERROR: invalid guess result')
			print('student_dict=' + str(student_dict))
			return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))
		if f_tiebreak == False:
			set_next_current_team()	
		return render(request, 'minefield/result.html', {
			'f_tiebreak': f_tiebreak,
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
	if request.method == 'POST':
		id = int(request.POST['question_id'])
		q = question_dict[id]
		if len(q['disabled_ans']) >= 3 and q['show_q'] == True:
			question_dict[id]['show_q'] = False						# after leave discussion page, hide this question
			return render(request, 'minefield/discussion.html', {
				'question': q,
				'teacher_name': teacher_name
			})
	return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))


def show_final_score(request, student_name):
	global tiebreak_students
	global student_dict
	student_list = convert_dict_to_list(student_dict)
	return render(request, 'minefield/final.html', {
		'student_list': student_list,
		'msg': 'The winner is ' + tiebreak_students[0] + '!!!'
	})


def show_scoreboard(request, teacher_name):
	global student_dict
	global scoreboard_msg
	student_list = convert_dict_to_list(student_dict)
	scoreboard_msg = 'CURRENT PENALTY: -' + str(penalty)
	context = {
		'for_type': 't',
		'teacher_name': teacher_name,
		'student_list': student_list,
		'msg': scoreboard_msg,
	}
	return render(request, 'minefield/scoreboard.html', context)


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
	return render(request, 'minefield/index.html', context)


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


# checks if all regular (non-tiebreak) Qs completed)
def check_questions_completed(question_dict):
	for q in question_dict:
		if q < 100 and question_dict[q]['show_q'] == True:
			return False
	return True


def check_winner(student_dict):
	max = -1000
	winners = []
	for s in student_dict:
		if student_dict[s]['present'] == True and student_dict[s]['score'] >= max:
			max = student_dict[s]['score']
	for s in student_dict:
		if student_dict[s]['present'] == True and student_dict[s]['score'] == max:
			winners.append(s)
	return winners 


def show_questions_context(for_type, name):
	global question_dict
	global student_dict
	global current_index
	global f_tiebreak
	global tiebreak_index
	global tiebreak_students
	question_list = convert_dict_to_list(question_dict)
	if question_dict[tiebreak_index]['show_q'] == False:		# if current tiebreak Q complete, go to next
		tiebreak_index += 1										# need to check even before tiebreak in case S has no Qs
		question_dict[tiebreak_index]['show_q'] = True
	tiebreak = copy.deepcopy(question_dict[tiebreak_index])
	team_members = []
	count = 0									# num of Qs current team eligible to guess
	# if for_type == 's':
	#	team_members = get_team_members(name)
	# elif for_type == 't':
	#	if f_tiebreak == False:
	#		team_members = teams[current_index]
	# else:
	#	print('Error reading for_type in show_questions_context()')
	print('In show_questions_context()..f_tiebreak=' + str(f_tiebreak))
	if f_tiebreak == False:		
		team_members = teams[current_index]
		team_str = build_students_str(team_members)
		for q in question_list:
			if q['person'] in team_members:
				q['show_q'] = False							# don't show question if about member of team
			elif q['show_q'] == True and q['id'] < 100:		# add only non-tiebreak Qs to count
				count += 1
		msg = 'Current team to guess: ' + team_str
	else:													# during tiebreak...
		print(' current_index=' + str(current_index))
		msg = "It's " + tiebreak_students[current_index] + "'s turn to guess!"
		question_list = []									# remove all questions other than tiebreak
	for q in question_list:				# remove tiebreak Q, so only available via 'tiebreak' var
		if q['id'] >= 100:
			question_list.remove(q)
	print('In show_questions_context()..count=' + str(count))
	context = {
		'msg': msg,
		'question_list': question_list,
		'for_type': for_type,
		'question_count': count,
		'tb': tiebreak
	}
	if for_type == 's':
		context.update({ 'student_name': name })
	elif for_type == 't':
		context.update({ 'teacher_name': name })
	return context


def show_questions_s(request, student_name):
	global f_tiebreak
	if f_tiebreak == True:
		return HttpResponseRedirect(reverse('minefield:final_score', args=(student_name,)))
	context = show_questions_context('s', student_name)
	return render(request, 'minefield/questionnaire.html', context)


# randomize list of tiebreak participants, select initial guesser
def prep_tiebreak_students():
	global tiebreak_students
	global current_index
	print('In prep_tiebreak_student()..(orig)current_index=' + str(current_index))
	random.shuffle(tiebreak_students)
	current_index = random.randrange(0, len(tiebreak_students))
	print(' (new)current_index=' + str(current_index))

	
def show_questions_t(request, teacher_name):
	global question_dict
	global student_dict
	# global tiebreak_dict
	global f_tiebreak
	global tiebreak_index
	global tiebreak_students
	global current_index
	if f_tiebreak == False and check_questions_completed(question_dict) == True:
		print('In show_questions_t()..all non-tiebreak Qs completed')
		f_tiebreak = True			# set flag here, so student UI will display final result, even if tiebreak not played
		winner_list = check_winner(student_dict)
		if len(winner_list) == 1:
			student_list = convert_dict_to_list(student_dict)
			tiebreak_students = winner_list		# set so student UI will display as winner, even tho no tiebreak played
			return render(request, 'minefield/scoreboard.html', {
				'for_type': 't',
				'teacher_name': teacher_name,
				'student_list': student_list,
				'msg': 'The winner is ' + winner_list[0] + '!!!'
			})
		else:
			f_tiebreak = True
			tiebreak_students = winner_list
			print(' tiebreak_students=' + str(tiebreak_students))
			prep_tiebreak_students()
			students_str = build_students_str(tiebreak_students)
			print(' f_tiebreak set, current_index=' + str(current_index))
			winning_score = student_dict[tiebreak_students[0]]['score']
			return render(request, 'minefield/tiebreaker.html', {
				'teacher_name': teacher_name,
				'msg': students_str + ' tied with a score of ' + str(winning_score) + "! It's PK time!!!"
			})
	if f_tiebreak == True and len(tiebreak_students) == 1:
		student_list = convert_dict_to_list(student_dict)
		return render(request, 'minefield/scoreboard.html', {
			'for_type': 't',
			'teacher_name': teacher_name,
			'student_list': student_list,
			'msg': 'The winner is ' + tiebreak_students[0] + '!!!'
		})
	context = show_questions_context('t', teacher_name)
	return render(request, 'minefield/questionnaire.html', context)


def get_team_members(student_name):
	global teams
	# team_num = -1
	print('teams=' + str(teams))
	print('In get_team_members()..' + student_name)
	for t in teams:
		# for s in t:
		#	if s == student_name:
		#		# team_name = ' & '.join(teams[t])
		#		# return team_name
		#		return t
		if student_name in t:
			return copy.deepcopy(t)
	return 'Error retrieving team members'


def check_guess_valid(q_id, ans_letter):
	global question_dict
	for q in question_dict:
		if q == q_id:
			if question_dict[q]['show_q'] == True and ans_letter not in question_dict[q]['disabled_ans']:
				return True 
	return False


def show_guess(request, new_context={}):
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
	global f_tiebreak
	team_members = []
	f_live_guess = True							# if flag set, no guesses can be submitted, tjr game UI will show guess
	print('In process_guess()..f_tiebreak=' + str(f_tiebreak) + ' for_type=' + for_type)
	question = question_dict[question_id]
	disable_answer(question_id, guess_letter)	# also called in show_result()
	context = {
		'f_tiebreak': f_tiebreak,
		'for_type': for_type,
		'question': question,
		'guess_letter': guess_letter,
		'student_name': student_name
	}
	if f_tiebreak == False:
		team_members = get_team_members(student_name)
		context.update({ 'team': team_members }) 
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
	if f_live_guess == True or team_num != current_index:		# don't allow guess if one already submitted, or not current team
		return HttpResponseRedirect(reverse('minefield:questions_s', args=(student_name,)))
	if request.method == 'POST':
		if 'choice' in request.POST:
			choice = request.POST['choice']
		else:
			context = {
				'student_name': student_name,
				'msg': 'You did not select anything.'
			}
			response = show_error_s(request, context)
			return response
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
	global current_index
	if f_tiebreak == False:
		student_name = teams[current_index][0]	# use 1st S in team arbitrarily (needed to get all team members for display in process_guess()))
		team_members = teams[current_index]
	else:
		student_name = tiebreak_students[current_index]			# get name by passing as hidden input?
	if request.method == 'POST':
		if 'choice' in request.POST:
			choice = request.POST['choice']
		else:
			return HttpResponseRedirect(reverse('minefield:questions_t', args=(teacher_name,)))
		num_ans = choice.split('_', 1)
		question_id = int(num_ans[0])
		guess_letter = num_ans[1]
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
		post_dict = request.POST.dict()
		ans = ['a', 'b', 'c', 'd']
		for q in question_dict:
			if str(question_dict[q]['id']) in post_dict:
				question_dict[q]['show_q'] = False
			else:
				question_dict[q]['show_q'] = True
			for a in ans:
				if str(question_dict[q]['id']) + '_' + a in post_dict:
					disable_answer(question_dict[q]['id'], a)
				else:
					enable_answer(question_dict[q]['id'], a)
			if str(question_dict[q]['id']) + '_dkn' in post_dict:
				question_dict[q]['show_dkn'] = False
			else:
				question_dict[q]['show_dkn'] = True
	return HttpResponseRedirect(reverse('minefield:master', args=(teacher_name,)))
		

def index(request):
	context = {}
	return render(request, 'minefield/index.html', context)
