import math
import random


def sort_dict(dict):
	sorted_dict = {}
	sorted_tuples = sorted(dict.items())
	i = 0
	for e in sorted_tuples:
		sorted_dict[e[0]] = e[1]
	return sorted_dict


def add_student(teams, student):
	# updated = teams
	f_added = False
	for t in teams:
		if len(teams[t]) < 3:
			teams[t].append(student)
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
			teams[i].remove(student)
			if len(teams[i]) >= 2:
				# return (teams, -1)				# return -1 to indicate no change in number of teams
				return -1
			elif len(teams[i]) == 1:
				for k in range(len(teams) - 1, -1, -1):
					print('k=' + str(k))
					if len(teams[k]) > 2:
						extra = teams[k].pop()
						print('extra student: ' + str(extra))
						teams[i].append(extra)
						# return (teams, -1)
						return -1					# return -1 to indicate no change in number of teams
				for t in teams:						# if no teams larger than 2 found, find first with 2 and append orphan
					if len(teams[t]) == 2:
						orphan = teams[i].pop()
						teams[t].append(orphan)
						del teams[i]
						# teams[0].append(teams[i].pop())
						# return (teams, i)				# return index of team from which student dropped
						return i
				teams[select_random(len(teams))].append(orphan)
				return i
			else:
				print('Error occurred. Team contains only 1 student.')
				# return (teams, 'error')
				return 'error'

def rearrange_pairs(current):
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


def select_random(teams_len):
	return math.floor(random() * teams_len) 
