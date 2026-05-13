import sys
import os.path
import re

def sort_diagnostic(path):
	path = os.path.realpath(path)
	with open(path, encoding='utf-8') as fd:
		lines = fd.read().splitlines()

	diag_map = {}
	diag = None
	key = ''
	root_dir = os.path.split(path)[0]
	root_dir = path[:len(root_dir) + 1]
	for line in lines:
		if m := re.match(r'(.+?):(\d+):(\d+):', line):
			source, lineno, column = m.group(1, 2, 3)
			key = 'trace'
			check = ''
			if line[-1] == ']':
				end = m.end(0)
				start = line.rfind('[', end)
				if start > 0:
					check = line[start:]
			line = line.removeprefix(root_dir)
			if check:
				if diag:
					head = diag['head']
					if head in diag_map:
						diag_map[head]['count'] += 1
					else:
						diag_map[head] = diag

				key = 'detail'
				diag = {
					'head': line, 'file': source, 'line': int(lineno), 'column': int(column),
					'check': check, 'count': 1, 'detail': [], 'trace': [],
				}
				continue

		if diag:
			diag[key].append(line)

	if diag:
		head = diag['head']
		if head in diag_map:
			diag_map[head]['count'] += 1
		else:
			diag_map[head] = diag

	diag_list = sorted(diag_map.values(), key=lambda m: (m['file'], m['line'], m['column']))
	diag_map = {}
	output = []
	indent = ' '*2
	for diag in diag_list:
		check = diag['check']
		count = diag['count']
		if check in diag_map:
			diag_map[check]['count'] += count
			diag_map[check]['diag'].append(diag)
		else:
			diag_map[check] = {'check': check, 'count': count, 'diag': [diag]}
		output.append(f'{diag["head"]} {count}')
		output.extend(diag["detail"])
		if trace := diag['trace']:
			trace = [f'{indent}{line}' for line in trace]
			diag['trace'] = trace
			output.extend(trace)

	items = sorted(diag_map.values(), key=lambda m: (len(m['diag']), m['count'], m['check']))
	print(f'diagnostic: {len(diag_list)} / {len(items)} {path}')
	output.append('')
	base, ext = os.path.splitext(path)
	path = f'{base}-file{ext}'
	print(f'write: {path}')
	with open(path, 'w', encoding='utf-8') as fd:
		fd.write('\n'.join(output))

	output = []
	for item in items:
		diag_list = item['diag']
		output.append(f'{item["check"]} {item["count"]} / {len(diag_list)}')
		for diag in diag_list:
			output.append(f'{indent}{diag["head"]} {count}')
			if detail := diag['detail']:
				detail = [f'{indent}{line}' for line in detail]
				output.extend(detail)
			if trace := diag['trace']:
				trace = [f'{indent}{line}' for line in trace]
				output.extend(trace)

	output.append('')
	path = f'{base}-count{ext}'
	print(f'write: {path}')
	with open(path, 'w', encoding='utf-8') as fd:
		fd.write('\n'.join(output))

if __name__ == '__main__':
	if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
		sort_diagnostic(sys.argv[1])
	else:
		print(f'Usage: {os.path.basename(sys.argv[0])} path')
