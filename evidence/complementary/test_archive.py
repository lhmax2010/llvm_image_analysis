#!/usr/bin/env python3
"""Rootless regression of only archive.py on the verified HQ dependency stack."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
assert os.geteuid() != 0
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
logs = []
mic = types.ModuleType('mic')
msger = types.ModuleType('mic.msger')
for level in ['info', 'warning', 'raw']:
    setattr(msger, level, lambda msg, level=level: logs.append({'level': level, 'message': msg}))
msger.error = lambda msg: (_ for _ in ()).throw(RuntimeError(msg))
errors_spec = importlib.util.spec_from_file_location('mic.utils.errors',
    ROOT / 'work/hq-validation/mic-2.1.3-integrated/mic/utils/errors.py')
errors = importlib.util.module_from_spec(errors_spec)
errors_spec.loader.exec_module(errors)
CreatorError = errors.CreatorError
mic.msger = msger
utils = types.ModuleType('mic.utils')
misc = types.ModuleType('mic.utils.misc')
# Avoid HQ's recursive du of real /var/tmp; only diagnostics is replaced.
misc.show_tar_diagnostics = lambda path: logs.append({'level': 'info', 'message': 'HQ diagnostics stub: ' + path})
utils.misc = misc
for name, module in [('mic', mic), ('mic.msger', msger), ('mic.utils.errors', errors),
                     ('mic.utils', utils), ('mic.utils.misc', misc)]:
    sys.modules[name] = module
source = ROOT / 'work/hq-validation/mic-2.1.3-integrated/mic/archive.py'
spec = importlib.util.spec_from_file_location('mic.archive', source)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)
old_path = os.environ['PATH']
results = []
work = ROOT / 'work/complementary'
work.mkdir(exist_ok=True)


def fake(directory, binary, mode):
    path = directory / binary
    if mode == 'failure':
        body = "import sys\nsys.stderr.write('write failed: No space left on device\\n  trailing spaces  \\n')\nsys.exit(1)\n"
    elif mode == 'kill':
        body = "import os,signal,sys\nopen(sys.argv[-1]+'.gz','wb').write(b'partial')\nsys.stderr.write('before injected SIGKILL\\n');sys.stderr.flush()\nos.kill(os.getpid(),signal.SIGKILL)\n"
    else:
        raise ValueError(mode)
    path.write_text('#!/usr/bin/python3\n' + body)
    path.chmod(0o755)


with tempfile.TemporaryDirectory(dir=work) as temp:
    case_root = Path(temp)
    for binary, func in [('gzip', archive._do_gzip), ('pigz', archive._do_gzip),
                         ('bzip2', archive._do_bzip2), ('zstd', archive._do_zstd),
                         ('lzop', archive._do_lzop)]:
        for compression in [True, False]:
            for mode, expected in [('failure', 1), ('kill', -9)]:
                case = case_root / (binary + str(compression) + mode)
                case.mkdir()
                fake(case, binary, mode)
                # Only this fake tool is discoverable; tar is not involved here.
                os.environ['PATH'] = str(case)
                filename = case / ('input.tar' if compression else 'input.tar.gz')
                filename.write_bytes(b'input data')
                before = len(logs)
                try:
                    func(str(filename), compression)
                except CreatorError as error:
                    assert 'rc=' + str(expected) in str(error), str(error)
                    assert binary in str(error)
                else:
                    raise AssertionError('Compression/decompression should fail')
                entries = logs[before:]
                raw = [x['message'] for x in entries if x['level'] == 'raw']
                expected_stderr = ('write failed: No space left on device\n  trailing spaces  \n'
                                   if mode == 'failure' else 'before injected SIGKILL\n')
                assert expected_stderr in raw, raw
                disklogs = [x for x in entries if 'Before compression:' in x['message']]
                assert bool(disklogs) == compression
                if compression:
                    assert 'input_bytes=10' in disklogs[0]['message']
                    assert 'free_bytes=' in disklogs[0]['message']
                results.append({'case': binary + ('-compress-' if compression else '-decompress-') + mode,
                                'expected_rc': expected, 'exception': 'CreatorError',
                                'raw_stderr_exact': True, 'disk_log': bool(disklogs)})
    os.environ['PATH'] = old_path
    # Real gzip roundtrip and API compatibility with HQ's return tuple.
    folder = case_root / 'normal'
    folder.mkdir()
    plain = folder / 'data.bin'
    original = os.urandom(256 * 1024)
    plain.write_bytes(original)
    packed = archive._do_gzip(str(plain), True)
    restored = archive._do_gzip(packed, False)
    assert Path(restored).read_bytes() == original
    results.append({'case': 'real-gzip-roundtrip', 'passed': True})
    # Successful dual-stream output preserves the HQ return tuple.
    rc, out, err = archive._call_external(['/usr/bin/python3', '-c',
                                         "import sys;sys.stdout.write('ok');sys.stderr.write('success diagnostic')"])
    assert rc == 0 and out == b'oksuccess diagnostic' and err == b'success diagnostic'
    results.append({'case': 'success-return-tuple', 'passed': True})
    # Fake tar rejects -S; delegate plain tar to the real executable.
    fallback = case_root / 'fallback'
    fallback.mkdir()
    tar = fallback / 'tar'
    tar.write_text("#!/usr/bin/python3\nimport os,sys\nif '-S' in sys.argv:\n sys.stderr.write('unsupported -S\\n');sys.exit(2)\nos.execv('/usr/bin/tar',['tar']+sys.argv[1:])\n")
    tar.chmod(0o755)
    os.environ['PATH'] = str(fallback) + os.pathsep + old_path
    src = fallback / 'source'
    src.mkdir()
    (src / 'item').write_text('archive item')
    target = fallback / 'result.tar.gz'
    assert archive._make_tarball(str(target), str(src), archive._do_gzip, sparse=True)
    with tarfile.open(target) as tf:
        assert tf.extractfile('item').read() == b'archive item'
    assert any('falling back' in x['message'] for x in logs)
    results.append({'case': 'HQ-sparse-fallback-preserved', 'passed': True})
    # Real sparse tar -S roundtrip, no mounts or images.
    os.environ['PATH'] = old_path
    tiny = case_root / 'sparse-input'
    tiny.mkdir()
    member = tiny / 'member.bin'
    with member.open('wb') as stream:
        stream.truncate(8 * 1024 * 1024)
        stream.seek(4 * 1024 * 1024)
        stream.write(b'data at offset')
    target = case_root / 'sparse-result.tar.gz'
    archive._make_tarball(str(target), str(tiny), archive._do_gzip, sparse=True)
    restored = case_root / 'restored'
    restored.mkdir()
    subprocess.run(['/usr/bin/tar', '-xf', str(target), '-C', str(restored)], check=True)
    assert (restored / 'member.bin').read_bytes() == member.read_bytes()
    assert (restored / 'member.bin').stat().st_blocks * 512 < member.stat().st_size
    results.append({'case': 'real-sparse-gztar-roundtrip', 'passed': True})
    # Full HQ _make_tarball calls must stop before publishing on failure/kill.
    for mode in ['failure', 'kill']:
        broken = case_root / ('pack-' + mode)
        broken.mkdir()
        fake(broken, 'gzip', mode)
        os.environ['PATH'] = str(broken) + os.pathsep + '/usr/bin:/bin'
        target = broken / 'result.tar.gz'
        target.write_bytes(b'existing published archive')
        try:
            archive._make_tarball(str(target), str(src), archive._do_gzip, sparse=False)
        except CreatorError:
            pass
        else:
            raise AssertionError('Must stop before move')
        assert target.read_bytes() == b'existing published archive'
        results.append({'case': 'HQ-make-tarball-' + mode, 'existing_final_preserved': True})
    # Verify the unmodified Gerrit code already checks compressor rc/output.
    hq_spec = importlib.util.spec_from_file_location('mic.archive_hq',
        ROOT / 'downloads/src/hq_mic/mic/mic/archive.py')
    hq = importlib.util.module_from_spec(hq_spec)
    hq_spec.loader.exec_module(hq)
    for mode, expected in [('failure', 1), ('kill', -9)]:
        directory = case_root / ('unmodified-hq-' + mode)
        directory.mkdir()
        fake(directory, 'gzip', mode)
        os.environ['PATH'] = str(directory)
        filename = directory / 'input.tar'
        filename.write_bytes(b'input data')
        try:
            hq._do_gzip(str(filename), True)
        except OSError as err:
            assert 'exit code ' + str(expected) in str(err)
            assert ('No space left on device' if mode == 'failure' else 'before injected SIGKILL') in str(err)
        else:
            raise AssertionError('HQ already must check gzip failure')
        results.append({'case': 'unmodified-HQ-gzip-' + mode,
                        'exception': 'OSError', 'rc_and_output_present': True})
os.environ['PATH'] = old_path
(ROOT / 'evidence/complementary/results.json').write_text(json.dumps({'uid': os.geteuid(),
    'base': '2.1.3 + original3cc580e + c446578 + eadc8fd5 + complementary.patch',
    'cases': results, 'all_passed': True, 'limits': 'Only mic.msger and show_tar_diagnostics are stubbed; real subprocesses/real tar/gzip; no do_create/root/mount.'}, indent=2) + '\n')
(ROOT / 'evidence/complementary/messages.json').write_text(json.dumps(logs, indent=2) + '\n')
print('PASS:', len(results), 'rootless cases')
