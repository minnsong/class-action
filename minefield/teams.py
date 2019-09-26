import math
import random


def sort_dict(dict):
	sorted_dict = {}
	sorted_tuples = sorted(dict.items())
	i = 0
	for e in sorted_tuples:
		sorted_dict[e[0]] = e[1]
	return sorted_dict


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
