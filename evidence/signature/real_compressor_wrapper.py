#!/usr/bin/env python3
"""Exec a real compressor. Optionally cap only its output or kill at a size mark.
No fabricated compressor exits/errors. RLIMIT_FSIZE uses the same kernel limit
as bash ulimit -f; ignoring SIGXFSZ is necessary to reach write() -> EFBIG.
"""
import json, os, resource, signal, sys, time
from pathlib import Path
real = os.environ['SIGNATURE_REAL']
mode = os.environ['SIGNATURE_MODE']
args = sys.argv[1:]
input_path = Path(args[-1]); output = Path(str(input_path)+'.gz')
resource.setrlimit(resource.RLIMIT_CORE, (0,0))
# Make disposition explicit rather than inheriting shell/Python defaults.
for signum in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP,signal.SIGXFSZ]:
    signal.signal(signum,signal.SIG_DFL)
if mode in ('efbig','fsize-signal'):
    cap = int(os.environ['SIGNATURE_CAP'])
    resource.setrlimit(resource.RLIMIT_FSIZE,(cap,cap))
    if mode == 'efbig': signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
if mode in ('sigkill','sigint','sigterm','sighup'):
    pid = os.getpid(); mark = int(os.environ['SIGNATURE_MARK'])
    signum = {'sigkill':signal.SIGKILL,'sigint':signal.SIGINT,
              'sigterm':signal.SIGTERM,'sighup':signal.SIGHUP}[mode]
    watcher = os.fork()
    if watcher == 0:
        begin = time.monotonic(); rec = {'pid':pid,'signal':int(signum),'threshold_bytes':mark}
        try:
            while time.monotonic()-begin < 120:
                try: size = output.stat().st_size
                except FileNotFoundError: size = 0
                if size >= mark:
                    rec.update(observed_bytes_before_signal=size,elapsed_since_watcher_s=time.monotonic()-begin)
                    os.kill(pid,signum)
                    rec['signal_sent'] = True
                    break
                # pid becomes reaped only by its original parent; check existence too.
                os.kill(pid,0)
                time.sleep(.0005)
            else: rec['timeout'] = True
        except ProcessLookupError: rec['process_gone_before_signal'] = True
        Path(os.environ['SIGNATURE_WATCH']).write_text(json.dumps(rec,indent=2)+'\n')
        os._exit(0)
os.execv(real,[real,*args])
