import math
import random


def sort_dict(dict):
	sorted_dict = {}
	sorted_tuples = sorted(dict.items())
	i = 0
	for e in sorted_tuples:
		sorted_dict[e[0]] = e[1]
	return sorted_dict


def arrange_teams(teams, students):
	random.shuffle(students)
	team_num = 0
	teams.append([])
	for s in students:
		if s['present'] == True:
			if len(teams[team_num]) < 2:
				teams[team_num].append(s['name'])
			else:
				team_num += 1
				teams.append([s['name']])
	if len(teams[team_num]) == 1:
		teams[0].append(teams[team_num][0])
		teams.pop(team_num)


def add_student(teams, student):
	# updated = teams
	f_added = False
	for t in teams:
		if len(t) < 3:
			t.append(student)
			f_added = True
			return
	if f_added == False:				# all teams already have 3 or more Ss
		teams[select_random(len(teams))].append(student)
		return


def drop_student(teams, student):
	# teams = teams_orig
	extra = ''			# poss 3rd student in large team
	print('len(teams)=' + str(len(teams)))
	orphan = ''
	for i in range(0, len(teams)):
		if student in teams[i]:
			teams[i].remove(student)					# first remove student
			if len(teams[i]) >= 2:						# if team still has at least 2 members, do nothing
				return -1								# return -1 to indicate no change in number of teams
			elif len(teams[i]) == 1:					# if team has only 1 member, find team w extra members, if any
				for k in range(len(teams) - 1, -1, -1):	# go through teams in reverse order
					if len(teams[k]) > 2:				# if team has extra members
						extra = teams[k].pop()			# pop last member
						teams[i].append(extra)			# add popped member to team where student removed
						return -1						# return -1 to indicate no change in number of teams
				for t in teams:							# if no teams larger than 2 found, find first with 2 and append orphan
					if len(t) == 2:
						orphan = teams[i].pop()			# get student left in team from which student removed		
						t.append(orphan)				# add this student to 1st team found w 2 members
						del teams[i]					# remove team, now empty, from which student removed
						return i						# return index of team from which student removed
				teams[select_random(len(teams))].append(orphan)
				return i
			else:
				print('Error occurred. Team contains only 1 student.')
				return 'error'


def rearrange_pairs_old(current):
	new_teams = {}
	num = 0
	last = len(current)
	for t in current:
		new_teams[num] = [current[t][0]]
		new_teams[num].append(current[t][1])
		if len(current[t]) > 2:
			if last not in new_teams:
				new_teams[last] = [current[t][2]]
			elif len(new_teams[last]) == 1:
				new_teams[last].append(current[t][2])
				last += 1
		num += 1
	new_teams = sort_dict(new_teams)
	head = new_teams[0][0]								# save first S name
	if len(new_teams[len(new_teams) - 1]) == 2:			# have 2 S in last dict entry
		tail = new_teams[len(new_teams) - 1][1]			# save last S name
	else:
		tail = None										# only 1 S in last dict entry
		new_teams[len(new_teams) - 1].append(None)
	f_orphan = False
	for i in range(0, len(new_teams) - 1):				# move Ss in 1st pos forward one entry
		new_teams[i][0] = new_teams[i+1][0]
	if tail is not None:								# have 2 S in last dict entry
		new_teams[len(new_teams) - 1][0] = tail			# move last S to 1st pos in last entry
	else:
		f_orphan = True									# flag that there was only 1 S in last dict entry
	for k in range(len(new_teams) - 1, 0, -1):			# move Ss in 2nd pos back one entry
		new_teams[k][1] = new_teams[k - 1][1]
	new_teams[0][1] = head								# move 1st S to 2nd pos in 1st entry
	if f_orphan:
		new_teams[0].append(new_teams[len(new_teams) - 1][1])
		new_teams.pop(len(new_teams) - 1)
	return new_teams


def rearrange_pairs(teams):
	for t in teams:
		if len(t) > 2:									# if team has more than 2 members...
			extra = t.pop()								# pop last member of team
			if len(teams[len(teams) - 1]) < 2:			# ...and if last team has fewer than 2 members...
				teams[len(teams) - 1].append(extra)		# add student to last team
			else:										# ...else if all teams have at least 2 members...
				teams.append([extra])					# add new team at tail, w student as 1st member
	head = teams[0][0]									# save first S name
	tail = ''
	if len(teams[len(teams) - 1]) == 2:					# have 2 S in last team
		tail = teams[len(teams) - 1][1]					# save last S name
	else:												# only 1 S in last team
		tail = None
		teams[len(teams) - 1].append(None)				# add None to last team
	f_orphan = False
	for i in range(0, len(teams) - 1):					# move 1st S in each team forward one team
		teams[i][0] = teams[i+1][0]
	if tail is not None:								# if have 2 S in last team...
		teams[len(teams) - 1][0] = tail					# ...move 2nd S to 1st pos
	else:
		f_orphan = True									# flag that there was only 1 S in last team
	for i in range(len(teams) - 1, 0, -1):				# move Ss in 2nd pos back one team
		teams[i][1] = teams[i - 1][1]
	teams[0][1] = head									# put original 1st S in 2nd pos of 1st team
	if f_orphan:
		teams[0].append(teams[len(teams) - 1][1])		# move orphaned S in last team to 1st team
		teams.pop()										# remove last team
	

def select_random(teams_len):
	return math.floor(random.random() * teams_len) 
