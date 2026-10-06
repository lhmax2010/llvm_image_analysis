"""无需 root 的原始打包代码探针；不等价于真实 ENOSPC/OOM。"""
import pathlib,os,sys,json,time,traceback,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)==1:
 records=[]
 for mode in ['exit1','sigkill']:
  with (R/'evidence'/f'original-{mode}-console.log').open('w') as f:
   subprocess.run([sys.executable,__file__,mode],stdout=f,stderr=f,check=True)
  records.append(json.loads((R/'evidence'/f'original-{mode}.json').read_text()))
 (R/'evidence/original_archive_probe.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 print(json.dumps(records,ensure_ascii=False,indent=2)); sys.exit(0)
sys.path.insert(0,str(R/'downloads/src/mic'))
from mic import archive,msger
mode=sys.argv[1]
script={'exit1':'#!/bin/sh\necho "gzip: simulated write failure: No space left on device" >&2\nexit 1\n','sigkill':'#!/bin/sh\nkill -KILL $$\n'}[mode]
d=R/'work/original-probe'/mode
(d/'bin').mkdir(parents=True,exist_ok=True); (d/'input').mkdir(exist_ok=True)
(d/'input/rootfs.img').write_bytes(b'probe\n'*1024)
(d/'bin/gzip').write_text(script); (d/'bin/gzip').chmod(0o755)
os.environ['PATH']=str(d/'bin')+':'+os.environ['PATH']
msger.set_logfile(str(R/'evidence'/f'original-{mode}-mic.log'))
t=time.monotonic()
raw=archive._call_external(['gzip','-f',str(d/'input/rootfs.img')])
rec={'mode':mode,'raw_returncode':raw[0],'raw_stdout':raw[1].decode(),'raw_stderr':raw[2]}
try: archive.packing(str(d/'output.tar.gz'),str(d/'input'))
except Exception as e:
 rec['exception']=repr(e); rec['traceback']=traceback.format_exc()
 # 模拟未捕获 Python 异常：traceback 只输出控制台，不主动调用 msger。
 print(rec['traceback'],file=sys.stderr)
rec['elapsed_s']=time.monotonic()-t
rec['mic_log']=(R/'evidence'/f'original-{mode}-mic.log').read_text()
(R/'evidence'/f'original-{mode}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2))
