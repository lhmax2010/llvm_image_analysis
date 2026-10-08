#!/usr/bin/env python3
"""Rootless ext4-file sparse archive experiment; all artifacts in workspace."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/sparse'
EVIDENCE = ROOT / 'evidence/sparse'
WORK.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
assert os.geteuid() != 0
results = {'report_date': '2026-10-08', 'uid': os.geteuid(), 'commands': []}


def run(argv, label):
    start = time.monotonic()
    proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          cwd=WORK, check=False)
    elapsed = time.monotonic() - start
    (EVIDENCE / (label + '.log')).write_bytes(proc.stdout)
    record = {'argv': list(map(str, argv)), 'rc': proc.returncode, 'seconds': elapsed,
              'output': 'evidence/sparse/' + label + '.log'}
    results['commands'].append(record)
    print(json.dumps(record), flush=True)
    if proc.returncode:
        raise RuntimeError(record)
    return record


def stat(path):
    info = path.stat()
    return {'path': str(path.relative_to(ROOT)), 'logical_bytes': info.st_size,
            'allocated_bytes': info.st_blocks * 512}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


run(['tar', '--version'], 'tar-version')
run(['gzip', '--version'], 'gzip-version')
run(['df', '-B1', str(WORK)], 'df-before')
image = WORK / 'filesystem.img'
if image.exists():
    raise RuntimeError('Refusing to overwrite previous experiment image')
run(['truncate', '-s', '2147483648', str(image)], 'truncate')
run(['mkfs.ext4', '-F', '-E', 'lazy_itable_init=0,lazy_journal_init=0',
     str(image)], 'mkfs')
payload = WORK / 'random-payload.bin'
with payload.open('xb') as stream:
    for _ in range(600):
        stream.write(os.urandom(1024 * 1024))
results['payload'] = stat(payload)
run(['debugfs', '-w', '-R', 'write ' + str(payload) + ' /random-payload',
     str(image)], 'debugfs-write')
run(['debugfs', '-R', 'stat /random-payload', str(image)], 'debugfs-stat')
results['image'] = stat(image)
results['image']['sha256'] = digest(image)
results['variants'] = {}
for variant, extra in [('normal', []), ('sparse', ['-S'])]:
    tarpath = WORK / (variant + '.tar')
    run(['tar', *extra, '-C', str(WORK), '-cf', str(tarpath),
         '--', image.name], variant + '-tar')
    entry = {'tar': stat(tarpath)}
    run(['du', '-B1', str(tarpath)], variant + '-du')
    run(['tar', '-tvf', str(tarpath)], variant + '-list')
    with tarpath.open('rb') as stream:
        header = stream.read(512)
    entry['first_header_typeflag'] = header[156:157].decode('ascii')
    entry['first_header_size_oct'] = header[124:136].decode('ascii').strip('\x00 ')
    gzip_path = WORK / (variant + '.tar.gz')
    start = time.monotonic()
    with gzip_path.open('xb') as stream:
        proc = subprocess.run(['gzip', '-c', str(tarpath)], stdout=stream,
                              stderr=subprocess.PIPE, check=False)
    elapsed = time.monotonic() - start
    (EVIDENCE / (variant + '-gzip.log')).write_bytes(proc.stderr)
    results['commands'].append({'argv': ['gzip', '-c', str(tarpath)],
                                'stdout_file': str(gzip_path.relative_to(ROOT)),
                                'rc': proc.returncode, 'seconds': elapsed})
    assert proc.returncode == 0
    entry['gzip'] = stat(gzip_path)
    extractdir = WORK / ('extract-' + variant)
    extractdir.mkdir()
    run(['tar', '-xf', str(tarpath), '-C', str(extractdir)], variant + '-extract')
    restored = extractdir / image.name
    entry['extracted'] = stat(restored)
    entry['extracted']['sha256'] = digest(restored)
    assert entry['extracted']['sha256'] == results['image']['sha256']
    results['variants'][variant] = entry
    print(json.dumps({variant: entry}), flush=True)
run(['df', '-B1', str(WORK)], 'df-after')
(EVIDENCE / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
