#!/usr/bin/env python3
"""待复现使用：每5秒采样；本轮sudo失败后未执行。"""
import argparse,csv,datetime,json,pathlib,subprocess,time
p=argparse.ArgumentParser()
p.add_argument('--workdir',required=True); p.add_argument('--outdir',required=True); p.add_argument('--csv',required=True)
a=p.parse_args()
def cmd(args):
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return {'rc':r.returncode,'output':r.stdout}
with pathlib.Path(a.csv).open('x',newline='') as f:
 w=csv.writer(f); w.writerow(['time','work_df','output_df','free_m','process_rss_kib','work_allocated_bytes'])
 while True:
  started=time.monotonic()
  ps=cmd(['ps','-eo','pid,ppid,comm,rss,args'])['output'].splitlines()
  selected=[]
  for line in ps[1:]:
   fields=line.split(None,4)
   if len(fields)==5 and (fields[2] in ['gzip','pigz','mic','tar'] or (fields[2].startswith('python') and '/mic' in fields[4])):
    selected.append({'pid':int(fields[0]),'ppid':int(fields[1]),'comm':fields[2],'rss_kib':int(fields[3]),'args':fields[4]})
  row=[datetime.datetime.now(datetime.timezone.utc).isoformat(),cmd(['df','-B1',a.workdir]),cmd(['df','-B1',a.outdir]),cmd(['free','-m']),selected,cmd(['du','-s','-B1',a.workdir])]
  w.writerow([row[0]]+[json.dumps(x,ensure_ascii=False) for x in row[1:]]); f.flush()
  time.sleep(max(0,5-(time.monotonic()-started)))
