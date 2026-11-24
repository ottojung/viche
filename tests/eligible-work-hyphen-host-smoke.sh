#!/bin/sh
# Regression: explicit() and _eligible_item accept hyphenated Execution-Host form.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
python3 - <<'PY' "$repo"
import importlib.util, sys
spec = importlib.util.spec_from_file_location('ew', sys.argv[1] + '/government/eligible-work.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# hyphenated Execution-Host in issue body (explicit)
assert m.explicit('Execution-Host: billy-dev')
assert m.explicit('execution-host: billy-dev')
assert m.explicit('Execution Target: billy-dev')
# _eligible_item: Founder comment with hyphenated execution-host prefix
issue = {'body': '', 'messages': [{'author': 'Vitalik', 'body': 'Execution-Host: billy-dev\nPlease proceed.'}]}
row = {'number': 'X1', 'title': 'T'}
item = m._eligible_item(row, issue)
assert item and item['number'] == 'X1', item
# hyphenated in body
issue2 = {'body': 'Execution-Host: billy-dev', 'messages': []}
item2 = m._eligible_item({'number': 'X2', 'title': 'T2'}, issue2)
assert item2 and item2['number'] == 'X2', item2
# negative control
assert not m.explicit('Execution-Host: somewhere-else')
print('eligible-work hyphen host smoke passed')
PY
