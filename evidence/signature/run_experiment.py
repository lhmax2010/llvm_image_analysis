#!/usr/bin/env python3
"""Non-root real compressor and unchanged mic archive signature experiments."""
from pathlib import Path
import contextlib, hashlib, io, json, os, shutil, subprocess, sys, time, traceback
ROOT = Path(__file__).resolve().parents[2]
E = ROOT/'evidence/signature'; W = ROOT/'work/signature'
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['TMPDIR']=str(W/'python-tmp')
(W/'python-tmp').mkdir(parents=True,exist_ok=True)
assert os.geteuid()!=0, 'Must run as ordinary user'
assert shutil.disk_usage(W).free > 15_000_000_000
COMPRESSORS={'gzip':Path('/usr/bin/gzip'),'pigz':ROOT/'work/pigz-src/pigz-2.8/pigz'}
CAP=102_400_000  # bash ulimit -f 100000 with bash's 1024-byte blocks (no POSIXLY_CORRECT)
MODES=['normal','efbig','fsize-signal','sigkill']
if len(sys.argv)>1 and sys.argv[1]=='mic-child':
    compressor,mode=sys.argv[2:4]; d=W/f'mic-{compressor}-{mode}'
    sys.path.insert(0,str(ROOT/'downloads/src/mic'))
    from mic import archive,msger
    msger.set_logfile(str(E/f'mic-{compressor}-{mode}.mic.log'))
    original=archive._call_external; calls=[]
    def record_call(argv):
        before=time.monotonic(); raw=original(argv)
        rec={'argv':argv,'rc':raw[0],'combined_stdout_stderr':raw[1].decode(errors='replace'),
             'separate_stderr':raw[2],'elapsed_s':time.monotonic()-before}
        if argv[0] in ('gzip','pigz'):
            output=Path(str(argv[-1])+'.gz')
            rec.update(output_before_move_exists=output.exists(),
                       output_before_move_bytes=output.stat().st_size if output.exists() else None)
        calls.append(rec)
        return raw # observe only; do NOT change archive's error handling
    archive._call_external=record_call
    output=d/'final.tar.gz'; before=time.monotonic()
    result={'compressor':compressor,'mode':mode,'layer':'mic','calls':calls}
    try:
        result['make_tarball_return']=archive._make_tarball(str(output),str(W/'input'),archive._do_gzip)
    except Exception as exc:
        result.update(exception_type=type(exc).__name__,exception=str(exc),traceback=traceback.format_exc())
        traceback.print_exc()
    result.update(elapsed_s=time.monotonic()-before,output_exists=output.exists(),
                  output_bytes=output.stat().st_size if output.exists() else None)
    (E/f'mic-{compressor}-{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    sys.exit(0)

# A unique run directory avoids overwriting evidence or reusing previous half-files.
assert not (E/'results.json').exists(), 'Existing experiment evidence: do not overwrite'
(W/'input').mkdir(exist_ok=True)
payload=W/'input/payload.bin'
assert not payload.exists()
with payload.open('xb') as f:
    remaining=300_000_000
    while remaining:
        n=min(1_048_576,remaining); f.write(os.urandom(n)); remaining-=n
source_tar=W/'random.tar'
subprocess.run(['/usr/bin/tar','-C',str(W/'input'),'-cf',str(source_tar),'payload.bin'],check=True)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while data:=f.read(1_048_576):h.update(data)
    return h.hexdigest()
manifest={'uid':os.getuid(),'payload_bytes':payload.stat().st_size,'payload_sha256':digest(payload),
          'tar_bytes':source_tar.stat().st_size,'tar_sha256':digest(source_tar),'file_limit_bytes':CAP,
          'versions':{k:subprocess.check_output([str(v),'--version'],text=True).splitlines()[0] for k,v in COMPRESSORS.items()},
          'binary_sha256':{k:digest(v) for k,v in COMPRESSORS.items()}, 'cases':[]}
# Bash itself verifies the numeric conversion without running compression or privilege tools.
manifest['ulimit_equivalent']=subprocess.check_output(['bash','-c','ulimit -f 100000; ulimit -f; python3 -c "import resource; print(resource.getrlimit(resource.RLIMIT_FSIZE))"'],text=True,env={k:v for k,v in os.environ.items() if k!='POSIXLY_CORRECT'})
(E/'input.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
wrapper=(E/'real_compressor_wrapper.py'); wrapper.chmod(0o755)
results=[]; expected={}
def setup(layer,comp,mode):
    d=W/f'{layer}-{comp}-{mode}'; (d/'bin').mkdir(parents=True)
    (d/'bin'/comp).symlink_to(wrapper)
    # PATH contains only this true compressor wrapper and GNU tar, so gzip's
    # mic path cannot accidentally choose an unrelated installed pigz.
    (d/'bin'/'tar').symlink_to('/usr/bin/tar')
    mark=int(expected.get(comp,source_tar.stat().st_size)*.5)
    if mode in ('sigint','sigterm','sighup'): mark=32_000_000
    env={**os.environ,'PATH':str(d/'bin'),'SIGNATURE_REAL':str(COMPRESSORS[comp]),
         'SIGNATURE_MODE':mode,'SIGNATURE_CAP':str(CAP),'SIGNATURE_MARK':str(mark),
         'SIGNATURE_WATCH':str(E/f'{layer}-{comp}-{mode}.watch.json')}
    # #!/usr/bin/env python3 in wrapper needs its interpreter in the restricted PATH.
    (d/'bin'/'python3').symlink_to(sys.executable)
    return d,env

def integrity(path):
    if not path.exists():return None
    check=subprocess.run(['/usr/bin/gzip','-t',str(path)],capture_output=True,text=True)
    return {'argv':['/usr/bin/gzip','-t',str(path)],'rc':check.returncode,'stderr':check.stderr}
for comp in COMPRESSORS:
    for mode in MODES+['sigint','sigterm','sighup']:
        d,env=setup('direct',comp,mode); inp=d/'input.tar';shutil.copyfile(source_tar,inp)
        cmd=[str(d/'bin'/comp),'-f',str(inp)]; t=time.monotonic()
        proc=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120)
        out=Path(str(inp)+'.gz')
        result={'layer':'direct','compressor':comp,'mode':mode,'command':cmd,'pid_is_real_compressor_after_exec':True,
            'rc':proc.returncode,'shell_equivalent_rc':128-proc.returncode if proc.returncode<0 else proc.returncode,
            'elapsed_s':time.monotonic()-t,'stdout':proc.stdout,'stderr':proc.stderr,
            'output_exists':out.exists(),'output_bytes':out.stat().st_size if out.exists() else None,
            'input_exists':inp.exists(),'integrity':integrity(out)}
        if mode=='normal':expected[comp]=result['output_bytes']
        (E/f'direct-{comp}-{mode}.stderr.txt').write_text(proc.stderr)
        (E/f'direct-{comp}-{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        results.append(result);print(comp,mode,proc.returncode,'exists',out.exists(),flush=True)
    for mode in MODES:
        d,env=setup('mic',comp,mode)
        with (E/f'mic-{comp}-{mode}.console.log').open('w') as out:
            proc=subprocess.run([sys.executable,__file__,'mic-child',comp,mode],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=120)
        assert proc.returncode==0
        result=json.loads((E/f'mic-{comp}-{mode}.json').read_text())
        result['integrity']=integrity(d/'final.tar.gz')
        (E/f'mic-{comp}-{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        results.append(result); print('mic',comp,mode,result.get('exception_type',result.get('make_tarball_return')),flush=True)
(E/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('Completed',len(results),'real-compressor cases',flush=True)
