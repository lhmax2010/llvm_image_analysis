"""压缩器资源量级探针；不是 mic 镜像基线。"""
from pathlib import Path
import os,subprocess,time,json,re
R=Path(__file__).resolve().parents[1]; D=R/'work/compressor-probe'; D.mkdir(exist_ok=True)
with (D/'random.bin').open('wb') as f:
 for _ in range(64): f.write(os.urandom(1024*1024))
records=[]
for name,cmd in [('gzip',['/usr/bin/gzip','-c']),('pigz-default',[str(R/'work/pigz-src/pigz-2.8/pigz'),'-c']),('pigz-p2',[str(R/'work/pigz-src/pigz-2.8/pigz'),'-p','2','-c'])]:
 argv=['/usr/bin/time','-v']+cmd+[str(D/'random.bin')]; t=time.monotonic()
 with (D/f'{name}.gz').open('wb') as output:
  p=subprocess.run(argv,stdout=output,stderr=subprocess.PIPE,text=True)
 elapsed=time.monotonic()-t
 (R/'evidence'/f'compressor-{name}.time.txt').write_text(p.stderr)
 records.append(dict(command=argv,rc=p.returncode,elapsed_s=elapsed,max_rss_kib=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',p.stderr)[1]),input_bytes=(D/'random.bin').stat().st_size,output_bytes=(D/f'{name}.gz').stat().st_size))
(R/'evidence/compressor_probe.json').write_text(json.dumps(dict(cpu_count=os.cpu_count(),affinity_cpus=len(os.sched_getaffinity(0)),results=records),ensure_ascii=False,indent=2))
print((R/'evidence/compressor_probe.json').read_text())
