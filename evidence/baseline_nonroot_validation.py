#!/usr/bin/env python3
"""Run the complete corrected baseline command as an ordinary user only."""
import configparser
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
assert os.geteuid() != 0, 'non-root validation must never run as root'
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['TMPDIR'] = str(ROOT / 'work/tmp')
variables = dict(ROOT=str(ROOT), MIC_PY='/usr/bin/python3',
    MIC_BIN=str(ROOT/'docs/mic_local.py'),
    CONF=str(ROOT/'work/mic-baseline-dryrun-nonroot.conf'),
    KS=str(ROOT/'downloads/logs/tizen-unified-toolchain_20260917.132101_tizen-headed-aarch64.ks'),
    RELEASE='tizen-unified-toolchain_20260917.132101',OUT=str(ROOT/'work/base'),
    PREFIX=str(ROOT/'evidence/baseline-dryrun-nonroot'))
conf = Path(variables['CONF'])
# Preserve both original attempts; use a separate local config with the same keys.
assert not conf.exists(), 'do not overwrite an earlier dry-run config'
conf.write_bytes((ROOT/'work/mic-baseline-20261006-214442.conf').read_bytes())
site = configparser.ConfigParser();site.read(conf)
plugin_dir = Path(site['common']['plugin_dir'])
if not (plugin_dir/'imager').is_dir():
    plugin_dir = ROOT/'downloads/src/mic/plugins'
    assert (plugin_dir/'imager').is_dir()
    site['common']['plugin_dir'] = str(plugin_dir)
    with conf.open('w') as stream: site.write(stream)
(ROOT/'evidence/baseline-dryrun-nonroot.conf.txt').write_bytes(conf.read_bytes())
cmd_assignment = next(s for s in (ROOT/'docs/need_sudo.sh').read_text().splitlines() if s.startswith('CMD=('))
script = '\n'.join(f'{k}={shlex.quote(v)}' for k,v in variables.items()) + '\n' + cmd_assignment + '\nprintf "%s\\0" "${CMD[@]}"\n'
cmd = subprocess.check_output(['bash','-c',script],cwd=ROOT).decode().rstrip('\0').split('\0')
(ROOT/'evidence/baseline-dryrun-nonroot-command.txt').write_text(shlex.join(cmd)+'\n')
env = {**os.environ, 'PYTHONPATH':str(ROOT/'work/tools/usr/lib/python3/dist-packages')}
# Verify the user's proposed global placement is unsupported by the original parser.
original_cmd = cmd.copy();original_cmd[1] = str(ROOT/'work/tools/usr/bin/mic')
raw = subprocess.run(original_cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
(ROOT/'evidence/baseline-original-global-c.log').write_text(raw.stdout+raw.stderr)
assert raw.returncode == 2 and 'invalid choice:' in raw.stderr
# Run the new local entry completely: no parse sentinel, no UID mocking.
with (ROOT/'evidence/baseline-dryrun-nonroot.log').open('w') as stream:
    trial = subprocess.run(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=30)
output = (ROOT/'evidence/baseline-dryrun-nonroot.log').read_text()
assert "Plugin dir is not a directory" not in output
assert "Can't support subcommand" not in output
assert 'Root permission is required, abort' in output
assert trial.returncode == 2
# The original nonroot guard occurs before get_plugins; verify actual loading
# separately without creating an image or changing the UID check.
capture = io.StringIO()
with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
    launcher = runpy.run_path(str(ROOT/'docs/mic_local.py'),run_name='mic_local_config_probe')
    forwarded,selected_conf = launcher['prepare'](cmd[2:])
    sys.path.insert(0,str(ROOT/'work/tools/usr/lib/python3/dist-packages'))
    from mic.conf import configmgr
    configmgr._siteconf = str(selected_conf)
    from mic.plugin import pluginmgr
    from mic import msger
    msger.set_loglevel('VERBOSE')
    plugins = pluginmgr.get_plugins('imager')
assert 'loop' in plugins and callable(plugins['loop'].do_create)
assert Path(pluginmgr.plugin_dir) == plugin_dir
for section in site.sections():
    assert section in configmgr.DEFAULTS
    for key in site[section]:
        assert key in configmgr.DEFAULTS[section],(section,key)
        value = getattr(configmgr,section)[key]
        if key == 'packages': assert value == ['mic-bootstrap-x86-arm']
        else: assert str(value) == site[section][key],(section,key,value)
(ROOT/'evidence/baseline-local-plugin-probe.log').write_text(capture.getvalue())
record = {'uid':os.getuid(),'euid':os.geteuid(),'command':cmd,'forwarded_original_argv':forwarded,
          'original_global_c_rc':raw.returncode,'nonroot_trial_rc':trial.returncode,
          'nonroot_guard_reached':True,'plugin_directory_warning':False,'unsupported_subcommand':False,
          'separate_actual_loop_plugin_load':True,'loaded_imager_plugins':sorted(plugins),
          'pluginmgr_plugin_dir':pluginmgr.plugin_dir,'config_sections':{s:dict(site[s]) for s in site.sections()},
          'config_keys_match_real_ConfigMgr_DEFAULTS':True,
          'upstream_entry_sha256':hashlib.sha256((ROOT/'work/tools/usr/bin/mic').read_bytes()).hexdigest(),
          'upstream_entry_unchanged':(ROOT/'work/tools/usr/bin/mic').read_bytes()==(ROOT/'downloads/src/mic/tools/mic').read_bytes(),
          'no_sudo_or_full_image':True,'root_guard_not_bypassed':True}
(ROOT/'evidence/baseline-dryrun-nonroot-result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
