#!/usr/bin/env python3
"""Read-only HQ CLI and KS parser tests; never call mic main/do_create."""
import argparse
import ast
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'downloads/src/hq_mic/mic'
sys.dont_write_bytecode = True
node = next(n for n in ast.parse((SRC/'tools/mic').read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == 'create_parser')
node.decorator_list = []
namespace = {'ArgumentParser': argparse.ArgumentParser, 'SUPPRESS': argparse.SUPPRESS}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SRC/'tools/mic'), 'exec'), namespace)
parser = argparse.ArgumentParser()
namespace['create_parser'](parser)
cli_results = []
for mode in ['auto', 'loop', 'raw', 'fs']:
    for enabled in [False, True]:
        args = parser.parse_args([mode, 'unused.ks'] + (['--sparse-tar'] if enabled else []))
        assert args.sparse_tar is enabled
        cli_results.append({'imager': mode, 'option_present': enabled, 'sparse_tar': args.sparse_tar})
sys.path.insert(0, str(SRC/'mic/3rdparty'))
spec = importlib.util.spec_from_file_location('hq_micboot', SRC/'mic/kickstart/custom_commands/micboot.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ks_results = []
for enabled in [False, True]:
    command = module.Mic_Bootloader()
    command.parse(['--sparse-tar'] if enabled else [])
    assert command.sparse_tar is enabled
    assert ('--sparse-tar' in command._getArgsAsStr()) is enabled
    ks_results.append({'option_present': enabled, 'sparse_tar': command.sparse_tar,
                       'serialized_option_present': '--sparse-tar' in command._getArgsAsStr()})
results = {'CLI': cli_results, 'KS': ks_results,
           'limits': 'Actual create_parser function without decorator; actual Mic_Bootloader/vendored pykickstart. No mic main, plugin, ConfigMgr full load or image creator execution.'}
(ROOT/'evidence/hq/parser-results.json').write_text(json.dumps(results, indent=2)+'\n')
print('PASS: 8 CLI cases, 2 KS parse/serialize cases')
