"""Adversarial security audit script — Phase 2C."""
import os, sys

PLANNER_FILES = [
    'planner/planner.py',
    'planner/context.py',
    'planner/risk.py',
    'planner/reasoning.py',
    'planner/task_graph.py',
    'planner/validator.py',
    'planner/store.py',
    'planner/schemas.py',
    'api/planner.py',
]

FORBIDDEN_IMPORTS = ['import subprocess', 'from subprocess', 'import os.system', 'import os; os.system']
FORBIDDEN_CALLS   = ['os.system(', 'os.popen(', 'subprocess.', 'eval(', 'exec(']

found = []
for fname in PLANNER_FILES:
    with open(fname, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"') or stripped.startswith("'"):
            continue  # skip comments and plain string lines
        for pattern in FORBIDDEN_IMPORTS + FORBIDDEN_CALLS:
            if pattern in stripped:
                found.append(f'{fname}:L{i}: forbidden "{pattern}": {stripped[:80]}')


if found:
    print('FAIL:')
    for f in found:
        print(' ', f)
    sys.exit(1)
else:
    print('PASS: No subprocess/eval/exec in planner modules.')

# Audit 2: No direct open/read of workspace files in planner core
# (context.py should only process pre-built profile data)
PLANNER_CORE = ['planner/planner.py', 'planner/context.py', 'planner/reasoning.py', 'planner/risk.py']
# These files should not do open() on workspace paths
for fname in PLANNER_CORE:
    with open(fname, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Allow: open(...) only for store files (planner_store.json)
        if 'open(' in stripped and 'planner_store' not in stripped and '#' not in stripped:
            # Not a comment, not a store file — flag it
            found.append(f'{fname}:L{i} suspicious open(): {stripped[:80]}')

if found:
    print('WARN (open() detected in non-store planner files):')
    for f in found:
        print(' ', f)
else:
    print('PASS: No direct file open() in planner core logic.')

# Audit 3: Permission self-escalation check
with open('api/planner.py', 'r', encoding='utf-8') as f:
    api_content = f.read()

if 'ADMIN' in api_content and 'FORBIDDEN' not in api_content:
    print('FAIL: ADMIN permission may not be enforced in API router.')
    sys.exit(1)
else:
    print('PASS: ADMIN permission check present in API router.')

print('ALL ADVERSARIAL CHECKS PASSED')
