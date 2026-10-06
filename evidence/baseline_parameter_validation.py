#!/usr/bin/env python3
"""Read-only: stop the real mic entry point immediately after argparse succeeds.
Never import the selected cmd_create module or run docs/need_sudo.sh.
Artifacts stay below the analysis root; the original baseline is preserved.
"""
from pathlib import Path
import contextlib, hashlib, io, json, os, runpy, shlex, subprocess, sys
ROOT = Path(__file__).resolve().parents[1]
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
os.environ['TMPDIR'] = str(ROOT / 'work/tmp')
sys.path.insert(0, str(ROOT / 'work/tools/usr/lib/python3/dist-packages'))
MIC = ROOT / 'work/tools/usr/bin/mic'
SOURCE = ROOT / 'downloads/src/mic/tools/mic'
assert MIC.read_bytes() == SOURCE.read_bytes(), 'installed/source parser differs'
old = shlex.split((ROOT / 'evidence/baseline-20261006-211839-command.txt').read_text())
# Replay the preserved stage2a assignment; the current script now uses a
# different launcher with early global-config handling (stage2a2).
cmd_line = json.loads((ROOT / 'evidence/baseline-command-validation.json').read_text())['cmd_assignment']
variables = dict(ROOT=str(ROOT), MIC_PY='/usr/bin/python3', MIC_BIN=str(MIC),
    KS=str(ROOT/'downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks'),
    CONF=str(ROOT/'work/mic-baseline-20261006-211839.conf'),
    PREFIX=str(ROOT/'evidence/baseline-20261006-211839'), OUT=str(ROOT/'work/base'),
    RELEASE='tizen-unified-toolchain_20260917.132101')
script = '\n'.join(f'{k}={shlex.quote(v)}' for k,v in variables.items()) + '\n' + cmd_line + '\nprintf "%s\\0" "${CMD[@]}"\n'
new = subprocess.check_output(['bash','-c',script], cwd=ROOT).decode().rstrip('\0').split('\0')
(ROOT/'evidence/baseline-command-fixed.txt').write_text(shlex.join(new)+'\n')
record = {'scope':'argparse and --help only; no sudo, cmd_create import, or image build',
          'parser_sha256':hashlib.sha256(MIC.read_bytes()).hexdigest(), 'cmd_assignment':cmd_line}
class ParsedOnly(Exception): pass
capture = io.StringIO()
with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
    module = runpy.run_path(str(MIC), run_name='mic_parser_read_only')
    Parser = module['ArgumentParser']; original = Parser.parse_args
    def parse_then_stop(parser, *args, **kwargs):
        result = original(parser, *args, **kwargs)
        record['parsed'] = vars(result)
        raise ParsedOnly()
    Parser.parse_args = parse_then_stop
    try:
        try: module['main'](old[1:].copy())
        except SystemExit as exc: record['old_parse_exit'] = exc.code
        try: module['main'](new[1:].copy())
        except ParsedOnly: record['fixed_parse'] = 'accepted; stopped immediately after parsing'
    finally: Parser.parse_args = original
assert record['old_parse_exit'] == 2
assert record['fixed_parse'].startswith('accepted')
assert record['parsed']['config'] == variables['CONF']
assert record['parsed']['release'] == variables['RELEASE']
assert record['parsed']['subcommand'] == 'auto'
assert record['parsed']['module'] == 'cmd_create'
assert 'mic.cmd_create' not in sys.modules
record['cmd_create_imported'] = False
# Child parser defaults interactive=True; mic.main overrides to False when it sees
# the global --non-interactive option after parse_args (source lines 298-300).
record['non_interactive'] = 'recognized globally; mic.main subsequently sets args.interactive=False'
help_result = subprocess.run(new + ['--help'], cwd=ROOT, capture_output=True, text=True,
    env={**os.environ, 'PYTHONPATH': str(ROOT/'work/tools/usr/lib/python3/dist-packages')})
record['help_exit'] = help_result.returncode
assert help_result.returncode == 0
(ROOT/'evidence/baseline-command-help.txt').write_text(help_result.stdout+help_result.stderr)
(ROOT/'evidence/baseline-command-parser-console.txt').write_text(capture.getvalue())
(ROOT/'evidence/baseline-command-validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
