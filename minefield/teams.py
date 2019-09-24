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
	print('current=' + str(current))
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
	print('new_teams(presort)=' + str(new_teams))
	new_teams = sort_dict(new_teams)
	print('new_teams(sorted)=' + str(new_teams))
	head = new_teams[0][0]				# save first S name
	if len(new_teams[len(new_teams) - 1]) == 2:			# have 2 in last entry of dict
		tail = new_teams[len(new_teams) - 1][1]	# save last S name, may be None
	else:
		tail = None
		new_teams[len(new_teams) - 1].append(None)
	f_orphan = False
	for i in range(0, len(new_teams) - 1):
		new_teams[i][0] = new_teams[i+1][0]
	if tail is not None:
		new_teams[len(new_teams) - 1][0] = tail
	else:
		f_orphan = True
	for k in range(len(new_teams) - 1, 0, -1):
		new_teams[k][1] = new_teams[k - 1][1]
	new_teams[0][1] = head
	if f_orphan:
		new_teams[0].append(new_teams[len(new_teams) - 1][1])
		new_teams.pop(len(new_teams) - 1)
	print(str(new_teams))
	return new_teams


team_list = {0: ['Amy', 'Bob', 'Cathy'], 1: ['Dan', 'Eli', 'Faye'], 2: ['Gina', 'Hank', 'Ian'], 3: ['Jan', 'Kay', 'Lee'], 4: ['Lisa', 'May'], 5: ['Nick', 'Olga'], 6: ['Pat', 'Quinn']}
rearrange_pairs(team_list)

